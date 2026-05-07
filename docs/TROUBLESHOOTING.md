# 트러블슈팅 — 자주 묻는 10개

## Q1. "자비스"라고 말해도 반응이 없어요

1. **마이크 권한** — 윈도우 설정 → 개인정보 보호 → 마이크 → "데스크톱 앱이 마이크에 액세스" ✅
2. **로그 확인** — `%LOCALAPPDATA%\voice_assistant\logs\app_<호스트>.log` 마지막 줄
3. **임계값** — 로그에 `[보정] 임계값 = N` 확인. 60 이상이면 환경 너무 시끄러움 → 마이크 가까이 두거나 노이즈 제거 헤드셋
4. **WAKE_WORDS 확장** — 인식이 자꾸 "차비스"·"자뱀스"로 들리면 `main.py`의 `WAKE_WORDS` 리스트에 본인 발음 패턴 추가

## Q2. PyAudio 설치가 자꾸 실패해요

```bash
pip install pipwin
pipwin install pyaudio
```

또는 [unofficial wheels](https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio)에서 본인 Python 버전 맞는 .whl 직접 다운로드 후 `pip install <파일>.whl`.

## Q3. HUD가 안 뜨거나 검은 화면만 떠요

- WebView2 런타임 미설치. 마이크로소프트에서 [Evergreen Standalone Installer](https://developer.microsoft.com/en-us/microsoft-edge/webview2/) 받아 설치.
- 일부 윈도우 11에서는 기본 포함이지만 LTSC 등은 별도 설치 필요.

## Q4. 자비스 호출했는데 명령이 자비스 본인 윈도우에 입력돼요

`find_target_window()`가 `kimassistant` 제목을 제외하는데, 일부 환경에서 윈도우 타이틀이 비어 있는 케이스 발생 가능. `main.py`의 `cb()` 콜백에서 `title.startswith` 또는 추가 키워드로 제외 강화.

## Q5. 부팅 시 자동 시작 안 돼요

1. `%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\Jarvis_Voice.lnk` 존재 확인
2. 바로가기 속성 → 대상이 `wscript.exe "%LOCALAPPDATA%\voice_assistant\bootstrap.vbs"`인지 확인
3. **Task Manager → 시작 앱 탭에서 사용 안 함으로 막혀있는지** 확인 — 윈도우 11이 자동으로 비활성화 시킬 수 있음
4. `wscript "%LOCALAPPDATA%\voice_assistant\bootstrap.vbs"` 수동 실행해서 `app_<호스트>.log` 시작 라인 떨어지는지 검사

## Q6. 클라우드 드라이브에 리포 두니 부팅이 30초씩 느려져요

이 리포는 그 문제를 해결하려고 만든 거라 install.bat 정상 실행했으면 안 그래야 함. 그래도 느리면:

- Startup 폴더의 `Jarvis_Voice.lnk` **대상**이 클라우드 경로 가리키고 있는지 확인 (가리키면 안 됨, 항상 `%LOCALAPPDATA%\voice_assistant\bootstrap.vbs`)
- 다시 `install.bat` 실행해서 재등록

## Q7. VSCode가 자비스 명령으로 안 떠요

- `main.py`의 `VSCODE_PATHS`에 본인 설치 경로 추가
- 또는 PATH에 `code` 등록 (VSCode 설치 시 옵션)
- Cursor나 다른 IDE 쓰면 `CUSTOMIZATION.md` 참고

## Q8. 한글 명령이 깨져서 들어가요

- `pyautogui.write()` 직접 입력은 한글 못 침. 이 리포는 클립보드 + `Ctrl+V` 패턴이라 안 깨져야 함.
- `pyperclip` 설치 확인. `pip show pyperclip`.
- 일부 IME에서 클립보드 한글 깨짐 → 윈도우 IME 설정에서 "한글" 활성 후 영어 모드로 두고 `Ctrl+V`.

## Q9. `claude` CLI 자동 시작 안 돼요

- 첫 실행은 OAuth 인증 모달이 떠서 사용자 클릭 필요. 한 번 인증 후엔 자동으로 됨.
- `npm install -g @anthropic-ai/claude-code` 또는 공식 설치 가이드대로 미리 설치 필요.
- 다른 CLI(`gpt`, `cursor` 등) 쓰려면 `main.py`의 `send_text("claude")` 라인 수정.

## Q10. 자비스 끄려면?

- 임시: 작업 관리자 → `pythonw.exe` 종료 (자비스 제목은 KimAssistant)
- 자동시작 해제 + 로컬 폴더 정리: `uninstall.bat` 더블클릭
- 리포 폴더 자체는 보존됨 → 수동 실행 (`python main.py`)은 여전히 가능
