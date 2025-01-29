"""
This module defines the API routes for the DAPA application.
"""

from fastapi import APIRouter, Depends, HTTPException

from auth import verify_bearer
from schema import SingleResponse, UserInput
from utils import get_llm_response, infer_chat_message, rate_limiter

bot_router = APIRouter(tags=["bot"], dependencies=[Depends(verify_bearer)])


@bot_router.post("/chat")
@rate_limiter
async def agent_chat(user_input: UserInput) -> SingleResponse:
    """
    Invoke an agent with user input to retrieve a response.
    Use thread_id to persist and continue a multi-turn conversation.
    """
    try:
        response, thread_id = await get_llm_response(user_input)
        last_message = infer_chat_message(response["messages"][-1])
        response = {
            "response_message": last_message.content,
            "responder": last_message.type,
            "thread_id": thread_id,
        }
        return SingleResponse(**response)
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail="Unexpected error")
