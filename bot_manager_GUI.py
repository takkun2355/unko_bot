# ===========================
# Ultimate Bot Manager GUI 完全版
# ===========================

import subprocess, threading, time, sys, os, random, math
from datetime import datetime
import tkinter as tk
from tkinter import scrolledtext, messagebox, simpledialog
from colorama import init, Fore, Style
from dotenv import load_dotenv

init(autoreset=True)

# ===========================
# 設定
# ===========================
BOT_FILE = "bot.py"
LOG_FILE_DIR = "logs"
MAX_LOG_LINES = 50
RESTART_DELAY = 2
points = 0  # ポイント管理用
start_time = time.time()

# .env 読み込み
load_dotenv()
TOKEN = os.getenv("DISCORD_BOT_TOKEN")
if not TOKEN:
    messagebox.showerror("Error", ".env に DISCORD_BOT_TOKEN が設定されていません")
    sys.exit(1)

os.makedirs(LOG_FILE_DIR, exist_ok=True)

bot_process = None
log_lines = []

# ログレベル・顔文字・装飾
LOG_LEVELS = [
    ("TRACE", ["trace"], "grey"),
    ("DEBUG", ["debug"], "blue"),
    ("VERBOSE", ["verbose"], "lightblue"),
    ("INFO", ["info"], "cyan"),
    ("SUCCESS", ["success","ok"], "green"),
    ("NOTICE", ["notice"], "lightcyan"),
    ("ALERT", ["alert"], "orange"),
    ("WARNING", ["warn","warning"], "yellow"),
    ("ERROR", ["error","fail","exception"], "red"),
    ("CRITICAL", ["critical","panic"], "magenta"),
    ("FATAL", ["fatal"], "white")
]

FACE_REACTIONS = {
    "ERROR": "(╯°□°）╯︵ ┻━┻",
    "SUCCESS": "(ﾉ◕ヮ◕)ﾉ*:･ﾟ✧",
    "WARNING": "⚠️ ( º﹃º )",
    "INFO": "💡",
    "CRITICAL": "💀",
    "FATAL": "☠️",
}

# ===========================
# ユーティリティ
# ===========================
def get_log_level(line):
    line_lower = line.lower()
    for name, keywords, color in LOG_LEVELS:
        if any(k in line_lower for k in keywords):
            return name, color
    return "UNKNOWN", "black"

def get_level(points, base_point=10):
    """ポイントが倍になるごとにレベル1上がる方式"""
    if points < 1:
        return 1
    level = math.floor(math.log2(points / base_point)) + 1
    return max(1, min(level, 999))

def get_title(points):
    """称号 + レベル"""
    level = get_level(points)
    if level >= 900:
        title = "あがりの臭さレベル"
    elif level >= 700:
        title = "宇宙最強"
    elif level >= 500:
        title = "世界最強"
    elif level >= 200:
        title = "マスター"
    elif level >= 50:
        title = "一人前"
    elif level >= 20:
        title = "半人前"
    elif level >= 10:
        title = "見習い"
    else:
        title = "初心者"
    return f"{title}　　　　　　　level.{level}"

# ===========================
# ログ取得
# ===========================
def enqueue_output(pipe):
    global log_lines, points
    log_file = os.path.join(LOG_FILE_DIR, f"{datetime.now().strftime('%Y-%m-%d')}.log")
    with open(log_file, "a", encoding="utf-8", errors="replace") as f:
        for raw_line in iter(pipe.readline, ''):
            if not raw_line:
                break
            # すでに str なので decode は不要
            line = raw_line.rstrip()

            level_name, color = get_log_level(line)
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            formatted = f"[{now} {level_name}] {line}"
            log_lines.append(formatted)
            if len(log_lines) > MAX_LOG_LINES:
                log_lines = log_lines[-MAX_LOG_LINES:]

            f.write(formatted + "\n")
            f.flush()

            # 顔文字反応・ポイント
            if level_name in FACE_REACTIONS:
                if level_name == "SUCCESS":
                    points += 1
                elif level_name in ["ERROR","CRITICAL","FATAL"]:
                    points = max(points - 1, 0)

            update_gui()


# ===========================
# Bot制御
# ===========================
def start_bot():
    global bot_process
    if bot_process and bot_process.poll() is None:
        messagebox.showinfo("Info","Botはすでに起動中です")
        return
    bot_process = subprocess.Popen(
        [sys.executable,BOT_FILE],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8"
    )
    threading.Thread(target=enqueue_output, args=(bot_process.stdout,), daemon=True).start()

def stop_bot():
    global bot_process
    if bot_process and bot_process.poll() is None:
        bot_process.terminate()
        try:
            bot_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            bot_process.kill()
        bot_process = None
    else:
        messagebox.showinfo("Info","Botは起動していません")

