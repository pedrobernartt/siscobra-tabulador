"""
Configurações da aplicação — persistidas em config.json.
"""
from __future__ import annotations

import json
from pathlib import Path

_CONFIG_PATH = Path(__file__).parent.parent / "config.json"

_PADROES: dict = {
    "modelo": "claude-sonnet-4-5",
    "operadores": [
        "LIZ", "PAULO", "JANAINA", "AMANDHA", "KAMILA", "JOSI",
        "ADM SOLUG", "ADM", "SOLUG COBRANÇAS", "SOLUG COBRANCAS",
        "WhatsApp Business", "WhatsApp Lite",
    ]
}


def carregar_config() -> dict:
    """Retorna a config atual do arquivo JSON, ou os padrões se não existir."""
    if _CONFIG_PATH.exists():
        try:
            return json.loads(_CONFIG_PATH.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass
    return _PADROES.copy()


def salvar_config(config: dict) -> None:
    """Persiste a config no arquivo JSON."""
    _CONFIG_PATH.write_text(
        json.dumps(config, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def obter_operadores() -> set[str]:
    """Retorna o conjunto de nomes de operadores em minúsculas."""
    config = carregar_config()
    nomes = config.get("operadores", _PADROES["operadores"])
    return {n.strip().lower() for n in nomes if n.strip()}


def salvar_operadores(nomes: list[str]) -> None:
    """Substitui a lista de operadores e persiste."""
    config = carregar_config()
    config["operadores"] = [n.strip() for n in nomes if n.strip()]
    salvar_config(config)
