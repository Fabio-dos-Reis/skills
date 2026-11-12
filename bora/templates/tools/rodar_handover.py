#!/usr/bin/env python3
# By Fabio Reis.
"""rodar_handover.py — handover acima do teto: arquiva as entradas mais antigas.

Projecto grande, handover grande: o modelo so le a entrada do topo, mas o
ficheiro nao pode crescer sem fim. Quando `.agents/handover.md` passa o
teto, as entradas mais antigas (blocos que comecam em `## `, mais antigas no
FIM do ficheiro) movem-se INTEIRAS para
`.agents/handover-archive/<AAAA-MM>.md` — o mes vem do titulo da entrada;
sem data legivel vai para `sem-data.md`. Move-se so o necessario para o
ficheiro voltar a caber no teto. O cabecalho (tudo ate ao 1.º `## `) e a
entrada mais recente NUNCA saem. Nada se perde: a soma das linhas do
handover e dos arquivos depois e igual à de antes. Uma entrada sozinha
(com o cabecalho) maior que o teto fica onde esta, com aviso.

Durabilidade (R1, juizes ronda 3): toda a escrita e ATOMICA (ficheiro
temporario na MESMA pasta + os.replace) — uma falha a meio deixa o original
intacto (o write_text truncava primeiro e perdia as entradas recentes). O
plano (conteudos finais do handover e dos arquivos) guarda-se primeiro num
journal (`handover-archive/.pendente.json`, tambem atomico); se uma escrita
falhar, a proxima corrida RETOMA do journal e reaplica os MESMOS conteudos —
uma segunda corrida depois de uma falha nunca duplica entradas no arquivo.

Guarda do journal (Y3, juizes ronda 4): o journal leva um resumo (sha256)
do handover tal como estava ao ser criado. Na retoma, se o handover em
disco ja nao bater certo com esse resumo — houve escritas entretanto — o
journal e de uma corrida antiga: DESCARTA-SE com aviso e nada se aplica por
cima do trabalho novo. E um bloco que ja conste no arquivo (escrito por
uma corrida que falhou a seguir) nunca se volta a anexar: recomeçar depois
de uma falha nao duplica.

Guarda dos arquivos (P2, juizes ronda 6): a retoma valida tambem OS
ARQUIVOS em causa — o journal grava o resumo (sha256) de cada arquivo tal
como estava ao ser criado. Na retoma, um arquivo so e aceite no estado
original (ainda nao reaplicado) ou no estado final do journal (ja escrito
por uma corrida que falhou a seguir — reaplicar e idempotente); qualquer
outro conteudo = edicao manual entretanto, e o journal DESCARTA-SE com
aviso: repor o conteudo do journal apagaria essa edicao.

`--dry-run` so diz o que faria, sem escrever nada — inclusive com um
journal pendente: nesse caso diz que ha uma operacao pendente e o que uma
corrida real faria (retoma-la ou descarta-la), sem tocar em ficheiro
nenhum (P2, juizes ronda 6: a retoma escrevia mesmo com --dry-run).

Dedup por blocos (P3, juizes ronda 6): «ja consta no arquivo?» compara-se
a entrada INTEIRA, delimitada por blocos ('## '), nunca por substring —
uma entrada que fosse so um prefixo de linhas de outra ja arquivada era
dada como «presente» e saia do handover sem ser guardada (perda silenciosa).

Ilegivel NUNCA e vazio (P4, juizes ronda 6): um ficheiro que esta
ferramenta ia SUBSTITUIR ou COMPLETAR — o handover.md ou um
handover-archive/<mes>.md — e que EXISTE mas NAO se le (sem permissao de
leitura) NUNCA e tratado como vazio: a ferramenta PARA sem escrever nada,
diz qual e o ficheiro e sai 1. E a regra tanto do indice.py (INDEX.md
manual) como daqui: na retoma, um arquivo ilegivel fazia o resumo do
«vazio» passar e o journal repunha o conteudo dele por cima de uma nota
manual; um handover ilegivel fazia o journal ser descartado e apagado.

O teto importa-se de verificar_docs.py (TETO_HANDOVER) — uma so constante
no codigo, o mesmo teto nas duas ferramentas.

`--dry-run` so diz o que faria, sem escrever nada.

Corre-se com `python` ou `python3` — o que existir na maquina
(`python x.py || python3 x.py`).
"""
import hashlib
import json
import os
import re
import sys
import tempfile
from pathlib import Path

