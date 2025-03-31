import os
import json
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from the .env file.
load_dotenv()

from chat_with_products import chat_with_products

def evaluate_chat_with_products(query):
    """
    Call the chat_with_products function with the provided query and extract the response and context.
    """
    response = chat_with_products(messages=[{"role": "user", "content": query}])
    return {
        "response": response["message"].content, 
        "context": response["context"]["grounding_data"]
    }

def generate_eval_dataset(input_file: Path, output_file: Path):
    """
    Reads an input JSONL file, processes each query by invoking evaluate_chat_with_products,
    and writes out a new JSONL file with additional 'response' and 'context' fields.
    """
    with input_file.open("r", encoding="utf-8") as fin, output_file.open("w", encoding="utf-8") as fout:
        for line in fin:
            record = json.loads(line)
            query = record.get("query")
            if query:
                eval_result = evaluate_chat_with_products(query)
                record.update(eval_result)
            fout.write(json.dumps(record) + "\n")

if __name__ == "__main__":
    # Assuming ASSET_PATH is defined in config.py and points to the directory with chat_eval_data.jsonl
    from config import ASSET_PATH

    input_path = Path(ASSET_PATH) / "chat_eval_data.jsonl"
    output_path = Path("./output_dataset.jsonl")
    
    generate_eval_dataset(input_path, output_path)
    print(f"Evaluation dataset generated at: {output_path.resolve()}")
