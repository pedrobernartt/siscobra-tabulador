"""
Persistência SQLite — log de todas as tabulações geradas.
"""
from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path

_DB_PATH = Path(__file__).parent.parent / "tabulacoes.db"

_SCHEMA = """
CREATE TABLE IF NOT EXISTS tabulacoes (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp           TEXT NOT NULL,
    conversa_input      TEXT NOT NULL,
    situacao            TEXT NOT NULL,
    situacao_codigo     INTEGER NOT NULL,
    complemento         TEXT NOT NULL,
    complemento_codigo  INTEGER NOT NULL,
    descritivo          TEXT NOT NULL,
    confianca           TEXT NOT NULL,
    observacoes         TEXT,
    modelo              TEXT NOT NULL,
    tokens_input        INTEGER NOT NULL DEFAULT 0,
    tokens_output       INTEGER NOT NULL DEFAULT 0,
    tokens_cache_write  INTEGER NOT NULL DEFAULT 0,
    tokens_cache_read   INTEGER NOT NULL DEFAULT 0,
    custo_usd           REAL NOT NULL DEFAULT 0.0,
    tempo_segundos      REAL NOT NULL DEFAULT 0.0,
    status_operador     TEXT,
    descritivo_editado  TEXT
);
"""


def _conectar() -> sqlite3.Connection:
    """Abre (ou cria) o banco e garante que o schema existe."""
    conn = sqlite3.connect(_DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.executescript(_SCHEMA)
    return conn


def salvar_tabulacao(
    conversa_input: str,
    situacao: str,
    situacao_codigo: int,
    complemento: str,
    complemento_codigo: int,
    descritivo: str,
    confianca: str,
    observacoes: str | None,
    modelo: str,
    tokens_input: int,
    tokens_output: int,
    tokens_cache_write: int,
    tokens_cache_read: int,
    custo_usd: float,
    tempo_segundos: float,
) -> int:
    """Insere uma nova tabulação e retorna o id gerado."""
    conn = _conectar()
    with conn:
        cursor = conn.execute(
            """
            INSERT INTO tabulacoes (
                timestamp, conversa_input, situacao, situacao_codigo,
                complemento, complemento_codigo, descritivo, confianca, observacoes,
                modelo, tokens_input, tokens_output, tokens_cache_write, tokens_cache_read,
                custo_usd, tempo_segundos
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                datetime.now().isoformat(),
                conversa_input,
                situacao,
                situacao_codigo,
                complemento,
                complemento_codigo,
                descritivo,
                confianca,
                observacoes,
                modelo,
                tokens_input,
                tokens_output,
                tokens_cache_write,
                tokens_cache_read,
                custo_usd,
                tempo_segundos,
            ),
        )
    return cursor.lastrowid


def atualizar_feedback(
    id_tabulacao: int,
    status_operador: str,
    descritivo_editado: str | None = None,
) -> None:
    """
    Atualiza o status do operador e, opcionalmente, o descritivo editado.
    status_operador: 'aprovado' | 'editado' | 'rejeitado'
    """
    conn = _conectar()
    with conn:
        conn.execute(
            """
            UPDATE tabulacoes
            SET status_operador = ?, descritivo_editado = ?
            WHERE id = ?
            """,
            (status_operador, descritivo_editado, id_tabulacao),
        )


def listar_historico(limite: int = 50, filtro_status: str | None = None) -> list[sqlite3.Row]:
    """Retorna as últimas tabulações, com filtro opcional por status."""
    conn = _conectar()
    if filtro_status:
        rows = conn.execute(
            "SELECT * FROM tabulacoes WHERE status_operador = ? ORDER BY id DESC LIMIT ?",
            (filtro_status, limite),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM tabulacoes ORDER BY id DESC LIMIT ?",
            (limite,),
        ).fetchall()
    return rows
