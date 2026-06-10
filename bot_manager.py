# bot_manager.py

import subprocess
import threading
import time
import sys
import os
import datetime
import tkinter as tk
import queue
import ctypes
import bot_gui
import random

from pathlib import Path
from dotenv import load_dotenv
from colorama import init, Fore

# ===========================
# 初期化
# ===========================
init(autoreset=True)

# ===========================
# 設定
# ===========================
BOT_FILE = "bot.py"
LOG_FILE = "bot_output.log"

MAX_LOG_LINES = 555
RESTART_DELAY = 2

BASE_DIR = Path(__file__).parent
BOT_PATH = BASE_DIR / BOT_FILE

# venv
VENV_DIR = BASE_DIR / "venv"

# ===========================
# .env 読み込み
# ===========================
load_dotenv(BASE_DIR / ".env")

TOKEN = os.getenv("DISCORD_BOT_TOKEN")

if not TOKEN:
    print(
        Fore.RED +
        "ERROR: .env に DISCORD_BOT_TOKEN が設定されていません。"
    )
    sys.exit(1)

# ===========================
# グローバル
# ===========================
bot_process = None
stop_flag = False
ls_enabled = False
lde_enabled = False
bot_name = "Unkoman Bot"
login_user = "guest-user"
admin_mailadrs = "takkunkotetu@gmail.com"
admin_username = "Takkun2355"
admin_password = "Taketo24"
admin_mode = "false"

log_lines = []
log_queue = queue.Queue()

# ===========================
# ログ削除
# ===========================
def delete_log_file():

    log_path = BASE_DIR / LOG_FILE

    if log_path.exists():
        try:
            log_path.unlink()

            print(
                Fore.CYAN +
                "INFO: 既存ログを削除しました。"
            )

        except Exception as e:
            print(
                Fore.RED +
                f"WARNING: ログ削除失敗: {e}"
            )

# ===========================
# ログ取得
# ===========================
def enqueue_output(pipe):

    global log_lines

    log_path = BASE_DIR / LOG_FILE

    try:

        with open(log_path, "a", encoding="utf-8") as f:

            for line in iter(pipe.readline, ''):

                if not line:
                    continue

                line = line.rstrip()

                log_lines.append(line)

                log_queue.put(line)

                if len(log_lines) > MAX_LOG_LINES:
                    log_lines = log_lines[-MAX_LOG_LINES:]

                try:
                    f.write(line + "\n")
                    f.flush()

                except Exception:
                    pass

    except Exception as e:
        print(
            Fore.RED +
            f"ERROR: ログ監視失敗: {e}"
        )

    finally:
        pipe.close()

