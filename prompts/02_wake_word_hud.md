# 프롬프트 #2 — 웨이크워드 + 자비스 풍 HUD 오버레이

## 클로드한테 던진 원문

> "자비스" 같은 웨이크워드 들었을 때만 우상단에 떠오르는 자비스 풍 HUD 만들어줘. 인식 중·실행 완료·오류 상태별로 색이 바뀌고, 1.2초 뒤 자동으로 사라져야 해. 윈도우 데스크탑 위에 항상 떠있는 형태.

## 받은 결과 요약

- 라이브러리: `pywebview` (HTML/CSS/JS로 데스크탑 윈도우 그리기)
- HUD UI: `overlay.html` — 회전 링 3개 + 중앙 마이크 + 상태 라벨, CSS 애니메이션
- 상태별 색: 시안(`#00D4FF` 듣는중) / 그린(`#00FF99` 성공) / 레드(`#FF3344` 오류)
- 윈도우 옵션: `frameless=True`, `on_top=True`, `transparent=False`, `resizable=False`
- 자동 페이드: `threading.Timer(1.2, lambda: ui("idle"))`

## 실측 트러블 + 해결

| 증상 | 원인 | 해결 프롬프트 |
|------|------|--------------|
| HUD 클릭 시 다른 창 포커스 뺏김 | 디폴트 윈도우는 클릭 시 활성화 | "HUD가 클릭돼도 포커스 안 가져가게 user32로 WS_EX_NOACTIVATE 적용해줘" |
| 작업표시줄에 자비스 아이콘 뜸 | 일반 윈도우는 taskbar에 등록됨 | (위와 같은 프롬프트에서) WS_EX_TOOLWINDOW 같이 적용 |
| 가끔 다른 항상위 윈도우에 가려짐 | TOPMOST가 한 번만 적용되고 풀림 | "SetWindowPos로 TOPMOST 강제 유지" |
| 한국어 텍스트가 JS evaluate_js에서 깨짐 | 따옴표·역슬래시 이스케이프 미처리 | "evaluate_js에 한국어 텍스트 넘기기 전에 \\ ' 개행 이스케이프 함수 만들어줘" |

→ 최종 코드: `apply_no_activate_style()`이 윈도우 핸들 찾아 `GWL_EXSTYLE`에 `WS_EX_NOACTIVATE | WS_EX_TOOLWINDOW` 추가, `SetWindowPos(HWND_TOPMOST)` 강제.

## 다음 단계로 이어갈 때 주의

- pywebview는 GTK/Qt/Edge 백엔드 자동 선택 — 윈도우는 Edge WebView2 기본. 일부 PC에서 **WebView2 런타임 미설치** 시 첫 실행 실패. README에 안내 필요.
- 다음 프롬프트(#3 hide/show)에서 `window.hide()` 호출 시 **현재 idle 상태 추적용 전역 플래그(`_ui_mode`)** 미리 도입.
