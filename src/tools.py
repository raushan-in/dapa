from langchain_core.tools import tool
from sqlmodel import select

from database import Scammer, get_session


@tool
async def register_scam(
    scammer_mobile: str, scam_id: int, reporter_ordeal: str, reporter_mobile: str
) -> str:
    """
    Registers a report of a scam incident into the database.

    Parameters:
            - scammer_mobile (str): The mobile_number of the alleged scammer.
              Must be formatted as "+XX-<mobile_number>", where "+XX" is the country code.
            - scam_id (int): The unique identifier for the type of scam.
            - reporter_ordeal (str): A summary of the ordeal narrated by the reporter.
              Should not exceed 50 words.
            - reporter_mobile (str): The mobile_number of the person reporting the scam.
              Must be formatted as "+XX-<mobile_number>", where "+XX" is the country code.

    Returns:
        str: A confirmation message if the report is registered successfully, or an error
        message if an exception occurs during the registration process.
    """
    try:
        scammer = Scammer(
            scammer_mobile=scammer_mobile,
            scam_id=scam_id,
            reporter_ordeal=reporter_ordeal,
            reporter_mobile=reporter_mobile,
        )
        async with get_session() as session:
            session.add(scammer)
            await session.commit()
            return f"{scammer_mobile} has been registered as a scammer. ✅ Thank you for combating scams! 🥇"
    except ValueError as e:
        print(repr(exc))
        return f"ValueError: {repr(exc)}"
    except Exception as exc:
        print(repr(exc))
        return f"An error occurred in registering a report for {scammer_mobile}."


register_scam.name = "Register Scam"


@tool
async def search_scam(scammer_mobile: str) -> str:
    """
    Searches the database for scam reports associated with the provided mobile number.

    Parameters:
        scammer_mobile (str): The mobile number of the alleged scammer, formatted as "+XX-<mobile_number>",
        where "+XX" is the country code.

    Returns:
        str: If a scam report is found, returns a string representation of the scam count.
        If no scams are found, returns a message indicating that the mobile number is not reported.
        If an error occurs during the search process, returns an error message.
    """
    try:
        async with get_session() as session:
            statement = select(Scammer).where(Scammer.scammer_mobile == scammer_mobile)
            result = await session.exec(statement)
            scams = result.all()
            if not scams:
                return f"{scammer_mobile} has never been reported for scams or fraudulent activity."
            return f"{scammer_mobile} has been reported as a scammer {len(scams)} times in the past. 🚨 Be alert! ⚠️"
    except Exception as exc:
        print(repr(exc))
        return f"An error occurred while searching scam for {scammer_mobile}."


search_scam.name = "Search Scam"