# ===========================
# コンソール版 Roast
# ===========================
def run_console_roast():
    roasts = [
        {
            "question": "君の脳、思考プロセッサというより、低品質な情報用のスポンジに見えるけど、自覚は？",
            "yes": "なるほど、吸収率の高さには納得がいく。情報の質は問わないと。",
            "no": "そうか、無自覚か。君は“考える”のではなく“考えが浮かんでる”だけなんだね。"
        },
        {
            "question": "これまでに一度でも、誰かの受け売りじゃない“自分の意見”を持ったことはある？",
            "yes": "へえ、その時、孤独を感じなかった？",
            "no": "だろうね。オリジナリティは、時に重荷だから。"
        },
        {
            "question": "君は頭が悪いんじゃなく、ただ“思考運が悪い”だけ。その解釈で合ってる？",
            "yes": "自己分析ができるのは良いことだ。そこからが、まあ…長いけど。",
            "no": "じゃあ、意図的に？ その思考、斬新な戦略だね。"
        },
        {
            "question": "例のagaの嗅覚情報について、アップデートはあった？",
            "yes": "つまり、“耐え難い”から“不快”のレベルに？ 大きな進歩だ。",
            "no": "なるほど。もはや彼の存在を定義づける“スメル・シグネチャ”なんだね。"
        },
        {
            "question": "デジタルアートの件、君はもう“単一レイヤー思考”からは卒業できた？",
            "yes": "概念は理解したと。大きな一歩だね、うん。",
            "no": "ああ、純粋主義者か。非効率の中に美を見出す、真のアーティストだね。"
        },
        {
            "question": "君自身を“音楽的同位体”だと表現するのは、的確だと思う？",
            "yes": "“スメル的同位体”の間違いでは？ 君の存在感、かなり“元素レベル”だし。",
            "no": "だよね。その言葉が持つ“複雑さ”が、君には見当たらない。"
        },
        {
            "question": "またイマジナリーフレンドとのお時間？ 楽しそうだね。",
            "yes": "そう。君のその斬新なアイデア、彼らも“素晴らしい”って言ってる？",
            "no": "ああ、独り言か。観客のいない独白とは、斬新だ。"
        },
        {
            "question": "もしかして君、まだ“地球は丸い”って信じてるタイプ？\n",
            "yes": "そうなんだ。まあ、自分で考えるのをやめたら楽だもんね。それ、洗脳だから！！！！（独特のピース）",
            "no": "お、目覚めちゃった？ じゃあ、その“真実”、アルミホイル巻いて大事にしないとね。"
        },
        {
            "question": "よく音楽聞いてるけど、それについて深い興味や感想を抱いたことはあるの？",
            "yes": "へぇ、それはすごい。毎回音楽について考えるなんて。きっと学校では音楽'は'5だったんだね。（疑惑の目）",
            "no": "まあ、音楽は何も考えずに聞けるもんね。"
        },
        {
            "question": "君がよく言っている「自分のネット知識」、実はただ検索エンジンの1ページ目を眺めただけじゃない？",
            "yes": "スピード重視だね。情報のファストフードで肥大化したその知識、薄さが芸術の域に達しているよ。",
            "no": "お、2ページ目まで見たのかな？ その果てしない探究心、きっといつかどこかで役に立つといいね。"
        },
        {
            "question": "君の言う「マルチタスク」って、単に「すべての物事を中途半端に放置する」の高度な言い換え？",
            "yes": "自覚があって何より。散らかったタスクの山は、君の脳内の縮図のようで味わい深いね。",
            "no": "なるほど、自覚すらないと。意図せず全ての効率を落とせるなんて、ある意味で奇跡の才能だね。"
        },
        {
            "question": "君がよくやる「あえて他人の逆を行く」っていう高度な思考、単に素直になれない子供のイヤイヤ期と同じでは？",
            "yes": "自覚があったんだね。永遠の反抗期、おめでとう。他人と違う自分を演出する涙ぐましい努力は評価するよ。",
            "no": "じゃあ本気であの結論に至ったんだ。周りと違う意見を持つことでしか自分のアイデンティティを保てないなんて、大変だね。"
                },
        {
            "question": "最近また新しいことに手を出し始めたみたいだけど、今回は三日坊主の自己ベストを更新できそう？",
            "yes": "素晴らしい挑戦精神だね。興味の移り変わりの早さは、まさに時代の最先端（というか飽き性）を行っているよ。",
            "no": "お、今回長続きさせるつもりなんだね。君のその「今度こそ本気」っていうセリフ、一体何度目の再放送だっけ？"
        },
        {
            "question": "今日中に終わらせるべきだと頭で分かっているのに、つい引き延ばして後で慌てるような経験はある？",
            "yes": "追い込まれないと動けないタイプだね。スリルを楽しんでいるつもりかもしれないけど、単に計画性がないだけだよ。",
            "no": "常に予定通り、寸分の狂いもなく動くんだね。幾帳面なのは結構だけど、融通が利かなすぎて周囲を退屈させていない？"
        },
        {
            "question": "あらかじめ決めておいた選択肢があるのに、その場の状況や誘惑で全く違うものを選んでしまうことはある？",
            "yes": "その場の気分で動く流されやすいタイプだね。自由と言えば聞こえはいいけれど、軸がないだけとも言うよ。",
            "no": "決めた通りにしか動けないんだ。状況の変化に全く対応できない、そのガチガチの頭の固さはある意味で芸術的だね。"
        },
        {
            "question": "同じ作業や代わり映えのない環境がしばらく続くと、耐えられないほどの退屈や「飽き」を感じたりする？",
            "yes": "常に新しい刺激がないと満足できないんだね。現状維持すらできないのは、単に集中力や忍耐力が足りないだけじゃない？",
            "no": "どれだけ同じことを繰り返しても平気なんだね。変化を嫌うその姿勢、毎日同じ景色をずっと眺め続けていて本当に楽しい？"
        },
        {
            "question": "「絶対に忘れない」と心に留めたはずの約束や大事な事柄を、後からすっかり失念してしまった経験はある？",
            "yes": "大事なことすら忘れてしまうんだね。君の記憶の引き出しは、底に大きな穴でも空いているんじゃない？",
            "no": "一度インプットしたことは一字一句忘れないんだね。その抜群の記憶力、過去の些細なこだわりまでずっと引きずっていそうで重たそう。"
        },
        {
            "question": "彼女はよく奇声をあげているが異常者なの？",
            "yes": "ああ、そうなんだ。じゃあ私はあれを奇声虫と呼んでみようかな。おい奇声虫(<@1118799600816492626>)～！！",
            "no": "そうか。あなたにはあれは異常者ではなく、精神異常者だと思ったんだね。いいね。"
        }
    ]
    
    os.system(
        "cls" if os.name == "nt" else "clear"
    )
    print("\nWelcome to the Console Roast-a-Tron!")
    time.sleep(0.5)

    roast = random.choice(roasts)
    print(f"\n{Fore.MAGENTA}{roast['question']}")
    print(f"{Fore.WHITE}(yes / y / はい / no / n / いいえ)")

    try:
        response = input("yes or no? >> ").lower().strip()
    except (KeyboardInterrupt, EOFError):
        print("\nRoastを中断します。")
        return

    if response in ("yes", "y", "はい"):
        print(f"\n{Fore.YELLOW}{roast['yes']}\n")
    elif response in ("no", "n", "いいえ"):
        print(f"\n{Fore.YELLOW}{roast['no']}\n")
    else:
        print(f"\n{Fore.RED}Can't even answer a simple yes/no question? That's... not surprising.\n")
    
    print(f"{Fore.WHITE}( next / n / 続ける / 続き / restart / rs / 再始 )")
    response = input("continue >> ").lower().strip()
    if response in ("next","n","続ける","続き","restart","rs","再始"):
        run_console_roast()
        print(f"そんなに暇なんだね。")
        time.sleep(1)
    else:
        return