def restart_bot():
    stop_bot()
    time.sleep(RESTART_DELAY)
    start_bot()

def send_command_gui():
    cmd = command_entry.get().strip()
    if bot_process and bot_process.poll() is None:
        bot_process.stdin.write(cmd + "\n")
        bot_process.stdin.flush()
    else:
        messagebox.showerror("Error","Botが起動していません")
    command_entry.delete(0, tk.END)
    update_gui()

# ===========================
# ミニゲーム（選択式）
# ===========================
def mini_game():
    global points
    root_dialog = tk.Tk()
    root_dialog.withdraw()

    game_choice = simpledialog.askstring(
        "ミニゲーム選択",
        "遊びたいゲームを選んでください:\n- guess（数字当て）\n- coin（コイントス）\n- roll（ダイスロール）\n- event（ランダムイベント）"
    )
    if not game_choice:
        return
    game_choice = game_choice.lower()

    if game_choice == "guess":
        number = random.randint(1, 10)
        guess = simpledialog.askinteger("数字当て", "1-10の数字を当ててね")
        if guess == number:
            messagebox.showinfo("正解", "正解！ポイント+5")
            points += 5
        else:
            messagebox.showinfo("はずれ", f"正解は {number}")
    elif game_choice == "coin":
        result = random.choice(["表", "裏"])
        messagebox.showinfo("コイントス", f"結果: {result}")
        if result == "表":
            points += 2
    elif game_choice == "roll":
        roll = random.randint(1, 6)
        messagebox.showinfo("ダイスロール", f"出た目: {roll}")
        points += roll
    elif game_choice == "event":
        event = random.choice(["🎉 ラッキー！ポイント+10", "💥 罠！ポイント-5", "✨ レア称号出現！"])
        messagebox.showinfo("ランダムイベント", event)
        if "ポイント+10" in event:
            points += 10
        if "ポイント-5" in event:
            points = max(points - 5, 0)
        if "レア称号" in event:
            points += 20
    elif game_choice == "あがり臭い":
        event = random.choice(["🎉 その通り+100000000000000000", "💥 アガの口+100000000000000000", "✨ あなたもあがりの被害者ですか？+100000000000000000"])
        messagebox.showinfo("！！あがりは臭い！！", event)
        if "ポイント+100000000000000000" in event:
            points += 5.358e+301
    else:
        messagebox.showwarning("エラー", "無効な選択です")

    update_gui()

# ===========================
# GUI更新
# ===========================
def update_gui():
    log_text.config(state=tk.NORMAL)
    log_text.delete(1.0, tk.END)
    for line in log_lines:
        level = line.split("]")[0][1:].split(" ")[1]
        color = next((c for n,k,c in LOG_LEVELS if n==level), "black")
        log_text.insert(tk.END, line+"\n", level)
        log_text.tag_config(level, foreground=color)
    log_text.config(state=tk.DISABLED)
    status_label.config(text=f"ポイント: {points} 称号: {get_title(points)} 稼働時間: {int(time.time()-start_time)}s")

# ===========================
# GUI構築
# ===========================
root = tk.Tk()
root.title("Ultimate Bot Manager GUI")
root.geometry("1200x800")

top_frame = tk.Frame(root)
top_frame.pack(fill=tk.X)

start_btn = tk.Button(top_frame,text="Start",command=start_bot,bg="green",fg="white")
start_btn.pack(side=tk.LEFT,padx=5,pady=5)
stop_btn = tk.Button(top_frame,text="Stop",command=stop_bot,bg="red",fg="white")
stop_btn.pack(side=tk.LEFT,padx=5,pady=5)
restart_btn = tk.Button(top_frame,text="Restart",command=restart_bot,bg="orange",fg="white")
restart_btn.pack(side=tk.LEFT,padx=5,pady=5)
mini_btn = tk.Button(top_frame,text="Mini Game",command=mini_game,bg="blue",fg="white")
mini_btn.pack(side=tk.LEFT,padx=5,pady=5)

command_entry = tk.Entry(top_frame,width=40)
command_entry.pack(side=tk.LEFT,padx=5)
send_btn = tk.Button(top_frame,text="Send Command",command=send_command_gui)
send_btn.pack(side=tk.LEFT,padx=5)

status_label = tk.Label(root,text="ポイント:0 称号:初心者 稼働時間:0s",anchor="w")
status_label.pack(fill=tk.X)

log_text = scrolledtext.ScrolledText(root,state=tk.DISABLED)
log_text.pack(fill=tk.BOTH, expand=True)

# 定期GUI更新
def periodic_update():
    update_gui()
    root.after(1000, periodic_update)

root.after(1000, periodic_update)
root.mainloop()
