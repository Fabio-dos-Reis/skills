#!/usr/bin/env python3
"""medico_precompact.py — hook PreCompact: snapshot do estado antes do compact.

Fire-and-forget: escreve/ sobrescreve .agents/handover-snapshot.md com
data, `git log --oneline -5`, `git status --porcelain` e as trailer lines
(`**Segue:**` / `**À espera ...:**`) atuais do handover.md.
O snapshot abre com "<!-- gerado: nao entra no INDEX -->" — o indice do
bora ignora-o, como os outros ficheiros que o medico escreve sozinho.
Exit 0 sempre — nunca bloqueia um compact.

Stdlib apenas, cross-platform. Corre com UM interpretador: o que o instalador
grava em __PYTHON__ nos snippets desta maquina. Nunca duas execucoes encadeadas
(python e depois python3): a repeticao substitui o codigo de saida da primeira.
"""
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

RAIZ = Path.cwd()
AGENTS = RAIZ / ".agents"
HANDOVER = AGENTS / "handover.md"
SNAPSHOT = AGENTS / "handover-snapshot.md"


def git(*args):
    try:
        r = subprocess.run(["git", *args], cwd=RAIZ, capture_output=True,
                           text=True, timeout=15)
        return r.stdout.strip() if r.returncode == 0 else ""
    except (OSError, subprocess.TimeoutExpired):
        return ""


def main():
    try:
        json.load(sys.stdin)
    except Exception:
        pass
    if not AGENTS.is_dir():
        return 0
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, OSError):
        pass
    trailers = []
    if HANDOVER.exists():
        try:
            for linha in HANDOVER.read_text(encoding="utf-8").splitlines():
                s = linha.strip()
                if s.startswith("**Segue:**") or s.startswith("**À espera"):
                    trailers.append(s)
        except OSError:
            pass
    corpo = [
        "<!-- gerado: nao entra no INDEX -->",
        "",
        "# handover-snapshot — estado no momento do compact",
        "",
        f"> Gerado: {datetime.now().strftime('%Y-%m-%d %H:%M')} (fire-and-forget, medico_precompact.py)",
        "",
        "## git log --oneline -5",
        "",
        "```",
        git("log", "--oneline", "-5") or "(sem git ou sem commits)",
        "```",
        "",
        "## git status --porcelain",
        "",
        "```",
        git("status", "--porcelain") or "(limpo)",
        "```",
        "",
        "## Trailer lines do handover no momento do compact",
        "",
        *(trailers or ["(handover.md sem trailer lines)"]),
        "",
    ]
    try:
        SNAPSHOT.write_text("\n".join(corpo), encoding="utf-8")
    except OSError:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
