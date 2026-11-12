#!/usr/bin/env python3
# By Fabio Reis.
"""verificar_docs.py — D6-lite: saude da documentacao .agents/ (stdlib, cross-platform).

Checks:
  1. arvore git por commitar                    -> aviso (lista ficheiros uncommitted)
  2. .md em .agents/ fora do git                -> ERRO (um .md cuja primeira
     linha comeca por `<!-- gerado` — escrito por hooks — nao e' documento do
     projecto e fica de fora, com a MESMA regra do indice.py)
  3. referencias: caminhos `*.py`/`*.md`/`*.sh` entre backticks em .agents/**/*.md
     e no AGENTS.md da raiz. Falta em disco e:
       - o git ja o conheceu (foi apagado)      -> aviso "referencia historica"
       - nunca existiu                          -> ERRO "referencia morta"
     Ignoram-se spans de comando: so os que tem flags (-x/--x), URL, placeholder
     (<...>), padroes com chavetas ({a,b}) ou metacaracteres de shell ($ | * ; ( ) &).
     Um caminho com espacos (`Bug Agent/bug.md`) NUNCA e comando — verifica-se tal qual.
     Resolucao tenta: raiz, pasta do doc, e `.agents/` (o mapa do AGENTS.md refere
     ficheiros que vivem em `.agents/`, e o "ja o conheceu" tambem tenta `.agents/`).
  4. codigo sem documentacao (D6): janela = ultimos JANELA_COMMITS commits COM
     mudancas (A/C/M/R) na linha principal — um commit so de apagamentos nao
     conta para a janela. (-m --first-parent: um merge conta com os ficheiros que trouxe
     relativamente ao primeiro pai — um .md introduzido so no merge commit NAO
     desaparece do historico). LINHA DE BASE: so se julgam commits a partir do
     primeiro que introduziu `.agents/` — o esqueleto nasce ai (decisao do
     supervisor, U1 da ronda 3: um repositorio com historia anterior ao
     esqueleto nao se reescreve para agradar ao verificador); projeto sem
     `.agents/` em historia nao comecou a disciplina e nada se julga. Commit
     que toca ficheiros de codigo e NENHUM .md
     (o INDEX.md gerado por maquina NAO conta — nao e documentacao de codigo):
       - .md em commit posterior que MENCIONE o codigo -> aviso (documentado so depois)
       - caso contrario                          -> ERRO (nomeia ficheiro + hash curto)
     REGRA "documentado depois" (decidida na correcao V1, ronda 2 — um .md qualquer
     em commit posterior convertia ERRO em aviso, semanas depois, sem relacao nenhuma
     com o codigo). Caminhos considerados:
       a) qualquer .md posterior conta           — REJEITADA: e o defeito V1;
       b) limite de horas entre commits          — REJEITADA: refem do relogio do
          commit e de fusos; horas nao provam relacao;
       c) o .md posterior tem de MENCIONAR o ficheiro de codigo (basename ou stem
          com fronteira de palavra)              — ESCOLHIDA: auditavel, sem relogio,
          e quem documenta atrasado nomeia o que documentou. Sem menção em nenhum
          .md posterior mantem-se o ERRO.
     Janela definida para um repositorio acabado de criar pelo bora PASSAR: o
     commit inicial do bora traz o esqueleto .agents/ cheio de .md, logo o codigo
     dele parte documentado no mesmo commit; um repositorio sem commits tambem
     passa (nada a verificar). Pastas geradas casam por COMPONENTE de caminho
     (src/layout/app.py NAO e pasta gerada apesar de conter "out/") e extensoes
     geradas nao contam como codigo (*.min.js, *_pb2.py, ...).
  5. estado das decisoes: ADR em .agents/decisions/ (exceto 0000-template.md) tem de
     ter linha `**Estado:**` com valor do modelo (proposto | aceite | substituido por
     ADR-NNNN — podendo o valor trazer data a seguir entre parenteses); so e' ADR
     o ficheiro cujo nome comeca por digitos (um README.md da pasta nao e ADR) e a
     extensao compara-se em minusculas (o MESMO em Windows e em Linux). "substituido
     por ADR-NNNN" reprova se esse ADR nao existir na mesma pasta. ORIGEM: regra do
     fundador — uma decisao revogada servida como atual e o pior defeito. Projeto
     sem ADRs passa.
  6. tetos de leitura obrigatoria: handover.md acima do teto -> ERRO (manda
     correr rodar_handover.py); AGENTS.md acima do teto -> aviso; INDEX.md
     em falta ou desatualizado -> ERRO (manda correr indice.py); ferramentas
     em falta em .agents/tools/ -> ERRO (modo `actualizar` do /bora — um
     projecto de versao antiga nao as recebe por atualizacao da skill, e
     mandar «gera o INDEX» com uma ferramenta inexistente era mentira). Uma
     ferramenta apagada de proposito (vista pelo git como deleted) fica de
     fora deste erro — quem a apagou nao a quer de volta.
     ORIGEM: escrever o teto sem o verificar e como nao o ter (este repo
     chegou as 856 linhas com a regra escrita). O teto e a regra de leitura
     vivem no AGENTS.md gerado — aqui VERIFICAM-SE, nao se repetem.

Exit 1 se houver qualquer ERRO. Projeto sem repositorio git: os checks que
precisam de git nao correm e o veredicto e NAO VERIFICADO (exit 1) — "APROVADO"
com a maioria dos checks por correr colava como prova de dia fechado. A linha
final declara a cobertura — a conclusao de um verificador limita-se ao que ele
verifica. Correr antes de declarar um dia/bloco fechado (ordem permanente do
AGENTS.md) e colar o resultado.
"""
import importlib.util
import re
import subprocess
import sys
from pathlib import Path

