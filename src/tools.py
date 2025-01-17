from langchain_core.tools import tool

from database import Scammer, session


@tool
async def register_scam(scammer: Scammer) -> str:
    """
    Registers a report of a scam incident into the database.

    Parameters:
        scammer (Scammer): An instance of the Scammer model containing the following fields:
            - scammer_mobile (str): The mobile number of the alleged scammer.
              Must be formatted as "+XX-<mobile_number>", where "+XX" is the country code.
            - scam_id (int): The unique identifier for the type of scam.
            - reporter_ordeal (str): A summary of the ordeal narrated by the reporter.
              Should not exceed 100 words.
            - reporter_mobile (str): The mobile number of the person reporting the scam.
              Must be formatted as "+XX-<mobile_number>", where "+XX" is the country code.
            - created_at (datetime): The timestamp when the scam report is created. Automatically generated.

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
        await session.add(scammer)
        await session.commit()
        return f"A report has been registered for {scammer.scammer_mobile}."
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

    Example:
        >>> search_scam("+91-9876543210")
        "Scammer(id=1, scammer_mobile='+91-9876543210', scam_id=4, reporter_ordeal='...', ...)"

        >>> search_scam("+91-1234567890")
        "+91-1234567890 is not reported as scammer."

        >>> search_scam("+91-0000000000")
        "An error occurred while searching scam for +91-0000000000."
    """
    try:
        scammer = await session.get(Scammer, mobile)
        if not scammer:
            return f"{mobile} is not reported as scammer."
        return scammer
    except Exception as exc:
        print(repr(exc))
        return f"An error occurred while searching scam for {mobile}."


search_scam.name = "Search Scam"
