@echo off
chcp 65001 >nul
setlocal EnableDelayedExpansion

:: ============================================================================
:: VBQ-UNIFIED — Bot de Apostas Quantitativo (Start End-to-End)
:: ============================================================================
:: Este script inicia o projeto completo com todas as verificações necessárias.
:: Modo default: Paper Trading (sem risco real)
:: ============================================================================

title VBQ-UNIFIED — Bot de Apostas Quantitativo

set "PROJECT_DIR=C:\Users\rodri\Desktop\bot de apostas"
set "APP_DIR=%PROJECT_DIR%\app"
set "PYTHON_MIN=3.11"
set "RUN_PREFIX="

cd /d "%PROJECT_DIR%"

cls
echo.
echo    ╔══════════════════════════════════════════════════════════════════════╗
echo    ║           VBQ-UNIFIED — Bot de Apostas Quantitativo                 ║
echo    ║              (Value Betting Quantitative System)                     ║
echo    ╚══════════════════════════════════════════════════════════════════════╝
echo.

:: ============================================================================
:: 1. VERIFICAR PYTHON (com fallback para py, python3 e .venv)
:: ============================================================================
echo [1/8] Verificando Python...

set "PYTHON_CMD="

:: Tentativa 1: .venv do projeto (preferencial — ambiente isolado)
if exist "%APP_DIR%\.venv\Scripts\python.exe" (
    set "PYTHON_CMD=%APP_DIR%\.venv\Scripts\python.exe"
    goto :PYTHON_FOUND
)

:: Tentativa 2: py launcher (Windows Python Launcher)
py --version >nul 2>&1
if not errorlevel 1 (
    set "PYTHON_CMD=py"
    goto :PYTHON_FOUND
)

:: Tentativa 3: python direto
python --version >nul 2>&1
if not errorlevel 1 (
    set "PYTHON_CMD=python"
    goto :PYTHON_FOUND
)

:: Tentativa 4: python3
python3 --version >nul 2>&1
if not errorlevel 1 (
    set "PYTHON_CMD=python3"
    goto :PYTHON_FOUND
)

:: Tentativa 5: Python em local comum
if exist "C:\Users\rodri\AppData\Local\Programs\Python\Python312\python.exe" (
    set "PYTHON_CMD=C:\Users\rodri\AppData\Local\Programs\Python\Python312\python.exe"
    goto :PYTHON_FOUND
)
if exist "C:\Users\rodri\AppData\Local\Programs\Python\Python311\python.exe" (
    set "PYTHON_CMD=C:\Users\rodri\AppData\Local\Programs\Python\Python311\python.exe"
    goto :PYTHON_FOUND
)
if exist "C:\Program Files\Python312\python.exe" (
    set "PYTHON_CMD=C:\Program Files\Python312\python.exe"
    goto :PYTHON_FOUND
)
if exist "C:\Program Files\Python311\python.exe" (
    set "PYTHON_CMD=C:\Program Files\Python311\python.exe"
    goto :PYTHON_FOUND
)

echo [ERRO] Python não encontrado. Instale Python %PYTHON_MIN%+ e adicione ao PATH.
echo        https://www.python.org/downloads/
pause
exit /b 1

:PYTHON_FOUND
for /f "tokens=2 delims=. " %%a in ('"%PYTHON_CMD%" --version 2^>^&1') do set PY_MAJOR=%%a
for /f "tokens=3 delims=. " %%a in ('"%PYTHON_CMD%" --version 2^>^&1') do set PY_MINOR=%%a

if %PY_MAJOR% LSS 3 (
    echo [ERRO] Python %PY_MAJOR%.%PY_MINOR% detectado. Requer Python %PYTHON_MIN%+.
    pause
    exit /b 1
)
if %PY_MAJOR%==3 if %PY_MINOR% LSS 11 (
    echo [ERRO] Python %PY_MAJOR%.%PY_MINOR% detectado. Requer Python %PYTHON_MIN%+.
    pause
    exit /b 1
)
echo        OK — Python %PY_MAJOR%.%PY_MINOR% detectado em %PYTHON_CMD%.

