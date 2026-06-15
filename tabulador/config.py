"""
Configurações da aplicação — persistidas em config.json.
Guarda o provedor de IA escolhido, o modelo e as chaves de API por provedor.
"""
from __future__ import annotations

import copy
import json
import os
from pathlib import Path

_CONFIG_PATH = Path(__file__).parent.parent / "config.json"

# Nome da variável de ambiente / secret de cada provedor (fallback quando a
# chave não foi colada na interface).
_ENV_KEYS: dict[str, str] = {
    "gemini": "GEMINI_API_KEY",
    "openai": "OPENAI_API_KEY",
    "anthropic": "ANTHROPIC_API_KEY",
}

_PADROES: dict = {
    # Provedor padrão: Gemini, que possui camada gratuita.
    "provedor": "gemini",
    "modelo": "gemini-2.5-flash",
    # Uma chave por provedor (coladas pelo usuário na aba Configurações).
    "chaves": {
        "gemini": "",
        "openai": "",
        "anthropic": "",
    },
    "operadores": [
        "LIZ", "PAULO", "JANAINA", "AMANDHA", "KAMILA", "JOSI",
        "ADM SOLUG", "ADM", "SOLUG COBRANÇAS", "SOLUG COBRANCAS",
        "WhatsApp Business", "WhatsApp Lite",
    ],
}


# Modelo padrão por provedor — evita herdar um MODEL_NAME de outra família.
_MODELO_PADRAO_PROVEDOR: dict[str, str] = {
    "gemini": "gemini-2.5-flash",
    "openai": "gpt-4o-mini",
    "anthropic": "claude-sonnet-4-5",
}


def _overlay_env(cfg: dict) -> dict:
    """Aplica PROVIDER / MODEL_NAME do ambiente sobre a config padrão
    (usado quando não há config.json, ex.: Streamlit Cloud).

    Só sobrescreve quando PROVIDER está definido. Assim, um MODEL_NAME
    "órfão" de uma configuração antiga (ex.: claude-sonnet-4-5 sobrando
    no .env/Secrets) NÃO é aplicado por engano sobre o provedor padrão
    (Gemini), o que causaria erro de modelo incompatível.
    """
    prov = os.getenv("PROVIDER", "").strip().lower()
    if not prov:
        return cfg
    cfg["provedor"] = prov
    modelo = os.getenv("MODEL_NAME", "").strip()
    cfg["modelo"] = modelo or _MODELO_PADRAO_PROVEDOR.get(prov, cfg["modelo"])
    return cfg


def carregar_config() -> dict:
    """
    Retorna a config atual do arquivo JSON mesclada com os padrões
    (garante que chaves novas existam mesmo em config.json antigos).
    Sem config.json (ex.: Streamlit Cloud), aplica PROVIDER/MODEL_NAME do ambiente.
    """
    if _CONFIG_PATH.exists():
        try:
            dados = json.loads(_CONFIG_PATH.read_text(encoding="utf-8"))
            cfg = {**copy.deepcopy(_PADROES), **dados}
            # Garante que o subdicionário de chaves esteja completo.
            cfg["chaves"] = {**_PADROES["chaves"], **(dados.get("chaves") or {})}
            return cfg
        except (json.JSONDecodeError, OSError):
            pass
    return _overlay_env(copy.deepcopy(_PADROES))


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


def obter_chave(provedor: str) -> str:
    """
    Resolve a chave de API do provedor, nesta ordem de prioridade:
      1. st.secrets (Streamlit Cloud)
      2. chave colada na interface (config.json → chaves[provedor])
      3. variável de ambiente / .env
    """
    env_name = _ENV_KEYS.get(provedor, "")

    # 1. Streamlit secrets
    try:
        import streamlit as st
        if env_name and env_name in st.secrets:
            return str(st.secrets[env_name])
    except Exception:
        pass

    # 2. Chave salva na config local
    config = carregar_config()
    chave = (config.get("chaves") or {}).get(provedor, "")
    if chave:
        return chave.strip()

    # 3. Ambiente
    return os.getenv(env_name, "").strip() if env_name else ""
