"""
자비스 음성 비서 — 자비스 풍 HUD 오버레이
- 마이크 상시 듣기 + '자비스' 호출
- 활성화 시 우측 상단에 푸른 네온 HUD 등장
- 인식 → 실행 → 자동 페이드 아웃

경로 정책:
- 코드·리소스(overlay.html): 스크립트 위치 기준 상대경로
- 작업 폴더: 환경변수 JARVIS_WORK_DIR (기본값: ~/Documents)
- 로그: %LOCALAPPDATA%\\voice_assistant\\logs\\ (PC별 로컬, 클라우드 동기화 충돌 방지)
"""
import os
import sys
import time
import ctypes
import socket
import subprocess
import threading
from pathlib import Path

import webview
import pyautogui
import pyperclip
import speech_recognition as sr

SCRIPT_DIR = Path(__file__).resolve().parent
HUD_HTML_PATH = SCRIPT_DIR / "overlay.html"
HUD_HTML_URL = HUD_HTML_PATH.as_uri()

LOG_DIR = Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / "voice_assistant" / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_PATH = LOG_DIR / f"app_{socket.gethostname()}.log"

_log = open(LOG_PATH, "a", encoding="utf-8", buffering=1)
sys.stdout = _log
sys.stderr = _log
print(f"\n=== 시작 {time.strftime('%Y-%m-%d %H:%M:%S')} | host={socket.gethostname()} | dir={SCRIPT_DIR} ===", flush=True)

WAKE_WORDS = ["자비스", "자 비스", "자비 스", "재비스", "차비스", "사비스", "Jarvis", "jarvis", "자배스", "자뱀스", "자버스"]

pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.02

window = None
_hide_timer = None
_style_applied = False
_ui_mode = None  # "idle" or "active"
_exec_lock = threading.Lock()
_active_until = 0  # 자비스 단독 호출 후 명령 대기 만료 시각
_active_expire_timer = None

# 클로드 코드 창 식별 우선순위 (제목 포함 문자열, 소문자)
TARGET_TITLES = ["visual studio code", "windows terminal", "powershell", "터미널", "command prompt", "cmd.exe"]
# 잡히면 안 되는 창 (브라우저 — claude.ai 탭 등이 있어도 무시)
EXCLUDE_PROC = ["chrome.exe", "msedge.exe", "firefox.exe", "brave.exe", "whale.exe", "opera.exe"]


def _get_process_name(hwnd):
    user32 = ctypes.windll.user32
    kernel32 = ctypes.windll.kernel32
    pid = ctypes.c_ulong()
    user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
    PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
    h = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid.value)
    if not h:
        return ""
    try:
        buf = ctypes.create_unicode_buffer(260)
        size = ctypes.c_ulong(260)
        if kernel32.QueryFullProcessImageNameW(h, 0, buf, ctypes.byref(size)):
            return buf.value.split("\\")[-1].lower()
    finally:
        kernel32.CloseHandle(h)
    return ""


def find_target_window():
    """클로드 코드 창 자동 식별 (브라우저 제외 + 우선순위)"""
    user32 = ctypes.windll.user32
    target = {"hwnd": None, "rank": 999}

    WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)

    def cb(hwnd, lparam):
        if not user32.IsWindowVisible(hwnd):
            return True
        length = user32.GetWindowTextLengthW(hwnd)
        if length == 0:
            return True
        buf = ctypes.create_unicode_buffer(length + 2)
        user32.GetWindowTextW(hwnd, buf, length + 2)
        title = buf.value.lower()
        if "kimassistant" in title:
            return True
        proc = _get_process_name(hwnd)
        if proc in EXCLUDE_PROC:
            return True
        for i, key in enumerate(TARGET_TITLES):
            if key in title:
                if i < target["rank"]:
                    target["rank"] = i
                    target["hwnd"] = hwnd
                break
        return True

    user32.EnumWindows(WNDENUMPROC(cb), 0)
    return target["hwnd"]


