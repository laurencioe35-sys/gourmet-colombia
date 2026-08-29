import os
from pathlib import Path

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")
load_dotenv(PROJECT_ROOT / ".env.local")


def get_env(name: str, default: str = "", aliases=()) -> str:
    """Resuelve variables de entorno con aliases útiles para Railway y entornos locales.

    Railway y otras plataformas suelen exponer nombres alternativos para los secretos y
    client IDs. Este helper centraliza ese comportamiento para evitar fallas por un valor
    ausente en una sola variable.
    """
    candidates = [name, *(tuple(aliases) if isinstance(aliases, (list, tuple, set)) else (aliases,))]
    for key in candidates:
        if not key:
            continue
        value = os.getenv(key, "").strip()
        if value:
            return value
    return default
