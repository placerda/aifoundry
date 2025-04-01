import os
from pathlib import Path
from opentelemetry import trace
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
from config import ASSET_PATH, get_logger, enable_telemetry
from get_product_documents import get_product_documents


# initialize logging and tracing objects
logger = get_logger(__name__)
tracer = trace.get_tracer(__name__)

# create a project client using environment variables loaded from the .env file
project = AIProjectClient.from_connection_string(
    conn_str=os.environ["AIPROJECT_CONNECTION_STRING"], credential=DefaultAzureCredential()
)

# create a chat client we can use for testing
chat = project.inference.get_chat_completions_client()

from azure.ai.inference.prompts import PromptTemplate

import base64
def encode_image_to_base64(filepath: str) -> str:
    with open(filepath, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')
    
@tracer.start_as_current_span(name="chat_with_products")
def chat_with_products(messages_with_images: list, context: dict = None) -> dict:
    if context is None:
        context = {}

    documents = get_product_documents(messages_with_images, context)

    # do a grounded chat call using the search results
    grounded_chat_prompt = PromptTemplate.from_prompty(Path(ASSET_PATH) / "grounded_chat.prompty")
    messages = grounded_chat_prompt.create_messages(documents=documents, context=context)

    # create message content
    message_content = []

    for document in documents:
        filepath = document['imagepath']
        if filepath:
            image_base64 = encode_image_to_base64(filepath)
            image_content = {
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{image_base64}"
                }
            }
            message_content.append(image_content)

    messages_with_images =  {
            "role": "user",
            "content": message_content
        }
    

    messages.append(messages_with_images)

    openai_client = project.inference.get_azure_openai_client(api_version="2024-06-01")

    response = openai_client.chat.completions.create(
        model=os.environ["CHAT_MODEL"],
        messages=messages,
        max_tokens=512
    )

    # captions = response.choices[0].message.content
    # logger.debug(f"🧠 Captions: {captions}")


    # response = chat.complete(
    #     model=os.environ["CHAT_MODEL"],
    #     messages=system_message + messages,
    #     **grounded_chat_prompt.parameters,
    # )
    logger.info(f"💬 Response: {response.choices[0].message}")


    # Return a chat protocol compliant response
    return {"message": response.choices[0].message, "context": context}

if __name__ == "__main__":
    import argparse

    # load command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--query",
        type=str,
        help="Query to use to search product",
        default="I need a new tent for 4 people, what would you recommend?",
    )
    parser.add_argument(
        "--enable-telemetry",
        action="store_true",
        help="Enable sending telemetry back to the project",
    )
    args = parser.parse_args()
    if args.enable_telemetry:
        enable_telemetry(True)

    # run chat with products
    response = chat_with_products(messages_with_images=[{"role": "user", "content": args.query}])