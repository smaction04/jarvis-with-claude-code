# Jarvis with Claude Code

> 한국어 음성으로 동작하는 자비스 풍 데스크탑 비서.
> 클로드 코드 하나로 만들고 운영합니다.

🎬 영상: [AI팀장 일지 EP.01 — 자비스 만들기](https://www.youtube.com/@ai_team_lead)
📖 풀가이드: [노션 페이지](#) <!-- 영상 공개 시 갱신 -->

---

## 무엇이 되나요

- "자비스, 일 시작하자" → VSCode 자동 실행 → Claude CLI 자동 시작
- "자비스, 깃 상태 보여줘" → 활성 터미널에 `git status` 입력
- 어떤 한국어 명령이든 활성 VSCode/터미널로 자동 전송
- 부팅 시 자동 가동 (로컬 부트스트랩 패턴 — 부팅 지연 없음)
- 신규 PC 셋업 1분 (`install.bat` 더블클릭)

플랫폼: **Windows 10/11** (user32 API + Startup 폴더 의존).

---

## 빠른 시작 (5분)

### 1. 저장소 받기

```bash
git clone https://github.com/ai-team-lead/jarvis-with-claude-code.git
cd jarvis-with-claude-code
```

또는 [ZIP 다운로드](https://github.com/ai-team-lead/jarvis-with-claude-code/archive/refs/heads/main.zip) 후 압축 해제.

### 2. Python 3.10+ 의존성 설치

```bash
pip install -r requirements.txt
```

PyAudio 설치 실패 시:

```bash
pip install pipwin
pipwin install pyaudio
```

### 3. 마이크 권한 허용

윈도우 설정 → 개인정보 보호 → **마이크** → "데스크톱 앱이 마이크에 액세스" ✅

### 4. 작업 폴더 지정 (선택)

자비스가 VSCode를 띄울 때 어느 폴더를 워크스페이스로 열지 환경변수로 지정:

```powershell
[System.Environment]::SetEnvironmentVariable('JARVIS_WORK_DIR', 'C:\path\to\your\project', 'User')
```

지정 안 하면 `~/Documents`가 기본값.

### 5. 수동 실행 (테스트)

```bash
python main.py
```

"자비스, 안녕"이라고 말해보세요. HUD가 우상단에 뜨면 정상.

### 6. 자동시작 등록

`install.bat` 더블클릭 → 다음 부팅부터 ~45초 후 자동 가동.

해제는 `uninstall.bat`.

---

## 차별점 — 부팅 지연 안 일으키는 자동시작

대부분의 자동시작 스크립트는 클라우드 드라이브(Google Drive, OneDrive 등)에 두고 시작 폴더가 그걸 직접 가리키게 합니다. 그러면 **로그인 시 드라이브 마운트 대기로 부팅이 느려집니다**.

이 리포는 **로컬 부트스트랩 패턴**을 씁니다:

```
Startup\Jarvis_Voice.lnk  (시작 폴더)
     ↓
%LOCALAPPDATA%\voice_assistant\bootstrap.vbs  ← 로컬!
     ↓ 45초 지연
     ↓ 메인 스크립트 마운트 폴링 (5초 간격, 최대 5분)
     ↓ pythonw 동적 탐색
     ↓ 백그라운드 실행
```

부팅에 영향 0. `install.bat`이 이 패턴을 자동 셋업.

---

## 폴더별 역할

| 파일 | 역할 |
|------|------|
| `main.py` | 마이크 듣기 + 웨이크워드 + HUD + 활성창 식별 + 키 입력 |
| `overlay.html` | 자비스 풍 HUD UI (pywebview로 띄움) |
| `bootstrap.vbs` | 로컬 부트스트랩 템플릿 (install.bat이 토큰 치환) |
| `install.bat` | Startup 등록 (1분 셋업) |
| `uninstall.bat` | Startup 해제 + 로컬 폴더 정리 |
| `prompts/` | 클로드한테 시킨 프롬프트 7개 원문 (시리즈로 따라하기 가능) |
| `docs/` | 트러블슈팅·아키텍처·커스터마이즈 |

---

## 트러블슈팅

자주 묻는 10개는 [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) 참고.

대표 3개:

- **"자비스"라고 말해도 반응 X** → 마이크 권한 + `app_<호스트>.log`에서 임계값 확인
- **PyAudio 설치 실패** → `pipwin install pyaudio` 사용
- **VSCode가 안 뜸** → `VSCODE_PATHS`에 경로 추가 또는 `code` PATH 등록

---

## 다른 IDE/CLI로 바꾸기

자비스는 VSCode + `claude` CLI를 가정하지만 Cursor, JetBrains, ChatGPT CLI 등으로 자유롭게 교체 가능.
[docs/CUSTOMIZATION.md](docs/CUSTOMIZATION.md) 참고.

---

## 라이선스

MIT. 자유롭게 쓰시고, 시리즈 만드시면 채널 멘션 한 번 부탁드려요.

---

## 채널

[AI팀장 일지](https://www.youtube.com/@ai_team_lead) — 혼자 9팀을 굴리는 1인 디렉터의 AI 자동화 로그.
