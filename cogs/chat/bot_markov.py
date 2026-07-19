import logging
import pathlib
import random
from collections import defaultdict
from janome.tokenizer import Tokenizer
from discord.ext import commands

logger = logging.getLogger(__name__)

SPECIAL_LOG = "special_log.txt"
TARGET_USER = 1118799600816492626

tokenizer = Tokenizer()

class MarkovCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

# -------------------------
# Tokenize
# -------------------------
def tokenize_japanese(text: str):
    return [t.surface for t in tokenizer.tokenize(text)]


# -------------------------
# Build Model (N-gram)
# -------------------------
def build_model(text: str, n: int = 2):
    words = tokenize_japanese(text)

    if len(words) < 2:
        return {}

    n = max(1, min(n, len(words) - 1))

    model = defaultdict(list)

    for i in range(len(words) - n):
        key = tuple(words[i:i + n])
        model[key].append(words[i + n])

    return dict(model)


# -------------------------
# Sentence Generation (robust)
# -------------------------
def generate_sentence(model, length: int = 50, n: int = 2, seed=None):
    if not model:
        return ""

    if seed is not None:
        random.seed(seed)

    key = random.choice(list(model.keys()))
    words = list(key)

    safety_counter = 0
    max_steps = 500

    while len("".join(words)) < length and safety_counter < max_steps:
        safety_counter += 1

        current_key = tuple(words[-n:]) if len(words) >= n else tuple(words)

        next_words = model.get(current_key)

        if not next_words:
            # フォールバック：ランダムジャンプ
            key = random.choice(list(model.keys()))
            words.extend(list(key))
            continue

        words.append(random.choice(next_words))

    return "".join(words)[:length]


# -------------------------
# Logging filter
# -------------------------
def _is_valid(text: str):
    if not text:
        return False
    if text.startswith(("!", "/", "^^")):
        return False
    if text.startswith("http"):
        return False
    return True


def save_log(author_id: int, text: str):
    if author_id != TARGET_USER:
        return
    if not _is_valid(text):
        return

    pathlib.Path(SPECIAL_LOG).open("a", encoding="utf-8").write(text + "\n")


# -------------------------
# Streaming loader (memory safe)
# -------------------------
def read_logs(limit_lines: int = 5000):
    path = pathlib.Path(SPECIAL_LOG)

    if not path.exists():
        return ""

    lines = []

    with path.open("r", encoding="utf-8") as f:
        for i, line in enumerate(f):
            if i >= limit_lines:
                break
            lines.append(line.strip())

    return "\n".join(lines)


# -------------------------
# Model builder (chunk safe)
# -------------------------
def build_model_from_logs(n: int = 2, max_lines: int = 5000):
    text = read_logs(max_lines)
    return build_model(text, n=n)

async def setup(bot: commands.Bot):
    await bot.add_cog(MarkovCog(bot))