# 프롬프트 #5 — VSCode 미실행 시 풀 부트스트랩 + Claude CLI 자동 시작

## 클로드한테 던진 원문

> VSCode가 꺼져있을 때 "자비스, 일 시작하자" 하면 VSCode 실행하고 터미널 열고 claude CLI까지 자동으로 띄우게 해줘. 워크스페이스는 내 작업 폴더로.

## 받은 결과 요약

- VSCode 경로 후보: `%LOCALAPPDATA%\Programs\Microsoft VS Code\Code.exe` → `Program Files` → `Program Files (x86)` → PATH 폴백
- 실행 인자: `--disable-workspace-trust` (신규 폴더 첫 오픈 시 신뢰 모달 차단 — 자동입력 막힘 방지)
- 워크스페이스: `os.environ.get("JARVIS_WORK_DIR", str(Path.home() / "Documents"))`
- 부트스트랩 시퀀스 (`was_launched=True` 분기):
  1. `time.sleep(4.0)` — VSCode 초기화·워크스페이스 로드 대기
  2. `find_target_window()` 재시도 + `activate_window()` 한 번 더
  3. `Ctrl+Shift+`` (백틱) — **새 터미널 생성** 단축키
  4. `time.sleep(2.5)` — 셸 프롬프트 정착 대기
  5. `send_text("claude")` — Claude CLI 시작
  6. `time.sleep(12.0)` — CLI 인증·모델 로드 대기

## 실측 트러블 + 해결

| 증상 | 원인 | 해결 프롬프트 |
|------|------|--------------|
| `Ctrl+`` (백틱) 토글이 기존 터미널을 닫아버림 | 토글 단축키는 양방향 | "Ctrl+Shift+` (Create New Terminal) 쓰자 — 항상 새 터미널 생성" |
| VSCode 환영 탭이 포커스 가져가서 명령이 환영 탭에 입력됨 | 워크스페이스 트러스트 안내 등이 잠깐 활성 | "find_target_window 재호출 + activate_window 한 번 더" |
| 클라우드 드라이브 워크스페이스 첫 로드 4초로 부족 | G드라이브·OneDrive는 첫 파일 인덱싱 느림 | "sleep을 4초로 늘리고 주석에 '클라우드 드라이브 첫 로드 대비' 명시" |
| `claude` 입력 후 즉시 다음 명령 보내면 인증 모달이 가로챔 | CLI 첫 실행 시 OAuth 흐름 | "12초 대기 추가, README에 첫 실행은 수동 인증 필요 명시" |

→ 최종 코드: `execute()` 안의 `if was_launched:` 블록.

## 다음 단계로 이어갈 때 주의

- 다음 프롬프트(#6 자동시작)에서 부팅 직후 자비스가 **클라우드 드라이브 마운트되기 전** 시작하면 main.py를 못 찾음 → 마운트 폴링 필요.
- 사용자별 IDE/CLI 변경 시 `VSCODE_PATHS`와 `send_text("claude")` 두 군데만 고치면 됨 → CUSTOMIZATION.md에 명시.
