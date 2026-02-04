# validators.py
import re
from django.core.exceptions import ValidationError

def validate_gstin(value):
    """
    Validates an Indian GSTIN number using regex.

    GSTIN Rules:
    - 15 characters
    - First 2 digits: state code (01-35)
    - Next 10 chars: PAN number (alphanumeric)
    - 13th char: entity code (alphanumeric)
    - 14th char: default 'Z'
    - 15th char: checksum (alphanumeric)
    """
    if not value:  # allow blank/null
        return

    gstin_pattern = r'^[0-3][0-9][A-Z]{5}[0-9]{4}[A-Z][0-9A-Z]Z[0-9A-Z]$'

    if not re.match(gstin_pattern, value):
        raise ValidationError(f"'{value}' is not a valid GSTIN number.")

    # Optional: validate state code (first 2 digits must be 01-35)
    state_code = int(value[:2])
    if state_code < 1 or state_code > 35:
        raise ValidationError(f"'{value}' has an invalid state code (first two digits).")
