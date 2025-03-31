import os
import pandas as pd
from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import ConnectionType
from azure.ai.evaluation import evaluate, GroundednessEvaluator
from azure.identity import DefaultAzureCredential
from chat_with_products import chat_with_products

# load environment variables from the .env file at the root of this repo
from dotenv import load_dotenv

load_dotenv()

# create a project client using environment variables loaded from the .env file
project = AIProjectClient.from_connection_string(
    conn_str=os.environ["AIPROJECT_CONNECTION_STRING"], 
    credential=DefaultAzureCredential()
)

connection = project.connections.get_default(
    connection_type=ConnectionType.AZURE_OPEN_AI, include_credentials=True
)

evaluator_model = {
    "azure_endpoint": connection.endpoint_url,
    "azure_deployment": os.environ["EVALUATION_MODEL"],
    "api_version": "2024-06-01",
    "api_key": connection.key,
}

groundedness = GroundednessEvaluator(evaluator_model)

# Custom evaluator implemented as a plain function.
def length_evaluator(query, response, context):
    # Ensure response is a string before evaluating its length.
    answer = response if isinstance(response, str) else ""
    score = 1 if len(answer) > 10 else 0
    return {"length_score": score}

def evaluate_chat_with_products(query):
    response = chat_with_products(messages=[{"role": "user", "content": query}])
    return {
        "response": response["message"].content, 
        "context": response["context"]["grounding_data"]
    }

# Evaluate must be called inside of __main__, not on import 
if __name__ == "__main__":
    from config import ASSET_PATH
    from pprint import pprint
    from pathlib import Path
    import multiprocessing
    import contextlib

    # workaround for multiprocessing issue on Linux
    with contextlib.suppress(RuntimeError):
        multiprocessing.set_start_method("spawn", force=True)


    from datetime import datetime

    evaluation_name = f"evaluate_chat_with_products_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    # run evaluation with a dataset and target function, log to the project
    result = evaluate(
        data=Path(ASSET_PATH) / "chat_eval_data.jsonl",
        target=evaluate_chat_with_products,
        evaluation_name=evaluation_name,
        evaluators={
            "groundedness": groundedness,
            "length": length_evaluator,
        },
        evaluator_config={
            "default": {
                "query": {"${data.query}"},
                "response": {"${target.response}"},
                "context": {"${target.context}"},
            }
        },
        azure_ai_project=project.scope,
        output_path="./myevalresults.json",
    )

    tabular_result = pd.DataFrame(result.get("rows"))

    pprint("-----Summarized Metrics-----")
    pprint(result["metrics"])
    pprint("-----Tabular Result-----")
    pprint(tabular_result)
    pprint(f"View evaluation results in AI Studio: {result['studio_url']}")