:: ============================================================================
:: 2. VERIFICAR ESTRUTURA DO PROJETO
:: ============================================================================
echo [2/8] Verificando estrutura do projeto...
if not exist "%APP_DIR%" (
    echo [ERRO] Pasta 'app' não encontrada em %PROJECT_DIR%
    pause
    exit /b 1
)
if not exist "%APP_DIR%\scripts" (
    echo [ERRO] Pasta 'app\scripts' não encontrada.
    pause
    exit /b 1
)
if not exist "%APP_DIR%\src" (
    echo [ERRO] Pasta 'app\src' não encontrada.
    pause
    exit /b 1
)
echo        OK — Estrutura do projeto validada.

:: ============================================================================
:: 3. VERIFICAR/INSTALAR DEPENDÊNCIAS
:: ============================================================================
echo [3/8] Verificando dependências...
cd /d "%APP_DIR%"

:: Verificar se existe .venv no projeto — usar preferencialmente
if exist "%APP_DIR%\.venv\Scripts\python.exe" (
    echo        .venv encontrado no projeto. A usar ambiente virtual...
    set "PYTHON_CMD=%APP_DIR%\.venv\Scripts\python.exe"
    goto :DEPS_CHECK
)

:: Verificar se poetry está instalado
poetry --version >nul 2>&1
if not errorlevel 1 (
    echo        Poetry detectado. Verificando ambiente...
    poetry run python -c "import fastapi" >nul 2>&1
    if errorlevel 1 (
        echo        Instalando dependências via Poetry...
        poetry install --no-interaction >nul 2>&1
    ) else (
        echo        Ambiente Poetry OK.
    )
    set "RUN_PREFIX=poetry run"
    goto :DEPS_CHECK
)

:: Fallback: usar pip com o PYTHON_CMD encontrado
echo        Poetry não encontrado. Tentando usar pip...

:: Verificar se já está instalado
"%PYTHON_CMD%" -c "import fastapi, uvicorn, sqlalchemy, xgboost, pandas, numpy, sklearn, mlflow, streamlit" >nul 2>&1
if errorlevel 1 (
    echo        Instalando dependências (pode demorar alguns minutos)...
    if exist "pyproject.toml" (
        "%PYTHON_CMD%" -m pip install -e . >nul 2>&1
    ) else if exist "requirements.txt" (
        "%PYTHON_CMD%" -m pip install -r requirements.txt >nul 2>&1
    ) else (
        echo [AVISO] Nenhum pyproject.toml ou requirements.txt encontrado.
        echo         Instalando pacotes essenciais manualmente...
        "%PYTHON_CMD%" -m pip install fastapi uvicorn sqlalchemy pydantic xgboost lightgbm scikit-learn pandas numpy mlflow streamlit requests plotly >nul 2>&1
    )
) else (
    echo        Dependências principais já instaladas.
)

:DEPS_CHECK
:: Verificação final das dependências críticas
"%PYTHON_CMD%" -c "import fastapi, uvicorn, sqlalchemy, xgboost, pandas, numpy, sklearn, mlflow" >nul 2>&1
if errorlevel 1 (
    echo [AVISO] Algumas dependências podem estar em falta. O sistema tentará continuar.
) else (
    echo        OK — Dependências principais validadas.
)

:: ============================================================================
:: 4. VERIFICAR FICHEIRO .env
:: ============================================================================
echo [4/8] Verificando configuração (.env)...
if not exist "%APP_DIR%\.env" (
    if exist "%APP_DIR%\.env.example" (
        echo        .env não encontrado. Criando a partir de .env.example...
        copy "%APP_DIR%\.env.example" "%APP_DIR%\.env" >nul
        echo [AVISO] Ficheiro .env criado a partir do template.
        echo         Edite '%APP_DIR%\.env' para configurar as suas credenciais.
    ) else (
        echo [AVISO] .env e .env.example não encontrados.
    )
) else (
    echo        OK — .env encontrado.
)

:: ============================================================================
:: 5. VERIFICAR/GERAR DADOS MOCK (Zero Custo)
:: ============================================================================
echo [5/8] Verificando dados de treino (modo zero custo)...
if not exist "%APP_DIR%\data" mkdir "%APP_DIR%\data" >nul 2>&1
if not exist "%APP_DIR%\data\bronze" mkdir "%APP_DIR%\data\bronze" >nul 2>&1

