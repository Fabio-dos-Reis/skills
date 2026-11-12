---
name: medico
description: Ritual de manutenção da documentação .agents/ — verifica drift entre código e docs, atualiza handover/progress/lessons, poda docs velhos. Dois modos: fim de sessão (rápido) e semanal (deep sweep).
type: prompt
whenToUse: Manutenção da documentação, fim de sessão de trabalho, "chama o médico", drift entre docs e código, revisão semanal. Use when the user says "medico", "médico", "chama o médico", "medico semanal", "fim de sessão", "docs em drift".
arguments: [modo]
---

# medico — ritual de manutenção da casa

O médico não constrói: **mede, reporta e mantém**. Trabalha sobre o esqueleto `.agents/` (criado pela skill `bora`). Se o projecto não tiver `.agents/`, diz ao utilizador para correr `/bora` primeiro e para.

Modos: `medico` (fim de sessão, rápido) · `medico semanal` (deep sweep; `$0` = `semanal`).

## Regras globais (valem para os dois modos)

- **Apagar > acrescentar.** Segue a regra «Manutenção apaga, não acrescenta» do `AGENTS.md` do projecto (é dele — aqui não se repete): antes de acrescentar uma linha, procura o que podes tirar.
- **Números sempre medidos-com-data.** Nunca escreves "ficou mais rápido"; escreves "passou de 420ms para 180ms (medido 2026-09-18)".
- **Output = relatório.** Escrita só nos ficheiros de estado (`handover.md`, `progress.md`, `lessons-learned.md`), no `INDEX.md` (regenerado por `tools/indice.py`) e no `handover-archive/` (movimento sem perda de `tools/rodar_handover.py`). Qualquer outro destino — `AGENTS.md`, docs de arquitetura, ADRs, specs — exige ordem expressa do utilizador.
- **INDEX em dia:** regenera o `INDEX.md` (`tools/indice.py`) quando a tabela de ficheiros do `AGENTS.md` do bora o manda (a regra D6 é dele e aqui não se repete); o verificador do bora reprova o INDEX desatualizado e diz porquê.
- **Nunca commitas** sem o utilizador pedir.
- Veredictos do relatório: ✓ ok · ⚠ aviso · ⛔ bloqueante.

## Modo rápido — `medico` (fim de sessão)

1. **Verificação estrutural:** corre `python .agents/tools/verificar_docs.py || python3 .agents/tools/verificar_docs.py` se existir e cola o resultado no relatório. Sem verificador, não improvisas checks à mão com ar de medição: o achado é ⚠ «verificador em falta — corre /bora para o instalar». Se reprovar por teto do handover (o número vem na mensagem do verificador — os tetos vivem lá, não aqui), corre `python .agents/tools/rodar_handover.py || python3 .agents/tools/rodar_handover.py` (escrita permitida — move para `handover-archive/`, sem perda), volta a gerar o INDEX e no relatório dizes quantas entradas arquivou e para onde.
2. **Drift código↔docs:** compara `git log --since="<data do handover>" --oneline` com o que `.agents/handover.md` diz. Trabalho de um commit **sem documentação nenhuma** → ⛔, listado. **Documentado num commit posterior** (mesma sessão) → ⚠, listado. Documentado no próprio handover → ✓.
3. **Atualiza o estado:** reescreve `.agents/handover.md` com a entrada desta sessão **no topo** (dentro do teto que o verificador do bora mede; trailer lines `**Segue:**` e `**À espera de decisão de <dono>:**` transportadas — uma decisão do humano nunca cai silenciosamente entre entradas) + entrada datada em `.agents/progress.md`.
4. **Lições:** lições novas em `.agents/lessons-learned.md` seguem a anatomia que abre esse ficheiro (é ela a fonte — aqui não se reescreve); entradas antigas noutro formato são aceites tal como estão e normalizadas na passagem seguinte. Se uma lição é recorrente (2ª vez), **propõe** a promoção da regra ao `AGENTS.md` no relatório (texto pronto na proposta) e marca a entrada `[promoção proposta]` — só escreves no `AGENTS.md` com ordem expressa do utilizador, como manda a regra global.
5. **Relatório final:** lista numerada de achados com veredictos ⚠/⛔, o que foi escrito, e o que ficou por decidir.

## Modo `medico semanal` (deep sweep)

Tudo o que o rápido faz, **mais poda**:

1. **Docs contraditórios/duplicados/velhos:**
   - facto em 2+ sítios com valores diferentes → ⛔ (lista ambos, com linha e valor);
   - docs >3 meses sem toque (mtime ou `git log -1 --format=%cs -- <ficheiro>`) → candidatos a arquivo.
2. **Propõe arquivo/delete NUMA LISTA ao utilizador — nunca apagas sem aprovação.** Uma linha por candidato: caminho · última modificação · porquê · destino proposto (`archive/` ou delete).
3. **Comprime progress.md:** entradas com >3 meses movem-se **inteiras** para `.agents/progress-archive/<AAAA-MM>.md` — nada se perde. O resumo de 1 linha que fica por entrada movida em `progress.md` entra na **lista de aprovação** do passo 2, como o resto da poda — nunca se escreve sem o utilizador aprovar.
4. **ADRs imutáveis:** verifica que nenhum ADR com estado "aceite" em `.agents/decisions/` foi editado depois de aceite (`git log --follow --format=%cs -- <adr>` vs data de aceitação no corpo). ADR editado → ⛔.
5. **Teto do AGENTS.md:** `AGENTS.md` acima do teto verificado → ⚠ com os blocos candidatos a sair (secções repetidas, exemplos longos, histórias antigas). O número é uma constante do `verificar_docs.py` do projecto (`.agents/tools/verificar_docs.py`), que o diz na mensagem quando reprova — o médico cita o que o verificador disse, não repete o valor. É sempre **proposta** — nunca cortas por tua conta.
6. **Deriva das ferramentas:** sha256 de cada `.agents/tools/*.py` do projecto contra o correspondente em `~/.agents/skills/bora/templates/tools/` (no layout de instalação padrão; senão, o caminho real da skill bora nesta máquina). Divergência → ⚠ com os dois hashes e o comando para realinhar: `cp ~/.agents/skills/bora/templates/tools/<ficheiro> .agents/tools/`.
7. **Medições válidas:** `python .agents/tools/medicoes.py validar || python3 .agents/tools/medicoes.py validar`. Inválido → ⛔ (uma medição sem régua é uma opinião com número).
8. **Relatório semanal:** rápido + poda, com a lista de aprovação no fim.

## Automação (opcional, fora deste SKILL.md)

- `hooks/` — scripts de hook por CLI (nudge no Stop, snapshot pré-compact, lembrete no arranque). Ver `hooks/README.md`.
- `cron/` — execução semanal agendada fora de sessão (Windows Task Scheduler ou cron/systemd). Ver `cron/README.md`.
