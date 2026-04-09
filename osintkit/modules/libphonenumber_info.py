"""Offline phone number analysis using the phonenumbers library."""

import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


async def run_libphonenumber(inputs: Dict[str, Any]) -> List[Dict]:
    """Parse and analyse a phone number using the phonenumbers library.

    Returns carrier, region, number type, validity, and E.164 format.
    Returns [] if no phone input, if phonenumbers is not installed,
    or if the number cannot be parsed.
    """
    phone = inputs.get("phone")
    if not phone:
        return []

    try:
        import phonenumbers
        from phonenumbers import carrier, geocoder, number_type, is_valid_number, format_number
        from phonenumbers import PhoneNumberFormat, PhoneNumberType
    except ImportError:
        logger.warning("phonenumbers library not installed; skipping phone analysis")
        return []

    try:
        parsed = phonenumbers.parse(phone, None)
    except phonenumbers.NumberParseException:
        try:
            # Retry with a default region hint
            parsed = phonenumbers.parse(phone, "US")
        except phonenumbers.NumberParseException:
            logger.warning(f"Could not parse phone number: {phone!r}")
            return []

    valid = is_valid_number(parsed)
    e164 = format_number(parsed, PhoneNumberFormat.E164)

    try:
        carrier_name = carrier.name_for_number(parsed, "en") or "unknown"
    except Exception:
        carrier_name = "unknown"

    try:
        region = geocoder.description_for_number(parsed, "en") or "unknown"
    except Exception:
        region = "unknown"

    ntype_int = number_type(parsed)
    type_map = {
        PhoneNumberType.MOBILE: "mobile",
        PhoneNumberType.FIXED_LINE: "fixed_line",
        PhoneNumberType.FIXED_LINE_OR_MOBILE: "fixed_line_or_mobile",
        PhoneNumberType.TOLL_FREE: "toll_free",
        PhoneNumberType.PREMIUM_RATE: "premium_rate",
        PhoneNumberType.SHARED_COST: "shared_cost",
        PhoneNumberType.VOIP: "voip",
        PhoneNumberType.PERSONAL_NUMBER: "personal_number",
        PhoneNumberType.PAGER: "pager",
        PhoneNumberType.UAN: "uan",
        PhoneNumberType.VOICEMAIL: "voicemail",
        PhoneNumberType.UNKNOWN: "unknown",
    }
    number_type_str = type_map.get(ntype_int, "unknown")

    return [{
        "source": "libphonenumber",
        "type": "phone_info",
        "data": {
            "carrier": carrier_name,
            "region": region,
            "number_type": number_type_str,
            "is_valid": valid,
            "e164_format": e164,
        },
        "url": None,
    }]
