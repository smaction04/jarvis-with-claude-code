@echo off
chcp 65001 >nul
REM ============================================================
REM  자비스 음성 비서 — 자동시작 해제 + 로컬 폴더 정리
REM
REM  하는 일:
REM   1) 실행 중인 자비스 프로세스 종료 (KimAssistant 윈도우 + pythonw)
REM   2) Startup 바로가기 삭제
REM   3) %LOCALAPPDATA%\voice_assistant\ 폴더 삭제
REM ============================================================

setlocal
set "DST_DIR=%LOCALAPPDATA%\voice_assistant"
set "LNK=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\Jarvis_Voice.lnk"

echo === 자비스 자동시작 해제 ===
echo  바로가기 : %LNK%
echo  로컬폴더 : %DST_DIR%
echo.

REM 1) 실행 중인 프로세스 종료
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
 "Get-Process pythonw -ErrorAction SilentlyContinue | Where-Object { $_.MainWindowTitle -eq 'KimAssistant' -or ($_.Modules.ModuleName -contains 'webview2.dll') } | Stop-Process -Force -ErrorAction SilentlyContinue"
echo [1] 실행 중 자비스 프로세스 종료 시도

REM 2) Startup 바로가기 삭제
if exist "%LNK%" (
  del /F /Q "%LNK%"
  echo [2] Startup 바로가기 삭제
) else (
  echo [2] Startup 바로가기 없음 (스킵)
)

REM 3) 로컬 폴더 삭제 (로그 포함)
if exist "%DST_DIR%" (
  rmdir /S /Q "%DST_DIR%"
  echo [3] 로컬 폴더 삭제 (로그 포함)
) else (
  echo [3] 로컬 폴더 없음 (스킵)
)

echo.
echo ============================================================
echo  자동시작 해제 완료.
echo  리포 폴더는 보존됨 — 수동 실행은 여전히 가능 (python main.py)
echo ============================================================
pause
