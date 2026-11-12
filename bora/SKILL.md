---
name: bora
description: Inicializa (ou adopta) um repositório com o esqueleto de documentação modular .agents/ + AGENTS.md com as regras da casa, registo de medições (medicoes.jsonl), pré-registo-lite e verificador de docs. Genérico — serve para qualquer linguagem, stack ou tamanho de projecto.
type: prompt
whenToUse: When starting a new project repository, or bringing an existing messy repo under the .agents/ documentation discipline ("arrumar a casa"). Use when the user says "bora", "iniciar projecto", "init", "adopt", "arrumar a casa", "scaffold dos docs".
arguments: [modo] [nome-do-projecto]
---

# bora — esqueleto de projecto com regras da casa

Gera um esqueleto **genérico** (qualquer stack) de documentação modular + um `AGENTS.md` com ordens permanentes. Baseia-se em convenções do ecossistema: AGENTS.md (padrão de 60k+ projectos), Memory Bank (Cline), specs por feature (spec-kit/OpenSpec), ADRs (decisões imutáveis), mais três padrões de manutenção provados em projecto real: **handover com trailer lines**, **registo de "já foi medido"** (`medicoes.jsonl`) e **pré-registo-lite** para mudanças medidas. Todo o output é Markdown + Python stdlib — portátil a Kimi Code, Claude Code, opencode, DeepSeek ou qualquer ferramenta que leia ficheiros de instruções.

Os modelos (templates) estão na pasta `templates/` ao lado deste SKILL.md. Lê o modelo antes de escrever cada ficheiro.

## Modo de operação

- `$0` = `adopt`, OU o diretório atual já contém código/manifests → **modo adopt**: NUNCA apagar nada.
  1. Mapeia a estrutura real do repositório (árvore de pastas, manifests, comandos de build detetáveis).
  2. Preenche `architecture.md` e `tech-stack.md` com FACTOS do repositório (não intenções).
  3. Cria o resto do esqueleto com o conteúdo inicial adaptado a essa realidade.
  4. No fim, lista ao utilizador as discrepâncias encontradas (docs soltos na raiz, ficheiros órfãos, pastas sem dono).
  A linha de base é o commit que cria `.agents/`: o histórico anterior não se julga (o verificador só conta a partir dele) — um repositório com commits antigos reprovados pode ser adoptado na mesma.
- Caso contrário → **modo init** (repositório novo ou vazio).

## Modo `actualizar` — projecto com `.agents/` de versão anterior

NUNCA apaga nada. A linha de base é o commit que cria `.agents/`: o histórico
anterior não se julga. Para um projecto criado por uma versão antiga do /bora (o
verificador reprova «ferramentas em falta em .agents/tools/»):

1. Copia byte-idênticas as ferramentas de `templates/tools/` para `.agents/tools/` (as antigas que diferirem guardam-se como `<nome>.bak` — se o `.bak` já existir, o novo chama-se `<nome>.bak2`, `.bak3`, …: nunca se sobrepõe um backup).
2. No `AGENTS.md` do projecto troca SÓ os comandos antigos (`py -3 .agents/tools/x.py …`) pela forma actual (`python .agents/tools/x.py … || python3 .agents/tools/x.py …`) — substituição mecânica, o resto do ficheiro e do projecto fica intocado.
3. Se o `handover.md` passar o teto, corre `rodar_handover.py`.
4. Gera o INDEX (`indice.py`).
5. Corre o verificador e LISTA ao utilizador o que mais difere do modelo actual (secções novas do `AGENTS.md.tpl`, ADRs sem `**Estado:**`, caminhos de máquina em ficheiros seguidos pelo git) — propõe, não aplica.
6. Não faz commit sem o utilizador pedir.

## Passo 1 — entrevista mínima (apenas o que não vier nos argumentos)

Pergunta no máximo isto, de uma vez só: nome do projecto · missão numa frase · para quem é · stack (linguagem, package manager, testes, base de dados) · 1-3 não-objectivos · idioma dos docs (omissão: pt-PT) · inicializar git (omissão: sim).
Se o utilizador disser "decide tu", decide com bom senso e regista os pressupostos em `project-brief.md`.

## Passo 2 — gerar os ficheiros

