import streamlit.web.cli as stcli
import os, sys
import threading
import time
import webbrowser
import subprocess

def resolve_path(path):
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(__file__)
    return os.path.join(base_path, path)

def run_streamlit():
    app_path = resolve_path("phage_atb_app_v9.py")
    sys.argv = [
        "streamlit",
        "run",
        app_path,
        "--server.port=8501",
        "--server.address=127.0.0.1",
        "--global.developmentMode=false",
        "--server.headless=true",
    ]
    stcli.main()

def launch_app():
    # Ждем запуска сервера
    time.sleep(3)
    url = "http://127.0.0.1:8501"
    
    # Пытаемся запустить Chrome в режиме приложения (без адресной строки)
    try:
        # Типичные пути к Chrome на Windows
        chrome_paths = [
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
            os.path.expanduser(r"~\AppData\Local\Google\Chrome\Application\chrome.exe")
        ]
        
        launched = False
        for path in chrome_paths:
            if os.path.exists(path):
                subprocess.Popen([path, f"--app={url}"])
                launched = True
                break
        
        if not launched:
            webbrowser.open(url)
    except Exception:
        webbrowser.open(url)

if __name__ == "__main__":
    # Запускаем streamlit в отдельном потоке
    threading.Thread(target=run_streamlit, daemon=True).start()
    
    # Запускаем "окно" приложения
    launch_app()
    
    # Держим основной поток живым
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        sys.exit(0)
