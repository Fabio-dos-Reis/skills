# AGENTS.md — <PROJECT_NAME>

> Regras quentes apenas. O detalhe vive em `.agents/` (mapa abaixo).
> Manter este ficheiro enxuto (com teto de linhas — o verificador diz qual): regras novas entram, regras mortas saem.
> **Manutenção apaga, não acrescenta.**

## O projecto (uma linha)

<MISSAO_UMA_FRASE>

## Comandos essenciais

- Build: `<BUILD_CMD | TBD>`
- Testes: `<TEST_CMD | TBD>`
- Lint: `<LINT_CMD | TBD>`

## Mapa da documentação (`.agents/`)

Projecto grande = leitura pequena: no arranque lê-se SÓ a entrada do topo
do `handover.md`. O `INDEX.md` não se lê por rotina — procura-se nele quando
a tarefa pede um documento; o resto só se abre quando a tarefa lhe toca.

| Ficheiro | O que é | Quando se atualiza | Lê-se quando |
|---|---|---|---|
| `INDEX.md` | índice gerado por máquina, 1 linha por `*.md` (caminho · título · estado · linhas) | no mesmo passo em que um `*.md` de `.agents/` muda (`tools/indice.py`) | quando a tarefa pede um documento — procura-se, não leitura de rotina |
| `project-brief.md` | visão, objectivos, não-objectivos | mudança de direcção | dúvida de âmbito |
| `architecture.md` | estrutura actual do sistema (facto, não intenção) | qualquer mudança estrutural | mexer na estrutura |
| `design.md` | decisões de design em curso | durante o design de features | feature nova |
| `tech-stack.md` | stack + versões + porquê | ao mudar dependências | dependências |
| `handover.md` | estado da última sessão (com teto de linhas — o verificador diz qual é e reprova acima dele; entrada mais recente no topo) | a cada bloco fechado; nunca só no fim | **arranque de sessão** — só a entrada do topo |
| `progress.md` | log datado de marcos | marcos; append-only | histórico de marcos |
| `lessons-learned.md` | erros → regras (Hipótese · Medição · Regra) | ao aprender algo caro, ANTES de fechar a tarefa | antes de repetir o erro |
| `medicoes.jsonl` | registo de "já foi medido" | antes/depois de qualquer medição | antes de medir (via `tools/medicoes.py`) |
| `tools/medicoes.py` | validador/consulta do registo de medições | só se o formato do registo mudar | corre-se, não se lê |
| `tools/indice.py` | gera e verifica o `INDEX.md` | só se o formato do INDEX mudar | corre-se, não se lê |
| `tools/rodar_handover.py` | arquiva entradas antigas do `handover.md` quando este estoura o teto | só se a regra do arquivo mudar | corre-se quando o verificador manda |
| `tools/verificar_docs.py` | verificador de saúde dos docs (tetos incluídos) | só se a régua de verificação mudar | corre-se antes de fechar dia/bloco |
| `decisions/` | ADRs imutáveis | cada decisão de arquitetura | decisão de arquitetura |
| `specs/NNN-slug/` | spec + plan + tasks por feature | ao planear/implementar | planear/implementar essa feature |
| `specs/pre-registo-template.md` | pré-registo-lite de mudanças medidas | — | antes de mexer no que se vai medir |

## Documentação segue a alteração (regra D6)

A documentação atualiza-se **no mesmo passo** da alteração — nunca só no fim do dia
ou da sessão: o que não estiver escrito quando o bloco fecha pode não chegar a ser escrito.

| a alteração é… | atualiza-se, no MESMO passo |
|---|---|
| código | o doc que o descreve (`architecture.md`, `design.md`, spec da feature) |
| passo novo de processo | este `AGENTS.md` — o passo **e** o comando exato |
| decisão executada | ADR novo em `decisions/`, com data e razão — um ADR aceite nunca se reescreve: substitui-se com outro ADR |
| achado ou lição | `lessons-learned.md`, antes de fechar a tarefa — lição recorrente (2.ª vez) promove-se a regra permanente neste `AGENTS.md` |
| `*.md` em `.agents/` muda | `INDEX.md` — regenera-se com `tools/indice.py` |
| bloco fechado (código + prova) | `handover.md` + entrada datada em `progress.md` |

## Ordem permanente (obrigatória)

1. **Arranque de sessão:** ler a entrada do TOPO de `.agents/handover.md` — a única leitura de rotina (regra: «Mapa da documentação» acima).
2. **Fim de sessão (e antes de qualquer compact):** atualizar `.agents/handover.md` (teto de linhas: «Mapa» acima) e acrescentar entrada datada em `progress.md`. Cada entrada de handover termina com duas linhas fixas:
   - `**Segue:**` — os próximos passos técnicos.
   - `**À espera de decisão de <dono>:**` — UMA linha transportada com as decisões que pertencem ao humano. Nunca se deixa cair silenciosamente entre entradas: ou foi decidida (e diz-se), ou é transportada.
3. **Antes de propor medir o que quer que seja:** `python .agents/tools/medicoes.py consultar "<hipótese>" || python3 .agents/tools/medicoes.py consultar "<hipótese>"`. Se já foi medido, citar a medição em vez de repetir. Mudança com medição planeadia → pré-registo-lite (`specs/pre-registo-template.md`) com régua assinada ANTES.
4. **Nunca declarar um dia/bloco fechado sem correr** `python .agents/tools/verificar_docs.py || python3 .agents/tools/verificar_docs.py` **e colar o resultado.** Fecha-se escrevendo o que falta, nunca relaxando o critério. _(Windows: se a seguir a um resultado já impresso aparecer `Python was not found`, ignora-se essa linha — é o atalho vazio da Microsoft Store; vale o resultado de cima. No Windows PowerShell 5.1 o `||` não é separador de comandos: corre-se só a primeira metade (`.agents/tools/verificar_docs.py`).)_
5. **Feature nova:** criar `.agents/specs/NNN-slug/{spec.md,plan.md,tasks}.md` — spec antes do código.
6. **Manutenção apaga, não acrescenta:** docs contraditórios/velhos pruneiam-se (com aprovação do utilizador); números citam-se sempre medidos-com-data.
7. Nada de documentação solta na raiz (exceções: README.md, AGENTS.md, CHANGELOG.md, INITIAL.md).
8. Respeitar os não-objectivos de `project-brief.md` — alterá-los exige ADR.

## Convenções deste repo

<CONVENCOES: estilo de código, commits, nomes, idioma dos docs — preencher na init>
