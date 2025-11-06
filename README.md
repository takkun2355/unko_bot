[![Deploy to Koyeb](https://www.koyeb.com/static/images/deploy/button.svg)](https://app.koyeb.com/deploy?name=discord-bot&type=git&repository=akikukeo%2FDiscord-Bot&branch=main&workdir=.%2Fapp&builder=dockerfile&privileged=true&instance_type=free&regions=was&instances_min=0&autoscaling_sleep_idle_delay=300&env%5BDISCORD_BOT_TOKEN%5D=MTQxNjcxODc2NjIwMDMyODI4Mw.GLxk_-.qcgWMuJ86AsmQV70dU-m3JuFXquTYDSJB4afgY&ports=8000%3Bhttp%3B%2F%3Btrue)

Dockerを利用してBOTを起動します。

~~秘密情報の流出を防止するため、DockerImageにはソースコードが含まれていません。
そのため、BOTの実行時には、依存関係のインストール、ソースコードのマウントなどが必要です。~~

```powershell
docker run -it --rm \
  -v ${PWD}:/app \
  -w /app \
  -e DISCORD_BOT_TOKEN="YOUR_DISCORD_BOT_TOKEN" \
  python:3.13-slim ./script/start_bot.sh
```
```bash
docker run -it --rm \
  -v ${PWD}:/app \
  -w /app \
  -e DISCORD_BOT_TOKEN="YOUR_DISCORD_BOT_TOKEN" \
  python:3.13-slim ./script/start_bot.sh
```

Dockerfileからビルドすると含まれます。

---

## 運用・管理ツール (`bot_manager.py`)

`bot_manager.py` は、Botの起動、停止、アップデートなどを対話形式で簡単に行うためのコマンドラインツールです。

### 主な機能

- **Botのライフサイクル管理**: `start`, `stop`, `restart` コマンドでBotを制御します。
- **Botへのコマンド送信**: `talk`, `hello` などのデバッグ用コマンドをBot本体に直接送信できます。
- **安全なアップデート機能**: GitHubリポジトリの最新の**リリース**を検知し、簡単なコマンドで安全にBotを更新できます。

### セットアップと起動

#### 1. 前提条件
- [Python](https://www.python.org/) 3.13以上
- [Git](https://git-scm.com/) がインストールされ、PATHが通っていること。
- できれば： [Docker](https://www.docker.com/) がインストールされていること。

#### 2. インストール
リポジトリをクローンし、必要なライブラリをインストールします。
```bash
git clone https://github.com/akikukeo/Discord-Bot.git
cd Discord-Bot
pip install -r requirements.txt
```

#### 3. 設定
プロジェクトのルートディレクトリに `.env` という名前のファイルを作成し、Discord Botのトークンを記述します。
```
DISCORD_BOT_TOKEN="ここにあなたのBotトークンを貼り付けます"
```

#### 4. 起動
以下のコマンドで管理ツールを起動します。
```bash
python bot_manager.py
```
起動すると、現在のBotのステータスや利用可能なコマンドが表示されます。

### アップデート機能について

このツールのアップデート機能は、開発の最先端（最新コミット）ではなく、安定版としてリリースされたバージョンを追跡します。

- **仕組み**: ツール起動時に、GitHubリポジトリの「リリース」ページを自動で確認し、ローカルのバージョン（Gitタグ）と比較します。新しいバージョンがリリースされている場合は、メニュー画面で通知されます。
- **実行**: `update` コマンドを入力すると、最新リリースのバージョンに更新するか確認のプロンプトが表示されます。`y`を入力すると、更新が実行され、Botは自動で再起動します。
- **安全性**: このプロセスは、ローカルの変更を上書きする可能性があるため、実行前に確認を求めます。また、`git checkout` を使用して特定のリリースバージョンに切り替えるため、`detached HEAD`状態になります。

### 開発者向け: リリース手順

このアップデート機能を正しく動作させるためには、以下の手順でGitHub上でリリースを作成する必要があります。

1.  **バージョンの決定**: [セマンティックバージョニング](https://semver.org/lang/ja/)（例: `v1.0.0`, `v1.1.0`）に従って、新しいバージョン番号を決定します。
2.  **Gitタグの作成**: ローカルでリリースしたいコミットに対して、決定したバージョン番号でタグを付けます。
    ```bash
    # 例: v1.2.3 というタグを作成
    git tag v1.2.3
    ```
3.  **タグのプッシュ**: 作成したタグをリモートリポジトリにプッシュします。
    ```bash
    # すべてのタグをプッシュ
    git push origin --tags
    ```
4.  **GitHubリリースの作成**:
    - GitHubリポジトリの「Releases」ページに移動します。
    - 「Draft a new release」をクリックします。
    - 先ほどプッシュしたタグを「Choose a tag」から選択します。
    - リリースノート（変更点など）を記述し、「Publish release」をクリックして公開します。

この手順により、`bot_manager.py`が新しいバージョンを検知できるようになります。

```

a
