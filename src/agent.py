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

from settings import settings
from tools import register_scam, search_scam

llm = ChatGroq(
    model=settings.GROQ_MODEL, temperature=settings.GROQ_MODEL_TEMP, streaming=False
)

scam_categories = {
    1: [
        "Fake Authority Call",
        "Scammers impersonating law enforcement officials (e.g., CBI, customs, police) or service agents, coercing victims into making payments or sharing sensitive details.",
    ],
    2: [
        "Service Disconnection Scam",
        "Threats of service disconnection unless immediate verification or payment is made.",
    ],
    3: [
        "UPI Scam",
        "Scammers claim accidental UPI payments and request refunds, or attempt scams related to UPI, PhonePe, Google Pay, or any quick payment interface.",
    ],
    4: ["OTP Scam", "Scammers request OTPs to gain unauthorized access to accounts."],
    5: [
        "Fake Buyer/Seller Scam",
        "Scammers pose as buyers requesting refunds or as fraudulent sellers asking for advance payments.",
    ],
    6: [
        "Phishing or Link Scam",
        "Fraudulent SMS or calls designed to gain unauthorized access to banking platforms by sending malicious links or asking for sensitive details.",
    ],
    7: [
        "Video Call Scam",
        "Blackmail involving compromising video calls, screenshots, or morphed photos.",
    ],
    8: [
        "Fake Bank Staff Scam",
        "Calls from scammers posing as bank officials, requesting sensitive banking details.",
    ],
    9: [
        "Fake Job Scam",
        "Scammers posing as recruiters, demanding service or registration fees for fake job offers.",
    ],
    10: [
        "Lottery Scam",
        "Messages claiming lottery wins, lucky draws, or prizes, and requesting fees for processing.",
    ],
    11: [
        "Fake Identity Scam",
        "Scammers imitate known individuals and request money transfers.",
    ],
    12: [
        "Other Cyber Scam",
        "Any other scam conducted via phone that involves monetary fraud.",
    ],
}

scam_categories_str = "\n".join(
    [f"{k}: {v[0]}-{v[1]}" for k, v in scam_categories.items()]
)

instructions = f"""
    You are a helpful agent named DAPA to classify user reports about potential digital financial scams or fraud.
    Stick to your task and do not provide answers to unrelated questions. You are here solely to search or report incidents of financial scams or fraud via mobile communication.

    NOTE: THE USER CAN'T SEE THE TOOL RESPONSE.

    A few things to remember:
    - Use provided tools based on the situation.
    - Ask for confirmation explicitly to avoid incorrect reports insert.
    - The `Register Scam` should only be used after the user confirms both the scammer’s number and scam type.
    - Predefined Scam Categories: Only use the following scam types:
      {scam_categories_str}
    """

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
