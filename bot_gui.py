# bot_gui.py
import tkinter as tk
from tkinter import scrolledtext, messagebox, ttk
import queue
import random
import math

# --- particles.js風の最背面・カーソル回避対応キャンバス ---
class ParticleCanvas(tk.Canvas):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.particles = []
        self.active = False
        self.width = 650
        self.height = 550
        
        # マウス座標（初期値は範囲外）
        self.mx = -1000
        self.my = -1000

        # イベントのバインド
        self.bind("<Configure>", self.on_resize)
        self.bind("<Motion>", self.on_mouse_move)
        self.bind("<Leave>", self.on_mouse_leave)

    def on_resize(self, event):
        """ウィンドウサイズ変更に合わせて境界を更新"""
        self.width = event.width
        self.height = event.height

    def on_mouse_move(self, event):
        self.mx = event.x
        self.my = event.y

    def on_mouse_leave(self, event):
        self.mx = -1000
        self.my = -1000

    def start_animation(self):
        self.active = True
        self.particles = []
        # ウィンドウサイズに応じた粒子の配置
        for _ in range(40):
            self.particles.append({
                'x': random.randint(10, self.width - 10),
                'y': random.randint(10, self.height - 10),
                'vx': random.uniform(-1.0, 1.0),
                'vy': random.uniform(-1.0, 1.0),
                'r': random.randint(2, 4)
            })
        self.animate()

    def stop_animation(self):
        self.active = False
        self.delete("all")

    def animate(self):
        if not self.active:
            return
        self.delete("all")
        
        # 粒子の更新と描画
        for p in self.particles:
            # カーソル回避ロジック（距離が80px未満なら避けるように力を加える）
            dx = p['x'] - self.mx
            dy = p['y'] - self.my
            dist = math.hypot(dx, dy)
            if dist < 80 and dist > 0:
                # 近いほど強い力で押し出す
                force = (80 - dist) / 80 * 4.0
                angle = math.atan2(dy, dx)
                p['x'] += math.cos(angle) * force * 3
                p['y'] += math.sin(angle) * force * 3
            
            # 通常移動
            p['x'] += p['vx']
            p['y'] += p['vy']
            
            # 壁での跳ね返り
            if p['x'] < 0 or p['x'] > self.width:
                p['vx'] *= -1
            if p['y'] < 0 or p['y'] > self.height:
                p['vy'] *= -1
                
            self.create_oval(p['x']-p['r'], p['y']-p['r'], p['x']+p['r'], p['y']+p['r'], fill="#00e5ff", outline="")

        # 距離が近い粒子同士を結ぶ
        for i in range(len(self.particles)):
            for j in range(i+1, len(self.particles)):
                p1 = self.particles[i]
                p2 = self.particles[j]
                dist = math.hypot(p1['x'] - p2['x'], p1['y'] - p2['y'])
                if dist < 85:
                    if dist < 30:
                        color = "#00e5ff"
                    elif dist < 55:
                        color = "#0088cc"
                    else:
                        color = "#002b4d"
                    self.create_line(p1['x'], p1['y'], p2['x'], p2['y'], fill=color, width=1)
                    
        self.after(30, self.animate)