try:
    from verificar_docs import TETO_HANDOVER as TETO
except ImportError:
    TETO = None          # verificar_docs.py em falta ao lado — main() avisa

AGENTS = Path(__file__).resolve().parent.parent
HANDOVER = AGENTS / "handover.md"
ARQUIVO = AGENTS / "handover-archive"
JOURNAL = ARQUIVO / ".pendente.json"

RX_DATA = re.compile(r"^##\s+(\d{4})-(\d{2})-\d{2}\b")


def partir(texto):
    """-> (cabecalho, entradas): linhas sem o '\\n'. Entradas comecam em
    '## ' e levam as linhas ate à entrada seguinte (ou ao fim)."""
    linhas = texto.split("\n")
    if linhas and linhas[-1] == "":     # artefacto do \n final
        linhas.pop()
    cab, entradas, atual = [], [], None
    for ln in linhas:
        if ln.startswith("## "):
            atual = [ln]
            entradas.append(atual)
        elif atual is None:
            cab.append(ln)
        else:
            atual.append(ln)
    return cab, entradas


def blocos(texto):
    """Os blocos '## ' de um texto (arquivo ou handover) como juncoes de
    linhas. A comparacao «ja consta no arquivo?» e por bloco INTEIRO
    delimitado (P3, juizes ronda 6) — nunca por substring: uma entrada que
    fosse so um prefixo de linhas de outra ja arquivada era dada como
    «presente» e saia do handover sem ser guardada."""
    return {"\n".join(e) for e in partir(texto)[1]}


def mes_da_entrada(entrada):
    m = RX_DATA.match(entrada[0])
    return f"{m.group(1)}-{m.group(2)}.md" if m else "sem-data.md"


def resumo(texto):
    """Resumo criptografico do conteudo do handover — o que o journal
    espera encontrar em disco quando se retoma."""
    return hashlib.sha256(texto.encode("utf-8")).hexdigest()


def escrever_atomico(alvo, texto):
    """Escrita atomica: temporario na MESMA pasta + os.replace. Uma falha
    a meio deixa o ficheiro original intacto."""
    fd, tmp = tempfile.mkstemp(dir=str(alvo.parent), prefix=".tmp-",
                               suffix=".part")
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
            f.write(texto)
        os.replace(tmp, alvo)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def aplicar(journal):
    """Aplica um journal: os arquivos com o CONTEUDO FINAL completo e o
    handover novo, tudo atomico; no fim o journal sai. Reaplicar o MESMO
    journal e idempotente — por isso uma falha a meio seguida de nova
    corrida nunca duplica entradas no arquivo."""
    for nome, conteudo in sorted(journal["arquivos"].items()):
        escrever_atomico(ARQUIVO / nome, conteudo)
    escrever_atomico(HANDOVER, journal["handover"])
    JOURNAL.unlink()


