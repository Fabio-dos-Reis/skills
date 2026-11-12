#!/usr/bin/env python3
# By Fabio Reis.
"""indice.py — gera .agents/INDEX.md: uma linha por .md de .agents/ (recursivo).

Listagem deterministica, sem pesquisa e sem adivinhar estados: cada campo
e tirado do PROPRIO ficheiro — caminho, titulo (o 1.º `# `), estado (a linha
`**Estado:**`, senao —) e numero de linhas. Sem datas de git nem do disco:
um indice que muda a cada commit nunca esta em dia. A mesma arvore da sempre
a mesma saida, byte a byte (fins de linha `\\n`), em Windows e em Linux.

Ficam fora do indice: os modelos (`000-template/`, `0000-template.md`,
`pre-registo-template.md`), os arquivos (`*-archive/` e a pasta `archive/`,
para onde o tasks.md manda arquivar specs), o proprio INDEX e
os .md GERADOS por hook/agenda (primeira linha `<!-- gerado`): esses
aparecem e desaparecem sem o INDEX ter de mudar.

Sem argumentos escreve o INDEX; `--verificar` sai 1 se o INDEX em disco for
diferente do que seria gerado agora (e 0 se estiver em dia). O `--verificar`
compara com os fins de linha normalizados dos dois lados: o core.autocrlf do
Windows poe CRLF no INDEX no checkout/merge, e isso e ruido, nao conteudo.

Guarda do INDEX manual (P1, juizes ronda 6): um INDEX.md escrito a mao —
sem o cabecalho «Gerado por» desta ferramenta — guarda-se primeiro como
INDEX.md.bak (sem sobrepor um .bak existente: .bak2, .bak3, …) antes de ser
substituido, e diz-se; o modo `actualizar` do /bora manda correr esta
escrita, e substituir um indice manual sem o guardar era perder o trabalho
de alguem. O INDEX gerado por esta ferramenta continua a ser regenerado em
silencio.

Ilegivel NUNCA e vazio (P4, juizes ronda 6): um INDEX.md que EXISTE mas
NAO se le (sem permissao de leitura) NAO e «seguro de substituir» — a
ferramenta PARA sem escrever nada, diz qual e o ficheiro e sai 1.

Corre-se com `python` ou `python3` — o que existir na maquina
(`python x.py || python3 x.py`).
"""
import re
import sys
from pathlib import Path

AGENTS = Path(__file__).resolve().parent.parent
INDEX = AGENTS / "INDEX.md"

NOME_INDEX = "INDEX.md"
MODELOS = ("0000-template.md", "pre-registo-template.md")
PASTA_MODELO = "000-template"
SUFIXO_ARQUIVO = "-archive"
PASTA_ARQUIVO = "archive"

RX_TITULO = re.compile(r"^#\s+(.+?)\s*$", re.M)
RX_ESTADO = re.compile(r"^\s*(?:[-*]\s*)?\*\*Estado:\*\*\s*(.+?)\s*$", re.M)

CABECALHO = (
    "# INDEX — indice de .agents/\n"
    "\n"
    "> Gerado por `tools/indice.py` — NAO editar a mao. Regenera-se no mesmo\n"
    "> passo em que um `*.md` de `.agents/` muda (regra D6 do AGENTS.md).\n"
    "> Uma linha por documento: so o que esta escrito no ficheiro.\n"
    "\n"
    "| Documento | Titulo | Estado | Linhas |\n"
    "|---|---|---|---|\n"
)


def fora_do_indice(rel):
    """Modelos, arquivos e o proprio INDEX nao sao documentos do projecto."""
    partes = rel.parts
    if rel.name == NOME_INDEX:
        return True
    if rel.name in MODELOS:
        return True
    if PASTA_MODELO in partes[:-1]:
        return True
    # os arquivos: pastas com o sufixo -archive E a pasta «archive» — para
    # onde o tasks.md manda arquivar specs (specs/archive/, uma subpasta por spec arquivada)
    return any(p == PASTA_ARQUIVO or p.endswith(SUFIXO_ARQUIVO)
               for p in partes[:-1])


def campo(rx, texto):
    m = rx.search(texto)
    return m.group(1).strip() if m else "—"


def celula(s):
    """O '|' parte a tabela — escapa-se (deterministico, igual em todo o lado)."""
    return s.replace("|", "\\|")


def docs_md():
    """Os documentos (.md) de .agents/, o MESMO em Windows e em Linux:
    rglob("*.md") casa "*.MD" em Windows (sistema de ficheiros sem
    distincao de caso) e nao em Linux — a mesma arvore dava indices
    diferentes. O sufixo compara-se em minusculas. Pastas com sufixo .md
    entram: nao se leem, mas ficam LISTADAS com o estado a dizer que nao se
    leram (tira-las em silencio e o pior)."""
    return sorted((p for p in AGENTS.rglob("*") if p.suffix.lower() == ".md"),
                  key=lambda p: p.relative_to(AGENTS).as_posix())


