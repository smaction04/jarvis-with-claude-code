# 프롬프트 #4 — 활성창 자동 식별 + 키 입력 라우팅

## 클로드한테 던진 원문

> 인식한 명령을 지금 켜져있는 VSCode나 터미널로 자동 입력하고 싶어. 근데 브라우저에 claude.ai 탭이 떠 있으면 거기로 들어가면 안 돼. 우선순위 정해서 골라줘.

## 받은 결과 요약

- 라이브러리: `ctypes.windll.user32` — `EnumWindows`, `GetWindowTextW`, `GetWindowThreadProcessId`
- 우선순위 리스트: `TARGET_TITLES = ["visual studio code", "windows terminal", "powershell", "터미널", "command prompt", "cmd.exe"]`
- 제외 리스트: `EXCLUDE_PROC = ["chrome.exe", "msedge.exe", "firefox.exe", ...]` (브라우저 탭 제목으로 잘못 매칭되는 거 차단)
- 자비스 본인 윈도우 제외: 제목에 `kimassistant` 포함된 hwnd skip
- 활성화: `IsIconic` 검사 후 최소화 상태일 때만 `SW_RESTORE` (최대화 풀리는 문제 회피)

## 실측 트러블 + 해결

| 증상 | 원인 | 해결 프롬프트 |
|------|------|--------------|
| 크롬에 "Visual Studio Code" 탭 떠 있으면 거기 입력됨 | 윈도우 제목 매칭만 함 | "프로세스명도 같이 검사해서 chrome.exe면 무조건 제외" |
| 최대화된 VSCode 활성화 시 일반 크기로 풀림 | `ShowWindow(SW_RESTORE)` 무조건 호출 | "IsIconic으로 최소화 여부 확인 후 최소화 상태에서만 RESTORE" |
| `GetWindowText`가 한글 제목 깨뜨림 | ANSI 버전 호출 | "유니코드 버전(GetWindowTextW)으로 교체" |
| `OpenProcess` 실패로 빈 문자열 리턴 | 권한 부족 | "PROCESS_QUERY_LIMITED_INFORMATION 플래그로 다운그레이드" |

→ 최종 코드: `find_target_window()` + `_get_process_name()` 콤보, `activate_window()`에 `IsIconic` 가드.

## 다음 단계로 이어갈 때 주의

- 다음 프롬프트(#5 VSCode 부트스트랩)에서는 **타깃 창이 아예 없을 때** 자비스가 직접 띄우는 분기 필요.
- 키 입력은 `pyautogui` + `pyperclip` 클립보드 우회. `pyautogui.write()` 직접 입력은 한글 못 침 → 클립보드 + `Ctrl+V` 패턴.
