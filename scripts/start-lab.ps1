param([switch]$Rebuild)
$ErrorActionPreference = 'Stop'
$project = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$envPath = Join-Path $project '.env'

if (-not (Test-Path -LiteralPath $envPath)) {
    $bytes = New-Object byte[] 24
    [System.Security.Cryptography.RandomNumberGenerator]::Fill($bytes)
    $password = [Convert]::ToHexString($bytes)
    Set-Content -LiteralPath $envPath -Value "JENKINS_ADMIN_PASSWORD=$password`nJENKINS_AGENT_SECRET=" -NoNewline
}

$settings = @{}
Get-Content -LiteralPath $envPath | ForEach-Object {
    if ($_ -match '^([^=]+)=(.*)$') { $settings[$matches[1]] = $matches[2] }
}
if (-not $settings.JENKINS_ADMIN_PASSWORD) { throw 'JENKINS_ADMIN_PASSWORD ausente no .env' }

$compose = @('compose', '--env-file', $envPath, '-f', (Join-Path $project 'compose.yaml'))
$up = @('up', '-d')
if ($Rebuild) { $up += '--build' }
& docker @compose @up docker jenkins
if ($LASTEXITCODE -ne 0) { throw 'Falha ao iniciar Docker/Jenkins' }

$auth = [Convert]::ToBase64String([Text.Encoding]::ASCII.GetBytes("admin:$($settings.JENKINS_ADMIN_PASSWORD)"))
$headers = @{ Authorization = "Basic $auth" }
$xml = $null
for ($attempt = 0; $attempt -lt 60; $attempt++) {
    try {
        $response = Invoke-WebRequest -Uri 'http://127.0.0.1:8080/computer/linux-docker/jenkins-agent.jnlp' -Headers $headers -UseBasicParsing
        $xml = [string]$response.Content
        break
    } catch { Start-Sleep -Seconds 2 }
}
if (-not $xml) { throw 'Jenkins não respondeu ou JCasC não criou o agent' }
$match = [regex]::Match($xml, '<argument>([a-f0-9]{64})</argument>')
if (-not $match.Success) { throw 'Secret do agent não encontrado no JNLP' }
$settings.JENKINS_AGENT_SECRET = $match.Groups[1].Value
Set-Content -LiteralPath $envPath -Value "JENKINS_ADMIN_PASSWORD=$($settings.JENKINS_ADMIN_PASSWORD)`nJENKINS_AGENT_SECRET=$($settings.JENKINS_AGENT_SECRET)" -NoNewline

& docker @compose --profile agent @up agent
if ($LASTEXITCODE -ne 0) { throw 'Falha ao iniciar o agent' }
Write-Output 'Jenkins e agent iniciados. Interface local: http://127.0.0.1:8080/'
Write-Output 'Credenciais locais: usuário admin; senha em .env (arquivo ignorado pelo Git).'
