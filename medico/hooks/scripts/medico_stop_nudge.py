#!/usr/bin/env python3
"""medico_stop_nudge.py — hook Stop: bloqueia se codigo mudou sem docs.

Le o payload JSON do hook pelo stdin (ignora se ausente/invalido).
Se .agents/ nao existir -> exit 0 (silencioso).
Se ficheiros de codigo mudaram (git status --porcelain; sem git -> mtimes)
e os docs nao foram tocados -> imprime uma linha para stderr e exit 2
(nudge: no Kimi/Claude o exit 2 bloqueia o Stop e alimenta o stderr ao modelo).
Anti-loop: grava .agents/.medico-nudge-state; dispara no maximo 1x por 4h.
O .medico-nudge-state (estado do proprio nudge) nao e documentacao: por
commitar, nao conta como doc tocado — senao o primeiro aviso calava os
seguintes mesmo depois das quatro horas. O mesmo vale para qualquer .md
cuja primeira linha comeca por "<!-- gerado" (handover-snapshot.md,
medico-log.md, ...) — a mesma regra do indice do bora: ficheiro gerado
por hook/agenda nao e um documento do projecto, por commitar nao cala
o nudge.

Stdlib apenas, cross-platform. Corre com UM interpretador: o que o instalador
grava em __PYTHON__ nos snippets desta maquina. Nunca duas execucoes encadeadas
(python e depois python3): a repeticao le o estado recem-gravado e mascara o exit 2.
"""
import json
import subprocess
import sys
import time
from pathlib import Path

RAIZ = Path.cwd()
AGENTS = RAIZ / ".agents"
HANDOVER = AGENTS / "handover.md"
ESTADO = AGENTS / ".medico-nudge-state"
INTERVALO_S = 4 * 3600

# Recurso local; a fonte e o EXT_CODIGO do verificar_docs.py do bora (usada abaixo, quando o projecto o tem).
EXT_CODIGO = {
    ".py", ".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs", ".ps1", ".sh",
    ".go", ".rs", ".java", ".cs", ".c", ".cc", ".cpp", ".h", ".hpp",
    ".rb", ".php", ".swift", ".kt", ".scala", ".lua", ".sql", ".html",
    ".css", ".vue", ".svelte",
}
DIRS_IGNORAR = {".git", ".agents", "node_modules", ".venv", "venv",
                "__pycache__", "dist", "build", "target", ".next"}


def _ext_codigo_do_projecto():
    """A mesma lista que o verificador usa: se o projecto tem
    .agents/tools/verificar_docs.py, importa-se a de la (a fonte unica).
    Import por caminho e nao por nome: qualquer erro — ficheiro em falta,
    versao antiga, sintaxe de outro interpretador — cai silenciosamente na
    lista local; o hook nunca rebenta por causa disto."""
    try:
        import importlib.util
        caminho = AGENTS / "tools" / "verificar_docs.py"
        if not caminho.is_file():
            return None
        spec = importlib.util.spec_from_file_location(
            "bora_verificar_docs", caminho)
        if spec is None or spec.loader is None:
            return None
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        ext = getattr(mod, "EXT_CODIGO", None)
        return set(ext) if ext else None
    except Exception:
        return None


EXT_CODIGO = _ext_codigo_do_projecto() or EXT_CODIGO


def git(*args):
    try:
        r = subprocess.run(["git", *args], cwd=RAIZ, capture_output=True,
                           text=True, timeout=15)
        return r.returncode, r.stdout
    except (OSError, subprocess.TimeoutExpired):
        return 1, ""


def mtime(p):
    try:
        return p.stat().st_mtime
    except OSError:
        return 0.0


def gerado(p):
    """True se p e um ficheiro gerado por hook/agenda: .md cuja primeira
    linha comeca por "<!-- gerado" — a regra do indice do bora. Nao e
    documentacao; por commitar, nao conta como doc tocado."""
    try:
        with open(p, encoding="utf-8", errors="replace") as f:
            primeira = f.readline().lstrip("\ufeff")
    except OSError:
        return False
    return primeira.startswith("<!-- gerado")


def e_doc(p):
    """p (em .agents/) conta como documentacao? O estado do nudge e os
    ficheiros gerados nao."""
    if p.name == ".medico-nudge-state":
        return False
    if p.suffix.lower() == ".md" and gerado(RAIZ / p):
        return False
    return True


def mudancas_com_git():
    """-> (codigo_mudado: list[str], docs_tocados: bool)"""
    rc, out = git("status", "--porcelain")
    if rc != 0:
        return None, None
    codigo, docs = [], False
    for linha in out.splitlines():
        if len(linha) < 4:
            continue
        caminho = linha[3:].strip().strip('"')
        if " -> " in caminho:  # rename: conta o destino
            caminho = caminho.split(" -> ", 1)[1]
        p = Path(caminho)
        if p.parts and p.parts[0] == ".agents":
            if e_doc(p):
                docs = True
        elif p.suffix.lower() in EXT_CODIGO:
            codigo.append(caminho)
    return codigo, docs


def mudancas_sem_git(ref_mtime):
    """Sem git: compara mtimes. -> (codigo_recente: list[str], docs_tocados: bool)
    docs_tocados usa > estrito: o proprio handover e a referencia temporal
    (ref_mtime = o mtime dele) e nao pode contar como doc tocado contra si
    proprio — com >=, o handover existente calava o nudge para sempre."""
    codigo, docs_mtime = [], 0.0
    for p in RAIZ.rglob("*"):
        if not p.is_file():
            continue
        partes = set(p.relative_to(RAIZ).parts)
        if partes & DIRS_IGNORAR:
            continue
        if p.suffix.lower() in EXT_CODIGO and mtime(p) > ref_mtime:
            codigo.append(str(p.relative_to(RAIZ)))
    if AGENTS.is_dir():
        for p in AGENTS.rglob("*"):
            if p.is_file() and e_doc(p):
                docs_mtime = max(docs_mtime, mtime(p))
    docs_tocados = docs_mtime > ref_mtime > 0
    return codigo, docs_tocados


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, OSError):
        pass
    try:
        json.load(sys.stdin)  # payload do hook: nao precisamos do conteudo
    except Exception:
        pass
    if not AGENTS.is_dir():
        return 0
    agora = time.time()
    if ESTADO.exists():
        try:
            if agora - float(ESTADO.read_text(encoding="utf-8").strip()) < INTERVALO_S:
                return 0
        except (ValueError, OSError):
            pass
    ref_mtime = mtime(HANDOVER)
    codigo, docs = mudancas_com_git()
    if codigo is None:
        codigo, docs = mudancas_sem_git(ref_mtime)
    if codigo and not docs:
        recentes = [c for c in codigo if mtime(RAIZ / c) > ref_mtime]
        if recentes or not HANDOVER.exists():
            try:
                ESTADO.write_text(str(agora), encoding="utf-8")
            except OSError:
                pass
            print(f"{len(codigo)} ficheiros de código mudaram sem docs —"
                  " corre /medico antes de fechar", file=sys.stderr)
            return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
