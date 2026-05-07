# 프롬프트 #7 — install.bat 신규 PC 1분 셋업 (멀티 PC)

## 클로드한테 던진 원문

> 신규 윈도우 PC에서 더블클릭 한 번으로 자비스 자동시작 등록되게 install.bat 만들어줘. bootstrap.vbs를 로컬로 복사하고 Startup에 바로가기 등록까지. 사용자가 어디에 clone했든 그 폴더 기준으로 동작해야 해.

## 받은 결과 요약

- `setlocal EnableDelayedExpansion` + `set "REPO_DIR=%~dp0"` (이 .bat 실행 폴더 = 리포 루트)
- 끝에 붙은 backslash 제거: `if "%REPO_DIR:~-1%"=="\" set "REPO_DIR=%REPO_DIR:~0,-1%"`
- 토큰 치환은 PowerShell 1줄로:
  ```bat
  powershell -NoProfile -ExecutionPolicy Bypass -Command ^
   "(Get-Content -Raw -Encoding UTF8 $src).Replace('__MAIN_PY__', $main).Replace('__WORK_DIR__', $work) | Set-Content -Encoding UTF8 -NoNewline $dst"
  ```
- Startup 바로가기 등록도 PowerShell COM:
  ```bat
  powershell -NoProfile -ExecutionPolicy Bypass -Command ^
   "$sh = New-Object -ComObject WScript.Shell; $l = $sh.CreateShortcut('%LNK%'); $l.TargetPath = $env:WINDIR + '\System32\wscript.exe'; $l.Arguments = '\"%DST%\"'; $l.WindowStyle = 7; $l.Save()"
  ```
  - `WindowStyle = 7` = 최소화 표시 안 함 (vbs는 어차피 콘솔 X지만 안전장치)

## 실측 트러블 + 해결

| 증상 | 원인 | 해결 프롬프트 |
|------|------|--------------|
| 한글 경로 PC에서 `chcp 65001 >nul` 없으면 깨짐 | bat 디폴트 코드페이지 949 | "맨 위에 chcp 65001 >nul 추가" |
| `Set-Content`에 BOM 붙어서 vbs 인코딩 깨짐 | PowerShell 5.1 `Set-Content -Encoding UTF8`은 BOM 포함 | "-NoNewline 추가하고, BOM 문제 발생 시 [System.IO.File]::WriteAllText로 교체" |
| 바로가기 `Arguments`에 따옴표 포함된 경로 처리 실패 | `'\"%DST%\"'` 이스케이프 까다로움 | "PowerShell 안에서 작은따옴표로 감싸고 \" 이스케이프" |
| install.bat을 한글 폴더에서 실행 시 PowerShell이 경로 못 받음 | `%~dp0` 결과 + bat 인코딩 미스매치 | "chcp 65001 + EnableDelayedExpansion 콤보로 해결" |

→ 최종 결과물: `install.bat` + `uninstall.bat` (Startup 해제 + `%LOCALAPPDATA%\voice_assistant` 정리).

## 다음 단계로 이어갈 때 주의

- README의 "빠른 시작 5분"에 PyAudio 설치 폴백(`pipwin install pyaudio`) **반드시 명시**. PyAudio가 가장 큰 첫 진입 장벽.
- 04 QA 검증 체크 (github_repo_spec_jarvis_v1.md §7): **신규 윈도우 PC에서 clone → install → 동작까지 15분 이내**가 목표.
