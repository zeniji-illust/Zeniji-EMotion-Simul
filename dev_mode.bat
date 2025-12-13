@echo off
ECHO ========================================
ECHO Zeniji Emotion Simul (Dev Mode) 시작 중...
ECHO ========================================
ECHO.

REM Python 앱 실행
ECHO Python 앱 시작 중 (Dev Mode)...
call .venv\Scripts\activate.bat
python -m python.app --dev-mode

REM 오류 코드 저장
set EXIT_CODE=%ERRORLEVEL%

REM 프로그램 종료 후 창이 자동으로 닫히지 않도록 대기
ECHO.
ECHO ========================================
if %EXIT_CODE% NEQ 0 (
    ECHO 프로그램이 오류 코드 %EXIT_CODE%로 종료되었습니다.
    ECHO 위의 오류 메시지를 확인하세요.
) else (
    ECHO 프로그램이 정상적으로 종료되었습니다.
)
ECHO ========================================
ECHO.
ECHO 아무 키나 누르면 창이 닫힙니다...
pause >nul
