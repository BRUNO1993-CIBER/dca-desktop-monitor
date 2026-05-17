import logging
import json
from pathlib import Path
import os

logger = logging.getLogger(__name__)


def _get_config_path() -> Path:
    return Path(__file__).resolve().parents[1] / "config" / "config.json"


def _carregar_config() -> dict:
    with _get_config_path().open("r", encoding="utf-8") as f:
        return json.load(f)


def _carregar_moedas_config() -> list[str]:
    try:
        data = _carregar_config()
        return ["Todas"] + data.get("moedas", [])
    except Exception as e:
        logger.warning(f"Não foi possível carregar config.json: {e}")
        return ["Todas"]


def _carregar_cores_moedas() -> dict[str, str]:
    try:
        data = _carregar_config()
        return data.get("cores_moedas", {})
    except Exception as e:
        logger.warning(f"Não foi possível carregar cores_moedas do config.json: {e}")
        return {}        