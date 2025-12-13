@echo off
ECHO ZenijiES용 Ollama 서버를 최적화된 설정으로 시작합니다...

REM Keep Alive 시간을 1초로 설정하여, 사용 후 VRAM을 빠르게 해제하도록 강제합니다.
set OLLAMA_KEEP_ALIVE=1s

REM 기본 포트와 호스트 설정
set OLLAMA_HOST=127.0.0.1:11434

REM =======================================================
REM 추가: 모델 파일 저장 경로 명시 
REM =======================================================
set OLLAMA_MODELS=D:\models\ollama

ECHO 모델 저장 경로: %OLLAMA_MODELS%

ECHO KEEP_ALIVE=1s, HOST=127.0.0.1:11434 로 설정되었습니다.
ECHO 서버를 종료하려면 이 창을 닫으세요.

REM 시스템에 설치된 ollama.exe를 실행합니다.
ollama serve

PAUSE