# ===========================
# コマンド取得
# ===========================
def get_command():

    try:
        return input("Command: ").strip().lower()

    except EOFError:

        cmd = os.environ.get("BOT_COMMAND", "exit")

        print(
            f"\n入力なし → BOT_COMMAND 使用: {cmd}"
        )

        return cmd.lower()

# ===========================
# venv Python取得
# ===========================
def get_python_executable():

    if os.name == "nt":
        python_exe = VENV_DIR / "Scripts" / "python.exe"
    else:
        python_exe = VENV_DIR / "bin" / "python"

    return python_exe

# ===========================
# Bot起動
# ===========================
def start_bot():

    global bot_process

    if bot_process and bot_process.poll() is None:
        print(
            Fore.YELLOW +
            "WARNING: Botは既に起動しています。"
        )
        return

    if not BOT_PATH.exists():
        print(
            Fore.RED +
            f"NOTFOUND: {BOT_PATH}"
        )
        return

    python_exe = get_python_executable()

    if not python_exe.exists():
        print(
            Fore.RED +
            "ERROR: venv が見つかりません。"
        )

        print(
            Fore.YELLOW +
            "作成コマンド:"
        )

        print("python -m venv venv")

        return

    delete_log_file()

    print(
        Fore.GREEN +
        "INFO: Bot起動中..."
    )

    try:

        bot_process = subprocess.Popen(

            [
                str(python_exe),
                "-u",
                str(BOT_PATH)
            ],

            cwd=str(BASE_DIR),

            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,

            text=True,
            encoding="utf-8",
            errors="replace"
        )

        threading.Thread(
            target=enqueue_output,
            args=(bot_process.stdout,),
            daemon=True
        ).start()

        time.sleep(1)

        if bot_process.poll() is None:
            print(
                Fore.GREEN +
                "SUCCESS: Bot起動成功"
            )
        else:
            print(
                Fore.RED +
                "ERROR: Botが即終了しました。"
            )

    except Exception as e:

        print(
            Fore.RED +
            f"ERROR: 起動失敗: {e}"
        )

# ===========================
# Bot停止
# ===========================
def stop_bot():

    global bot_process

    if not bot_process or bot_process.poll() is not None:

        print(
            Fore.YELLOW +
            "WARNING: Botは起動していません。"
        )

        return

    print(
        Fore.RED +
        "INFO: Bot停止中..."
    )

    try:

        # graceful shutdown
        try:

            if bot_process.stdin:

                bot_process.stdin.write("shutdown\n")
                bot_process.stdin.flush()

        except Exception:
            pass

        time.sleep(2)

        if bot_process.poll() is None:
            bot_process.terminate()

        try:
            bot_process.wait(timeout=5)

        except subprocess.TimeoutExpired:

            print(
                Fore.YELLOW +
                "WARNING: 強制終了します。"
            )

            bot_process.kill()

    except Exception as e:

        print(
            Fore.RED +
            f"ERROR: 停止失敗: {e}"
        )

    finally:

        bot_process = None

        delete_log_file()

