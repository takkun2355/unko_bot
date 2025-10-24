# ベースイメージ
FROM python:3.13-slim

# 環境変数
ENV PYTHONUNBUFFERED=1
ENV TERM=xterm

# 作業ディレクトリ
WORKDIR /app

# 必要なツールをインストール
RUN apt-get update && apt-get install -y \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 依存関係をコピーしてインストール
COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Bot のソースコードをコピー
COPY . .

# コンテナ起動時に bot.py を実行
CMD ["python", "bot.py"]

