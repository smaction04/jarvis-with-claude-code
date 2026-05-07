' 자비스 음성 비서 — 로컬 부트스트랩 (부팅 가속용)
' 목적: Startup 폴더가 클라우드 드라이브를 직접 가리켜서 발생하는 로그인 지연 제거
' 동작:
'   1) 로그인 직후 45초 대기 → 시스템 디스크/네트워크 경합 회피
'   2) 메인 스크립트가 마운트될 때까지 폴링 (최대 5분, 클라우드 드라이브 대비)
'   3) 동적으로 pythonw 탐색 후 백그라운드 실행 (콘솔 X)
'
' 이 파일은 install.bat이 토큰 치환 후 %LOCALAPPDATA%\voice_assistant\로 복사함.
' 토큰: __MAIN_PY__ → main.py 절대경로 / __WORK_DIR__ → 리포 폴더 절대경로

Set fso = CreateObject("Scripting.FileSystemObject")
Set ws = CreateObject("WScript.Shell")

mainPy = "__MAIN_PY__"
workDir = "__WORK_DIR__"

' 1) 로그인 후 45초 지연 — 부팅 체감 지연 제거
WScript.Sleep 45000

' 2) 메인 스크립트 마운트 대기 (최대 5분, 5초 간격)
'    로컬 디스크면 즉시 통과. 클라우드 드라이브면 마운트될 때까지 폴링.
maxWaitMs = 300000
elapsed = 0
Do While Not fso.FileExists(mainPy) And elapsed < maxWaitMs
  WScript.Sleep 5000
  elapsed = elapsed + 5000
Loop

If Not fso.FileExists(mainPy) Then
  ' 메인 스크립트가 5분 안에 안 뜨면 이번 부팅에는 자비스 비활성 (조용히 종료)
  WScript.Quit 0
End If

' 3) pythonw 탐색
pythonw = ""
candidates = Array( _
  "%LOCALAPPDATA%\Programs\Python\Python313\pythonw.exe", _
  "%LOCALAPPDATA%\Programs\Python\Python312\pythonw.exe", _
  "%LOCALAPPDATA%\Programs\Python\Python311\pythonw.exe", _
  "%LOCALAPPDATA%\Programs\Python\Python310\pythonw.exe", _
  "C:\Program Files\Python313\pythonw.exe", _
  "C:\Program Files\Python312\pythonw.exe", _
  "C:\Program Files\Python311\pythonw.exe", _
  "C:\Program Files\Python310\pythonw.exe", _
  "C:\Program Files (x86)\Python313\pythonw.exe", _
  "C:\Program Files (x86)\Python312\pythonw.exe", _
  "C:\Program Files (x86)\Python311\pythonw.exe", _
  "C:\Program Files (x86)\Python310\pythonw.exe" _
)
For Each c In candidates
  expanded = ws.ExpandEnvironmentStrings(c)
  If fso.FileExists(expanded) Then
    pythonw = expanded
    Exit For
  End If
Next

If pythonw = "" Then
  pythonw = "pythonw.exe"  ' PATH 폴백
End If

ws.CurrentDirectory = workDir
ws.Run """" & pythonw & """ -u """ & mainPy & """", 0, False