RAIZ = Path.cwd()
SPAN = re.compile(r"`([^`\n]+)`")
EXTENSOES_DOC = (".py", ".md", ".sh")
JANELA_COMMITS = 15

# Teto do handover: o numero e constante AQUI, unico no codigo (o
# rodar_handover.py importa-a — o mesmo teto nas duas ferramentas). O facto
# (e a regra de leitura de arranque) vivem no AGENTS.md gerado. Verifica-se,
# nao se promete.
TETO_HANDOVER = 150
TETO_AGENTS = 120

EXT_CODIGO = (".py", ".js", ".mjs", ".cjs", ".jsx", ".ts", ".tsx", ".mts",
              ".java", ".c", ".cc", ".cpp", ".cxx", ".h", ".hh", ".hpp",
              ".cs", ".go", ".rs", ".rb", ".php", ".sh", ".bash", ".ps1",
              ".sql", ".kt", ".kts", ".swift", ".m", ".mm", ".scala",
              ".lua", ".pl", ".pm", ".r", ".vue", ".svelte", ".html", ".css",
              ".ex", ".exs", ".erl", ".fs", ".clj", ".dart", ".groovy")
# FONTE da lista «o que e' codigo»: o medico_stop_nudge.py (skill medico) espelha-a.
# casam por COMPONENTE de caminho (ex.: "dist" como pasta), nunca por substring —
# "src/layout/app.py" contem "out/" mas "layout" nao e pasta gerada.
PASTAS_GERADAS = ("node_modules", "bower_components", "dist", "build", "out",
                  "target", "bin", "obj", "vendor", "coverage", ".next",
                  ".nuxt", "__pycache__", ".venv", "venv", ".git", ".idea",
                  ".gradle", "gen", "generated", "third_party")
SUFIXOS_GERADOS = (".min.js", ".min.css", "_pb2.py", ".pb.go", ".designer.cs",
                   ".g.cs", ".generated.", ".gen.")

LINHA_ESTADO = re.compile(r"^\s*(?:[-*]\s*)?\*\*Estado:\*\*\s*(.+?)\s*$", re.M)
# o estado pode trazer data a seguir entre parenteses: «aceite (2026-10-02)»
# (U5, ronda 3) — o que conta e' o valor do modelo, nao a data da decisao
ESTADO_ADR_OK = re.compile(r"^(proposto|aceite)(?:\s*\(.*\))?\s*$", re.IGNORECASE)
ESTADO_ADR_SUB = re.compile(r"^substitu[ií]do\s+por\s+ADR-(\d+)"
                            r"(?:\s*\(.*\))?\s*$", re.IGNORECASE)


