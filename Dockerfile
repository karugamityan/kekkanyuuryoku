FROM python:3.11 

# 作業ディレクトリを /bot に設定
WORKDIR /bot

# 依存関係を事前にインストール（キャッシュを活用）
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# 残りのファイルをコピー
COPY . . 

# 実行コマンドを修正
CMD ["python3", "/bot/main.py"]
