#!/bin/sh
# medico-weekly.sh — corre o medico semanal headless num projecto (POSIX).
# By Fabio Reis
# Uso: sh medico-weekly.sh <dir-do-projecto> [cli-cmd...]
#   cli-cmd...: comando do CLI que invoca a skill "medico semanal", passado
#   como ARGUMENTOS — fronteiras preservadas, nada e re-analisado por um shell
#   (espacos ficam dentro do argumento; ';' e $(...) nunca executam).
#   Se vazio, usa $MEDICO_CMD (string de config, partida por espacos sem
#   globbing); sem ela, o comando do .ps1 (paridade):
#   kimi -p "/skill:medico semanal"
# A run semanal produz um RELATORIO (append a .agents/medico-log.md) — NUNCA commits.
# O log abre com "<!-- gerado: nao entra no INDEX -->" (o indice do bora
# ignora-o); a marca entra tambem num log de uma run antiga que nao a tenha.
# Sem .agents/ no projecto sai 1 com "corre /bora primeiro".

set -u
unset CDPATH

proj="${1:?uso: medico-weekly.sh <dir-do-projecto> [cli-cmd...]}"
shift
if [ "$#" -eq 0 ]; then
    if [ -n "${MEDICO_CMD:-}" ]; then
        set -f
        set -- $MEDICO_CMD
        set +f
    else
        set -- kimi -p "/skill:medico semanal"
    fi
fi

if [ ! -d "$proj" ]; then
    echo "medico-weekly: projecto nao existe: $proj" >&2
    exit 1
fi
# Caminho absoluto e canonico SEM depender de CDPATH (com CDPATH definido,
# um cd de caminho relativo pode parar noutra pasta homonima com .agents/ e
# o medico correria no projecto errado). O $(cd ...) corre em subshell: nao
# muda o cwd do script.
proj=$(cd -- "$proj" 2>/dev/null && pwd -P) || {
    echo "medico-weekly: nao consigo entrar em $proj" >&2
    exit 1
}
cd -- "$proj" 2>/dev/null || {
    echo "medico-weekly: nao consigo entrar em $proj" >&2
    exit 1
}
# Confirma que se ficou MESMO na pasta pedida.
if [ "$(pwd -P)" != "$proj" ]; then
    echo "medico-weekly: cd parou em $(pwd -P), esperava $proj" >&2
    exit 1
fi

if [ ! -d ".agents" ]; then
    echo "medico-weekly: sem .agents/ em $proj — corre /bora primeiro" >&2
    exit 1
fi

log=".agents/medico-log.md"
marca='<!-- gerado: nao entra no INDEX -->'
# O log abre com a marca — tambem se ja existia de uma run antiga sem ela.
if [ ! -f "$log" ]; then
    printf '%s\n' "$marca" > "$log"
elif ! head -n 1 "$log" | grep -q '^<!-- gerado'; then
    tmp="$log.$$"
    { printf '%s\n' "$marca"; cat "$log"; } > "$tmp" && mv "$tmp" "$log"
fi

data=$(date '+%Y-%m-%d %H:%M')
{
    echo
    echo "## $data — medico semanal (agendado)"
    echo
    "$@" 2>&1
} >> "$log"
rc=$?
if [ "$rc" -ne 0 ]; then
    {
        echo
        echo "⚠ o CLI saiu com codigo $rc"
        echo
    } >> "$log"
fi
exit "$rc"
