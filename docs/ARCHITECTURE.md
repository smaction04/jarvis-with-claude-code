# 아키텍처

## 전체 데이터 흐름

```
┌──────────────────┐
│  마이크 (PyAudio)  │
└────────┬─────────┘
         │ raw audio
         ▼
┌──────────────────────────────┐
│  SpeechRecognition.listen()  │ (메인 스레드 — 끊김 없는 listen 루프)
└────────┬─────────────────────┘
         │ audio chunk
         ▼ (background thread)
┌──────────────────────────────────┐
│  recognize_google(ko-KR)         │
│  → 텍스트                          │
└────────┬─────────────────────────┘
         │
         ▼
┌──────────────────────────────────┐
│  has_wake?  is_active?           │
│  └─ 웨이크워드 + 명령 → execute()  │
│  └─ 웨이크워드만 → activate_listening()
│  └─ active 상태 + 텍스트 → execute()
└────────┬─────────────────────────┘
         │
         ▼
┌──────────────────────────────────┐
│  execute(text)                   │
│   ├─ ui("processing")             │
│   ├─ find_or_launch_target()      │
│   │    ├─ 있으면 → activate         │
│   │    └─ 없으면 → VSCode 풀 부트스트랩
│   ├─ send_text(text)  (clipboard) │
│   └─ ui("result", text) → 1.2초 후 idle
└──────────────────────────────────┘
```

## 컴포넌트

### 1. 음성 인식 레이어 (`voice_loop`, `process_audio`, `recognize`)

- `Recognizer.energy_threshold = max(20, ambient * 0.6)` — 환경 소음 보정 후 60%로 낮춰서 작은 발화도 잡음
- `pause_threshold = 1.0` — 발화 끝 판단에 1초 침묵 필요
- 메인 스레드는 listen만, 인식·실행은 백그라운드 스레드 → 발화 놓침 최소화

### 2. UI 레이어 (`ui`, `apply_no_activate_style`, `overlay.html`)

- pywebview로 frameless 윈도우 생성
- 윈도우 생성 직후 user32로 `WS_EX_NOACTIVATE | WS_EX_TOOLWINDOW` 적용 → 클릭해도 포커스 안 뺏고, 작업표시줄에도 안 뜸
- `SetWindowPos(HWND_TOPMOST)` 강제로 항상 위
- idle 상태 = `window.hide()` (OS 레벨), active 상태 = show + resize + move
- HTML 측은 상태별 CSS 클래스(`error`, `success`)로 색만 토글

### 3. 활성창 식별 레이어 (`find_target_window`, `_get_process_name`)

- `EnumWindows`로 모든 visible 윈도우 순회
- 자비스 본인(`kimassistant`) + 브라우저(`EXCLUDE_PROC`) 제외
- 우선순위 리스트(`TARGET_TITLES`)에서 가장 앞쪽 매치하는 hwnd 선택
- `OpenProcess` + `QueryFullProcessImageNameW`로 프로세스명 확인

### 4. 풀 부트스트랩 레이어 (`launch_vscode`, `find_or_launch_target`)

- VSCode 후보 경로 3개 + PATH 폴백
- 워크스페이스 = `JARVIS_WORK_DIR` 환경변수 (기본값: `~/Documents`)
- 신규 실행 시 4초 대기 → 재활성화 → `Ctrl+Shift+`` (새 터미널) → `claude` CLI → 12초 대기

### 5. 자동시작 레이어 (`bootstrap.vbs`, `install.bat`)

- **로컬 부트스트랩 패턴** — Startup이 가리키는 vbs는 항상 로컬, 메인 .py는 클라우드여도 무방
- vbs가 45초 대기 + 마운트 폴링(5초 간격, 최대 5분) + pythonw 동적 탐색
- install.bat이 vbs의 `__MAIN_PY__`/`__WORK_DIR__` 토큰을 본인 폴더 기준으로 치환

## 스레드 모델

| 스레드 | 역할 | 시작점 |
|--------|------|--------|
| 메인 | pywebview 이벤트 루프 + `safe_listen` | `webview.start()` |
| voice_loop | 마이크 listen 무한 루프 | `on_loaded()` |
| process_audio | 발화 1건당 1 스레드 (인식 + 실행) | `voice_loop` 안 |
| apply_no_activate_style | 윈도우 핸들 찾을 때까지 폴링 | `on_loaded()` |
| _hide_timer | 결과 표시 후 1.2초 뒤 idle 복귀 | `ui()` |

`_exec_lock`으로 동시 execute 방지. 한 발화 처리 중 다음 명령은 lock 풀린 뒤 직렬 실행.

## 로그 정책

- 위치: `%LOCALAPPDATA%\voice_assistant\logs\app_<호스트>.log`
- PC별 분리(`socket.gethostname()`) — 클라우드 동기화 충돌 회피
- 모든 `print()`는 `_log` 단일 라우팅 (sys.stdout/stderr 리디렉트)
- 줄 바꿈마다 flush — 비정상 종료 시에도 마지막 라인 유실 X