:: Verificar se existem dados mock (vários nomes possíveis)
set "MOCK_FOUND=0"
if exist "%APP_DIR%\data\bronze\football_mock.parquet" set "MOCK_FOUND=1"
if exist "%APP_DIR%\data\football_mock.parquet" set "MOCK_FOUND=1"
if exist "%APP_DIR%\data\bronze\matches_football_mock.parquet" set "MOCK_FOUND=1"
if exist "%APP_DIR%\data\matches_football_mock.parquet" set "MOCK_FOUND=1"

if %MOCK_FOUND%==0 (
        echo        Dados mock não encontrados. Gerando dataset sintético...
        %RUN_PREFIX% "%PYTHON_CMD%" scripts\ingest_free_data.py --sport football --source mock >nul 2>&1
        if errorlevel 1 (
            echo [AVISO] Não foi possível gerar dados mock automaticamente.
        ) else (
            echo        OK — Dados mock gerados.
        )
    ) else (
        echo        OK — Dados mock encontrados.
    )
) else (
    echo        OK — Dados mock encontrados.
)

:: ============================================================================
:: 6. VERIFICAR MODELOS TREINADOS
:: ============================================================================
echo [6/8] Verificando modelos treinados...
if not exist "%APP_DIR%\models" mkdir "%APP_DIR%\models" >nul 2>&1

set "MODEL_FOUND=0"
if exist "%APP_DIR%\models\*.pkl" set "MODEL_FOUND=1"
if exist "%APP_DIR%\models\*.joblib" set "MODEL_FOUND=1"
if exist "%APP_DIR%\models\*.json" set "MODEL_FOUND=1"
:: Verificar também em subpastas
for /d %%D in ("%APP_DIR%\models\*") do (
    if exist "%%D\*.pkl" set "MODEL_FOUND=1"
    if exist "%%D\*.joblib" set "MODEL_FOUND=1"
    if exist "%%D\*.json" set "MODEL_FOUND=1"
)

if %MODEL_FOUND%==0 (
    echo        Nenhum modelo treinado encontrado.
    echo.
    echo    ╔══════════════════════════════════════════════════════════════════════╗
    echo    ║  PRIMEIRA EXECUÇÃO DETETADA                                          ║
    echo    ║                                                                      ║
    echo    ║  É necessário treinar o modelo antes de executar o pipeline.         ║
    echo    ║                                                                      ║
    echo    ╚══════════════════════════════════════════════════════════════════════╝
    echo.
    echo        Deseja treinar o modelo agora? (S/N)
    set /p TRAIN_CHOICE="> "
    if /I "%TRAIN_CHOICE%"=="S" (
        echo.
        echo [TREINO] Iniciando treino do modelo football (mock)...
        %RUN_PREFIX% "%PYTHON_CMD%" scripts\train_bot.py football --source mock --walk-forward
        if errorlevel 1 (
            echo [ERRO] Treino falhou. Verifique os logs acima.
            pause
            exit /b 1
        )
        echo [TREINO] Modelo treinado com sucesso.
    ) else (
        echo [AVISO] A continuar sem modelo treinado. Algumas funcionalidades podem não funcionar.
    )
) else (
    echo        OK — Modelos treinados encontrados.
)

:: ============================================================================
:: 7. HEALTH CHECK (VBQ Doctor)
:: ============================================================================
echo [7/8] Executando health check...
%RUN_PREFIX% "%PYTHON_CMD%" scripts\vbq_doctor.py --verbose >nul 2>&1
if errorlevel 1 (
    echo [AVISO] Health check reportou problemas. Verifique '%PYTHON_CMD% scripts\vbq_doctor.py --verbose'.
) else (
    echo        OK — Health check passou.
)

:: ============================================================================
:: 8. MENU PRINCIPAL
:: ============================================================================
echo [8/8] Sistema pronto!
echo.

