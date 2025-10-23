# bot_manager.py
import subprocess
import threading
import time
import sys
import os
from pathlib import Path
from dotenv import load_dotenv
from colorama import init, Fore, Style

init(autoreset=True)  # colorama 初期化

# ===========================
# 設定
# ===========================
BOT_FILE = "bot.py"
LOG_FILE = "bot_output.log"
MAX_LOG_LINES = 500
RESTART_DELAY = 2  # 自動再起動待機秒数

# bot_manager.py と同じフォルダを基準にする
BASE_DIR = Path(__file__).parent
BOT_PATH = BASE_DIR / BOT_FILE

# .env からトークンを読み込む
load_dotenv(BASE_DIR / ".env")
TOKEN = os.getenv("DISCORD_BOT_TOKEN")
if not TOKEN:
    print(Fore.RED + "❌ Botトークンが設定されていません。 .env に DISCORD_BOT_TOKEN を設定してください。")
    sys.exit(1)

bot_process = None
stop_flag = False
log_lines = []

# ===========================
# 標準出力のリアルタイム取得
# ===========================
def enqueue_output(pipe):
    global log_lines
    for line in iter(pipe.readline, ''):
        if line:
            line = line.rstrip()
            log_lines.append(line)
            if len(log_lines) > MAX_LOG_LINES:
                log_lines = log_lines[-MAX_LOG_LINES:]
    pipe.close()

# ===========================
# Bot制御
# ===========================
def start_bot():
    global bot_process
    if bot_process and bot_process.poll() is None:
        print(Fore.YELLOW + "⚠ Botはすでに起動しています。")
        return
    if not BOT_PATH.exists():
        print(Fore.RED + f"❌ Botファイルが見つかりません: {BOT_PATH}")
        return
    
    print(Fore.GREEN + "🚀 Botを起動中...")
    
    bot_process = subprocess.Popen(
        [sys.executable, str(BOT_PATH)],
        cwd=str(BASE_DIR),                # ← 作業フォルダを明示
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace"
    )
    
    threading.Thread(target=enqueue_output, args=(bot_process.stdout,), daemon=True).start()
    time.sleep(1)

def stop_bot():
    global bot_process
    if bot_process and bot_process.poll() is None:
        print(Fore.RED + "⏹ Botを停止中...")
        bot_process.terminate()
        try:
            bot_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            bot_process.kill()
        bot_process = None
    else:
        print(Fore.YELLOW + "⚠ Botは起動していません。")

def restart_bot():
    stop_bot()
    time.sleep(RESTART_DELAY)
    start_bot()

def send_command(cmd):
    if bot_process and bot_process.poll() is None:
        bot_process.stdin.write(cmd + "\n")
        bot_process.stdin.flush()
    else:
        print(Fore.RED + "⚠ Botが起動していません。")

# ===========================
# メニュー・ログ表示
# ===========================
def show_menu():
    os.system("cls")  # 画面クリア
    status = Fore.GREEN + "🟢 Running" if bot_process and bot_process.poll() is None else Fore.RED + "🔴 Stopped"
    print("="*40)
    print("       Bot Control Menu")
    print("="*40)
    print(f"Bot Status: {status}")
    print("Type a command below.")
    print("-"*40)
    print("start       - Start the Bot")
    print("stop        - Stop the Bot")
    print("restart     - Restart the Bot")
    print("help        - Show this menu")
    print("exit        - Close this menu")
    print("aga         - She is smell!!!")
    print("-"*40)
    print(f"----- Bot Log (最新{MAX_LOG_LINES}行) -----")
    for line in log_lines[-MAX_LOG_LINES:]:
        print(line)
    print("------------------------------")

# ===========================
# メインループ
# ===========================
def main():
    global stop_flag
    start_bot()
    while not stop_flag:
        show_menu()
        cmd = input("Command: ").strip().lower()
        if cmd == "start":
            start_bot()
        elif cmd == "stop":
            stop_bot()
        elif cmd == "restart":
            restart_bot()
        elif cmd in ["talk", "hello", "korosuzo"]:
            if bot_process and bot_process.poll() is None:
                send_command(cmd)
            else:
                print(Fore.RED + "⚠ Botが起動していません。")
                time.sleep(1)
        elif cmd == "help":
            continue
        elif cmd == "exit":
            stop_bot()
            stop_flag = True
        else:
            print(Fore.RED + "❌ 不明なコマンドです。")
            time.sleep(1)

if __name__ == "__main__":
    main()
