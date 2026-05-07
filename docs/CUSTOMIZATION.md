# 커스터마이즈 — 다른 IDE/CLI로 바꾸기

## 다른 IDE로 (Cursor, Windsurf, JetBrains 등)

`main.py`에서 두 군데만 수정:

### 1. 실행 파일 경로

```python
# 변경 전 (VSCode)
VSCODE_PATHS = [
    os.path.expandvars(r"%LOCALAPPDATA%\Programs\Microsoft VS Code\Code.exe"),
    r"C:\Program Files\Microsoft VS Code\Code.exe",
    r"C:\Program Files (x86)\Microsoft VS Code\Code.exe",
]

# 변경 후 — Cursor 예시
VSCODE_PATHS = [
    os.path.expandvars(r"%LOCALAPPDATA%\Programs\cursor\Cursor.exe"),
    r"C:\Program Files\Cursor\Cursor.exe",
]
```

### 2. 활성창 식별 키워드

```python
# 변경 전
TARGET_TITLES = ["visual studio code", "windows terminal", "powershell", "터미널", "command prompt", "cmd.exe"]

# 변경 후 — Cursor + 기존 터미널
TARGET_TITLES = ["cursor", "windows terminal", "powershell", "터미널"]
```

### 3. (선택) 함수명·로그 메시지

`launch_vscode()` 함수명은 의미상 그냥 두거나 `launch_ide()`로 일괄 rename.

---

## 다른 CLI로 (gpt-cli, aider, gemini 등)

`execute()` 안의 부트스트랩 마지막 단계 한 줄만 변경:

```python
# 변경 전
send_text("claude")

# 변경 후
send_text("aider")          # Aider
# 또는
send_text("gpt")            # gpt-cli
# 또는
send_text("gemini chat")    # gemini-cli
```

CLI별 첫 실행 인증 시간이 다르므로 `time.sleep(12.0)`도 조정:

| CLI | 권장 sleep |
|-----|-----------|
| claude | 12초 (OAuth + 모델 로드) |
| aider | 4초 (API 키만) |
| gpt-cli | 4초 |
| gemini | 6초 |

---

## 웨이크워드 변경 ("자비스" → 다른 이름)

```python
# 변경 전
WAKE_WORDS = ["자비스", "자 비스", "자비 스", "재비스", ...]

# 변경 후 — 예: "조수" 사용
WAKE_WORDS = ["조수", "조수야", "조수님"]
```

발음 인식 안정화를 위해 **본인이 자주 잘못 들리는 변형 3~5개** 같이 추가.

`strip_wake()` 함수가 자동으로 웨이크워드 다음 텍스트만 명령으로 추출하므로 추가 수정 불필요.

---

## HUD 색·크기 변경

`overlay.html`만 건드리면 됨:

| 항목 | CSS 셀렉터 | 변경 위치 |
|------|-----------|----------|
| 듣는중 색 | `.core` `box-shadow` | line 92~94 |
| 성공 색 | `#stage.success .core` | line 195 |
| 오류 색 | `#stage.error .core` | line 184~190 |
| HUD 크기 | `main.py`의 `LARGE_W`, `LARGE_H` | 200~340 권장 |
| HUD 위치 | `main.py`의 `RIGHT_EDGE_X`, `TOP_Y_POS` | 우상단 기본, 좌상단 원하면 `RIGHT_EDGE_X = LARGE_W` |

---

## 입력 방식 변경 (클립보드 → 직접 타이핑)

영문 명령만 쓸 거면 `pyautogui.typewrite()`로 바꿔서 클립보드 우회 가능. 한글 쓸 거면 클립보드 + `Ctrl+V` 유지 권장.

```python
# 변경 전 (클립보드 + Ctrl+V — 한글 OK)
def send_text(text: str):
    pyperclip.copy(text)
    pyautogui.keyDown("ctrl"); pyautogui.press("v"); pyautogui.keyUp("ctrl")
    pyautogui.press("enter")

# 변경 후 (직접 타이핑 — 영문만, 클립보드 안 씀)
def send_text(text: str):
    pyautogui.typewrite(text, interval=0.01)
    pyautogui.press("enter")
```

---

## 다중 작업 폴더 (프로젝트 전환)

`JARVIS_WORK_DIR` 환경변수 대신 명령에서 폴더 키워드로 분기:

```python
def execute(text: str):
    global WORK_DIR
    if "회사" in text:
        WORK_DIR = r"C:\work\company"
        text = text.replace("회사", "").strip()
    elif "사이드" in text:
        WORK_DIR = r"C:\work\side"
        text = text.replace("사이드", "").strip()
    # ... 이하 기존 로직
```

→ "자비스, 회사 일 시작하자" / "자비스, 사이드 깃 상태 보여줘" 식으로 사용.