def _carregar_gerado():
    """A regra «isto nao e' um documento do projecto» e' a MESMA do
    indice.py: a primeira linha comeca por `<!-- gerado` (ficheiros que os
    hooks — medico, handover — escrevem sozinhos). Importa-se a funcao DE
    LA' (mesma pasta, mesma regra nos dois lados); se o indice.py faltar,
    cai-se numa copia minima local — a assinatura gerado(texto) e' contratada
    e nao muda."""
    try:
        import indice
        return indice.gerado
    except ImportError:
        pass
    caminho = Path(__file__).resolve().parent / "indice.py"
    if caminho.is_file():
        spec = importlib.util.spec_from_file_location("indice_local", caminho)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod.gerado

    def gerado_minimo(texto):
        return texto.split("\n", 1)[0].startswith("<!-- gerado")

    return gerado_minimo


gerado = _carregar_gerado()


def numero_do_adr(nome):
    """Numero de um ADR a partir do nome do ficheiro: '0001-x.md' -> 1,
    'ADR-0002-y.md' -> 2, '0002 segunda.md' -> 2, '0001.md' -> 1 (o
    separador depois dos digitos pode ser '-', espaco, ponto — o fim do
    numero antes da extensao — ou fim; P7, juizes ronda 6: '0001.md' era
    ignorado e um ADR sem estado com esse nome passava em branco),
    'relatorio.md' -> None. So e' ADR o ficheiro cujo nome comeca por
    digitos. O numero compara-se como NUMERO (R4): zeros a esquerda nao
    distinguem ADRs e prefixos de outro numero ('ADR-00020-x.md' nao e o
    ADR-0002)."""
    m = re.match(r"^(?:ADR-)?(\d+)(?:[-\s.]|$)", nome)
    return int(m.group(1)) if m else None


def git(*args):
    try:
        # TODA a saida do git se le como UTF-8 com errors='replace' (U3,
        # ronda 3): text=True sem encoding pega no encoding por defeito da
        # maquina (cp1252 no Windows) e `git show` de um .md com «Í»
        # rebentava — o MESMO repositorio dava ⛔ no Windows e ✓ no Linux
        r = subprocess.run(["git", *args], cwd=RAIZ, capture_output=True,
                           text=True, encoding="utf-8", errors="replace",
                           timeout=30)
        return r.returncode, r.stdout
    except (OSError, subprocess.TimeoutExpired):
        return 1, ""


def e_git():
    rc, out = git("rev-parse", "--is-inside-work-tree")
    return rc == 0 and out.strip() == "true"


def check_arvore_limpa():
    """-> (avisos, erros)"""
    rc, out = git("status", "--porcelain")
    if not out.strip():
        return [], []
    linhas = [l for l in out.splitlines() if l.strip()]
    lista = [f"    {l}" for l in linhas[:20]]
    return [f"arvore git por commitar ({len(linhas)} ficheiros):"] + lista, []


def docs_md(pasta):
    """Os `*.md` de uma pasta, o MESMO em Windows e em Linux: rglob("*.md")
    casa "*.MD" em Windows (sistema de ficheiros sem distincao de caso) e
    nao em Linux — a mesma arvore dava veredictos diferentes. O sufixo
    compara-se em minusculas. Pastas com sufixo .md entram na lista (nao se
    leem, mas quem consome decide o que lhes faz — o indice lista-as como
    ilegiveis, aqui contam como doc fora do git)."""
    return sorted((p for p in pasta.rglob("*") if p.suffix.lower() == ".md"),
                  key=lambda p: p.relative_to(pasta).as_posix())


