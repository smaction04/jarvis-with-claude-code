# 프롬프트 #3 — HUD idle 시 완전 숨김 → 호출 시 등장

## 클로드한테 던진 원문

> 평소엔 HUD 안 보이게, 자비스 호출했을 때만 등장하게 해줘. 듀얼 모니터 위에 작은 아크 리액터 점 같은 게 떠 있으면 거슬려서 싫어.

## 받은 결과 요약

- 변경: idle 상태에서 `window.hide()` (HTML 토글이 아니라 OS 레벨 윈도우 숨김)
- 호출 시: `window.show()` → `resize(LARGE_W, LARGE_H)` → `move(우상단)`
- 결과 표시 후 1.2초: `Timer(1.2, lambda: ui("idle"))` → 다시 hide
- HTML 측: idle 클래스에서 stage 자체 숨김 (이중 안전장치)

## 실측 트러블 + 해결

| 증상 | 원인 | 해결 프롬프트 |
|------|------|--------------|
| `window.hide()` 호출이 가끔 무시됨 | pywebview 일부 버전에서 hide 직후 show 호출하면 race | "ui() 호출 시 기존 hide_timer 먼저 cancel하고 진행하게 해줘" |
| 호출 후 HUD 위치가 가끔 좌상단 (0,0)에 뜸 | `_ui_mode` 비교 실패 시 resize/move 스킵 | "_ui_mode 새로 추가해서 idle ↔ active 전이 시에만 resize/move 하게" |
| 듀얼 모니터에서 우측 모니터에 안 뜸 | DPI 미반영, GetSystemMetrics는 주 모니터만 | "GetDeviceCaps로 DPI scale 구하고 logical 좌표로 RIGHT_EDGE_X 계산" |

→ 최종 코드: 시작 시 DPI scale 계산, `RIGHT_EDGE_X = sw_logical - 120`. ui() 진입에서 항상 `_hide_timer.cancel()` 먼저.

## 다음 단계로 이어갈 때 주의

- hide/show는 **WebView2 백엔드에서만 검증**. GTK/Qt 백엔드(리눅스/맥)는 동작 다를 수 있음 — 이 리포는 Windows 전제.
- 다음 프롬프트(#4 활성창)에서 자비스 본인 윈도우(`KimAssistant`)를 활성창 후보에서 제외하는 로직 필수.
