from uuid import uuid4

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


async def get_llm_response(user_input: UserInput):
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