def check_docs_tracked():
    """.md em .agents/ nao tracked pelo git -> erros. Um .md cuja primeira
    linha comece por `<!-- gerado` NAO e documento do projecto (e' escrito
    por hooks — medico, handover — e commitar esses ficheiros era pedir luta
    com o proprio hook): fica de fora deste check, com a MESMA regra do
    indice.py (U2, ronda 3)."""
    pasta = RAIZ / ".agents"
    if not pasta.is_dir():
        return [], []
    # -z: com nomes acentuados o git cita-os entre aspas com octais
    # («"0001-decis\303\243o.md"») e um doc tracked reprovava como «fora do
    # git» sem remedio (U4, ronda 3); com -z o git nunca cita nomes
    rc, out = git("ls-files", "-z", "--", ".agents")
    tracked = {l for l in out.split("\0") if l}
    erros = []
    for md in docs_md(pasta):
        rel = md.relative_to(RAIZ).as_posix()
        try:
            with md.open("r", encoding="utf-8", errors="replace") as f:
                primeira = f.readline()
        except OSError:
            primeira = ""
        if primeira and gerado(primeira):
            continue
        if rel not in tracked:
            erros.append(f"doc fora do git: {rel} (faz git add)")
    return [], erros


def parece_comando(span):
    """Ignora-se APENAS comando/URL/placeholder/padrão. Caminho com espacos nao e comando."""
    if "://" in span or "<" in span or ">" in span:
        return True
    if any(c in span for c in "$|*;()&{}"):
        return True
    return any(tok.startswith("-") for tok in span.split())


def candidatos(span, md):
    """Caminhos a verificar dentro de um span que passou o filtro de extensao."""
    if " " not in span:
        return [span]
    s = span[2:] if span.startswith("./") else span
    if (RAIZ / s).exists() or (md.parent / s).exists():
        return [s]                       # caminho com espacos que existe em disco
    primeiro = s.split()[0]
    if "/" in primeiro or "\\" in primeiro:
        return [s]      # comeca por caminho e nao existe -> referencia morta, nao comando
    ultimo = s.split()[-1]
    if "/" in ultimo or "\\" in ultimo:
        return [s]      # R2: o ultimo token e um caminho — o span e um caminho
                        # com espacos em falta, que se verifica TAL QUAL; um
                        # sufixo dele existir em disco ("Agent/bug.md" quando
                        # se pede "Bug Agent/bug.md") nao o salva
    return []           # "comando ficheiro.py" — nenhum caminho com espacos


def existiu_no_git(alvo):
    """O git ja conheceu este caminho? Tenta tambem `.agents/<alvo>` — o mapa do
    AGENTS.md refere ficheiros que viviam dentro de .agents/."""
    for cand in (alvo, f".agents/{alvo}"):
        rc, out = git("log", "--diff-filter=D", "--pretty=format:%h", "-n", "1",
                      "--", cand)
        if rc == 0 and out.strip():
            return True
    return False


def check_referencias():
    """Referencias entre backticks que nao existem em disco."""
    ficheiros = docs_md(RAIZ / ".agents") if (RAIZ / ".agents").is_dir() else []
    if (RAIZ / "AGENTS.md").is_file():
        ficheiros.append(RAIZ / "AGENTS.md")
    erros, avisos = [], []
    vistos = set()
    for md in ficheiros:
        rel_doc = md.relative_to(RAIZ).as_posix()
        try:
            texto = md.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        if gerado(texto):
            continue                     # escrito por hook: nao e' documento
                                         # do projecto (mesma regra do
                                         # indice.py e do check «fora do git»)
        for span in SPAN.findall(texto):
            tokens = span.split()
            acaba_ext = span.endswith(EXTENSOES_DOC) or \
                (bool(tokens) and tokens[-1].endswith(EXTENSOES_DOC))
            if not acaba_ext or parece_comando(span):
                continue
            for alvo in candidatos(span, md):
                a = alvo[2:] if alvo.startswith("./") else alvo
                a = a.lstrip("/")
                chave = (rel_doc, span, a)
                if chave in vistos:
                    continue
                vistos.add(chave)
                if ((RAIZ / a).exists() or (md.parent / a).exists()
                        or (RAIZ / ".agents" / a).exists()):
                    continue
                if existiu_no_git(a):
                    avisos.append(f"referencia historica (ficheiro apagado) "
                                  f"em {rel_doc}: `{span}`")
                else:
                    erros.append(f"referencia morta em {rel_doc}: `{span}`")
    return avisos, erros


