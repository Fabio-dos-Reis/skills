# medico-weekly.ps1 — corre o medico semanal headless num projecto.
# By Fabio Reis
# Uso: powershell -NoProfile -ExecutionPolicy Bypass -File medico-weekly.ps1 -ProjectDir "C:\caminho\do\projecto" [-CliCmd "<comando>"]
#   -CliCmd: comando do CLI que invoca a skill "medico semanal", como UMA
#   string partida por espacos (mesmo contrato de $env:MEDICO_CMD). O .sh
#   aceita argumentos com fronteiras preservadas; o PowerShell nao deixa —
#   flags como -p ligam por abreviacao aos parametros deste script — por
#   isso aqui o comando alternativo e uma string. Sem -CliCmd usa
#   $env:MEDICO_CMD; sem ela, a omissao e a LISTA ja separada
#   kimi -p "/skill:medico semanal" (nunca partida por espacos).
# A run semanal produz um RELATORIO (append a .agents/medico-log.md) — NUNCA commits.
# O log abre com "<!-- gerado: nao entra no INDEX -->" (o indice do bora
# ignora-o); a marca entra tambem num log de uma run antiga que nao a tenha.
# O log e escrito em UTF-8 SEM BOM (o PowerShell 5.1 poe BOM com -Encoding
# UTF8 e a marca deixaria de ser a primeira linha).

param(
    [Parameter(Mandatory = $true)]
    [string]$ProjectDir,

    [string]$CliCmd
)

$ErrorActionPreference = "Stop"

# Caminhos absolutos sempre: o .NET ([System.IO.File]) usa o cwd do
# processo, que o Set-Location do PowerShell NAO muda — um Join-Path
# relativo escreveria o log fora do projecto.
$ProjectDir = [System.IO.Path]::GetFullPath($ProjectDir)
$logPath = Join-Path $ProjectDir ".agents/medico-log.md"

$Marca = '<!-- gerado: nao entra no INDEX -->'
$Utf8NoBom = New-Object System.Text.UTF8Encoding($false)

function Garantir-Marca($caminho) {
    # o log abre com a marca — tambem se ja existia de uma run antiga sem ela.
    # Nunca WriteAllText no lugar (trunca o log antes de escrever: uma falha
    # a meio apaga o historico). O conteudo novo vai para um temporario ao
    # lado e so no fim substitui o antigo — como o .sh, que guarda o antigo
    # e so depois faz mv.
    $tmp = "$caminho.tmp.$([System.Guid]::NewGuid().ToString('N'))"
    $bak = "$caminho.bak.$([System.Guid]::NewGuid().ToString('N'))"
    try {
        if (Test-Path -LiteralPath $caminho) {
            $leitor = New-Object System.IO.StreamReader($caminho, $true)
            $texto = ""
            try { $texto = $leitor.ReadToEnd() } finally { $leitor.Close() }
            if ($texto -notlike '<!-- gerado*') {
                [System.IO.File]::WriteAllText($tmp, $Marca + "`n" + $texto, $Utf8NoBom)
                [System.IO.File]::Replace($tmp, $caminho, $bak)
            }
        } else {
            [System.IO.File]::WriteAllText($tmp, $Marca + "`n", $Utf8NoBom)
            [System.IO.File]::Move($tmp, $caminho)
        }
    } finally {
        if (Test-Path -LiteralPath $tmp) {
            Remove-Item -LiteralPath $tmp -Force -ErrorAction SilentlyContinue
        }
        if (Test-Path -LiteralPath $bak) {
            Remove-Item -LiteralPath $bak -Force -ErrorAction SilentlyContinue
        }
    }
}

function Acrescentar-Log($caminho, $texto) {
    Garantir-Marca $caminho
    [System.IO.File]::AppendAllText($caminho, $texto, $Utf8NoBom)
}

try {
    if (-not (Test-Path -LiteralPath $ProjectDir -PathType Container)) {
        throw "ProjectDir nao existe: $ProjectDir"
    }
    Set-Location -LiteralPath $ProjectDir

    if (-not (Test-Path -LiteralPath ".agents" -PathType Container)) {
        throw "Sem .agents/ em $ProjectDir — corre /bora primeiro."
    }

    # Comando do CLI que invoca a skill "medico semanal": -CliCmd e
    # $env:MEDICO_CMD sao strings partidas por espacos (o mesmo contrato do
    # .sh com a variavel); a omissao e uma LISTA de argumentos ja separada —
    # nunca uma string a partir (o split partia "/skill:medico semanal" no
    # espaco e o medico nao corria). Argumentos posicionais nao existem
    # aqui: o PowerShell liga flags do CLI (ex: -p) por abreviacao aos
    # parametros deste script.
    $cli = 'kimi'
    $cliArgs = @('-p', '/skill:medico semanal')
    $cmd = $null
    if ($CliCmd) {
        $cmd = $CliCmd
    } elseif ($env:MEDICO_CMD) {
        $cmd = $env:MEDICO_CMD
    }
    if ($null -ne $cmd) {
        $partes = @($cmd -split '\s+' | Where-Object { $_ -ne '' })
        $cli = $partes[0]
        # statement e nao expressao: o if-expression desembrulharia um
        # array de 1 elemento numa string e o splatting partia o caminho
        # por chars
        $cliArgs = @()
        if ($partes.Count -gt 1) {
            $cliArgs = @($partes[1..($partes.Count - 1)])
        }
    }

    $data = Get-Date -Format "yyyy-MM-dd HH:mm"
    $cabecalho = "`n## $data — medico semanal (agendado)`n"

    # Kimi print mode: headless, uma so passagem. O relatorio sai no stdout.
    $saida = & $cli @cliArgs 2>&1 | Out-String
    $exitCode = $LASTEXITCODE

    Acrescentar-Log $logPath ($cabecalho + $saida)

    if ($exitCode -ne 0) {
        Acrescentar-Log $logPath "`n⚠ $cli saiu com codigo $exitCode`n"
        exit $exitCode
    }
    exit 0
}
catch {
    $msg = "$(Get-Date -Format 'yyyy-MM-dd HH:mm') medico-weekly FALHOU: $($_.Exception.Message)"
    try {
        Acrescentar-Log $logPath "`n## $msg`n"
    }
    catch {
        Write-Error $msg
    }
    exit 1
}
