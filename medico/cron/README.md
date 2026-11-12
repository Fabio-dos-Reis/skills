# cron do medico — execução semanal agendada

`medico-weekly.ps1` (Windows) e `medico-weekly.sh` (POSIX) correm o medico
semanal headless (`/skill:medico semanal`) num projecto e acrescentam o
relatório a `.agents/medico-log.md`. A run semanal produz um **RELATÓRIO** —
nunca commits. Sem `.agents/` no projecto saem 1 com «corre /bora primeiro».
A invocação por omissão é `kimi -p "/skill:medico semanal"` nos dois
(no `.ps1` a omissão é uma lista de argumentos já separada — a frase com
espaços chega inteira); outro comando passa por `MEDICO_CMD` (variável de
ambiente, também nos dois).

## Agendar (Windows Task Scheduler), por projecto

Exemplo: segundas-feiras às 09:17 (evita :00/:30 — esses minutos acumulam tarefas de toda a gente):

```powershell
schtasks /create /tn "MedicoSemanal-MeuProjecto" `
  /tr "powershell -NoProfile -ExecutionPolicy Bypass -File \"__MEDICO_HOME__\cron\medico-weekly.ps1\" -ProjectDir \"C:\caminho\do\projecto\"" `
  /sc weekly /d MON /st 09:17 /f
```

(`__MEDICO_HOME__` = caminho real da pasta da skill nesta máquina — o
instalador materializa-o, ver `../hooks/README.md`; num comando manual,
substitui-o pelo caminho real.)

Uma tarefa por projecto (muda o `/tn` e o `-ProjectDir`). Verificar: `schtasks /query /tn "MedicoSemanal-MeuProjecto"`. Remover: `schtasks /delete /tn "MedicoSemanal-MeuProjecto" /f`.

Para outro comando, `-CliCmd "<comando>"` (uma string, partida por espaços).
O PowerShell liga flags como `-p` por abreviação aos parâmetros do script,
por isso o comando alternativo não passa aqui como argumentos posicionais —
o `.sh` sim (abaixo).

## Agendar (Linux: crontab ou systemd), por projecto

A diferença está na passagem do comando: aqui como argumentos
(`[cli-cmd...]`). Uso:
`sh medico-weekly.sh <dir-do-projecto> [cli-cmd...]`; os argumentos passam
**intactos** ao CLI (um argumento com espaços chega inteiro; `;` e `$(...)`
ficam literais — nada é re-analisado por um shell). Sem `cli-cmd` usa
`$MEDICO_CMD` (string de config, partida por espaços) e, na falta desta, a
omissão.

Crontab (segundas às 09:17):

```sh
17 9 * * 1 sh /caminho/para/medico-weekly.sh /caminho/do/projecto
```

Systemd (serviço one-shot + timer). Sem `Unit=` no timer, o systemd procura
um serviço com o MESMO nome do timer (`<nome>.timer` → `<nome>.service`) —
por isso o par tem nomes que casam (muda `meuprojecto` nos dois):

```ini
# /etc/systemd/system/medico-weekly-meuprojecto.service
[Unit]
Description=medico semanal do meu projecto

[Service]
Type=oneshot
ExecStart=/bin/sh /caminho/para/medico-weekly.sh /caminho/do/projecto
```

```ini
# /etc/systemd/system/medico-weekly-meuprojecto.timer
[Unit]
Description=medico semanal do meu projecto

[Timer]
OnCalendar=Mon 09:17
Persistent=true

[Install]
WantedBy=timers.target
```

Ativar: `sudo systemctl enable --now medico-weekly-meuprojecto.timer`.

## Alternativa in-session (Kimi cron)

O CronCreate do Kimi pode agendar `/skill:medico semanal` dentro de uma sessão viva —
mas **morre com a sessão**. Para algo que sobrevive a reinícios, usa o schtasks/cron acima.

## Notas

- Requer o CLI de destino no PATH e o projecto com `.agents/` (skill `bora`).
- Logs: `.agents/medico-log.md` no projecto. O log abre com `<!-- gerado: nao entra no INDEX -->` (a regra que o deixa fora do índice vive no `tools/indice.py` do bora); a marca entra também num log antigo sem ela.
- Falhas do CLI saem com o código dele (≠0); erros do próprio script (projecto em falta, sem `.agents/`) saem 1. Em ambos os casos fica registado no log.
