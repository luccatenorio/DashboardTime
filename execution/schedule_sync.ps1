# Script PowerShell para criar tarefa agendada no Windows Task Scheduler
# Executa sync_meta_metrics.py a cada 1 hora

$scriptPath = Join-Path $PSScriptRoot "sync_meta_metrics.py"
$pythonPath = "python"  # Ajuste se necessário (ex: "C:\Python39\python.exe")

# Verificar se o Python está disponível
try {
    $pythonVersion = & $pythonPath --version 2>&1
    Write-Host "✅ Python encontrado: $pythonVersion"
}
catch {
    Write-Host "❌ Python não encontrado. Por favor, instale Python e adicione ao PATH."
    Write-Host "   Ou ajuste a variável `$pythonPath neste script com o caminho completo."
    exit 1
}

# Nome da tarefa
$taskName = "SyncMetaMetricsToSupabase"

# Verificar se a tarefa já existe
$existingTask = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue

if ($existingTask) {
    Write-Host "⚠️  Tarefa '$taskName' já existe. Removendo..."
    Unregister-ScheduledTask -TaskName $taskName -Confirm:$false
}

# Criar ação (executar o script Python)
$action = New-ScheduledTaskAction -Execute $pythonPath -Argument "`"$scriptPath`"" -WorkingDirectory $PSScriptRoot

# Criar trigger (a cada 12 horas, começando agora)
$trigger = New-ScheduledTaskTrigger -Once -At (Get-Date) -RepetitionInterval (New-TimeSpan -Hours 12) -RepetitionDuration (New-TimeSpan -Days 365)

# Configurações da tarefa
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable

# Criar tarefa
try {
    Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Settings $settings -Description "Sincroniza métricas do Meta para Supabase a cada 12 horas" -RunLevel Highest
    
    Write-Host ""
    Write-Host "✅ Tarefa agendada criada com sucesso!"
    Write-Host "   Nome: $taskName"
    Write-Host "   Frequência: A cada 12 horas"
    Write-Host "   Script: $scriptPath"
    Write-Host ""
    Write-Host "Para gerenciar a tarefa, use:"
    Write-Host "   - Ver tarefa: Get-ScheduledTask -TaskName '$taskName'"
    Write-Host "   - Executar agora: Start-ScheduledTask -TaskName '$taskName'"
    Write-Host "   - Remover: Unregister-ScheduledTask -TaskName '$taskName' -Confirm:`$false"
}
catch {
    Write-Host "❌ Erro ao criar tarefa: $_"
    exit 1
}
