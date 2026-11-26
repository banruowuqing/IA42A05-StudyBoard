import os
import uuid
from datetime import datetime, timedelta, timezone

from flask import Flask, render_template, request, redirect, url_for
from azure.data.tables import TableServiceClient

app = Flask(__name__)

# 日本時間
JST = timezone(timedelta(hours=9))

# Azure Table Storageの設定
CONNECTION_STRING = os.environ.get(
    "AZURE_STORAGE_CONNECTION_STRING", ""
)

TABLE_NAME = "posts"

table = None
messages = []

# 接続文字列がある場合
if CONNECTION_STRING:
    service = TableServiceClient.from_connection_string(
        CONNECTION_STRING
    )

    table = service.create_table_if_not_exists(TABLE_NAME)


# トップページ
@app.route("/")
def index():
    return app.send_static_file("index.html")


# 掲示板ページ
@app.route("/board")
def board():

    # Azure Table Storageを使う場合
    if table is not None:
        posts = list(table.list_entities())

    # Azure Table Storageを使わない場合
    else:
        posts = messages

    # 新しい投稿を先に表示する
    posts.sort(
        key=lambda m: m["posted_at"],
        reverse=True
    )

    return render_template(
        "board.html",
        messages=posts
    )


# 投稿する
@app.route("/post", methods=["POST"])
def post():

    # フォームから値を受け取る
    name = request.form.get("name", "").strip()
    category = request.form.get("category", "勉強")
    text = request.form.get("message", "").strip()

    # 名前がない場合
    if not name:
        name = "名無し"

    # 文字数の確認
    name = name[:30]
    text = text[:500]

    if category not in ["勉強", "テスト", "学校生活", "相談"]:
        category = "勉強"

    # メッセージがある場合
    if text:

        data = {
            "PartitionKey": "board",
            "RowKey": str(uuid.uuid4()),
            "name": name,
            "category": category,
            "text": text,
            "posted_at": datetime.now(JST).strftime(
                "%Y/%m/%d %H:%M:%S"
            )
        }

        # Azure Table Storageに保存
        if table is not None:
            table.create_entity(data)

        # リストに保存
        else:
            messages.append(data)

    # 掲示板に戻る
    return redirect(url_for("board"))


if __name__ == "__main__":
    app.run(debug=True)