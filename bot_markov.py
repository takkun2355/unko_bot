# bot_markov.py
import os
import random
from janome.tokenizer import Tokenizer

CHAT_LOG = "chatlog.txt"
SPECIAL_LOG = "special_log.txt"
TARGET_USER = 1118799600816492626

tokenizer = Tokenizer()

def tokenize_japanese(text: str):
    return [token.surface for token in tokenizer.tokenize(text)]

def build_model(text, n=5):
    """Markovモデルを作成"""
    words = tokenize_japanese(text)
    if not words:
        return {}
    if n > len(words):
        n = max(1, len(words)-1)
    model = {}
    for i in range(len(words)-n):
        key = tuple(words[i:i+n])
        next_word = words[i+n]
        model.setdefault(key, []).append(next_word)
    return model

def generate_sentence(model, length=50):
    """文字数lengthまで生成"""
    if not model:
        return ""
    key = random.choice(list(model.keys()))
    words = list(key)
    for _ in range(length - len(words)):
        next_words = model.get(tuple(words[-len(key):]))
        if not next_words:
            break
        words.append(random.choice(next_words))
    return "".join(words)[:length]

def read_logs():
    combined_text = ""
    for file in (SPECIAL_LOG, CHAT_LOG):
        if os.path.exists(file):
            with open(file, "r", encoding="utf-8") as f:
                combined_text += f.read() + "\n"
    return combined_text
