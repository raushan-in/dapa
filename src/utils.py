"""
This module provides common utility functions for the DAPA application.
"""

from functools import wraps
from uuid import uuid4

import redis
from fastapi import HTTPException
from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    ChatMessage,
    HumanMessage,
    ToolMessage,
)
from langchain_core.runnables import RunnableConfig

from agent import cyber_guard
from schema import Chat, UserInput
from settings import settings

# Connect to Redis
redis_client = redis.StrictRedis.from_url(settings.REDIS_URL, decode_responses=True)


async def get_llm_response(user_input: UserInput):
    """
    Sends user input to the language model and retrieves the response.

    Parameters:
    - user_input: An instance of UserInput containing the user's message and optional thread ID and email.

    Returns:
    - The response from the language model.

    If the user provides an email, it is appended to the user message for context.
    The function uses the thread ID to maintain conversation context across multiple interactions.
    """
    thread_id = user_input.thread_id or str(uuid4())
    user_email = user_input.email or None

    if user_email:
        user_input.user_message = (
            f"{user_input.user_message} \n Reporter Email: {user_email}"
        )
        kwargs = {
            "input": {"messages": [HumanMessage(content=user_input.user_message)]},
            "config": RunnableConfig(
                configurable={"thread_id": thread_id, "email": user_email},
            ),
        }
        response = await cyber_guard.ainvoke(**kwargs)
    else:
        kwargs = {
            "input": {"messages": [HumanMessage(content=user_input.user_message)]},
            "config": RunnableConfig(configurable={"thread_id": thread_id}),
        }
        response = await cyber_guard.ainvoke(**kwargs)

    return response, thread_id


def convert_message_content_to_string(content: str | list[str | dict]) -> str:
    """Convert message content to a string."""
    if isinstance(content, str):
        return content
    text: list[str] = []
    for content_item in content:
        if isinstance(content_item, str):
            text.append(content_item)
            continue
        if content_item["type"] == "text":
            text.append(content_item["text"])
    return "".join(text)


def infer_chat_message(message: BaseMessage) -> Chat:
    """Create a Chat from a LangChain message."""
    match message:
        case HumanMessage():
            human_message = Chat(
                type="human",
                content=convert_message_content_to_string(message.content),
            )
            return human_message
        case AIMessage():
            ai_message = Chat(
                type="ai",
                content=convert_message_content_to_string(message.content),
            )
            if message.tool_calls:
                ai_message.tool_calls = message.tool_calls
            if message.response_metadata:
                ai_message.response_metadata = message.response_metadata
            return ai_message
        case ToolMessage():
            tool_message = Chat(
                type="tool",
                content=convert_message_content_to_string(message.content),
                tool_call_id=message.tool_call_id,
            )
            return tool_message
        case ChatMessage():
            if message.role == "custom":
                custom_message = Chat(
                    type="custom",
                    content="",
                    custom_data=message.content[0],
                )
                return custom_message
            else:
                raise ValueError(f"Unsupported chat message role: {message.role}")
        case _:
            raise ValueError(f"Unsupported message type: {message.__class__.__name__}")


def rate_limiter(func):
    """
    Rate limiter to restrict the number of requests per email.
    """

    @wraps(func)
    async def wrapper(user_input: UserInput, *args, **kwargs):

        RATE_LIMIT = 10  # Max API calls per email
        HOUR = 24
        TIME_WINDOW = HOUR * 60 * 60  # hours in seconds

        email = user_input.email
        email_key = f"rate_limit:{email}"

        # Get current request count
        request_count = redis_client.get(email_key)

        if request_count is not None and int(request_count) >= RATE_LIMIT:
            raise HTTPException(
                status_code=429,
                detail=f"Rate limit exceeded. Only {RATE_LIMIT} requests allowed per {HOUR} hours.",
            )

        # Increment count and set expiry if it's a new key
        redis_client.incr(email_key)
        if request_count is None:
            redis_client.expire(email_key, TIME_WINDOW)

        return await func(user_input, *args, **kwargs)

    return wrapper
