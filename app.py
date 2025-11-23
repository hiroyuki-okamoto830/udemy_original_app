# app.py
# -*- coding: utf-8 -*-
"""
Render（無料プラン）で動かせる最小構成の ToDo 管理アプリ
Flask + SQLAlchemy + Render PostgreSQL（DATABASE_URL）
単一ファイル構成。1ページで「一覧＋新規登録」を実装。
"""

import os
from datetime import datetime
from flask import Flask, request, redirect, render_template_string
from sqlalchemy import Column, Integer, String, Text, Date, DateTime
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, Session
from sqlalchemy.orm import declarative_base, sessionmaker
from dotenv import load_dotenv

# ------------------------
# .env の読み込み（ローカル用）
# ------------------------
load_dotenv()

# ------------------------
# Flask アプリ作成
# ------------------------
app = Flask(__name__)

# -------------------------------------------------
#  ★ db_init.py と同じ DB URL に固定（ここが重要）
# -------------------------------------------------
DATABASE_URL = (
    "postgresql+psycopg2://"
    "todolist_mvpv_user:BwWye7JQp52RkMDAe0BJYKJYL35QGVjm@"
    "dpg-d4h8ai2dbo4c73bafql0-a.singapore-postgres.render.com/"
    "todolist_mvpv"
    "?sslmode=require"
)

engine = create_engine(DATABASE_URL, pool_pre_ping=True)


class Base(DeclarativeBase):
    pass

# ------------------------
# SQLAlchemy 初期化
# ------------------------
engine = create_engine(DATABASE_URL, echo=False, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()

# ------------------------
# モデル定義
# ------------------------
class Todo(Base):
    __tablename__ = "todolist"

    id = Column(Integer, primary_key=True, autoincrement=True)
    task = Column(String(200), nullable=False)
    description = Column(Text)
    due = Column(Date)
    submission_destination = Column(String(200), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

# 起動時にテーブル作成
Base.metadata.create_all(engine)

# ------------------------
# HTMLテンプレート（1ファイル完結）
# ------------------------
HTML = """
<!doctype html>
<html lang="ja">
<head>
<meta charset="utf-8">
<title>ToDo管理アプリ（Render）</title>
<style>
body { font-family: sans-serif; margin: 30px; }
h1 { margin-bottom: 10px; }
.container { display: flex; gap: 40px; }
.form-box, .list-box { width: 50%; }
label { display: block; margin-top: 10px; }
input[type=text], input[type=date], textarea {
    width: 100%; padding: 8px; margin-top: 4px;
}
button { margin-top: 15px; padding: 8px 16px; }
.error { background: #ffdede; padding: 10px; margin-bottom: 15px; }
table { border-collapse: collapse; width: 100%; margin-top: 10px; }
th, td { border: 1px solid #ccc; padding: 6px; }
th { background: #f0f0f0; }
</style>
</head>
<body>

<h1>ToDo管理アプリ（Render版）</h1>

{% if errors %}
<div class="error">
  <strong>入力エラーがあります：</strong>
  <ul>
    {% for e in errors %}
    <li>{{ e }}</li>
    {% endfor %}
  </ul>
</div>
{% endif %}

<div class="container">
  <!-- 左：フォーム -->
  <div class="form-box">
    <h2>新規ToDo追加</h2>
    <form method="POST">
      <label>タスク（必須）
        <input type="text" name="task" value="{{ form.task }}">
      </label>

      <label>詳細説明
        <textarea name="description">{{ form.description }}</textarea>
      </label>

      <label>期日
        <input type="date" name="due" value="{{ form.due }}">
      </label>

      <label>提出先（必須）
        <input type="text" name="submission_destination" value="{{ form.submission_destination }}">
      </label>

      <button type="submit">登録する</button>
    </form>
  </div>

  <!-- 右：一覧 -->
  <div class="list-box">
    <h2>ToDo一覧（期日が近い順）</h2>
    <table>
      <tr>
        <th>ID</th>
        <th>タスク</th>
        <th>期日</th>
        <th>提出先</th>
        <th>作成日</th>
      </tr>
      {% for item in todos %}
      <tr>
        <td>{{ item.id }}</td>
        <td>{{ item.task }}</td>
        <td>{{ item.due }}</td>
        <td>{{ item.submission_destination }}</td>
        <td>{{ item.created_at.strftime("%Y-%m-%d") }}</td>
      </tr>
      {% endfor %}
    </table>
  </div>
</div>

</body>
</html>
"""

# ------------------------
# ルート1本で 全機能（一覧＋登録）
# ------------------------
@app.route("/", methods=["GET", "POST"])
def index():
    session = SessionLocal()
    errors = []
    form_data = {
        "task": "",
        "description": "",
        "due": "",
        "submission_destination": "",
    }

    try:
        if request.method == "POST":
            # 入力値取得
            task = request.form.get("task", "").strip()
            description = request.form.get("description", "").strip()
            due_str = request.form.get("due", "").strip()
            submission_destination = request.form.get("submission_destination", "").strip()

            # バリデーション
            form_data.update({
                "task": task,
                "description": description,
                "due": due_str,
                "submission_destination": submission_destination,
            })

            if not task:
                errors.append("タスクは必須です。")

            # if not submission_destination:
            #     errors.append("提出先は必須です。")

            due_date = None
            if due_str:
                try:
                    due_date = datetime.strptime(due_str, "%Y-%m-%d").date()
                except ValueError:
                    errors.append("期日の日付形式が正しくありません。")

            # エラーなし → 登録
            if not errors:
                new_todo = Todo(
                    task=task,
                    description=description,
                    due=due_date,
                    submission_destination=submission_destination,
                )
                session.add(new_todo)
                session.commit()
                session.close()
                return redirect("/")  # PRG パターン
        else:
            # GET: フォーム初期化
            pass

        # 一覧取得（期日が近い順：NULL は後ろの方）
        todos = session.query(Todo).order_by(Todo.due.is_(None), Todo.due.asc()).all()

        return render_template_string(
            HTML, todos=todos, errors=errors, form=form_data
        )

    finally:
        session.close()

# ------------------------
# アプリ起動
# ------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    debug = os.environ.get("DEBUG", "false").lower() == "true"
    app.run(host="0.0.0.0", port=port, debug=debug)
