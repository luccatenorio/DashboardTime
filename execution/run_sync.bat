@echo off
REM Script batch simples para executar a sincronização
REM Útil para testes manuais ou execução via Task Scheduler

cd /d "%~dp0"
python sync_meta_metrics.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Erro ao executar sincronizacao!
    pause
    exit /b %ERRORLEVEL%
)

echo.
echo Sincronizacao concluida com sucesso!
timeout /t 5
