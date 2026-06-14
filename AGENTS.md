# コードを書く際に気をつけるべき点

AIがコードを書く際に気をつけるべき点

## はじめに
このドキュメントは、AIがPythonコードを生成する際に、より高品質で保守性の高いコードを作成するためのガイドラインを提供します。特に、以下の点に焦点を当てます。

- 必ずloggingを使うこと

---

1. 例外の握りつぶし・雑なexcept
AIは「とりあえず動かす」ためによくこんなコードを書きます。

```python
# Bad - AIがよく書くパターン
try:
    result = api_call()
    process_data(result)
except Exception:  # または bare except:
    pass  # エラーを無視
```

何が危険？
- エラーが見えなくなり、デバッグ不可能
- 想定外の例外まで隠してしまう
- 本番でサイレント障害の原因に

[ 修正例 ]

```python
# Good
import logging

logger = logging.getLogger(__name__)

try:
    result = api_call()
    process_data(result)
except APIError as e:
    logger.exception("API呼び出しに失敗: %s", e)
    raise  # 再発生させてエラーを隠さない
except DataProcessingError as e:
    logger.exception("データ処理に失敗: %s", e)
    # 必要に応じてデフォルト値を返すなど
    return default_response()
```

---

2. 可変デフォルト引数の罠
これもAIが頻繁に書く典型的なバグの温床です。
AIでなくても初心者がやりがち。

```python
# Bad
def add_item(item, bucket=[]):
    bucket.append(item)
    return bucket


# 実行すると...
list1 = add_item("a")  # ["a"]
list2 = add_item("b")  # ["a", "b"] ← 前の結果が残る！
```

何が危険？
- 関数呼び出し間で状態が共有されてしまう
- 予期しないデータ混入でバグの原因に
- デバッグが困難で本番で気づきにくい

[ 修正例 ]

```python
# Good
def add_item(item, bucket=None):
    if bucket is None:
        bucket = []
    bucket.append(item)
    return bucket
```

---

3. セキュリティ危険APIの安易な使用
AIは「動けばいい」で危険な関数を平気で使います。

```python
# Bad - 全部危険
eval(user_input)  # 任意コード実行
exec(code_string)  # 同上
subprocess.run(cmd, shell=True)  # コマンドインジェクション
yaml.load(data, Loader=yaml.Loader)  # 任意オブジェクト実行
pickle.loads(untrusted_data)  # 任意コード実行
requests.get(url, verify=False)  # TLS検証無効化
```

何が危険？
- 任意コード実行・システム乗っ取りのリスク
- 通信傍受・データ改ざんの脆弱性

> PickleはPython標準の便利な仕組みですが、外部から渡されたデータに使うと任意コード実行のリスクがあります。「自分で保存したものを自分で読み戻す」用途以外では避けてください。

> requests.get(..., verify=False) はSSL検証を無効化するため、中間者攻撃のリスクがあります。あくまでデバッグや社内プロキシ環境などに限定しましょう。

[ 修正例 ]

```python
# Good
import ast
import json
import subprocess
import yaml
import requests

# JSONは必ずjsonライブラリで
result = json.loads('{"key": "value"}')

# Pythonリテラルのみast.literal_eval
config = ast.literal_eval("{'debug': True, 'port': 8080}")

# シェル経由せずに直接実行（timeout必須）
completed = subprocess.run(["convert", input_file, output_file], check=True, timeout=30, capture_output=True, text=True)

# 安全なYAMLロード（信頼できる入力のみ）
data = yaml.safe_load(yaml_string)

# ネットワークI/Oはタイムアウト必須
response = requests.get(url, timeout=10)  # verify=Trueがデフォルト

# Pickleは任意コード実行を許す設計なので外部入力では使わない
# 代替: JSON、msgpack、protobufなど
```

---

4. SQLインジェクション・パス操作
古典的だけど今でもAIがやらかします。

```python
# Bad
import sqlite3


def get_user(name):
    cur.execute(f"SELECT * FROM users WHERE name='{name}'")


def read_file(filename):
    return open(f"/uploads/{filename}").read()
```

何が危険？
- SQLインジェクション：任意のSQL文が実行される
- パストラバーサル：../../../etc/passwdで機密ファイルアクセス
- データベース改ざん・システム乗っ取りのリスク

[ 修正例 ]

