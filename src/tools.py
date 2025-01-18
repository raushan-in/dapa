from langchain_core.tools import tool

from database import Scammer, get_session

from sqlmodel import select


@tool
async def register_scam(scammer_mobile: str, scam_id: int, reporter_ordeal:str,  reporter_mobile:str) -> str:
    """
    Registers a report of a scam incident into the database.

    Parameters:
            - scammer_mobile (str): The mobile number of the alleged scammer.
              Must be formatted as "+XX-<mobile_number>", where "+XX" is the country code.
            - scam_id (int): The unique identifier for the type of scam.
            - reporter_ordeal (str): A summary of the ordeal narrated by the reporter.
              Should not exceed 100 words.
            - reporter_mobile (str): The mobile number of the person reporting the scam.
              Must be formatted as "+XX-<mobile_number>", where "+XX" is the country code.

    Returns:
        str: A confirmation message if the report is registered successfully, or an error
        message if an exception occurs during the registration process.

    Example:
        >>> scammer = Scammer(
                scammer_mobile="+91-9876543210",
                scam_id=4,
                reporter_ordeal="Received a fraudulent call asking for bank OTP.",
                reporter_mobile="+1-9934567890"
            )
        >>> register_scam(scammer)
        "A report has been registered for +91-9876543210."
    """
    try:
        scammer = Scammer(scammer_mobile = scammer_mobile, scam_id = scam_id, reporter_ordeal= reporter_ordeal,  reporter_mobile= reporter_mobile)
        async with get_session() as session:
            session.add(scammer)
            await session.commit()
            return f"A report has been registered for {scammer_mobile}."
    except Exception as exc:
        print(repr(exc))
        return f"An error occurred in registering a report for {scammer_mobile}."


register_scam.name = "Register Scam"


@tool
async def search_scam(mobile: str) -> str:
    """
    Searches the database for scam reports associated with the provided mobile number.

    Parameters:
        mobile (str): The mobile number of the alleged scammer, formatted as "+XX-<mobile_number>",
        where "+XX" is the country code.

    Returns:
        str: If a scam report is found, returns a string representation of the Scammer object.
        If no scams are found, returns a message indicating that the mobile number is not reported.
        If an error occurs during the search process, returns an error message.
    """
    try:
        async with get_session() as session:
            statement = select(Scammer).where(Scammer.scammer_mobile == mobile)
            result = await session.exec(statement)
            scammer = result.first()  # Get the first matching result
            if not scammer:
                return f"{mobile} is not reported as scammer."
            return f"Scammer found: {scammer}"
    except Exception as exc:
        print(repr(exc))
        return f"An error occurred while searching scam for {mobile}."


search_scam.name = "Search Scam"