def activate_window(hwnd):
    if not hwnd:
        return False
    user32 = ctypes.windll.user32
    # 최소화 상태일 때만 복원. 최대화·일반 상태에서는 ShowWindow 호출 X
    # (SW_RESTORE가 최대화 상태에 호출되면 일반 크기로 풀려서 창이 작아짐)
    if user32.IsIconic(hwnd):
        SW_RESTORE = 9
        user32.ShowWindow(hwnd, SW_RESTORE)
    user32.BringWindowToTop(hwnd)
    user32.SetForegroundWindow(hwnd)
    return True


VSCODE_PATHS = [
    os.path.expandvars(r"%LOCALAPPDATA%\Programs\Microsoft VS Code\Code.exe"),
    r"C:\Program Files\Microsoft VS Code\Code.exe",
    r"C:\Program Files (x86)\Microsoft VS Code\Code.exe",
]

# 자비스가 VSCode를 신규 실행할 때 강제로 여는 작업 폴더
# 환경변수 JARVIS_WORK_DIR로 덮어쓸 수 있음. 기본값은 사용자 문서 폴더.
WORK_DIR = os.environ.get(
    "JARVIS_WORK_DIR",
    str(Path.home() / "Documents")
)


def launch_vscode():
    """VSCode 실행 + 작업 폴더 강제 오픈 + 신뢰 다이얼로그 우회"""
    # --disable-workspace-trust: 새 폴더 첫 오픈 시 뜨는 신뢰 모달 차단 (자동입력 막힘 방지)
    args_extra = ["--disable-workspace-trust"]
    for p in VSCODE_PATHS:
        if os.path.exists(p):
            subprocess.Popen([p, *args_extra, WORK_DIR])
            print(f"[실행] VSCode 시작: {p} (워크스페이스={WORK_DIR})", flush=True)
            return True
    try:
        subprocess.Popen(["code", *args_extra, WORK_DIR], shell=True)
        print(f"[실행] VSCode (PATH) 시작 (워크스페이스={WORK_DIR})", flush=True)
        return True
    except Exception as e:
        print(f"[실행 에러] VSCode 시작 실패: {e}", flush=True)
        return False


def find_or_launch_target(timeout_seconds=20):
    """타깃 창 찾고, 없으면 VSCode 실행 후 윈도우 뜰 때까지 대기.
    리턴: (hwnd, was_launched) — was_launched True면 새로 실행한 것"""
    target = find_target_window()
    if target:
        return target, False
    if not launch_vscode():
        return None, False
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        time.sleep(0.5)
        target = find_target_window()
        if target:
            time.sleep(2.5)  # VSCode 초기화·워크스페이스 로드·터미널 복원 여유
            return target, True
    return None, False


def send_text(text: str):
    """클립보드 통한 텍스트 입력 + Enter (창 활성화 끝난 상태에서 호출)"""
    pyperclip.copy(text)
    time.sleep(0.05)
    pyautogui.keyDown("ctrl")
    pyautogui.press("v")
    pyautogui.keyUp("ctrl")
    time.sleep(0.15)
    pyautogui.press("enter")

SMALL_W, SMALL_H = 140, 140
LARGE_W, LARGE_H = 340, 340
RIGHT_EDGE_X = 0
TOP_Y_POS = 0


def apply_no_activate_style():
    """비서 윈도우: 포커스 비활성 + 작업표시줄 안 뜸 + 강제 TOPMOST"""
    global _style_applied
    user32 = ctypes.windll.user32
    GWL_EXSTYLE = -20
    WS_EX_NOACTIVATE = 0x08000000
    WS_EX_TOOLWINDOW = 0x00000080
    HWND_TOPMOST = -1
    SWP_NOMOVE = 0x0002
    SWP_NOSIZE = 0x0001
    SWP_NOACTIVATE = 0x0010
    for _ in range(20):
        hwnd = user32.FindWindowW(None, "KimAssistant")
        if hwnd:
            style = user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
            user32.SetWindowLongW(hwnd, GWL_EXSTYLE, style | WS_EX_NOACTIVATE | WS_EX_TOOLWINDOW)
            user32.SetWindowPos(hwnd, HWND_TOPMOST, 0, 0, 0, 0, SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE)
            _style_applied = True
            print("[UI] 포커스 비활성 + TOPMOST 적용", flush=True)
            return
        time.sleep(0.3)
    print("[UI] 윈도우 핸들 못 찾음", flush=True)