Usar os templates em `templates/`, substituindo os `<PLACEHOLDERS>` por conteúdo concreto das respostas. Não deixar stubs vazios — cada ficheiro nasce com conteúdo inicial útil.

- `AGENTS.md` ← `templates/AGENTS.md.tpl` (preencher comandos reais de build/test/lint se detetados; senão `<TBD>` + nota em handover.md)
- `.agents/project-brief.md`, `.agents/architecture.md`, `.agents/design.md`, `.agents/tech-stack.md`, `.agents/handover.md`, `.agents/progress.md`, `.agents/lessons-learned.md`
- `.agents/medicoes.jsonl` — ficheiro VAZIO (registo de "já foi medido"; preenche-se com `tools/medicoes.py registar`)
- `.agents/tools/medicoes.py` ← `templates/tools/medicoes.py` (copiar byte-idêntico)
- `.agents/tools/verificar_docs.py` ← `templates/tools/verificar_docs.py` (copiar byte-idêntico)
- `.agents/tools/indice.py` ← `templates/tools/indice.py` (copiar byte-idêntico)
- `.agents/tools/rodar_handover.py` ← `templates/tools/rodar_handover.py` (copiar byte-idêntico)
- `.agents/specs/pre-registo-template.md` ← `templates/specs/pre-registo-template.md`
- `.agents/decisions/0000-template.md` (modelo de ADR)
- `.agents/specs/000-template/{spec.md,plan.md,tasks.md}` (modelo de spec por feature)
- `INITIAL.md` (template de intake por feature), `CHANGELOG.md` (stub)
- `CLAUDE.md` ← `templates/CLAUDE.md` (shim de 3 linhas que aponta para AGENTS.md; compatibilidade Claude Code)
- `.gitignore`: acrescentar entradas óbvias conforme o stack (`.env`, `node_modules/`, `__pycache__/`, `.venv/`, `dist/`, …)

## Passo 3 — arranque

- Gerar o índice: `python .agents/tools/indice.py || python3 .agents/tools/indice.py` (cria `.agents/INDEX.md`) — **antes** do commit inicial, para o INDEX nascer versionado.
- `git init` + `git add` do esqueleto + commit inicial `chore: esqueleto .agents/ + AGENTS.md` (se git = sim). Os `.md` de `.agents/` têm de ficar tracked — o `verificar_docs.py` reprova docs fora do git.
- Validar a instalação: `python .agents/tools/medicoes.py validar || python3 .agents/tools/medicoes.py validar` (registo vazio = válido), `python .agents/tools/indice.py --verificar || python3 .agents/tools/indice.py --verificar` (INDEX em dia) e `python .agents/tools/verificar_docs.py || python3 .agents/tools/verificar_docs.py` (⛔ zero).
- Escrever `.agents/handover.md` inicial: esqueleto criado, estado real, próximo passo concreto — com as trailer lines do modelo (`templates/handover.md.tpl`; a anatomia fixa de cada entrada vive no AGENTS.md gerado, ordem permanente 2). Se a escrita mudou linhas de algum `.md`, regenera o INDEX no mesmo passo.
- Resumo final ao utilizador: árvore criada · o ritual (leitura de arranque, fecho de sessão e tetos: as ordens permanentes do `AGENTS.md` gerado — aqui não se repetem) · memória externa do projecto (RAG, bases vetoriais, índices) fica fora do âmbito deste esqueleto — se existir, documenta-se a convenção em `architecture.md`.

## Regras

- Idioma dos docs: o escolhido na entrevista (omissão pt-PT). Nomes de ficheiros: sempre minúsculas com hífens, em inglês.
- Nunca inventar comandos de build/test: se não detetados, `<TBD>`.
- Em modo adopt, nunca reescrever um ficheiro existente sem o guardar como `<nome>.bak` antes (exceção: `AGENTS.md`/`CLAUDE.md` novos, que não existiam).
- Nenhum conteúdo gerado pode depender de ferramenta específica — é Markdown + instruções, ponto. Os quatro scripts em `.agents/tools/` são Python stdlib, sem dependências, cross-platform.
- Se o projecto já tiver docs com nomes diferentes (README velho, NOTES.md, TODO.txt), não os mover: indexá-los em `handover.md` sob "Legado a migrar" e propor migração no próximo passo.
- Manutenção posterior destes ficheiros NÃO é trabalho desta skill — é da skill `medico`.