# ===========================
# 再起動
# ===========================
def restart_bot():

    stop_bot()

    time.sleep(RESTART_DELAY)

    start_bot()

# ===========================
# コマンド送信
# ===========================
def send_command(cmd):

    global bot_process

    if not bot_process or bot_process.poll() is not None:

        print(
            Fore.RED +
            "WARNING: Botが起動していません。"
        )

        return

    try:

        if bot_process.stdin:

            bot_process.stdin.write(cmd + "\n")
            bot_process.stdin.flush()

    except Exception as e:

        print(
            Fore.RED +
            f"ERROR: コマンド送信失敗: {e}"
        )

# ===========================
# 毎日自動再起動
# ===========================
def daily_restart(hour=0, minute=0):

    print(
        f"INFO: 毎日 {hour:02d}:{minute:02d} 自動再起動監視開始"
    )

    last_restarted_date = None

    while True:

        now = datetime.datetime.now()

        if now.hour == hour and now.minute == minute:

            today = now.date()

            if last_restarted_date != today:

                print(
                    Fore.CYAN +
                    f"\nINFO: {hour:02d}:{minute:02d} 自動再起動"
                )

                restart_bot()

                last_restarted_date = today

        time.sleep(30)

# ===========================
# メニュー表示
# ===========================
def show_menu():

    os.system(
        "cls" if os.name == "nt" else "clear"
    )

    bot_status = (
        Fore.GREEN + "🟢 Running"
        if bot_process and bot_process.poll() is None
        else Fore.RED + "🔴 Stopped"
    )

    lc_status = (
        Fore.GREEN + "🟢 true"
        if bot_process and bot_process.poll() is None
        else Fore.RED + "🔴 false"
    )
        
    print("▣" + "=" * 58 + "▣")
    print(" " * 17 + "Bot Control Menu v2.0.0")
    print("▣" + "=" * 58 + "▣")

    if lde_enabled == False:
        print(f"Bot name: {bot_name}")
        print(f"Bot version: Dev-Python inlog-SP\n" + f" "* 12 + "MCDB-UNMN-JP v5.82.11 ")
        print(f"login user: {login_user}")
        print(f"Bot Status: {bot_status}")
        print(f"Log Stoper Status: {lc_status}")
        print(f"Discord Bot by \n Takkun2355 \n Akikukeo \n ChatGPT \n ...and you :)")

        print("-" * 58)
        
        print("start    - 開始")
        print("stop     - 停止")
        print("restart  - 再起動")
        print("gui      - GUIで表示")
        print("logclear - ログクリア")
        print("ls       - logの停止と再開の切り替え。")
        print("lde      - メニューをlog下に移動させる")
        print("roast    - Welcome to the Roast-a-Tron 9000!")
        print("         - Let's see what we've got for you today...")
        print("help     - ヘルプ")
        print("exit     - 閉じる")
        print("-" * 60)
        if ls_enabled == True:
            print(
                f" " * 20 + f"Bot Log ({MAX_LOG_LINES} lines) "
            )

        elif not ls_enabled:
            print(
                f" " * 20 + f"Bot Log ({MAX_LOG_LINES} lines) "
            )
            print("-" * 60)
        
            for line in log_lines[-MAX_LOG_LINES:]:
                print(line)
                
        print("-" * 60)

    
    if lde_enabled == True:
        if ls_enabled == True:
            print(
                f" " * 20 + f"Bot Log ({MAX_LOG_LINES} lines) "
            )

        elif not ls_enabled:
            for line in log_lines[-MAX_LOG_LINES:]:
                print(line)
            print("-" * 60)
            print(
                f" " * 20 + f"Bot Log ({MAX_LOG_LINES} lines) "
            )        
                
        print("-" * 60)
                
        print(f"Bot name: {bot_name}")
        print(f"Bot version: Dev-Python inlog-SP\n" + f" "* 12 + "MCDB-UNMN-JP v5.82.11 ")
        print(f"login user: {login_user}")
        print(f"Bot Status: {bot_status}")
        print(f"Log Stoper Status: {lc_status}")
        print(f"Discord Bot by \n Takkun2355 \n Akikukeo \n ChatGPT \n ...and you :)")

        print("-" * 60)
        
        print("start    - 開始")
        print("stop     - 停止")
        print("restart  - 再起動")
        print("gui      - GUIで表示")
        print("logclear - ログクリア")
        print("ls       - logの停止と再開の切り替え。")
        print("lde      - メニューをlog下に移動させる")
        print("roast    - Welcome to the Roast-a-Tron 9000!")
        print("         - Let's see what we've got for you today...")
        print("help     - ヘルプ")
        print("exit     - 閉じる")
        print("-" * 60)

