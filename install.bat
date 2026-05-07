@echo off
chcp 65001 >nul
REM ============================================================
REM  자비스 음성 비서 — 부트스트랩 설치 (신규 PC / 재설치)
REM  더블클릭 한 번이면 끝.
REM
REM  하는 일:
REM   1) %LOCALAPPDATA%\voice_assistant\ 폴더 생성
REM   2) bootstrap.vbs를 토큰 치환 후 로컬로 복사
REM      (__MAIN_PY__, __WORK_DIR__ → 이 install.bat 실행 폴더 기준 절대경로)
REM   3) Startup 바로가기를 로컬 vbs로 등록
REM
REM  결과: 다음 로그인 ~45초 후 자비스 자동 가동
REM ============================================================

setlocal EnableDelayedExpansion
set "REPO_DIR=%~dp0"
if "%REPO_DIR:~-1%"=="\" set "REPO_DIR=%REPO_DIR:~0,-1%"

set "SRC=%REPO_DIR%\bootstrap.vbs"
set "MAIN_PY=%REPO_DIR%\main.py"
set "DST_DIR=%LOCALAPPDATA%\voice_assistant"
set "DST=%DST_DIR%\bootstrap.vbs"
set "LNK=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\Jarvis_Voice.lnk"

echo === 자비스 부트스트랩 설치 ===
echo  리포 폴더 : %REPO_DIR%
echo  메인 .py  : %MAIN_PY%
echo  대상 vbs  : %DST%
echo  바로가기  : %LNK%
echo.

if not exist "%SRC%" (
  echo [X] bootstrap.vbs 가 없음. 리포 폴더에서 install.bat 을 실행하세요.
  pause
  exit /b 1
)
if not exist "%MAIN_PY%" (
  echo [X] main.py 가 없음. 리포 폴더에서 install.bat 을 실행하세요.
  pause
  exit /b 1
)

REM 1) 로컬 폴더 생성
if not exist "%DST_DIR%" (
  mkdir "%DST_DIR%"
  echo [1] 로컬 폴더 생성
) else (
  echo [1] 로컬 폴더 이미 존재
)

REM 2) bootstrap.vbs 토큰 치환 + 복사 (PowerShell 1줄)
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
 "$src='%SRC%'; $dst='%DST%'; $main='%MAIN_PY%'; $work='%REPO_DIR%'; (Get-Content -Raw -Encoding UTF8 $src).Replace('__MAIN_PY__', $main).Replace('__WORK_DIR__', $work) | Set-Content -Encoding UTF8 -NoNewline $dst"
if errorlevel 1 (
  echo [X] bootstrap.vbs 치환 실패
  pause
  exit /b 1
)
echo [2] bootstrap.vbs 토큰 치환 + 복사 완료

REM 3) Startup 바로가기 등록 (PowerShell 1줄)
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
 "$sh = New-Object -ComObject WScript.Shell; $l = $sh.CreateShortcut('%LNK%'); $l.TargetPath = $env:WINDIR + '\System32\wscript.exe'; $l.Arguments = '\"%DST%\"'; $l.WorkingDirectory = '%DST_DIR%'; $l.WindowStyle = 7; $l.Description = 'Jarvis Voice Assistant (local bootstrap)'; $l.Save()"
if errorlevel 1 (
  echo [X] 바로가기 등록 실패
  pause
  exit /b 1
)
echo [3] Startup 바로가기 등록 완료
echo.
echo ============================================================
echo  설치 성공. 다음 부팅부터 적용.
echo  - 로그인 약 45초 후 자비스 자동 가동
echo  - 즉시 테스트: wscript "%DST%"
echo  - 끄기: uninstall.bat 실행
echo ============================================================
pause
