@echo off
chcp 65001 >nul
ECHO ========================================
ECHO Zeniji Emotion Simul 설치 스크립트
ECHO ========================================
ECHO.

REM Python 설치 여부 확인 (UV 설치를 위해 필요)
ECHO Python 설치 확인 중...
python --version >nul 2>&1
if errorlevel 1 (
    ECHO [오류] Python이 설치되어 있지 않습니다.
    ECHO.
    ECHO Python 3.11.x 을 설치해주세요: https://www.python.org/downloads/release/python-3110/
    ECHO.
    ECHO 설치 시 "Add Python to PATH" 옵션을 체크하세요.
    ECHO.
    pause
    exit /b 1
)

REM pip 설치 여부 확인 및 자동 설치
pip --version >nul 2>&1
if errorlevel 1 (
    ECHO pip가 설치되어 있지 않습니다. 자동으로 설치합니다...
    python -m ensurepip --upgrade
    if errorlevel 1 (
        ECHO [오류] pip 설치에 실패했습니다.
        ECHO Python과 함께 pip가 설치되어 있는지 확인해주세요.
        ECHO.
        pause
        exit /b 1
    )
    ECHO [완료] pip 설치 완료
    ECHO.
)

ECHO [확인] Python과 pip가 설치되어 있습니다.
ECHO.

REM Python 버전 확인
ECHO Python 버전 확인 중...
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
ECHO 현재 Python 버전: %PYTHON_VERSION%

REM 버전 문자열에서 3.11 확인
echo %PYTHON_VERSION% | findstr /R "^3\.11\." >nul
if errorlevel 1 (
    ECHO Python 3.11.x가 아니므로 UV를 사용하여 Python 3.11 가상환경을 생성합니다.
    set USE_UV=1
) else (
    ECHO Python 3.11.x가 설치되어 있습니다. 일반 venv를 사용합니다.
    set USE_UV=0
)
ECHO.

REM 저장소가 이미 클론되어 있는지 확인 (.git 폴더 존재 여부)
if exist ".git" (
    ECHO [1/4] 저장소가 이미 존재합니다. 기존 저장소 사용
    set REPO_DIR=%~dp0
) else (
    ECHO [1/4] 저장소 클론 중...
    ECHO 저장소를 클론할 위치: %CD%
    ECHO.
    git clone https://github.com/zeniji-illust/Zeniji-EMotion-Simul
    if errorlevel 1 (
        ECHO [오류] 저장소 클론에 실패했습니다.
        pause
        exit /b 1
    )
    ECHO [완료] 저장소 클론 완료
    ECHO.
    ECHO 저장소 폴더로 이동 중...
    cd Zeniji-EMotion-Simul
    if errorlevel 1 (
        ECHO [오류] 저장소 폴더로 이동할 수 없습니다.
        pause
        exit /b 1
    )
    set REPO_DIR=%CD%
)

ECHO.

REM UV가 필요한 경우 UV 설치 확인
if "%USE_UV%"=="1" (
    ECHO [2/4] UV 설치 확인 중...
    uv --version >nul 2>&1
    if errorlevel 1 (
        ECHO UV가 설치되어 있지 않습니다. 설치 중...
        pip install uv
        if errorlevel 1 (
            ECHO [오류] UV 설치에 실패했습니다.
            pause
            exit /b 1
        )
        ECHO [완료] UV 설치 완료
    ) else (
        ECHO [확인] UV가 이미 설치되어 있습니다.
    )
    ECHO.
)

REM 가상환경이 이미 존재하는지 확인
if exist ".venv" (
    ECHO [경고] .venv 폴더가 이미 존재합니다.
    ECHO 기존 가상환경을 삭제하고 새로 만들까요? (Y/N)
    set /p RECREATE_VENV=
    if /i "%RECREATE_VENV%"=="Y" (
        ECHO 기존 가상환경 삭제 중...
        rmdir /s /q .venv
        ECHO.
    ) else (
        ECHO 기존 가상환경을 유지합니다.
        ECHO.
        ECHO ========================================
        ECHO 설치가 완료되었습니다!
        ECHO ========================================
        ECHO.
        ECHO 다음 단계:
        ECHO 1. start.bat를 실행하여 애플리케이션을 시작하세요.
        ECHO.
        ECHO ========================================
        ECHO.
        pause
        exit /b 0
    )
)

REM 가상환경 생성
if "%USE_UV%"=="1" (
    ECHO [3/4] UV를 통해 가상환경 생성 중...
    uv venv --python 3.11 --seed
    if errorlevel 1 (
        ECHO [오류] 가상환경 생성에 실패했습니다.
        pause
        exit /b 1
    )
    ECHO [완료] 가상환경이 생성되었습니다.
) else (
    ECHO [3/4] 가상환경 생성 중...
    python -m venv .venv
    if errorlevel 1 (
        ECHO [오류] 가상환경 생성에 실패했습니다.
        pause
        exit /b 1
    )
    ECHO [완료] 가상환경이 생성되었습니다.
)
ECHO.

REM requirements.txt 확인
if not exist "requirements.txt" (
    ECHO [오류] requirements.txt 파일을 찾을 수 없습니다.
    pause
    exit /b 1
)

REM 의존성 설치
ECHO [4/4] 의존성 설치 중...
ECHO 이 작업은 몇 분이 걸릴 수 있습니다...
ECHO.
.venv\Scripts\pip.exe install -r requirements.txt
if errorlevel 1 (
    ECHO.
    ECHO [오류] 의존성 설치에 실패했습니다.
    pause
    exit /b 1
)

ECHO.
ECHO ========================================
ECHO 설치가 완료되었습니다!
ECHO ========================================
ECHO.
ECHO 다음 단계:
ECHO 1. start.bat를 실행하여 애플리케이션을 시작하세요.
ECHO 2. 또는 수동으로:
ECHO    - start_ollama_serve.bat 실행 (Ollama 서버)
ECHO    - .venv\Scripts\activate
ECHO    - python python\app.py
ECHO.
ECHO ========================================
ECHO.
pause
