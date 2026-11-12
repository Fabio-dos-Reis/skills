#!/usr/bin/env python3
"""medicoes.py — registo de "ja foi medido" (.agents/medicoes.jsonl).

Uma medicao sem regua e uma opiniao com numero: uma entrada malformada
invalida o registo inteiro.

Comandos:
  validar                     valida o registo inteiro (exit 2 se invalido)
  consultar "<termos>"        procura deterministica (zero tokens de modelo):
                              palavra inteira, sem acentos, tolerante a plural
  registar                    le um objeto JSON do stdin, valida e acrescenta

Codigos de saida: 0 = ok (inclui consultar sem resultados: a resposta esta no texto) | 2 = erro de carga/validacao
Porque nao 1 para «sem resultados»: os comandos escrevem-se `python x.py || python3 x.py`; um exit != 0 num caso
normal disparava a segunda perna, e no Windows o atalho `python3` da Store respondia «Python was not found».
Stdlib apenas. Cross-platform: corre-se com `python` ou `python3` — o que existir na
maquina (`python x.py || python3 x.py`); nenhum dos dois nomes existe em todas as
plataformas.
Encoding (juizes, ronda 4): o stdin de `registar` le-se como UTF-8 PELOS BYTES
(sys.stdin.buffer) — sem isso, no Windows sem PYTHONIOENCODING a consola decidia
cp1252 e «medição» gravava-se «mediÃ§Ã£o», calado; e o stdout reconfigura-se
para UTF-8 no arranque (como as outras ferramentas), para um pipe nunca
rebentar com UnicodeEncodeError.
"""
import json
import re
import sys
import unicodedata
from datetime import datetime
from pathlib import Path

REGISTO = Path(__file__).resolve().parent.parent / "medicoes.jsonl"

CAMPOS_OBRIGATORIOS = {
    "id": int,
    "titulo": str,
    "data": str,
    "pergunta": str,
    "resultado": str,
    "veredicto": str,
    "porque": str,
    "regua": str,
    "reabre_se": str,
    "termos": list,
    "sistema": str,
}

SUFIXOS_PLURAL = (("oes", "ao"), ("aes", "ao"), ("ais", "al"),
                  ("eis", "el"), ("ois", "ol"), ("s", ""))


def normalizar(palavra):
    """Minusculas, sem acentos, singular aproximado (pt)."""
    p = unicodedata.normalize("NFKD", palavra.lower())
    p = "".join(c for c in p if not unicodedata.combining(c))
    for sufixo, troca in SUFIXOS_PLURAL:
        if p.endswith(sufixo) and len(p) > len(sufixo) + 1:
            return p[: -len(sufixo)] + troca
    return p


def palavras(texto):
    return [normalizar(p) for p in re.findall(r"[A-Za-zÀ-ÿ0-9]+", texto)]


def carregar(registo=REGISTO):
    """Carrega e valida TUDO; uma entrada ma falha a carga inteira."""
    if not registo.exists():
        return []
    entradas = []
    with open(registo, encoding="utf-8") as f:
        for n, linha in enumerate(f, 1):
            linha = linha.strip()
            if not linha:
                continue
            try:
                e = json.loads(linha)
            except json.JSONDecodeError as ex:
                raise ValueError(f"linha {n}: JSON invalido ({ex})")
            erros = validar_entrada(e)
            if erros:
                raise ValueError(f"linha {n}: " + "; ".join(erros))
            entradas.append(e)
    return entradas