def gerado(texto):
    """Saida gerada por hook/agenda: a PRIMEIRA linha comeca por
    '<!-- gerado'. Nao e um documento do projecto — fica fora do indice."""
    return texto.split("\n", 1)[0].startswith("<!-- gerado")


def gerar():
    """Conteudo do INDEX para a arvore atual, ou None se nao ha .agents/."""
    if not AGENTS.is_dir():
        return None
    linhas = [CABECALHO]
    for p in docs_md():
        rel = p.relative_to(AGENTS)
        if fora_do_indice(rel):
            continue
        try:
            texto = p.read_text(encoding="utf-8", errors="replace")
        except OSError:
            linhas.append(f"| `{rel.as_posix()}` | — | ilegível (não lido) "
                          "| — |\n")
            continue
        if gerado(texto):
            continue
        linhas.append(
            f"| `{rel.as_posix()}` | {celula(campo(RX_TITULO, texto))} "
            f"| {celula(campo(RX_ESTADO, texto))} "
            f"| {len(texto.splitlines())} |\n")
    return "".join(linhas)


def guardar_index_manual():
    """P1 (juizes, ronda 6): um INDEX.md escrito a mao — sem o cabecalho
    «Gerado por» desta ferramenta — guarda-se antes de ser substituido
    (INDEX.md.bak; se existir, .bak2, .bak3, … — nunca se sobrepoe um
    backup). O INDEX gerado por esta ferramenta e substituido em silencio,
    como sempre. P4 (juizes, ronda 6): um INDEX que EXISTE mas NAO se le
    NUNCA e tratado como vazio — a ferramenta para sem escrever, diz qual
    e o ficheiro e main sai 1. -> True se e seguro escrever; False se o
    manual ficou por guardar ou e ilegivel (nesse caso nada se substitui)."""
    if not INDEX.is_file():
        return True
    try:
        em_disco = INDEX.read_text(encoding="utf-8", errors="replace")
    except OSError as e:
        # ilegivel NUNCA e vazio (P4, juizes ronda 6): existir sem se ler
        # nao e «seguro de substituir» — e o indice manual de alguem. Parar
        # sem escrever nada; main sai 1.
        print(f"INDEX.md em disco existe mas NAO o consigo ler ({e}) — "
              "ilegivel NUNCA e vazio: parei SEM o guardar e SEM o "
              "substituir; resolve a mao.")
        return False
    if "Gerado por `tools/indice.py`" in em_disco:
        return True                      # gerado por esta ferramenta
    bak = INDEX.with_name(INDEX.name + ".bak")
    n = 2
    while bak.exists():
        bak = INDEX.with_name(f"{NOME_INDEX}.bak{n}")
        n += 1
    try:
        INDEX.replace(bak)
    except OSError as e:
        print(f"INDEX.md em disco foi escrito a mao e NAO o consegui guardar "
              f"como {bak.name}: {e} — nada foi substituido; resolve a mao.")
        return False
    print(f"INDEX.md em disco foi escrito a mao (sem o cabecalho «Gerado "
          f"por» desta ferramenta) — guardado primeiro como {bak.name}.")
    return True


def main(argv):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, OSError):
        pass
    conteudo = gerar()
    if conteudo is None:
        print(f"sem pasta .agents/ ao lado de tools/ — nada a indexar ({AGENTS})")
        return 1
    if "--verificar" in argv:
        try:
            em_disco = INDEX.read_bytes()
        except OSError:
            em_disco = None
        # normalizam-se os fins de linha DOS DOIS lados antes de comparar:
        # o core.autocrlf do Windows poe CRLF no INDEX no checkout/merge —
        # ruido de fim de linha, nao desatualizacao de conteudo. O conteudo
        # e que conta: um INDEX certo com CRLF NAO e «em falta ou desatualizado»
        gerado = conteudo.encode("utf-8").replace(b"\r\n", b"\n")
        if em_disco is not None and em_disco.replace(b"\r\n", b"\n") == gerado:
            print(f"INDEX em dia ({INDEX})")
            return 0
        print(f"INDEX em falta ou desatualizado ({INDEX}) — regenera: "
              "`python .agents/tools/indice.py || python3 .agents/tools/indice.py`")
        return 1
    if not guardar_index_manual():
        return 1
    INDEX.write_text(conteudo, encoding="utf-8", newline="\n")
    n = conteudo.count("\n") - CABECALHO.count("\n")
    print(f"INDEX escrito ({INDEX}): {n} documento(s) listado(s).")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
