import asyncio
import os

import httpx
import streamlit as st
from dotenv import load_dotenv
from streamlit_google_auth import Authenticate

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
        secret_credentials_path=os.getenv("GOOGLE_SECRET_JSON_PATH"),
        cookie_name="dapa_cookie",
        cookie_key=os.getenv("GOOGLE_AUTH_COOKIE_KEY"),
        redirect_uri=os.getenv("GOOGLE_REDIRECT_URI"),
    )
    st.session_state["authenticator"] = authenticator

# Catch the login event
st.session_state["authenticator"].check_authentification()


async def get_response(user_message: str, thread_id: str | None = None) -> dict:
    payload = {"user_message": user_message, "thread_id": thread_id}
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.post(CHAT_API, json=payload)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            return {"error": f"Error connecting to backend: {str(e)}"}


async def main():
    # Initialize session states
    if "thread_id" not in st.session_state:
        st.session_state.thread_id = None
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Main Chat Interface
    st.title(f"{APP_ICON} DAPA AI Assistant")
    st.write(
        "This bot helps you identify or report phone numbers involved in financial fraud or cyber scams."
        "Please describe your incident below."
    )

    for message in st.session_state.messages:
        responder_type = message["responder"]
        if responder_type == "tool":
            st.chat_message("tool", avatar="🛡️").write(message["content"])
        else:
            st.chat_message(responder_type).write(message["content"])

    # User Input
    if user_input := st.chat_input("Type your message here..."):
        st.session_state.messages.append({"responder": "human", "content": user_input})
        st.chat_message("human").write(user_input)

        response = await get_response(user_input, st.session_state.thread_id)

        if "error" in response:
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

    # Sidebar for Google Login and Other Features
    with st.sidebar:
        if st.session_state["connected"]:
            st.image(st.session_state["user_info"]["picture"])
            st.write(st.session_state["user_info"].get("name"))
            # st.write(st.session_state["user_info"].get("email"))
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


if __name__ == "__main__":
    asyncio.run(main())
