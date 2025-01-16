from langchain_core.tools import tool


@tool
def register_scam(
    scammer_mobile: str, scam_id: int, reporter_ordeal: str, reporter_mobile: str
) -> str:
    """
    Registers a report of a scam incident into the database.

    Parameters:
        scammer_mobile (str): The mobile number of the alleged scammer.
                              The mobile number must be in the format "+XX-<mobile_number>"
                              where "+XX" is the country code.
        scam_id (int): The unique identifier for the scam report.
        reporter_ordeal (str): A summary of the ordeal narrated by the reporter.
                               The summary should be in English and must not exceed 100 words.
        reporter_mobile (str): The mobile number of the person reporting the scam.
                               The mobile number must be in the format "+XX-<mobile_number>"
                               where "+XX" is the country code.

    Returns:
        str: A confirmation message if the report is registered successfully,
             or an error message if an exception occurs during the registration process.

    Example:
        >>> register_scam("+91-1876543210", 4, "Received a fraudulent call asking for bank OTP.", "+1-9934567890")
        "A report has been registered for +91-9876543210."
    """
    try:
        # Database insert operation  TODO
        return f"A report has been registered for {scammer_mobile}."
    except Exception as exc:
        print(repr(exc))
        return f"An error occurred in registering a report for {scammer_mobile}."


register_scam.name = "Register Scam"


@tool
def search_scam(mobile: str) -> str:
    """
    Searches the database for scam reports associated with the provided mobile number.

    Parameters:
        mobile (str): The mobile number of the alleged scammer, formatted as "+XX-<mobile_number>"
                      where "+XX" is the country code.

    Returns:
        str: A comma-separated list of scam categories associated with the mobile number.
             If no scams are found, returns an empty string.
             If an error occurs during the search process, returns an error message.

    Example:
        >>> search_scam("+91-9876543210")
        "Fake Authority Call, UPI Scam"

        >>> search_scam("+91-1234567890")
        ""

        >>> search_scam("+91-0000000000")
        "An error occurred while searching scam for +91-0000000000."
    """
    try:
        # Database select query to search scams by scammer mobile number - TODO
        return f"{mobile} searched..."
    except Exception as exc:
        print(repr(exc))
        return f"An error occurred while searching scam for {mobile}."


search_scam.name = "Search Scam"