def ui(state, text=""):
    """비활성(idle) = 윈도우 완전 숨김 / 활성 = 큰 파란 HUD 등장"""
    global window, _hide_timer, _ui_mode
    if window is None:
        return
    if _hide_timer:
        _hide_timer.cancel()
        _hide_timer = None
    is_idle = (state == "idle")
    new_mode = "idle" if is_idle else "active"
    safe = (text or "").replace("\\", "\\\\").replace("'", "\\'").replace("\n", " ")
    try:
        if is_idle:
            try:
                window.evaluate_js(f"setState('idle','')")
            except Exception:
                pass
            try:
                window.hide()
            except Exception as he:
                print(f"[UI hide 에러] {he}", flush=True)
            _ui_mode = new_mode
            return
        # 활성 상태: 큰 HUD 표시
        if new_mode != _ui_mode:
            try:
                window.resize(LARGE_W, LARGE_H)
                window.move(RIGHT_EDGE_X - LARGE_W, TOP_Y_POS)
            except Exception as re:
                print(f"[UI resize 에러] {re}", flush=True)
            _ui_mode = new_mode
        try:
            window.show()
        except Exception as se:
            print(f"[UI show 에러] {se}", flush=True)
        window.evaluate_js(f"setState('{state}','{safe}')")
        if state in ("result", "error"):
            _hide_timer = threading.Timer(1.2, lambda: ui("idle"))
            _hide_timer.start()
    except Exception as e:
        print(f"[UI 에러] {e}", flush=True)


def strip_wake(text: str) -> str:
    for w in WAKE_WORDS:
        if w in text:
            return text.split(w, 1)[1].strip()
    return text.strip()


def execute(text: str):
    if not text:
        return
    print(f"[실행] {text}", flush=True)
    ui("processing")
    target, was_launched = find_or_launch_target()
    if target:
        activate_window(target)
        time.sleep(0.4)
        if was_launched:
            # VSCode를 자비스가 새로 띄운 케이스 → 환영 탭/워크스페이스 로드 안정화 후 터미널 강제 생성
            # 클라우드 드라이브에 워크스페이스가 있는 경우 첫 로드가 느림 — 충분히 기다려야 keystroke가 묻히지 않음
            time.sleep(4.0)
            # 한 번 더 활성화 (워크스페이스 트러스트 안내·환영 탭 등이 잠깐 포커스를 가져갈 수 있음)
            t2 = find_target_window()
            if t2:
                activate_window(t2)
                time.sleep(0.4)
            # Ctrl+Shift+` = "Create New Terminal" — Ctrl+`(토글)과 달리 항상 새 터미널이 생성·포커스됨
            # (기존 터미널이 복원돼 있던 경우 토글이 닫아버리는 문제 회피)
            pyautogui.hotkey("ctrl", "shift", "`")
            time.sleep(2.5)  # 새 터미널 생성 + 셸 프롬프트 정착
            print(f"[부팅] claude CLI 자동 시작 (cwd={WORK_DIR})", flush=True)
            send_text("claude")
            time.sleep(12.0)  # 클로드 CLI 인증·모델 로드 대기 (느린 회선 여유)
        else:
            # 이미 떠 있던 VSCode → 사용자 매핑 F13(terminal.focus) 가정
            pyautogui.press("f13")
            time.sleep(0.5)
    send_text(text)
    ui("result", text)


def safe_listen(r, source, timeout=None, phrase_time_limit=15):
    try:
        return r.listen(source, timeout=timeout, phrase_time_limit=phrase_time_limit)
    except sr.WaitTimeoutError:
        return None


def activate_listening():
    global _active_until, _active_expire_timer
    _active_until = time.time() + 15
    if _active_expire_timer:
        _active_expire_timer.cancel()
    _active_expire_timer = threading.Timer(15.5, lambda: ui("idle"))
    _active_expire_timer.start()
    ui("listening")