:MENU
cls
echo.
echo    ╔══════════════════════════════════════════════════════════════════════╗
echo    ║                    VBQ-UNIFIED — MENU PRINCIPAL                      ║
echo    ╠══════════════════════════════════════════════════════════════════════╣
echo    ║  Modo atual: PAPER TRADING (sem risco real)                          ║
echo    ╠══════════════════════════════════════════════════════════════════════╣
echo    ║                                                                      ║
echo    ║  [1] Pipeline Live (Paper Trading) — Executar análise diária         ║
echo    ║  [2] Backtest — Testar estratégia em dados históricos                ║
echo    ║  [3] Treinar Modelo — Treinar novo modelo com dados mock             ║
echo    ║  [4] Dashboard — Abrir interface web (Streamlit)                     ║
echo    ║  [5] Relatório CLV — Analisar Closing Line Value                     ║
echo    ║  [6] Relatório Diário — Gerar relatório do dia anterior              ║
echo    ║  [7] Doctor — Verificar saúde do sistema                             ║
echo    ║  [8] Ingestão de Dados — Atualizar dados gratuitos                   ║
echo    ║  [9] Arbitragem — Detetar oportunidades de arbitragem                ║
echo    ║                                                                      ║
echo    ║  [T] Testes — Executar suite de testes                               ║
echo    ║  [C] Clean — Limpar caches e ficheiros temporários                   ║
echo    ║  [D] Docker — Iniciar stack completa (Docker Compose)                ║
echo    ║                                                                      ║
echo    ║  [0] Sair                                                            ║
echo    ╚══════════════════════════════════════════════════════════════════════╝
echo.
set /p CHOICE="Escolha uma opção: "

if "%CHOICE%"=="1" goto PIPELINE_LIVE
if "%CHOICE%"=="2" goto BACKTEST
if "%CHOICE%"=="3" goto TRAIN
if "%CHOICE%"=="4" goto DASHBOARD
if "%CHOICE%"=="5" goto CLV_REPORT
if "%CHOICE%"=="6" goto DAILY_REPORT
if "%CHOICE%"=="7" goto DOCTOR
if "%CHOICE%"=="8" goto INGEST_DATA
if "%CHOICE%"=="9" goto ARBITRAGE
if /I "%CHOICE%"=="T" goto TESTS
if /I "%CHOICE%"=="C" goto CLEAN
if /I "%CHOICE%"=="D" goto DOCKER
if "%CHOICE%"=="0" goto EXIT

echo Opção inválida. Tente novamente.
timeout /t 2 >nul
goto MENU

:: ============================================================================
:: OPÇÃO 1: PIPELINE LIVE (PAPER TRADING)
:: ============================================================================
:PIPELINE_LIVE
cls
echo.
echo    ╔══════════════════════════════════════════════════════════════════════╗
echo    ║  PIPELINE LIVE — Paper Trading                                       ║
echo    ╚══════════════════════════════════════════════════════════════════════╝
echo.
echo    A executar pipeline em modo PAPER (sem apostas reais)...
echo.
%RUN_PREFIX% "%PYTHON_CMD%" scripts\run_pipeline.py --sport football --mode live --dry-run
echo.
echo    Pressione qualquer tecla para voltar ao menu...
pause >nul
goto MENU

:: ============================================================================
:: OPÇÃO 2: BACKTEST
:: ============================================================================
:BACKTEST
cls
echo.
echo    ╔══════════════════════════════════════════════════════════════════════╗
echo    ║  BACKTEST — Teste Histórico                                          ║
echo    ╚══════════════════════════════════════════════════════════════════════╝
echo.
set /p SPORT="Desporto (football/nba/ufc) [football]: "
if "%SPORT%"=="" set "SPORT=football"
set /p START_DATE="Data início (YYYY-MM-DD) [2024-01-01]: "
if "%START_DATE%"=="" set "START_DATE=2024-01-01"
set /p END_DATE="Data fim (YYYY-MM-DD) [2024-12-31]: "
if "%END_DATE%"=="" set "END_DATE=2024-12-31"
echo.
echo    A executar backtest walk-forward...
echo.
%RUN_PREFIX% "%PYTHON_CMD%" scripts\run_pipeline.py --sport %SPORT% --mode backtest --start %START_DATE% --end %END_DATE% --check-leakage
echo.
echo    Pressione qualquer tecla para voltar ao menu...
pause >nul
goto MENU

:: ============================================================================
:: OPÇÃO 3: TREINAR MODELO
:: ============================================================================
:TRAIN
cls
echo.
echo    ╔══════════════════════════════════════════════════════════════════════╗
echo    ║  TREINAR MODELO                                                      ║
echo    ╚══════════════════════════════════════════════════════════════════════╝
echo.
set /p SPORT="Desporto (football/nba) [football]: "
if "%SPORT%"=="" set "SPORT=football"
echo.
echo    Opções de treino:
echo    [1] Treino simples com dados mock
echo    [2] Treino com walk-forward validation
echo    [3] Treino com calibração isotónica
echo.
set /p TRAIN_OPT="Opção [2]: "
if "%TRAIN_OPT%"=="" set "TRAIN_OPT=2"

