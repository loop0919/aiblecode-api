# AIbleCode-API

AIbleCodeのバックエンド＆APIエンドポイントです。

---

## 環境
以下の条件を満たす環境で動作するはずです。
- Bashシェルが使える（ubuntu-22.04、amazon linux 2023 で動作を確認済み）
- Python3 や pip が使える

---

## 依存関係
ジャッジサーバーとして、[Judge0 API](https://ce.judge0.com/) を使うようになってます。

---

## 始め方

1. `.env-dummy` を `.env` に変更し、以下の内容を記入する。

```.env
HOST="[起動するサーバーのホスト名]" # デフォルト: localhost
PORT=[起動するサーバーのポート番号] # デフォルト: 8888

SECRET_KEY="[JWTトークン用のシークレットキー（ランダム値）]"
ALGORITHM="[JWTトークン用のアルゴリズム]"
ACCESS_TOKEN_EXPIRE_MINUTES=[トークンの期限切れ時間（分）]

ADMIN_USERNAME="[管理者のユーザー名]"
ADMIN_PASSWORD="[管理者のパスワード]"

JUDGE_API_URL="[ジャッジサーバーのAPIのURL]"

DATABASE_URL="[DBサーバーのURL]"
GEMINI_API_KEY="[Gemini（生成AI）のAPIキー]"
```

2. 以下のコマンドを実行する。
```bash
$ pip install -r requirements.txt
$ python3 ./migrate_db.py # 初回起動時 or データベースをリセットするときのみ
$ python3 ./main.py
```

3. http://localhost:8888/api/docs （http://[HOST]:[PORT] に適宜変える）を見よう！

---

## 使い方

- 初回起動時は管理者のユーザー名・パスワードでログインするか、`/sign_up` でユーザー登録＆ `/token` でログインすると良いかも。

- 管理者ログインをして `/create_category` や `/create_problem` 、 `/create_testcase` で問題を作れます。
  - [AIbleCode-Problem](https://github.com/loop0919/aiblecode-problem) を使うと効率的に問題が作れると思います。

- ジャッジサーバーが生きていれば提出もできます。

- データベースをリセットしたいときは、
  ```bash
  $ python3 ./migrate_db.py
  ```
  をしましょう。
