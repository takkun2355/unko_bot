# bot_markov.py
import os
import random
from janome.tokenizer import Tokenizer

# chatlog.txtは廃止し、special_log.txtのみに統合
SPECIAL_LOG = "special_log.txt"
TARGET_USER = 1118799600816492626

tokenizer = Tokenizer()


def tokenize_japanese(text: str):
    return [token.surface for token in tokenizer.tokenize(text)]


def build_model(text, n=2):
    """Markovモデルを作成"""
    words = tokenize_japanese(text)
    if not words:
        return {}
    if n > len(words):
        n = max(1, len(words) - 1)
    model = {}
    for i in range(len(words) - n):
        key = tuple(words[i : i + n])
        next_word = words[i + n]
        model.setdefault(key, []).append(next_word)
    return model


def generate_sentence(model, length=50):
    """実際の文字数が length に達するまで生成"""
    if not model:
        return ""
    key = random.choice(list(model.keys()))
    words = list(key)
    while len("".join(words)) < length:
        current_key = tuple(words[-len(key) :])
        next_words = model.get(current_key)
        if not next_words:
            break
        words.append(random.choice(next_words))
    return "".join(words)[:length]


def save_log(author_id: int, text: str):
    """対象ユーザー(TARGET_USER)の発言のみをspecial_log.txtに保存"""
    if author_id == TARGET_USER:
        # 空のメッセージや、ボットへのコマンド（例: ! や / から始まるメッセージ）は除外
        if not text or text.startswith("!") or text.startswith("/"):
            return

        # ログを追記保存
        with open(SPECIAL_LOG, "a", encoding="utf-8") as f:
            f.write(text + "\n")


def read_logs():
    """special_log.txtのみからテキストを読み込む"""
    if os.path.exists(SPECIAL_LOG):
        with open(SPECIAL_LOG, "r", encoding="utf-8") as f:
            return f.read()
    return ""
