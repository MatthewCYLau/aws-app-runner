from datetime import datetime

DATETIME_FORMAT_CODE = "%Y-%m-%d"


def validate_date_string(date_text):
    try:
        if date_text != datetime.strptime(date_text, DATETIME_FORMAT_CODE).strftime(
            DATETIME_FORMAT_CODE
        ):
            raise ValueError("Invalid date input. Must be in format YYYY-MM-DD")
        return True
    except ValueError:
        return False
