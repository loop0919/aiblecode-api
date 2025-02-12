from api.core.config import HOST, PORT

# 実行するPythonがあるパス
pythonpath = "./api/"

# ワーカー数
workers = 3

# ワーカーのクラス、*2 にあるようにUvicornWorkerを指定 (Uvicornがインストールされている必要がある)
worker_class = "uvicorn.workers.UvicornWorker"

# IPアドレスとポート
bind = f"{HOST}:{PORT}"

# プロセスIDを保存するファイル名
pidfile = "prod.pid"

# Pythonアプリに渡す環境変数
raw_env = ["MODE=PROD"]

# デーモン化する場合はTrue
daemon = True

# エラーログ
errorlog = "./logs/error_log.txt"

# プロセスの名前
proc_name = "aiblecode_api"

# アクセスログ
accesslog = "./logs/access_log.txt"