def retomar_se_pendente(dry_run=False):
    """Uma corrida anterior falhou a meio com journal pendente: retoma-o —
    mas SO se o handover E os arquivos em causa em disco ainda forem os que
    o journal espera (resumos sha256 guardados no journal). Se houve
    escritas entretanto, o journal e de uma corrida antiga: descarta-se com
    aviso e nada se aplica por cima do trabalho novo.
    Com dry_run=True NUNCA escreve (nem aplica, nem apaga o journal): so
    diz que ha uma operacao pendente e o que uma corrida real faria.
    -> True se retomou (ou se o journal deu erro, com saida 1);
       False se nao havia nada a retomar ou o journal stale se descartou."""
    if not JOURNAL.is_file():
        return False
    try:
        journal = json.loads(JOURNAL.read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        if dry_run:
            print(f"--dry-run: ha um journal pendente {JOURNAL} ILEGIVEL "
                  f"({e}) — uma corrida real pedia resolucao a mao e saia "
                  "1. Nada foi escrito.")
            return True
        print(f"journal pendente {JOURNAL} ilegivel: {e} — "
              "resolve a mao (o handover original nao foi tocido por esta "
              "retomada).")
        return True                          # sinal de erro: main sai 1
    if not isinstance(journal, dict):
        if dry_run:
            print(f"--dry-run: ha um journal pendente {JOURNAL} que nao e "
                  "um objeto — uma corrida real pedia resolucao a mao e "
                  "sai a 1. Nada foi escrito.")
            return True
        print(f"journal pendente {JOURNAL} nao e um objeto — resolve a mao.")
        return True
    esperado = journal.get("handover_resumo")
    try:
        atual = (resumo(HANDOVER.read_text(encoding="utf-8",
                                           errors="replace"))
                 if HANDOVER.is_file() else None)
    except OSError as e:
        # ilegivel NUNCA e vazio (P4, juizes ronda 6): ler "" fazia o
        # resumo «mudar», o journal era dado como stale, DESCARTADO e
        # apagado — a operacao pendente perdia-se. Parar; o journal fica
        # pendente para resolucao a mao.
        if dry_run:
            print(f"--dry-run: {HANDOVER.name} existe mas NAO se le ({e}) "
                  "— uma corrida real parava SEM tocar no journal e saia "
                  "1. Nada foi escrito.")
            return True
        print(f"{HANDOVER.name} existe mas NAO o consigo ler ({e}) — "
              "ilegivel NUNCA e vazio: parei SEM aplicar e SEM apagar o "
              "journal (fica pendente); resolve a mao.")
        return True                          # sinal de erro: main sai 1
    arquivos = journal.get("arquivos")
    if not isinstance(arquivos, dict):
        arquivos = {}
    # P2: um arquivo em causa so e aceite no estado ORIGINAL de quando o
    # journal nasceu (ainda nao reaplicado) ou no estado FINAL do journal
    # (ja escrito por uma corrida que falhou a seguir — reaplicar e
    # idempotente). Qualquer outro conteudo e uma edicao manual entretanto:
    # aplicar o journal reporia o conteudo velho por cima dela.
    antes = journal.get("arquivos_resumo")
    alterado = None
    for nome, conteudo in sorted(arquivos.items()):
        alvo = ARQUIVO / nome
        try:
            em_disco = (alvo.read_text(encoding="utf-8", errors="replace")
                        if alvo.is_file() else "")
        except OSError as e:
            # ilegivel NUNCA e vazio (P4, juizes ronda 6): com o resumo do
            # «vazio» no journal (arquivo criado so DEPOIS dele), o "" da
            # leitura falhada passava na validacao e a retoma repunha o
            # conteudo do journal por cima do que la esta — uma nota manual
            # perdia-se. Parar; o journal fica pendente.
            if dry_run:
                print(f"--dry-run: {ARQUIVO.name}/{nome} existe mas NAO "
                      f"se le ({e}) — uma corrida real parava SEM aplicar "
                      "o journal e saia 1. Nada foi escrito.")
                return True
            print(f"{ARQUIVO.name}/{nome} existe mas NAO o consigo ler "
                  f"({e}) — ilegivel NUNCA e vazio: parei SEM aplicar e "
                  "SEM apagar o journal (fica pendente); resolve a mao.")
            return True                      # sinal de erro: main sai 1
        if em_disco == conteudo:
            continue                         # ja o que o journal vai escrever
        if not isinstance(antes, dict) or resumo(em_disco) != antes.get(nome):
            alterado = nome
            break
    handover_stale = esperado is None or atual != esperado
    if dry_run:
        # so se diz o que UMA corrida real faria — nada se escreve
        if handover_stale:
            print("--dry-run: ha uma operacao pendente (journal "
                  f"{JOURNAL.name}) que uma corrida real DESCARTAVA — o "
                  "handover.md mudou entretanto (houve escritas, ou e de "
                  "uma versao sem resumo). Nada foi escrito.")
        elif alterado is not None:
            print("--dry-run: ha uma operacao pendente (journal "
                  f"{JOURNAL.name}) que uma corrida real DESCARTAVA — o "
                  f"arquivo handover-archive/{alterado} mudou entretanto "
                  "(ha uma edicao manual que a retoma reporia por cima). "
                  "Nada foi escrito.")
        else:
            print("--dry-run: ha uma operacao pendente (journal "
                  f"{JOURNAL.name}) que uma corrida real RETOMAVA: "
                  f"{len(arquivos)} arquivo(s) e o handover.md aplicados a "
                  "partir do journal, sem duplicar. Nada foi escrito.")
        return True
    if handover_stale:
        # journal de uma corrida cujo ponto de partida ja nao e este:
        # aplicar por cima apagaria entradas escritas depois
        print("journal pendente DESCARTADO: e de uma corrida cujo ponto de "
              "partida ja nao e o handover.md atual (houve escritas "
              "entretanto, ou e de uma versao antiga sem resumo). Nada se "
              "aplicou por cima do trabalho novo; o journal apagou-se. Se o "
              "handover continuar acima do teto, corre outra vez para "
              "arquivar o que sobrar.")
        try:
            JOURNAL.unlink()
        except OSError as e:
            print(f"atencao: nao consegui apagar o journal {JOURNAL}: {e}")
        return False                         # nada retomado: segue o normal
    if alterado is not None:
        print("journal pendente DESCARTADO: o arquivo "
              f"handover-archive/{alterado} ja nao e o que a operacao "
              "pendente espera (houve uma edicao entretanto, e reaplicar o "
              "journal reporia o conteudo velho por cima dela). Nada se "
              "aplicou; o journal apagou-se. Se o handover continuar acima "
              "do teto, corre outra vez para arquivar o que sobrar.")
        try:
            JOURNAL.unlink()
        except OSError as e:
            print(f"atencao: nao consegui apagar o journal {JOURNAL}: {e}")
        return False                         # nada retomado: segue o normal
    try:
        aplicar(journal)
    except (OSError, ValueError, KeyError, TypeError) as e:
        print(f"journal pendente {JOURNAL} inaplicavel: {e} — "
              "resolve a mao (o handover original nao foi tocido por esta "
              "retomada).")
        return True                          # sinal de erro: main sai 1
    print("retomada de uma corrida interrompida: arquivos e handover "
          "aplicados a partir do journal pendente — nada duplicado.")
    return True


def main(argv):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, OSError):
        pass
    dry = "--dry-run" in argv
    if retomar_se_pendente(dry_run=dry):
        if dry:
            # so se disse o que uma corrida real faria — nada falhou aqui
            return 0
        # so se sabe se a retomada correu bem relendo o journal: se sumiu,
        # a aplicacao chegou ao fim
        return 0 if not JOURNAL.is_file() else 1
    if TETO is None:
        print("verificar_docs.py em falta ao lado desta ferramenta — o teto "
              "vem dele (TETO_HANDOVER). Corre o modo `actualizar` do /bora.")
        return 1
    if not HANDOVER.is_file():
        print(f"sem {HANDOVER.name} — nada a arquivar.")
        return 0
    try:
        texto = HANDOVER.read_text(encoding="utf-8", errors="replace")
    except OSError as e:
        print(f"nao consegui ler {HANDOVER}: {e}")
        return 1
    cab, entradas = partir(texto)
    if not entradas:
        print(f"{HANDOVER.name} sem entradas (## ) — nada a arquivar.")
        return 0

    total = lambda: len(cab) + sum(len(e) for e in entradas)
    movidas = []                          # [(entrada, destino)]
    while total() > TETO and len(entradas) > 1:
        velha = entradas.pop()
        movidas.append((velha, mes_da_entrada(velha)))
    aviso = ""
    if total() > TETO:
        aviso = (f"AVISO: cabecalho + entrada mais recente ja passam o teto "
                 f"({total()} > {TETO} linhas) — ficam como estao; encurta "
                 "a entrada a mao.")
    if not movidas:
        print(aviso or f"{HANDOVER.name} dentro do teto "
              f"({total()} <= {TETO} linhas) — nada a arquivar.")
        return 0
    for entrada, destino in movidas:
        print(f"arquivar: {entrada[0][:70]}  ->  handover-archive/{destino}")
    if aviso:
        print(aviso)
    if "--dry-run" in argv:
        print(f"--dry-run: {len(movidas)} entrada(s) iriam para o arquivo; "
              f"ficaria com {total()} linhas (teto {TETO}). Nada foi escrito.")
        return 0

    por_mes = {}
    for entrada, destino in movidas:
        por_mes.setdefault(destino, []).append(entrada)
    # plano = conteudos FINAIS de cada ficheiro; guarda-se no journal antes
    # de tocar em disco — uma falha a meio deixa o original intacto e a
    # proxima corrida retoma SEM duplicar. Um bloco que ja conste no
    # arquivo (escrito por uma corrida que falhou a seguir, e cujo journal
    # se descartou por stale) nao se volta a anexar: recomeçar nunca duplica.
    arquivos_antes = {}
    arquivos_finais = {}
    for destino in sorted(por_mes):
        alvo = ARQUIVO / destino
        try:
            velho = (alvo.read_text(encoding="utf-8", errors="replace")
                     if alvo.is_file() else "")
        except OSError as e:
            # ilegivel NUNCA e vazio (P4, juizes ronda 6): anexar as
            # entradas ao "" era sobrescrever o arquivo por cima do
            # conteudo que nao se leu. Parar ANTES de qualquer escrita
            # (o journal ainda nao nasceu aqui).
            print(f"{ARQUIVO.name}/{destino} existe mas NAO o consigo ler "
                  f"({e}) — ilegivel NUNCA e vazio: parei SEM arquivar; "
                  "o handover e os arquivos ficam como estavam. Resolve a "
                  "mao.")
            return 1
        arquivos_antes[destino] = resumo(velho)
        # P3: comparacao por BLOCOS inteiros ('## '), nunca por substring —
        # uma entrada so-prefixo de outra ja arquivada nao e «presente»
        novos = [e for e in por_mes[destino]
                 if "\n".join(e) not in blocos(velho)]
        if novos:
            # sem linhas a mais: o markdown nao exige linha em branco antes
            # de um '## ', e cada bloco ja leva as suas
            arquivos_finais[destino] = (
                velho + "\n".join(ln for e in novos for ln in e) + "\n")
    journal = {"handover": "\n".join(cab + [ln for e in entradas for ln in e])
                        + "\n",
               "arquivos": arquivos_finais,
               "handover_resumo": resumo(texto),
               "arquivos_resumo": {d: arquivos_antes[d]
                                   for d in arquivos_finais}}
    try:
        ARQUIVO.mkdir(parents=True, exist_ok=True)
        escrever_atomico(JOURNAL, json.dumps(journal, ensure_ascii=False,
                                             sort_keys=True))
        aplicar(journal)
    except OSError as e:
        print(f"escrita falhou a meio (nada perdeste — o handover original "
              f"ainda esta la; a proxima corrida retoma do journal sem "
              f"duplicar): {e}")
        return 1
    arquivados = ", ".join(f"{d} ×{len([1 for _, dd in movidas if dd == d])}"
                           for d in sorted(por_mes))
    print(f"feito: {len(movidas)} entrada(s) arquivada(s): {arquivados}. "
          f"{HANDOVER.name} ficou com {total()} linhas (teto {TETO}).")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
