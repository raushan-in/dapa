"""AI agents"""

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, SystemMessage
from langchain_core.runnables import (
    RunnableConfig,
    RunnableLambda,
    RunnableSerializable,
)
from langchain_groq import ChatGroq
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode

from prompts import instructions
from settings import settings
from tools import register_scam, search_scam

llm = ChatGroq(
    model=settings.GROQ_MODEL, temperature=settings.GROQ_MODEL_TEMP, streaming=False
)


tools = [register_scam, search_scam]


class AgentState(MessagesState, total=False):
    """`total=False` is PEP589 specs.

    documentation: https://typing.readthedocs.io/en/latest/spec/typeddict.html#totality
    """


def wrap_model(model: BaseChatModel) -> RunnableSerializable[AgentState, AIMessage]:
    model_with_tools = model.bind_tools(tools)
    preprocessor = RunnableLambda(
        lambda state: [SystemMessage(content=instructions)] + state["messages"],
        name="StateModifier",
    )
    return preprocessor | model_with_tools


async def acall_model(state: AgentState, config: RunnableConfig) -> AgentState:
    model_runnable = wrap_model(llm)
    response = await model_runnable.ainvoke(state, config)
    # We return a list, because this will get added to the existing list
    return {"messages": [response]}


# Define the graph
agent = StateGraph(AgentState)
agent.add_node("model", acall_model)
agent.add_node("tools", ToolNode(tools))

agent.set_entry_point("model")

# Add edges (transitions)
agent.add_edge("model", "tools")
agent.add_edge("tools", END)

cyber_guard = agent.compile(checkpointer=MemorySaver())
