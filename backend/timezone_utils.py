from datetime import datetime
from zoneinfo import ZoneInfo

CHILE_TZ = ZoneInfo("America/Santiago")

def get_chile_time() -> datetime:
    """Retorna la fecha y hora actual con zona horaria de Chile (America/Santiago)."""
    return datetime.now(CHILE_TZ)

def get_chile_date_str() -> str:
    """Retorna la fecha actual en Chile formateada como YYYY-MM-DD."""
    return get_chile_time().strftime("%Y-%m-%d")

def get_chile_timestamp_str() -> str:
    """Retorna el timestamp actual en Chile formateado como YYYY-MM-DD HH:MM:SS."""
    return get_chile_time().strftime("%Y-%m-%d %H:%M:%S")