def e_codigo(f):
    fl = f.lower().replace("\\", "/")
    componentes = fl.split("/")
    if any(c in PASTAS_GERADAS for c in componentes[:-1]):
        return False                     # pasta gerada: por componente, nao substring
    if any(fl.endswith(s) for s in SUFIXOS_GERADOS):
        return False
    if "." not in componentes[-1]:
        return False
    return ("." + componentes[-1].rsplit(".", 1)[-1]) in EXT_CODIGO


_TEXTO_COMMIT = {}


def _texto_no_commit(h, caminho):
    chave = (h, caminho)
    if chave not in _TEXTO_COMMIT:
        rc, out = git("show", f"{h}:{caminho}")
        _TEXTO_COMMIT[chave] = out if rc == 0 else None
    return _TEXTO_COMMIT[chave]


def _commit_base_esqueleto():
    """Hash curto do commit mais antigo que introduziu `.agents/` — a linha
    de base do check 4. DEFINICAO (decisao do supervisor, U1 da ronda 3):
    o esqueleto nasce nesse commit, logo a disciplina «codigo documentado»
    so julga commits DESSE em diante; os anteriores sao historia e nao se
    julgam — nao se reescreve historia para agradar ao verificador.
    Sem `.agents/` em historia: None (a disciplina nao comecou).
    A leitura e a MESMA da janela (check_codigo_documentado): `-m
    --first-parent` (P6, juizes ronda 6) — sem isso, um esqueleto trazido
    por `merge --no-ff` dava um hash de um commit de RAMO, invisivel na
    janela (que so ve a linha principal), e commits anteriores a adopcao
    reprovavam; base e janela tem de ler a historia da mesma forma."""
    rc, out = git("log", "--reverse", "-m", "--first-parent",
                  "--diff-filter=A", "--pretty=format:%h", "--", ".agents")
    if rc != 0 or not out.strip():
        return None
    return out.splitlines()[0].strip()


def commit_documenta_codigo(h, codigo):
    """True se algum .md do commit h menciona algum ficheiro de codigo
    (basename ou stem com fronteira de palavra). Regra V1: menção, não relógio.
    -m --first-parent: sem -m, `git show` de um MERGE nao lista os ficheiros
    que o ramo trouxe (diff combinado so mostra o que difere de TODOS os
    pais) — um .md commitado no ramo ficava invisivel. -z: com acentos no
    nome o git cita-o entre aspas com octais e o fim «.md» deixava de se
    reconhecer (o MESMO defeito do ls-files, U4)."""
    rc, out = git("show", "-z", "-m", "--first-parent", "--name-only",
                  "--format=", h)
    if rc != 0:
        return False
    # o sufixo compara-se em minusculas: o MESMO criterio do docs_md() —
    # um .MD de um commit posterior conta como documentacao como um .md
    mds = [l for l in out.split("\0")
           if l.strip().lower().endswith(".md")]
    if not mds:
        return False
    padroes = []
    for f in codigo:
        base = f.replace("\\", "/").rsplit("/", 1)[-1]
        stem = base.rsplit(".", 1)[0]
        if stem:
            padroes.append(re.escape(base))
            padroes.append(r"\b" + re.escape(stem) + r"\b")
    if not padroes:
        return False
    rx = re.compile("|".join(padroes))
    for md in mds:
        texto = _texto_no_commit(h, md)
        if texto is not None and rx.search(texto):
            return True
    return False