```python
# Good
from pathlib import Path


def get_user(name):
    cur.execute("SELECT * FROM users WHERE name = ?", (name,))


def read_file(filename):
    # エンコーディング明示＋パス正規化でディレクトリ脱出を防ぐ
    base = Path("uploads").resolve()
    target = (base / Path(filename).name).resolve()

    # Python 3.11+: 厳密なパスチェック
    if not target.is_relative_to(base):
        raise ValueError("Invalid path")

    return target.read_text(encoding="utf-8")
```

---

5. ログに秘密情報を出力
デバッグ用にとAIがよくやります。

```python
# Bad
logger.info(f"APIトークン: {token}")
logger.debug(f"パスワード: {password}")
print(f"クレジット情報: {credit_card}")
```

何が危険？
- ログからの認証情報漏洩
- コンプライアンス違反のリスク

[ 修正例 ]

```python
# Good
logger.info("認証完了")  # 秘密情報は出さない
logger.debug("ユーザーID: %s", user.id)  # IDのみ
# クレジット情報は下4桁のみ
logger.info("カード登録: ****%s", card_number[-4:])
```

---

6. 時刻・タイムゾーンの無自覚
AIは時刻処理が苦手で、よくこんなコードを書きます。

```python
# Bad
from datetime import datetime

now = datetime.now()  # ナイーブなdatetime
expiry = now + timedelta(days=1)
```

何が危険？
- サーバーとクライアントで時刻がずれる
- 夏時間切り替え時に予期しない動作
- 国際展開時にタイムゾーンバグが頻発

[ 修正例 ]

```python
# Good
from datetime import datetime, timezone, timedelta

# 必ずタイムゾーン付きで
now = datetime.now(timezone.utc)
expiry = now + timedelta(days=1)


# 保存はUTC、表示時にローカル変換
def format_for_user(utc_time, user_timezone):
    local_time = utc_time.astimezone(user_timezone)
    return local_time.strftime("%Y-%m-%d %H:%M")
```

---

7. 浮動小数点の直接比較
数値計算でAIがよくハマるパターン。

```python
# Bad
score = 0.1 + 0.1 + 0.1
if score == 0.3:  # False になることがある
    print("正解")
```

何が危険？
- 浮動小数点の丸め誤差で比較が失敗
- 金融系では計算結果が狂う重大バグ
- 条件分岐が期待通りに動かない

[修正例]

```python
# Good
import math

score = 0.1 + 0.1 + 0.1
if math.isclose(score, 0.3, rel_tol=1e-9):
    print("正解")

# 金銭計算はDecimalを使う（丸め方針も明示）
from decimal import Decimal, getcontext, ROUND_HALF_UP

getcontext().rounding = ROUND_HALF_UP

price = Decimal("19.99")
tax = Decimal("0.08")
total = price * (1 + tax)
```

---

8. Pandasの警告を無視したチェーン代入
データ分析でAIがよく書くけど警告が出るパターン。

```python
# Bad - SettingWithCopyWarningが出る
df[df.score > 80]["grade"] = "A"
```

何が危険？
- 元のデータが変更されない場合がある
- データ更新が反映されずサイレント障害
- 大規模データ処理で気づきにくいバグ

[ 修正例 ]

```python
# Good
mask = df.score > 80
df.loc[mask, "grade"] = "A"

# または
df = df.copy()  # 明示的にコピーしてから操作
df[df.score > 80]["grade"] = "A"
```

---

9. 非同期処理でのブロッキングI/O
async/awaitを使ってるのに中身がブロッキング。

```python
# Bad
import requests


async def fetch_data(url):
    response = requests.get(url)  # ブロッキング
    return response.json()
```

何が危険？
- 非同期の恩恵が全くない（むしろ遅い）
- イベントループがブロックされる
- 高負荷時にアプリケーション全体が停止

[ 修正例 ]

```python
# Good
import httpx


async def fetch_data(url):
    async with httpx.AsyncClient() as client:
        response = await client.get(url, timeout=10)
        response.raise_for_status()
        return response.json()
```

> httpx はサードパーティライブラリです。
> 使用するには pip install httpx を忘れずに。

---

10. リソースの未解放
AIはwith文を忘れがちです。

```python
# Bad
def process_file(path):
    f = open(path)
    data = f.read()  # closeし忘れ
    return data.upper()
```

何が危険？
- ファイルハンドルリーク
- "too many open files"エラーでアプリ停止
- メモリリークやリソース枯渇

[ 修正例 ]

```python
# Good
def process_file(path):
    with open(path, encoding="utf-8") as f:
        data = f.read()
    return data.upper()


# 複数リソースの場合
def copy_file(src, dst):
    with open(src, encoding="utf-8") as f_in, open(dst, "w", encoding="utf-8") as f_out:
        f_out.write(f_in.read())
```