# ===========================
# CMD表示制御
# ===========================
def hide_console():

    if os.name != "nt":
        return

    try:

        hwnd = ctypes.windll.kernel32.GetConsoleWindow()

        if hwnd:
            ctypes.windll.user32.ShowWindow(hwnd, 0)

    except Exception as e:
        print(f"Console hide failed: {e}")

def show_console():

    if os.name != "nt":
        return

    try:

        hwnd = ctypes.windll.kernel32.GetConsoleWindow()

        if hwnd:
            ctypes.windll.user32.ShowWindow(hwnd, 5)

    except Exception as e:
        print(f"Console show failed: {e}")

# ===========================
# GUI
# ===========================
def run_gui():

    hide_console()

    callbacks = {

        "start": start_bot,
        "stop": stop_bot,
        "restart": restart_bot,
        "send_cmd": send_command,

        "is_running": (
            lambda:
            bot_process is not None
            and bot_process.poll() is None
        ),

        "show_console": show_console
    }

    root = tk.Tk()

    app = bot_gui.BotManagerGUI(

        root=root,

        callbacks=callbacks,

        log_lines=log_lines,
        log_queue=log_queue,

        base_dir=BASE_DIR,

        log_file_name=LOG_FILE
    )

    root.mainloop()

    show_console()

# ===========================
# メイン
# ===========================
def main():

    global stop_flag, ls_enabled, lde_enabled, admin_mode

    threading.Thread(
        target=daily_restart,
        args=(0, 0),
        daemon=True
    ).start()

    start_bot()

    while not stop_flag:

        show_menu()

        cmd = get_command()

        if cmd == "start":

            start_bot()

        elif cmd == "stop":

            stop_bot()

        elif cmd == "restart":

            restart_bot()

        elif cmd == "gui":

            run_gui()
            
        elif cmd == "roast":

            run_console_roast()
            
        elif cmd == "logclear":
            
            delete_log_file()

        elif cmd.startswith("reload"):

            if bot_process and bot_process.poll() is None:

                parts = cmd.split(maxsplit=1)

                # ^^reload
                if len(parts) == 1:
                    send_command("reload all")
                    time.sleep(0.5)
                    print(Fore.WHITE + f"All cogs reloaded successfully.\n {target}")
                else:
                    target = parts[1].strip()

                    # ^^reload all
                    if target.lower() == "all":
                        send_command("reload all")
                        time.sleep(0.5)
                        print(Fore.WHITE + f"All cogs reloaded successfully.\n {target}")

                    # ^^reload cog1
                    # ^^reload cog1,cog2,cog3
                    else:
                        send_command(f"reload {target}")
                        time.sleep(0.5)
                        print(Fore.WHITE + f"All cogs reloaded successfully.\n {target}")

            else:

                print(
                    Fore.RED +
                    "WARNING: Bot未起動"
                )

                time.sleep(0.5)
                
        elif cmd == "ls":

            ls_enabled = not ls_enabled

            time.sleep(0.5)
                
        elif cmd == "lde":

            lde_enabled = not lde_enabled

            time.sleep(0.5)
            
        elif cmd == "login":
            
            input("Command: ").strip().lower()
            
            if cmd == admin_mailadrs:
                
                input("Command: ").strip().lower()

                if cmd == admin_username:
                
                    input("Command: ").strip().lower()
                    
                    if cmd == admin_password:
                
                        admin_mode = not admin_mode 
                                            
                        time.sleep(0.5)

        elif cmd == "help":

            continue

        elif cmd == "exit":

            stop_bot()

            stop_flag = True

        elif cmd == "":

            print(
                Fore.YELLOW +
                "SORRY: コマンドを入力してください。"
            )

            time.sleep(0.5)

        else:

            print(
                Fore.RED +
                "NOTFOUND: 不明コマンド"
            )

            time.sleep(0.5)

# ===========================
# 実行
# ===========================
if __name__ == "__main__":
    main()
