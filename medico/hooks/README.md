# hooks do medico — instalação por CLI

Três scripts stdlib em `scripts/` (cross-platform — o interpretador é o que o
instalador materializar para esta máquina):

| Script | Evento | Comportamento |
|---|---|---|
| `medico_stop_nudge.py` | Stop / fim de turno | Código mudou sem docs → stderr + exit 2 (bloqueia/nudge). Máx. 1×/4h (`.agents/.medico-nudge-state`). |
| `medico_precompact.py` | PreCompact | Escreve `.agents/handover-snapshot.md`. Exit 0 sempre. |
| `medico_sessionstart.py` | SessionStart | Snapshot mais recente que o handover → lembrete de 2 linhas no stdout. |

Todos: se `.agents/` não existir no cwd → exit 0 silencioso. O cwd do hook é a raiz do projecto.

## Marcadores que o instalador materializa

Os snippets desta pasta são **modelos**: trazem dois marcadores
(`__MEDICO_HOME__`, `__PYTHON__`) em vez de caminhos de máquina. Colar um
modelo destes na config de um CLI deixa os marcadores literais e os hooks
**não arrancam**.

O caminho certo — o instalador materializa os snippets DESTA máquina:

1. `sh Infra/skills/instalar.sh --instalar` — instala a skill em
   `~/.agents/skills/medico/`.
2. `sh Infra/skills/instalar.sh --hooks` — escreve os snippets preenchidos
   (python detetado, caminho entre aspas — pasta pessoal com espaços não
   parte o comando) em `~/.agents/skills/medico/hooks/gerados/`.
3. Copiar o conteúdo dos ficheiros **de `gerados/`** para a config de cada
   CLI, como abaixo. Não mexer nos modelos desta pasta.

| Marcador | O que é | Materializado em |
|---|---|---|
| `__MEDICO_HOME__` | caminho da pasta da skill instalada | o caminho real desta máquina, entre aspas no comando |
| `__PYTHON__` | comando do interpretador desta máquina | o comando certo desta máquina — não há um nome único: numas é o launcher `py`, noutras é `python3` |

Não há um nome de interpretador que corra em todas as máquinas — por isso o
snippet guarda o marcador e o instalador resolve-o. Não troques os
marcadores à mão: deixa o instalador trabalhar.

## Kimi Code (+ DeepSeek via wrapper Kimi)

Correr `sh Infra/skills/instalar.sh --hooks` e acrescentar o conteúdo de
`~/.agents/skills/medico/hooks/gerados/kimi-hooks.toml.snippet` (o ficheiro
**gerado**, não o modelo desta pasta) a `~/.kimi-code/config.toml`
(NÃO substituir — fazer append das 3 tabelas `[[hooks]]`).
No Kimi: exit 2 num hook Stop bloqueia o Stop e alimenta o stderr ao modelo;
stdout de SessionStart é acrescentado ao contexto.

## Claude Code

Correr `sh Infra/skills/instalar.sh --hooks` e mergear
`~/.agents/skills/medico/hooks/gerados/claude-settings.json.snippet` em
`~/.claude/settings.json` (chave `hooks`).
Stop com exit 2 equivale a `decision: "block"` (stderr vai para o Claude);
stdout de SessionStart vira `additionalContext`.

## opencode (v2)

Correr `sh Infra/skills/instalar.sh --hooks` e copiar
`~/.agents/skills/medico/hooks/gerados/opencode-plugin.ts` para
`~/.config/opencode/plugins/medico.ts`.
O plugin v2 exporta `{ id: "medico", setup }` e subscreve `session.idle`
e `session.compacted` via `ctx.event.subscribe()` (best-effort: falhas são
engolidas, o opencode nunca bloqueia).

A forma v1 (`export default async ({ $ }) => ({ event })`) **não carrega**
no OpenCode 2 — o servidor recusa com
`Plugin must export a default definition with an id and an effect or setup function`.

## Codex

O Codex só tem o hook `notify` (notificações de desktop) — não serve para isto.
Alternativa: agendar o medico semanal via Task Scheduler ou cron (ver `../cron/README.md`).

## Grok

Sem mecanismo de hooks conhecido → invocação manual (`/medico` no fim da sessão)
ou Task Scheduler/cron (`../cron/README.md`).

## Notas

- O hook corre com cwd = pasta do projecto aberto na sessão; os scripts resolvem
  `.agents/` a partir daí, por isso o mesmo hook serve todos os projectos.