---

11. ハードコードされた値
設定をコードに直書きするAI。

```python
# Bad
API_URL = "https://api.example.com"
MAX_RETRIES = 3
SECRET_KEY = "abc123"
```


何が危険？
- 環境切り替え時の設定ミス
- 秘密情報がソースコードに露出
- デプロイ時の設定変更で障害発生

[ 修正例 ]

```python
# Good
import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    api_url: str = "http://localhost:8000"
    max_retries: int = 3
    secret_key: str

    class Config:
        env_file = ".env"


settings = Settings()
```

> pydantic-settings はサードパーティライブラリです。
> 使用するには pip install pydantic-settings を忘れずに。

---

12. 存在しない引数・関数名（ハルシネーション）
AIが「ありそうな」APIを勝手に作ります。

```python
# Bad - pandas.DataFrame.save_to_csv()は存在しない
df.save_to_csv("output.csv")

# Bad - requests.get()にheader引数はない
requests.get(url, header={"Authorization": token})
```

何が危険？
- 実行時にAttributeErrorで即座にクラッシュ
- テストしていないとデプロイ後に発覚
- API仕様を間違えると予期しない動作

[ 修正例 ]

```python
# Good - 正しいAPI名
df.to_csv("output.csv", index=False)

# Good - 正しい引数名
requests.get(url, headers={"Authorization": f"Bearer {token}"})
```

> 不明なAPIや挙動は、必ず公式ドキュメントで確認してください。
> AIが生成したコードには「存在しないメソッド名」「誤った引数」が混じることがあります。

---

13. パフォーマンス地雷
AIが書く「一見動くけど遅い」コード。

```python
# Bad - 文字列結合
result = ""
for item in large_list:
    result += str(item)  # 毎回新しい文字列を作成

# Bad - 全ファイル読み込み
with open("huge_file.txt") as f:
    lines = f.read().split("\n")  # メモリを食い尽くす

# Bad - 二重ループ
matches = []
for a in list1:
    for b in list2:  # O(n²)
        if a.id == b.id:
            matches.append((a, b))
```

何が危険？
- 文字列結合：データ量に比例してメモリ使用量が爆発
- 大ファイル読み込み：OutOfMemoryErrorでアプリ停止
- 二重ループ：処理時間が二乗で増加し応答不能に

[ 修正例 ]

```python
## Good
result = "".join(str(item) for item in large_list)

# Good - ストリーミング処理
with open("huge_file.txt") as f:
    for line in f:  # 1行ずつ処理
        process_line(line.strip())

# Good - 辞書で高速化
lookup = {b.id: b for b in list2}
matches = [(a, lookup[a.id]) for a in list1 if a.id in lookup]
```

---

14. セキュリティ用途での一般乱数使用
暗号用途にrandomを使うAI。

```python
# Bad - セキュリティ用途には不適切
import random

token = "".join(random.choices("abcdefghijklmnopqrstuvwxyz", k=32))
```

何が危険？

- 予測可能な乱数でトークンが推測される
- セッションハイジャック・なりすましのリスク
- 暗号学的強度が不十分で攻撃を受ける

[ 修正例 ]

```python
# Good - 暗号学的に安全
import secrets

token = secrets.token_urlsafe(32)
password = secrets.token_hex(16)

# セキュアな比較（タイミング攻撃対策）
from hmac import compare_digest

if compare_digest(provided_token, expected_token):
    authenticate_user()
```

---

15. ログ出力でのf文字列使用
パフォーマンスが悪く、セキュリティリスクもあります。

```python
# Bad
logger.info(f"ユーザー {user.name} がログインしました")
logger.debug(f"処理時間: {elapsed:.2f}秒")
```

何が危険？
- ログレベルがoffでも文字列フォーマットが実行される
- 大量ログ出力時にCPU使用率が上昇
- ログフォーマット処理がパフォーマンスボトルネックに

[ 修正例 ]

```python
# Good - 遅延フォーマット
logger.info("ユーザー %s がログインしました", user.name)
logger.debug("処理時間: %.2f秒", elapsed)

# ログレベルがoffの時はフォーマット処理されない
```

---

生成AIは確かに開発を加速してくれますが、「動くコード」と「安全なコード」は別物です。特に本番環境に投入する前には、ぜひこのチェックリストで最低限の安全確認をしてみてください。