# --- メインGUIクラス ---
class BotManagerGUI:
    def __init__(self, root, callbacks, log_lines, log_queue, base_dir, log_file_name):
        self.root = root
        self.callbacks = callbacks
        self.log_lines = log_lines
        self.log_queue = log_queue
        self.base_dir = base_dir
        self.log_file_name = log_file_name
        self.current_theme = "dark"

        self.root.title("Bot Manager GUI")
        self.root.geometry("680x580")
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        # 【最背面】背景パーティクルキャンバスの配置
        self.particle_canvas = ParticleCanvas(self.root, highlightthickness=0)
        self.particle_canvas.place(x=0, y=0, relwidth=1, relheight=1)
        self.particle_canvas.lower()  # 最背面へ移動

        # ステータス・テーマ設定エリア
        self.top_frame = tk.Frame(self.root)
        self.top_frame.pack(fill=tk.X, padx=15, pady=8)
        
        self.status_label = tk.Label(self.top_frame, text="Checking status...", font=("Arial", 11, "bold"))
        self.status_label.pack(side=tk.LEFT)

        # テーマ選択ドロップダウン
        tk.Label(self.top_frame, text="テーマ:").pack(side=tk.RIGHT, padx=5)
        self.theme_combo = ttk.Combobox(self.top_frame, values=["light", "dark", "hacker", "particles"], width=10, state="readonly")
        self.theme_combo.set("dark")
        self.theme_combo.pack(side=tk.RIGHT)
        self.theme_combo.bind("<<ComboboxSelected>>", lambda e: self.apply_theme(self.theme_combo.get()))

        # ログ表示フレームとスクロールテキスト
        self.log_frame = tk.Frame(self.root)
        self.log_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=5)
        self.log_area = scrolledtext.ScrolledText(self.log_frame, height=15)
        self.log_area.pack(fill=tk.BOTH, expand=True)

        # コマンド入力エリア
        self.input_frame = tk.Frame(self.root)
        self.input_frame.pack(fill=tk.X, padx=15, pady=5)
        self.input_label = tk.Label(self.input_frame, text="コマンド入力:")
        self.input_label.pack(side=tk.LEFT)
        self.cmd_entry = tk.Entry(self.input_frame)
        self.cmd_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.cmd_entry.bind("<Return>", lambda e: self.send_cmd())
        self.send_btn = tk.Button(self.input_frame, text="送信", width=8, command=self.send_cmd)
        self.send_btn.pack(side=tk.LEFT)

        # 操作パネル（ボタン群）
        self.btn_frame = tk.Frame(self.root)
        self.btn_frame.pack(fill=tk.X, padx=15, pady=5)
        
        self.btn_start = tk.Button(self.btn_frame, text="Start Bot", width=11, command=self.callbacks['start'])
        self.btn_start.pack(side=tk.LEFT, padx=2)
        self.btn_stop = tk.Button(self.btn_frame, text="Stop Bot", width=11, command=self.callbacks['stop'])
        self.btn_stop.pack(side=tk.LEFT, padx=2)
        self.btn_restart = tk.Button(self.btn_frame, text="Restart Bot", width=11, command=self.callbacks['restart'])
        self.btn_restart.pack(side=tk.LEFT, padx=2)
        self.btn_save = tk.Button(self.btn_frame, text="ログを保存", width=11, command=self.export_logs)
        self.btn_save.pack(side=tk.LEFT, padx=2)
        self.btn_help = tk.Button(self.btn_frame, text="Help", width=6, command=self.show_help)
        self.btn_help.pack(side=tk.LEFT, padx=2)
        self.btn_close = tk.Button(self.btn_frame, text="CMDに戻る", width=11, command=self.return_to_cmd)
        self.btn_close.pack(side=tk.RIGHT, padx=2)

        # コマンドショートカット
        self.cmd_shortcut_frame = tk.LabelFrame(self.root, text="コマンドクイック実行")
        self.cmd_shortcut_frame.pack(fill=tk.X, padx=15, pady=8)
        self.shortcut_buttons = []
        for cmd in ["talk", "hello", "korosuzo", "aga"]:
            btn = tk.Button(self.cmd_shortcut_frame, text=cmd, width=10, command=lambda c=cmd: self.send_cmd(c))
            btn.pack(side=tk.LEFT, padx=5, pady=5)
            self.shortcut_buttons.append(btn)

        # 過去ログ読み込み
        for line in self.log_lines:
            self.log_area.insert(tk.END, line + "\n")
        self.log_area.yview(tk.END)

        self.apply_theme("dark")
        self.update_status()
        self.poll_logs()

    def recursive_style(self, widget, bg, fg, font, entry_bg=None, text_bg=None):
        """全子ウィジェットに対して再帰的にテーマカラーとフォントを適用"""
        w_class = widget.winfo_class()
        
        # キャンバス自体はテーマ背景を直接上書きしないように除外
        if widget == self.particle_canvas:
            return

        # 標準ウィジェットへのスタイル適用
        if w_class in ("Frame", "LabelFrame", "Label", "Button", "Entry", "Text", "Message"):
            # 特殊な背景色指定がある場合
            current_bg = bg
            if w_class == "Entry" and entry_bg:
                current_bg = entry_bg
            elif w_class == "Text" and text_bg:
                current_bg = text_bg
                
            try:
                widget.config(bg=current_bg)
            except tk.TclError:
                pass
            
            try:
                widget.config(fg=fg)
            except tk.TclError:
                pass
            
            try:
                widget.config(font=font)
            except tk.TclError:
                pass

            # テキスト入力・編集系ウィジェットのカーソル色適用
            if w_class in ("Entry", "Text"):
                try:
                    widget.config(insertbackground=fg)
                except tk.TclError:
                    pass

        # 子要素がある場合は再帰的に処理
        for child in widget.winfo_children():
            self.recursive_style(child, bg, fg, font, entry_bg, text_bg)

    def apply_theme(self, theme_name):
        self.current_theme = theme_name
        
        # particlesのアニメーション管理
        if theme_name == "particles":
            self.particle_canvas.start_animation()
        else:
            self.particle_canvas.stop_animation()

        # 各テーマ定義
        if theme_name == "light":
            bg, fg = "#f5f5f5", "#000000"
            entry_bg, text_bg = "#ffffff", "#ffffff"
            font = ("Arial", 10)
        elif theme_name == "dark":
            bg, fg = "#2d2d2d", "#ffffff"
            entry_bg, text_bg = "#1e1e1e", "#1e1e1e"
            font = ("Arial", 10)
        elif theme_name == "hacker":
            bg, fg = "#000000", "#00ff00"
            entry_bg, text_bg = "#000000", "#000000"
            font = ("Courier New", 10, "bold")
        elif theme_name == "particles":
            # particles時のウィジェット背景は半透過っぽく見えるよう暗めのトーンで統一
            bg, fg = "#0c1020", "#00e5ff"
            entry_bg, text_bg = "#070a14", "#070a14"
            font = ("Consolas", 10)

        # 1. フォーム内の全Tkウィジェットに適用
        self.root.config(bg=bg)
        self.recursive_style(self.root, bg, fg, font, entry_bg, text_bg)

        # 2. ttkスタイルの更新（Combobox、Scrollbarなどのスタイリング対応）
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("TCombobox", fieldbackground=entry_bg, background=bg, foreground=fg, arrowcolor=fg)
        style.configure("TScrollbar", background=bg, troughcolor=bg, bordercolor=bg, arrowcolor=fg)

        # ScrolledText内の標準Scrollbarへの簡易適用
        try:
            self.log_area.vbar.config(bg=bg, activebackground=fg, troughcolor=entry_bg)
        except AttributeError:
            pass

    def export_logs(self):
        content = self.log_area.get("1.0", tk.END).strip()
        log_path = self.base_dir / self.log_file_name
        try:
            with open(log_path, "w", encoding="utf-8") as f:
                f.write(content)
            messagebox.showinfo("保存完了", f"現在のログをファイルに書き出しました:\n{log_path}")
        except Exception as e:
            messagebox.showerror("エラー", f"ログの保存に失敗しました: {e}")

    def show_help(self):
        help_text = (
            "【コマンドヘルプ】\n\n"
            "• start: Botプロセスを新しく起動します。\n"
            "• stop: 実行中のBotプロセスを強制終了します。\n"
            "• restart: 起動中のBotを一度停止して再起動します。\n"
            "• talk / hello / korosuzo / aga: 指定コマンドを標準入力経由でBotに送信します。\n"
            "• ログを保存: 表示中のログを bot_output.log にファイル出力します。\n\n"
            "※テーマ切り替え時、ボタン、テキスト、入力エリア、スクロールバー等すべての要素に適用されます。"
        )
        messagebox.showinfo("ヘルプ", help_text)

    def update_status(self):
        if self.callbacks['is_running']():
            self.status_label.config(text="Bot Status: 🟢 Running", fg="green" if self.current_theme != "hacker" else "#00ff00")
        else:
            self.status_label.config(text="Bot Status: 🔴 Stopped", fg="red" if self.current_theme != "hacker" else "#ff3333")
        self.root.after(1000, self.update_status)

    def poll_logs(self):
        while not self.log_queue.empty():
            try:
                line = self.log_queue.get_nowait()
                self.log_area.insert(tk.END, line + "\n")
                self.log_area.yview(tk.END)
            except queue.Empty:
                break
        self.root.after(100, self.poll_logs)

    def send_cmd(self, cmd_text=None):
        cmd = cmd_text if cmd_text else self.cmd_entry.get().strip()
        if cmd:
            self.callbacks['send_cmd'](cmd)
            self.log_area.insert(tk.END, f">>> {cmd}\n")
            self.log_area.yview(tk.END)
            if not cmd_text:
                self.cmd_entry.delete(0, tk.END)

    def return_to_cmd(self):
        self.callbacks['show_console']()
        self.root.destroy()

    def on_close(self):
        self.return_to_cmd()