def check_codigo_documentado():
    """D6: codigo sem .md no mesmo commit nem em commit posterior (janela
    recente). LINHA DE BASE (U1, ronda 3): so se julgam commits a partir
    do primeiro que introduziu `.agents/` — o esqueleto nasce ai; os
    anteriores sa'o historia e nao se julgam. Projeto sem `.agents/` em
    historia: a disciplina nao comecou, nada a julgar."""
    if not e_git():
        return [], []
    base = _commit_base_esqueleto()
    if base is None:
        return [], []
    # -m --first-parent: um merge conta como commit com os ficheiros que trouxe
    # relativamente ao primeiro pai — senao um .md so introduzido no merge (ex.:
    # resolucao de conflito) desaparecia do historico com --no-merges.
    rc, out = git("log", "-z", "-m", "--first-parent", "--diff-filter=ACMR",
                  "--pretty=format:@@%h",
                  "-n", str(JANELA_COMMITS), "--name-only")
    if rc != 0 or not out.strip():
        return [], []                    # sem historico (repo novo) -> passa
    # -z (U4): com acentos no nome o git cita-o entre aspas com octais no
    # modo linha — «"0001-decis\303\243o.md"» nao acaba em .md e o commit
    # parecia so de codigo; com -z os nomes vêm em UTF-8 cru, um registo
    # por NUL. ATENCAO: o marcador @@hash fica colado ao PRIMEIRO ficheiro
    # com '\n' («@@abc1234\nficheiro») — o registo do marcador parte-se em
    # '\n' antes de se classificar
    commits = []                         # [(hash, [ficheiros])], mais recente primeiro
    atual = None
    for registo in out.split("\0"):
        if registo.startswith("@@"):
            marcador = registo[2:].split("\n")
            atual = (marcador[0].strip(), [])
            commits.append(atual)
            if len(marcador) > 1 and marcador[1].strip():
                atual[1].append(marcador[1].strip())
        elif registo.strip() and atual is not None:
            atual[1].append(registo.strip())
    # julgam-se so' os commits da base (inclusive) ate' ao mais recente; se
    # a base esta' fora da janela, TODOS os da janela sao mais recentes que
    # ela e julgam-se inteiros
    for i, (h, _) in enumerate(commits):
        if h == base:
            commits = commits[:i + 1]
            break
    erros, avisos = [], []
    for i, (h, ficheiros) in enumerate(commits):
        codigo = [f for f in ficheiros if e_codigo(f)]
        # o INDEX.md e indice gerado por maquina, nao documentacao de codigo:
        # um commit de so codigo + regeneracao do INDEX continua a contar como
        # codigo sem documentacao. O sufixo compara-se em minusculas: o
        # MESMO criterio do docs_md() (um .MD real conta como doc)
        mds_reais = [f for f in ficheiros
                     if f.replace("\\", "/").lower().endswith(".md")
                     and f.replace("\\", "/") != ".agents/INDEX.md"]
        if not codigo or mds_reais:
            continue                     # sem codigo, ou .md real no mesmo commit
        doc_posterior = any(commit_documenta_codigo(commits[j][0], codigo)
                            for j in range(i))
        if doc_posterior:
            etiqueta = "documentado so em commit posterior"
            destino = avisos
        else:
            etiqueta = ("nenhum .md no mesmo commit nem em commit posterior "
                        "que mencione este codigo")
            destino = erros
        for f in codigo[:5]:
            destino.append(f"codigo sem documentacao: {f} ({h}) — {etiqueta}")
        if len(codigo) > 5:
            destino.append(f"codigo sem documentacao: … +{len(codigo) - 5} "
                           f"ficheiros ({h}) — {etiqueta}")
    return avisos, erros