if "%TRAIN_OPT%"=="1" (
    %RUN_PREFIX% "%PYTHON_CMD%" scripts\train_bot.py %SPORT% --source mock
)
if "%TRAIN_OPT%"=="2" (
    %RUN_PREFIX% "%PYTHON_CMD%" scripts\train_bot.py %SPORT% --source mock --walk-forward
)
if "%TRAIN_OPT%"=="3" (
    %RUN_PREFIX% "%PYTHON_CMD%" scripts\train_bot.py %SPORT% --source mock --calibrate
)

echo.
echo    Pressione qualquer tecla para voltar ao menu...
pause >nul
goto MENU

:: ============================================================================
:: OPÇÃO 4: DASHBOARD STREAMLIT
:: ============================================================================
:DASHBOARD
cls
echo.
echo    ╔══════════════════════════════════════════════════════════════════════╗
echo    ║  DASHBOARD — Interface Web                                           ║
echo    ╚══════════════════════════════════════════════════════════════════════╝
echo.
echo    A iniciar dashboard Streamlit...
echo    Aceda em: http://localhost:8501
echo.
echo    (Feche a janela do dashboard ou pressione Ctrl+C para parar)
echo.
%RUN_PREFIX% "%PYTHON_CMD%" -m streamlit run scripts\dashboard.py
echo.
echo    Pressione qualquer tecla para voltar ao menu...
pause >nul
goto MENU

:: ============================================================================
:: OPÇÃO 5: RELATÓRIO CLV
:: ============================================================================
:CLV_REPORT
cls
echo.
echo    ╔══════════════════════════════════════════════════════════════════════╗
echo    ║  RELATÓRIO CLOSING LINE VALUE (CLV)                                  ║
echo    ╚══════════════════════════════════════════════════════════════════════╝
echo.
echo    A gerar relatório CLV...
echo.
%RUN_PREFIX% "%PYTHON_CMD%" scripts\run_clv_report.py
echo.
echo    Pressione qualquer tecla para voltar ao menu...
pause >nul
goto MENU

:: ============================================================================
:: OPÇÃO 6: RELATÓRIO DIÁRIO
:: ============================================================================
:DAILY_REPORT
cls
echo.
echo    ╔══════════════════════════════════════════════════════════════════════╗
echo    ║  RELATÓRIO DIÁRIO                                                    ║
echo    ╚══════════════════════════════════════════════════════════════════════╝
echo.
echo    A gerar relatório diário...
echo.
%RUN_PREFIX% "%PYTHON_CMD%" scripts\daily_report.py
echo.
echo    Pressione qualquer tecla para voltar ao menu...
pause >nul
goto MENU

:: ============================================================================
:: OPÇÃO 7: DOCTOR (HEALTH CHECK)
:: ============================================================================
:DOCTOR
cls
echo.
echo    ╔══════════════════════════════════════════════════════════════════════╗
echo    ║  VBQ DOCTOR — Diagnóstico do Sistema                                 ║
echo    ╚══════════════════════════════════════════════════════════════════════╝
echo.
%RUN_PREFIX% "%PYTHON_CMD%" scripts\vbq_doctor.py --verbose --fail-on-error
echo.
echo    Pressione qualquer tecla para voltar ao menu...
pause >nul
goto MENU

:: ============================================================================
:: OPÇÃO 8: INGESTÃO DE DADOS
:: ============================================================================
:INGEST_DATA
cls
echo.
echo    ╔══════════════════════════════════════════════════════════════════════╗
echo    ║  INGESTÃO DE DADOS GRATUITOS                                         ║
echo    ╚══════════════════════════════════════════════════════════════════════╝
echo.
set /p SPORT="Desporto (football/nba) [football]: "
if "%SPORT%"=="" set "SPORT=football"
echo.
echo    Fontes disponíveis:
echo    [1] Mock (dados sintéticos gratuitos)
echo    [2] football-data.org (API gratuita — requer token)
echo.
set /p SOURCE="Fonte [1]: "
if "%SOURCE%"=="" set "SOURCE=1"