def process_audio(r, audio):
    """백그라운드 인식 + 실행. 메인 listen 루프와 분리"""
    global _active_until
    text = recognize(r, audio)
    if not text:
        return
    has_wake = any(w in text for w in WAKE_WORDS)
    is_active = time.time() < _active_until

    if has_wake:
        command = strip_wake(text)
        if command:
            print(f"[들음] {text}", flush=True)
            _active_until = 0
            with _exec_lock:
                execute(command)
        else:
            print(f"[들음] {text} (활성화)", flush=True)
            activate_listening()
    elif is_active:
        print(f"[들음 명령] {text}", flush=True)
        _active_until = 0
        with _exec_lock:
            execute(text)


def recognize(r, audio):
    try:
        return r.recognize_google(audio, language="ko-KR")
    except sr.UnknownValueError:
        return ""
    except sr.RequestError as e:
        print(f"[API 에러] {e}", flush=True)
        return None


def voice_loop():
    time.sleep(0.3)
    r = sr.Recognizer()
    r.energy_threshold = 20
    r.dynamic_energy_threshold = False
    r.pause_threshold = 1.0
    r.non_speaking_duration = 0.3

    print("[자비스] 시작", flush=True)
    with sr.Microphone() as source:
        print("[보정] 주변 소음 측정 중 (1초)...", flush=True)
        r.adjust_for_ambient_noise(source, duration=1)
        r.energy_threshold = max(20, int(r.energy_threshold * 0.6))
        print(f"[보정] 임계값 = {int(r.energy_threshold)}", flush=True)
        print("[대기]", flush=True)
        ui("idle")

        while True:
            audio = safe_listen(r, source)
            if audio is None:
                continue
            # 인식·실행은 백그라운드 — 메인은 즉시 다음 발화 listen
            threading.Thread(target=process_audio, args=(r, audio), daemon=True).start()


def on_loaded():
    print("[디버그] HTML 로드 완료 — 음성 루프 시작", flush=True)
    threading.Thread(target=apply_no_activate_style, daemon=True).start()
    time.sleep(0.3)
    ui("idle")
    threading.Thread(target=voice_loop, daemon=True).start()


def start_voice():
    pass  # 실제 시작은 on_loaded에서


if __name__ == "__main__":
    user32 = ctypes.windll.user32
    hdc = user32.GetDC(0)
    dpi = ctypes.windll.gdi32.GetDeviceCaps(hdc, 88)
    user32.ReleaseDC(0, hdc)
    scale = dpi / 96.0
    sw_phys = user32.GetSystemMetrics(0)
    sh_phys = user32.GetSystemMetrics(1)
    sw_logical = int(sw_phys / scale)
    sh_logical = int(sh_phys / scale)
    RIGHT_EDGE_X = sw_logical - 120
    TOP_Y_POS = 60
    globals()["RIGHT_EDGE_X"] = RIGHT_EDGE_X
    globals()["TOP_Y_POS"] = TOP_Y_POS
    # 처음에는 화면 밖에 작게 띄움 → on_loaded → ui("idle") → window.hide() 로 즉시 숨김
    # (자비스 호출 시에만 LARGE 사이즈로 정위치에 등장)
    W, H = LARGE_W, LARGE_H
    x = -9999
    y = -9999
    sw, sh = sw_logical, sh_logical
    print(f"[디버그] DPI scale={scale} physical={sw_phys}x{sh_phys} logical={sw_logical}x{sh_logical}", flush=True)

    with open(HUD_HTML_PATH, encoding="utf-8") as _f:
        html_content = _f.read()
    window = webview.create_window(
        "KimAssistant",
        html=html_content,
        frameless=True,
        transparent=False,
        on_top=True,
        resizable=False,
        width=W,
        height=H,
        x=x,
        y=y,
        background_color="#000010",
    )
    window.events.loaded += on_loaded
    print(f"[디버그] 윈도우 위치 x={x} y={y} 화면크기 {sw}x{sh}", flush=True)
    webview.start(start_voice, debug=False)