def check_estado_decisoes():
    """ADR em .agents/decisions/ fora do modelo de estados -> ERRO.
    Modelo (templates/decisions/0000-template.md): proposto | aceite |
    substituido por ADR-NNNN — o estado pode trazer data a seguir entre
    parenteses («aceite (2026-10-02)», U5). «substituido por ADR-NNNN»
    reprova se o ADR-NNNN nao existir na mesma pasta — comparado como
    NUMERO (0002 == 2) e o destino nao pode ser o proprio ADR.
    SO e' ADR o ficheiro cujo nome comeca por digitos (U5): um README.md
    da pasta decisions nao e' ADR e nao leva estado. A extensao compara-se
    em minusculas — a MESMA regra do docs_md() (um «.MD» era visto em
    Windows e ignorado em Linux). ORIGEM: regra do fundador — uma decisao
    revogada servida como atual e o pior defeito. Projeto sem ADRs passa."""
    pasta = RAIZ / ".agents" / "decisions"
    if not pasta.is_dir():
        return [], []
    adrs = sorted((p for p in pasta.iterdir()
                   if p.is_file() and p.suffix.lower() == ".md"),
                  key=lambda p: p.name.lower())
    existentes = {f.name for f in adrs
                  if f.name != "0000-template.md"
                  and numero_do_adr(f.name) is not None}
    erros = []
    for adr in adrs:
        if adr.name == "0000-template.md":
            continue                     # o modelo nao e um ADR
        if numero_do_adr(adr.name) is None:
            continue                     # README.md e afins: nao sao ADRs
        rel = adr.relative_to(RAIZ).as_posix()
        try:
            texto = adr.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            erros.append(f"ADR ilegivel: {rel}")
            continue
        m = LINHA_ESTADO.search(texto)
        if not m:
            erros.append(f"ADR sem estado: {rel} — falta `- **Estado:**` "
                         "(proposto | aceite | substituido por ADR-XXXX)")
            continue
        valor = m.group(1).strip()
        if ESTADO_ADR_OK.match(valor):
            continue
        ms = ESTADO_ADR_SUB.match(valor)
        if ms:
            destino = int(ms.group(1))
            existe = any(numero_do_adr(x) == destino and x != adr.name
                         for x in existentes)
            if existe:
                continue
            erros.append(f"ADR substituido por inexistente: {rel} aponta "
                         f"ADR-{ms.group(1)}, que nao esta em "
                         f".agents/decisions/ (o destino tem de existir e "
                         "nao pode ser o proprio ADR)")
            continue
        erros.append(f"ADR com estado fora do modelo: {rel} — `{valor}` "
                     "(proposto | aceite | substituido por ADR-XXXX)")
    return [], erros


def ferramenta_apagada(nome):
    """A ferramenta existiu e foi apagada de proposito? «Vista pelo git como
    deleted» — apagada num commit (historico) ou por commitar (status em D).
    Quem a removeu deliberadamente sabe o que faz: exigi-la de volta apagava
    uma decisao do projecto e condenava o modo `actualizar` a repor o que
    o projecto decidiu tirar (a referencia historica fica no aviso do
    check 3)."""
    rc, out = git("log", "--diff-filter=D", "--pretty=format:%h", "-n", "1",
                  "--", f".agents/tools/{nome}")
    if rc == 0 and out.strip():
        return True
    rc, out = git("status", "--porcelain", "--", f".agents/tools/{nome}")
    if rc != 0:
        return False
    return any(l[:2] in ("D ", " D", "DD") for l in out.splitlines())