if "%SOURCE%"=="1" (
    %RUN_PREFIX% "%PYTHON_CMD%" scripts\ingest_free_data.py --sport %SPORT% --source mock
)
if "%SOURCE%"=="2" (
    %RUN_PREFIX% "%PYTHON_CMD%" scripts\ingest_free_data.py --sport %SPORT% --source football-data
)

echo.
echo    Pressione qualquer tecla para voltar ao menu...
pause >nul
goto MENU

:: ============================================================================
:: OPÇÃO 9: ARBITRAGEM
:: ============================================================================
:ARBITRAGE
cls
echo.
echo    ╔══════════════════════════════════════════════════════════════════════╗
echo    ║  DETEÇÃO DE ARBITRAGEM                                               ║
echo    ╚══════════════════════════════════════════════════════════════════════╝
echo.
echo    A procurar oportunidades de arbitragem...
echo.
%RUN_PREFIX% "%PYTHON_CMD%" scripts\run_arbitrage.py
echo.
echo    Pressione qualquer tecla para voltar ao menu...
pause >nul
goto MENU

:: ============================================================================
:: OPÇÃO T: TESTES
:: ============================================================================
:TESTS
cls
echo.
echo    ╔══════════════════════════════════════════════════════════════════════╗
echo    ║  SUITE DE TESTES                                                     ║
echo    ╚══════════════════════════════════════════════════════════════════════╝
echo.
%RUN_PREFIX% "%PYTHON_CMD%" -m pytest tests\ -q --tb=short
echo.
echo    Pressione qualquer tecla para voltar ao menu...
pause >nul
goto MENU

:: ============================================================================
:: OPÇÃO C: CLEAN
:: ============================================================================
:CLEAN
cls
echo.
echo    ╔══════════════════════════════════════════════════════════════════════╗
echo    ║  LIMPEZA DE CACHES                                                   ║
echo    ╚══════════════════════════════════════════════════════════════════════╝
echo.
echo    A limpar __pycache__ e ficheiros temporários...
for /d /r "%APP_DIR%" %%d in (__pycache__) do @if exist "%%d" rd /s /q "%%d" 2>nul
del /s /q "%APP_DIR%\*.pyc" 2>nul
echo    Limpeza concluída.
echo.
echo    Pressione qualquer tecla para voltar ao menu...
pause >nul
goto MENU

:: ============================================================================
:: OPÇÃO D: DOCKER
:: ============================================================================
:DOCKER
cls
echo    ║  DOCKER COMPOSE                                                      ║
echo    ╚══════════════════════════════════════════════════════════════════════╝
echo.
docker --version >nul 2>&1
if errorlevel 1 (
    echo [ERRO] Docker não encontrado. Instale o Docker Desktop.
    echo        https://www.docker.com/products/docker-desktop/
) else (
    echo    Opções:
    echo    [1] Up (Iniciar stack)
    echo    [2] Down (Parar stack)
    echo    [3] Logs (Ver logs)
    echo.
    set /p DOCKER_OPT="Opção [1]: "
    if "%DOCKER_OPT%"=="" set "DOCKER_OPT=1"

    if "%DOCKER_OPT%"=="1" (
        echo    A iniciar stack completa...
        docker compose -f "%APP_DIR%\docker-compose.yml" up -d
        echo.
        echo    - API:        http://localhost:8000
        echo    - MLflow:     http://localhost:5000
        echo    - Grafana:    http://localhost:3000
        echo    - Prometheus: http://localhost:9090
    )
    if "%DOCKER_OPT%"=="2" (
        docker compose -f "%APP_DIR%\docker-compose.yml" down
        echo    Stack parada.
    )
    if "%DOCKER_OPT%"=="3" (
        docker compose -f "%APP_DIR%\docker-compose.yml" logs -f
    )
)
echo.
echo    Pressione qualquer tecla para voltar ao menu...
pause >nul
goto MENU

:: ============================================================================
:: SAIR
:: ============================================================================
:EXIT
cls
echo.
echo    Obrigado por usar o VBQ-UNIFIED!
echo.
echo    Lembre-se: este sistema opera em MODO PAPER TRADING por defeito.
echo    Nenhuma aposta real é colocada sem configuração explícita.
echo.
timeout /t 3 >nul
endlocal
exit /b 0
