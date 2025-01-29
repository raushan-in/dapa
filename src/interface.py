"""
This module sets up the Streamlit interface for the DAPA application.
It initializes the chatbot and handles user input and bot responses.
Google authentication is used to allow users to sign in.
"""

import asyncio
import os

import httpx
import streamlit as st
from dotenv import load_dotenv
from streamlit_google_auth import Authenticate

# Constants
APP_TITLE = "DAPA"
APP_ICON = "🛡️"
st.set_page_config(page_title=APP_TITLE, page_icon=APP_ICON)

# Load environment variables
load_dotenv()
BACKEND_URL = os.getenv("BACKEND_URL")
CHAT_API = BACKEND_URL + "/chat"
SECRET_JSON_PATH = os.getenv("GOOGLE_SECRET_JSON_PATH")
COOKIE_KEY = os.getenv("GOOGLE_AUTH_COOKIE_KEY")
REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI")

# Initialize Google Authenticator
if "connected" not in st.session_state:
    authenticator = Authenticate(
        secret_credentials_path=SECRET_JSON_PATH,
        cookie_name="dapa_cookie",
        cookie_key=COOKIE_KEY,
        redirect_uri=REDIRECT_URI,
    )
    st.session_state["authenticator"] = authenticator

# Catch the login event
st.session_state["authenticator"].check_authentification()

if not st.session_state.get("connected", False):
    st.warning(
        "**🔑 Please sign in to report a number or search for a scammer.**\n\n"
        "Click on **`>`** (top-left corner) to open the sidebar and sign in with Google."
    )


async def get_response(user_message: str) -> dict:
    """
    Sends a user message to the backend chat API and returns the response.

    Parameters:
    - user_message: The message from the user to be sent to the backend.

    Returns:
    - A dictionary containing the response from the backend or an error message if the request fails.
    """
    thread_id = st.session_state.thread_id
    user_email = st.session_state.user_email
    if not user_email:
        return {
            "response_message": "Please sign in to report a number or search for a scammer.",
            "responder": "tool",
            "thread_id": thread_id,
        }
    payload = {
        "user_message": user_message,
        "thread_id": thread_id,
        "email": user_email,
    }
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.post(CHAT_API, json=payload)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            if response.status_code == 429:
                # Handle Rate Limit Error (429)
                return {
                    "error": "cooling_period_active",
                }
            return {"error": f"Error connecting to backend: {repr(e)}"}


async def initialize_session():
    """Initialize session state variables."""
    if "thread_id" not in st.session_state:
        st.session_state.thread_id = None
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "user_email" not in st.session_state:
        st.session_state.user_email = None


async def display_chat():
    """Displays chat messages."""
    for message in st.session_state.messages:
        responder_type = message["responder"]
        if responder_type == "tool":
            st.chat_message("tool", avatar="🛡️").write(message["content"])
        else:
            st.chat_message(responder_type).write(message["content"])


async def handle_user_input():
    """Handles user input and bot responses."""
    if user_input := st.chat_input("Type your message here..."):
        st.session_state.messages.append({"responder": "human", "content": user_input})
        st.chat_message("human").write(user_input)

        response = await get_response(user_input)

        if "error" in response:
            if response["error"] == "cooling_period_active":
                st.chat_message("tool", avatar="🛡️").write(
                    "A cooling period applied. 🥶 Please try after some time."
                )
            else:
                st.error(response["error"])
        else:
            response_message = response["response_message"]
            responder = response["responder"]
            st.session_state.thread_id = response["thread_id"]

            # Append the response to session state
            st.session_state.messages.append(
                {"responder": responder, "content": response_message}
            )
            if responder == "tool":
                st.chat_message("tool", avatar="🛡️").write(response_message)
            else:
                st.chat_message(responder).write(response_message)


async def setup_sidebar():
    """Sets up the sidebar with authentication and app info."""
    with st.sidebar:
        if st.session_state["connected"]:
            st.image(st.session_state["user_info"]["picture"])
            st.write(st.session_state["user_info"].get("name"))
            st.session_state.user_email = st.session_state["user_info"].get("email")
            if st.button("Log out"):
                st.session_state["authenticator"].logout()
        else:
            st.session_state["authenticator"].login()

        st.write("---")
        st.header(f"{APP_ICON} {APP_TITLE}")
        st.write("DAPA chatbot for secure reporting of scams.")

        # Privacy Section
        with st.expander("🔒 Privacy"):
            st.write(
                """
                1. Queries and responses in this app may be anonymously recorded by LangSmith to improve product performance.  
                2. Your email address will only be stored if you choose to report a number.
                3. This app uses cookies to remember your login session. 
                """
            )

        st.write("---")
        st.markdown(
            "Made with ❤️ by [Raushan](https://www.linkedin.com/in/raushan-in/) in Trier"
        )


async def main():
    """Main function to run the Streamlit app."""
    await initialize_session()

    # Title and Description
    st.title(f"{APP_ICON} DAPA AI Assistant")
    st.write(
        "This bot helps you identify or report phone numbers involved in financial fraud or cyber scams."
        "Please describe your incident below."
    )

    await display_chat()
    await handle_user_input()
    await setup_sidebar()


if __name__ == "__main__":
    asyncio.run(main())