def check_tetos():
    """Leitura obrigatoria com teto verificado (nao so prometido):
    handover acima de TETO_HANDOVER -> ERRO (manda arquivar); AGENTS.md
    acima de TETO_AGENTS -> aviso; INDEX.md em falta ou desatualizado ->
    ERRO (manda regenerar — um .md de .agents/ mudou sem o mesmo passo);
    ferramentas em falta em .agents/tools/ -> ERRO (ferramentas apagadas
    de proposito, vistas pelo git como deleted, ficam de fora — quem as
    apagou nao as quer de volta). As duas situacoes distinguem-se (R7a):
    «faltam ferramentas» e um projecto criado por uma versao antiga do
    /bora — manda-se o modo `actualizar`; «INDEX em falta» com as
    ferramentas instaladas e so o ficheiro por gerar."""
    avisos, erros = [], []
    n_linhas = lambda p: len(p.read_text(encoding="utf-8", errors="replace")
                             .splitlines())
    tools = RAIZ / ".agents" / "tools"
    FERRAMENTAS = ("indice.py", "verificar_docs.py", "rodar_handover.py",
                   "medicoes.py")
    faltam = [f for f in FERRAMENTAS
              if not (tools / f).is_file() and not ferramenta_apagada(f)]
    if faltam and (RAIZ / ".agents").is_dir():
        erros.append("ferramentas em falta em .agents/tools/: "
                     + ", ".join(faltam)
                     + " — um projecto criado por uma versao antiga do /bora "
                       "nao as recebe por atualizacao da skill: corre o modo "
                       "`actualizar` do /bora (instala-as sem apagar nada)")
    handover = RAIZ / ".agents" / "handover.md"
    if handover.is_file() and n_linhas(handover) > TETO_HANDOVER:
        erros.append(
            f"handover acima do teto: {n_linhas(handover)} linhas "
            f"(teto {TETO_HANDOVER}) — arquiva as entradas antigas: "
            "`python .agents/tools/rodar_handover.py || "
            "python3 .agents/tools/rodar_handover.py`")
    agents = RAIZ / "AGENTS.md"
    if agents.is_file() and n_linhas(agents) > TETO_AGENTS:
        avisos.append(f"AGENTS.md com {n_linhas(agents)} linhas "
                      f"(teto ~{TETO_AGENTS}) — manutencao apaga, "
                      "nao acrescenta")
    index = RAIZ / ".agents" / "INDEX.md"
    indice = tools / "indice.py"
    if not index.is_file():
        if (RAIZ / ".agents").is_dir() and indice.is_file():
            erros.append("INDEX em falta — gera-o: "
                         "`python .agents/tools/indice.py || "
                         "python3 .agents/tools/indice.py`")
        # sem indice.py a causa ja vem no erro «ferramentas em falta» —
        # mandar «gera-o» seria um comando de uma ferramenta inexistente
    elif indice.is_file():
        try:
            r = subprocess.run([sys.executable, str(indice), "--verificar"],
                               cwd=RAIZ, capture_output=True, text=True,
                               encoding="utf-8", errors="replace",
                               timeout=60)
            desatualizado = r.returncode != 0
        except (OSError, subprocess.TimeoutExpired):
            desatualizado = False          # nao verificavel agora: nao se afirma
            avisos.append("INDEX: tools/indice.py --verificar nao correu — "
                          "frescura por verificar")
        if desatualizado:
            erros.append("INDEX desatualizado (um .md de .agents/ mudou sem "
                         "regenerar) — atualiza-o: "
                         "`python .agents/tools/indice.py || "
                         "python3 .agents/tools/indice.py`")
    else:
        avisos.append("INDEX existe mas tools/indice.py em falta — impossivel "
                      "verificar se esta atualizado (o modo `actualizar` do "
                      "/bora realinha as ferramentas)")
    return avisos, erros


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, OSError):
        pass
    avisos, erros = [], []
    print(f"verificar_docs — {RAIZ}")
    sem_git = not e_git()
    if sem_git:
        avisos.append("nao e um repositorio git — checks 1, 2 e 4 impossiveis")
    else:
        a, e = check_arvore_limpa()
        avisos += a
        erros += e
        a, e = check_docs_tracked()
        avisos += a
        erros += e
        a, e = check_codigo_documentado()
        avisos += a
        erros += e
    a, e = check_referencias()
    avisos += a
    erros += e
    a, e = check_estado_decisoes()
    avisos += a
    erros += e
    a, e = check_tetos()
    avisos += a
    erros += e

    for a in avisos:
        print(f"⚠ {a}")
    for e in erros:
        print(f"⛔ {e}")
    cobertura = ("Cobertura: arvore git por commitar · docs .agents/ fora do git "
                 "(exceto `<!-- gerado`) · referencias mortas em .agents/** e "
                 "AGENTS.md · codigo documentado desde o commit que introduziu "
                 f".agents/ (janela: ultimos {JANELA_COMMITS} commits com "
                 "mudancas A/C/M/R) · estado "
                 "dos ADRs · tetos de leitura obrigatoria (handover, AGENTS.md, "
                 "INDEX). Nao verifica mais nada.")
    if sem_git:
        print("\n⛔ NAO VERIFICADO (sem repositorio git): a maioria dos checks "
              "nao correu — nao serve como prova de dia fechado.")
        print(cobertura)
        return 1
    if erros:
        print(f"\n⛔ REPROVADO: {len(erros)} erro(s), {len(avisos)} aviso(s)."
              " Fecha-se escrevendo o que falta, nunca relaxando o criterio.")
        print(cobertura)
        return 1
    print(f"\n✓ APROVADO ({len(avisos)} aviso(s)).")
    print(cobertura)
    return 0


if __name__ == "__main__":
    sys.exit(main())
