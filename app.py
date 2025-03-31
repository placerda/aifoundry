import chainlit as cl
from chat_with_products import chat_with_products

# Global variables to keep conversation history and context.
# (For a production app you might want a session-specific storage)
conversation_history = []
conversation_context = {}

@cl.on_message
async def main(message: str):
    global conversation_history, conversation_context

    response_msg = cl.Message(content="")

    # Append the incoming user message to the conversation history.
    conversation_history.append({"role": "user", "content": message.content})

    # Call the chat_with_products function using the full history and current context.
    response = chat_with_products(messages=conversation_history, context=conversation_context)

    # Append the assistant's response to the history.
    conversation_history.append(response["message"])

    # Update the conversation context for future followup queries.
    conversation_context = response["context"]

    # Send the assistant's response back to the user.
    await response_msg.stream_token(response["message"]["content"])
    await response_msg.update()

    # await cl.Message(content=).send()
