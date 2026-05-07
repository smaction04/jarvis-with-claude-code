# 프롬프트 #1 — 마이크 상시 듣기 + 한국어 인식

## 클로드한테 던진 원문

> 윈도우에서 마이크를 상시 듣고 한국어로 인식해서 콘솔에 찍는 파이썬 스크립트 만들어줘. 음성인식은 무료로 쓸 수 있는 걸로. 백그라운드에서 돌아가야 하고, 한 번 발화 끝나면 다음 발화로 자동 넘어가게.

## 받은 결과 요약

- 라이브러리: `SpeechRecognition` (PyPI) + Google Web Speech API (무료, 별도 키 X)
- 핵심 함수: `recognizer.listen(source)` → `recognizer.recognize_google(audio, language="ko-KR")`
- 무한 루프 안에서 `with sr.Microphone() as source:` 컨텍스트 유지
- `WaitTimeoutError` / `UnknownValueError` 분리 처리

## 실측 트러블 + 해결

| 증상 | 원인 | 해결 프롬프트 |
|------|------|--------------|
| `OSError: PyAudio not installed` | PyAudio는 wheel 이슈로 pip install 실패 잦음 | "PyAudio 설치 실패하는데 pipwin으로 우회하는 방법 알려줘" |
| 조용한 환경에서 인식 잘 됨, 키보드 소리에 묻힘 | `energy_threshold` 동적 조정이 너무 민감 | "음성 인식 임계값을 환경 보정 후 60%로 낮춰서 작은 목소리도 잡게 해줘" |
| 한 발화 인식 중 다음 발화 놓침 | 메인 루프에서 `recognize` 동기 호출 | "인식·실행을 백그라운드 스레드로 빼서 메인 루프는 즉시 다음 listen으로 가게 해줘" |

→ 최종 코드: `r.adjust_for_ambient_noise(source, duration=1)` 후 `r.energy_threshold = max(20, int(r.energy_threshold * 0.6))`, 인식은 `threading.Thread(target=process_audio, ...)`로 분리.

## 다음 단계로 이어갈 때 주의

- 다음 프롬프트(#2 HUD)에서 마이크 루프와 UI 스레드 충돌 발생 가능. **pywebview는 메인 스레드에서 webview.start() 해야** 하고, 마이크 루프는 백그라운드 스레드로.
- Google Web Speech는 무료지만 비공식. 안정 운영용 상용 서비스로 갈 거면 Whisper API나 Google Cloud Speech-to-Text 컨텍스트로 첨부 필요.
