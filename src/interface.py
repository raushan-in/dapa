import asyncio
import os
import urllib.parse
import httpx
import streamlit as st
from dotenv import load_dotenv

APP_TITLE = "DAPA"
APP_ICON = "🛡️"

# Load environment variables
load_dotenv()
BACKEND_URL = os.getenv("BACKEND_URL")
CHAT_API = BACKEND_URL + "/chat"

async def get_response(user_message: str, thread_id: str | None = None) -> dict:
    """
    Sends the user message to the backend and returns the bot response.
    """
    payload = {"user_message": user_message, "thread_id": thread_id}
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.post(CHAT_API, json=payload)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            return {"error": f"Error connecting to backend: {str(e)}"}

async def main():
    st.set_page_config(page_title=APP_TITLE, page_icon=APP_ICON)

    if "thread_id" not in st.session_state:
        st.session_state.thread_id = None
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Application Title and Description
    st.title(f"{APP_ICON} DAPA AI Chatbot")
    st.write("This chatbot helps you report cyber scams and fraudulent activities. Please describe your issue below.")

    # Display chat history
    for message in st.session_state.messages:
        sender = "user" if message["sender"] == "user" else "bot"
        st.chat_message(sender).write(message["content"])

    # User input
    if user_input := st.chat_input("Type your message here..."):
        st.session_state.messages.append({"sender": "user", "content": user_input})
        st.chat_message("user").write(user_input)

        # Send the user message to the backend
        response = await get_response(user_input, st.session_state.thread_id)

        if "error" in response:
            st.error(response["error"])
        else:
            response_message = response["response_message"]
            responder = response["responder"]
            st.session_state.thread_id = response["thread_id"]  # Update thread_id for multi-turn conversations
            st.session_state.messages.append({"sender": responder, "content": response_message})
            st.chat_message(responder).write(response_message)

    with st.sidebar:
        st.header(f"{APP_ICON} {APP_TITLE}")
        st.write("DAPA chatbot for secure reporting of scams.")
        chat_url = f"{st.get_option('browser.serverAddress')}/?thread_id={st.session_state.thread_id}"
        st.code(f"Share your chat: {chat_url}")

if __name__ == "__main__":
    asyncio.run(main())
