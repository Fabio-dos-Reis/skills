#!/usr/bin/env python3
"""medico_sessionstart.py — hook SessionStart: lembra o snapshot pos-compact.

Se .agents/handover-snapshot.md existir e for mais recente que o handover.md,
imprime um lembrete de 2 linhas (o stdout e injetado no contexto da sessao).
Caso contrario exit 0 silencioso.

Stdlib apenas, cross-platform. Corre com UM interpretador: o que o instalador
grava em __PYTHON__ nos snippets desta maquina. Nunca duas execucoes encadeadas
(python e depois python3): a repeticao substitui o codigo de saida da primeira.
"""
import json
import sys
from pathlib import Path

RAIZ = Path.cwd()
AGENTS = RAIZ / ".agents"
HANDOVER = AGENTS / "handover.md"
SNAPSHOT = AGENTS / "handover-snapshot.md"


def mtime(p):
    try:
        return p.stat().st_mtime
    except OSError:
        return 0.0


def main():
    try:
        json.load(sys.stdin)
    except Exception:
        pass
    if not SNAPSHOT.exists():
        return 0
    if mtime(SNAPSHOT) <= mtime(HANDOVER):
        return 0
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, OSError):
        pass
    print(f"Existe um snapshot pré-compact mais recente que o handover: {SNAPSHOT}")
    print("Lê-o antes de retomar — o handover pode estar em drift. Corre /medico se divergirem.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
