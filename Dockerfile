# Python 3.13.7 公式イメージ
FROM python:3.13.7

# 作業ディレクトリ
WORKDIR /app

# OS パッケージ更新（脆弱性軽減）
RUN apt-get update && apt-get upgrade -y && apt-get clean && rm -rf /var/lib/apt/lists/*

COPY . /app

# 1. 依存関係のインストール
RUN pip install -r requirements.txt

CMD [ "./script/start_bot.sh" ]
