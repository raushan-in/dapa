import asyncio
import os
import urllib.parse
from collections.abc import AsyncGenerator

import streamlit as st
from dotenv import load_dotenv
from pydantic import ValidationError
from streamlit.runtime.scriptrunner import get_script_run_ctx

# A Streamlit app for interacting with the backend AI agent.



APP_TITLE = "Agent Service Toolkit"
APP_ICON = "🛡️"


async def main() -> None:
    st.set_page_config(
        page_title=APP_TITLE,
        page_icon=APP_ICON,
        menu_items={},
    )


if __name__ == "__main__":
    asyncio.run(main())
