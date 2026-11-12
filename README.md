# skills — AI agent skills by Fabio dos Reis

Portable prompt skills for coding agents (Claude Code · Kimi Code · OpenCode · any agent that reads instruction files). Plain Markdown + Python stdlib, no dependencies.

> Skills para agentes de IA — documentação de projecto com disciplina: regras permanentes, registo de medições e manutenção contínua.

| Skill | What it does |
|---|---|
| **bora** | Initializes (or adopts) a repo with a modular `.agents/` documentation skeleton: house rules in `AGENTS.md`, measurement log (`medicoes.jsonl`), pre-registration templates for measured changes, and a docs health checker. Stack-agnostic — any language, any size. |
| **medico** | Maintenance ritual on top of the `.agents/` skeleton: checks code↔docs drift, updates handover / progress / lessons-learned, prunes stale docs. Two modes — session-end (fast) and weekly (deep sweep). Includes cron scripts and agent hooks. |

## Install

Copy the skill folders you want into your agent's skills directory:

```sh
# Claude Code
cp -r bora medico ~/.claude/skills/      # then run /bora or /medico in chat

# Kimi Code / OpenCode
cp -r bora medico ~/.agents/skills/
```

`bora` runs standalone. `medico` expects an existing `.agents/` skeleton — on a new repo, run `/bora` first.

## Layout

```
skills/
├── bora/     SKILL.md + templates/   (the generated skeleton: AGENTS.md, .agents/, tools/)
├── medico/   SKILL.md + cron/ + hooks/ + install/   (maintenance ritual)
└── LICENSE
```

## Provenance

Built from real project usage (see [fabionunes](https://www.linkedin.com/in/fabionunes)), not written in the abstract: handover trailer lines, "already measured" registry and the doc verifier all came from keeping a live repo honest.

## License

MIT — see [LICENSE](LICENSE).
