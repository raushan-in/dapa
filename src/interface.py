import asyncio
import os

import httpx
import streamlit as st
from dotenv import load_dotenv
from google_auth_oauthlib.flow import Flow

APP_TITLE = "DAPA"
APP_ICON = "🛡️"

# Load environment variables
load_dotenv()
BACKEND_URL = os.getenv("BACKEND_URL")
CHAT_API = BACKEND_URL + "/chat"
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI")

# Initialize Google OAuth flow
def google_login_flow():
    flow = Flow.from_client_config(
        {
            "web": {
                "client_id": GOOGLE_CLIENT_ID,
                "client_secret": GOOGLE_CLIENT_SECRET,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
            }
        },
        scopes=[
            "https://www.googleapis.com/auth/userinfo.email",
            "https://www.googleapis.com/auth/userinfo.profile",
        ]
    )
    flow.redirect_uri = REDIRECT_URI 
    auth_url, _ = flow.authorization_url(prompt="consent")
    return flow, auth_url

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
    st.set_page_config(page_title=APP_TITLE, page_icon=APP_ICON)

    # Initialize session states
    if "thread_id" not in st.session_state:
        st.session_state.thread_id = None
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "google_user" not in st.session_state:
        st.session_state.google_user = None

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

    # User input
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

    with st.sidebar:
        st.header(f"{APP_ICON} {APP_TITLE}")
        st.write("DAPA chatbot for secure reporting of scams.")

        # Privacy Section
        with st.expander("🔒 Privacy"):
            st.write(
                "Query and response in this app are anonymously recorded and saved to LangSmith for product evaluation and improvement purposes."
            )

        st.markdown(
            "Made with ❤️ by [Raushan](https://www.linkedin.com/in/raushan-in/) in Trier"
        )

        st.write("---")

        # Google Login Section
        if st.session_state.google_user:
            st.write(f"Welcome, {st.session_state.google_user['name']}!")
            st.write(f"Email: {st.session_state.google_user['email']}")
            if st.button("Logout"):
                st.session_state.google_user = None
        else:
            st.write("Login with Google to access more features.")
            flow, auth_url = google_login_flow()
            st.session_state.flow = flow
            st.markdown(f"[Login]({auth_url})")


if __name__ == "__main__":
    asyncio.run(main())