def validar_entrada(e):
    erros = []
    if not isinstance(e, dict):
        return ["entrada nao e um objeto JSON"]
    desconhecidos = set(e) - set(CAMPOS_OBRIGATORIOS)
    if desconhecidos:
        erros.append(f"campos desconhecidos: {sorted(desconhecidos)}")
    for campo, tipo in CAMPOS_OBRIGATORIOS.items():
        if campo not in e:
            erros.append(f"falta campo obrigatorio '{campo}'")
        elif not isinstance(e[campo], tipo):
            erros.append(f"'{campo}' devia ser {tipo.__name__}")
    if erros:
        return erros
    if e["id"] <= 0:
        erros.append("'id' tem de ser inteiro positivo")
    try:
        datetime.strptime(e["data"], "%Y-%m-%d")
    except ValueError:
        erros.append("'data' tem de ser AAAA-MM-DD")
    for campo in ("titulo", "pergunta", "resultado", "veredicto", "porque",
                  "regua", "reabre_se", "sistema"):
        if not e[campo].strip():
            erros.append(f"'{campo}' nao pode estar vazio")
    if not e["termos"] or not all(isinstance(t, str) and t.strip() for t in e["termos"]):
        erros.append("'termos' tem de ser lista de strings nao vazias")
    return erros


def cmd_validar():
    try:
        entradas = carregar()
    except ValueError as ex:
        print(f"INVALIDO: {ex}")
        return 2
    print(f"OK: {len(entradas)} medicao(oes) valida(s) em {REGISTO}")
    return 0


def cmd_consultar(query):
    try:
        entradas = carregar()
    except ValueError as ex:
        print(f"INVALIDO: {ex}")
        return 2
    alvos = set(palavras(query))
    if not alvos:
        print("consulta vazia")
        return 2
    resultados = []
    for e in entradas:
        corpus = set(palavras(" ".join(e["termos"]))) | set(palavras(e["titulo"]))
        acertos = alvos & corpus
        if acertos:
            resultados.append((len(acertos), e))
    if not resultados:
        print(f"nada medido sobre: {query!r} — podes propor medir")
        return 0
    resultados.sort(key=lambda r: (-r[0], r[1]["id"]))
    print(f"{len(resultados)} medicao(oes) ja feita(s) — NAO medir outra vez sem ler:\n")
    for _, e in resultados:
        print(f"#{e['id']} [{e['data']}] {e['titulo']}")
        print(f"  pergunta:   {e['pergunta']}")
        print(f"  resultado:  {e['resultado']}")
        print(f"  veredicto:  {e['veredicto']}")
        print(f"  regua:      {e['regua']}")
        print(f"  reabre_se:  {e['reabre_se']}\n")
    return 0


def cmd_registar():
    try:
        # UTF-8 pelos BYTES: a consola nao manda aqui (no Windows sem
        # PYTHONIOENCODING o stdio cai em cp1252 e corrompia o registo)
        nova = json.loads(sys.stdin.buffer.read().decode("utf-8-sig"))
    except UnicodeDecodeError as ex:
        print(f"stdin nao e UTF-8 valido: {ex}")
        return 2
    except json.JSONDecodeError as ex:
        print(f"stdin nao e JSON valido: {ex}")
        return 2
    try:
        entradas = carregar()
    except ValueError as ex:
        print(f"registo atual INVALIDO, corrige antes de acrescentar: {ex}")
        return 2
    if "id" not in nova:
        nova["id"] = max((e["id"] for e in entradas), default=0) + 1
    erros = validar_entrada(nova)
    if erros:
        print("entrada recusada: " + "; ".join(erros))
        return 2
    if any(e["id"] == nova["id"] for e in entradas):
        print(f"entrada recusada: id {nova['id']} ja existe")
        return 2
    with open(REGISTO, "a", encoding="utf-8") as f:
        f.write(json.dumps(nova, ensure_ascii=False) + "\n")
    print(f"registada medicao #{nova['id']}: {nova['titulo']}")
    return 0


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, OSError):
        pass
    if len(sys.argv) < 2 or sys.argv[1] not in ("validar", "consultar", "registar"):
        print(__doc__)
        return 2
    cmd = sys.argv[1]
    if cmd == "validar":
        return cmd_validar()
    if cmd == "consultar":
        if len(sys.argv) < 3:
            print('uso: medicoes.py consultar "<termos>"')
            return 2
        return cmd_consultar(" ".join(sys.argv[2:]))
    return cmd_registar()


if __name__ == "__main__":
    sys.exit(main())
