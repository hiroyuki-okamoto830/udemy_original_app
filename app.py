# app.py
# -*- coding: utf-8 -*-
"""
ToDo 管理アプリ（Render 用）
- 新規追加
- 一覧表示
- 削除
- 編集（モーダルウインドウ）
"""

import os
from datetime import datetime
from flask import Flask, request, redirect, render_template_string
from sqlalchemy import Column, Integer, String, Text, Date, DateTime
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, Session
from sqlalchemy.orm import declarative_base, sessionmaker
from dotenv import load_dotenv

load_dotenv()
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

engine = create_engine(DATABASE_URL, echo=False, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()

# ------------------------
# モデル
# ------------------------
class Todo(Base):
    __tablename__ = "todolist"

    id = Column(Integer, primary_key=True, autoincrement=True)
    task = Column(String(200), nullable=False)
    description = Column(Text)
    due = Column(Date)
    submission_destination = Column(String(200))
    created_at = Column(DateTime, default=datetime.utcnow)

Base.metadata.create_all(engine)

# ------------------------
# HTMLテンプレート（編集モーダル付き）
# ------------------------
HTML = """
<!doctype html>
<html lang="ja">
<head>
<meta charset="utf-8">
<title>ToDo管理アプリ</title>
<style>
body { font-family: sans-serif; margin: 30px; }
h1 { margin-bottom: 10px; }
.container { display: flex; gap: 40px; }
.form-box, .list-box { width: 50%; }
label { display: block; margin-top: 10px; }
input[type=text], input[type=date], textarea { width: 100%; padding: 8px; margin-top: 4px; }
button { margin-top: 8px; padding: 6px 12px; }
table { border-collapse: collapse; width: 100%; margin-top: 10px; }
th, td { border: 1px solid #ccc; padding: 6px; }
th { background: #f0f0f0; }

/* モーダル */
.modal-overlay {
  position: fixed;
  top:0; left:0; right:0; bottom:0;
  background: rgba(0,0,0,0.4);
  display:none;
  justify-content:center;
  align-items:center;
}
.modal {
  background: #fff;
  padding: 20px;
  width: 400px;
  border-radius: 8px;
}
.close-btn {
  float:right;
  cursor:pointer;
  font-size:18px;
}
</style>
</head>
<body>

<h1>ToDo管理アプリ（編集モーダル）</h1>

<div class="container">

  <!-- 新規登録フォーム -->
  <div class="form-box">
    <h2>新規ToDo追加</h2>
    <form method="POST">
      <label>タスク
        <input type="text" name="task" value="{{ form.task }}">
      </label>

      <label>詳細説明
        <textarea name="description">{{ form.description }}</textarea>
      </label>

      <label>期日
        <input type="date" name="due" value="{{ form.due }}">
      </label>

      <label>提出先（任意）
        <input type="text" name="submission_destination" value="{{ form.submission_destination }}">
      </label>

      <button type="submit">登録する</button>
    </form>
  </div>

  <!-- 一覧 -->
  <div class="list-box">
    <h2>ToDo一覧</h2>
    <table>
      <tr>
        <th>ID</th>
        <th>タスク</th>
        <th>説明</th>
        <th>期日</th>
        <th>提出先</th>
        <th>編集</th>
        <th>削除</th>
      </tr>
      {% for item in todos %}
      <tr>
        <td>{{ item.id }}</td>
        <td>{{ item.task }}</td>
        <td>{{ item.description or "" }}</td>
        <td>{{ item.due }}</td>
        <td>{{ item.submission_destination or "" }}</td>

        <!-- 編集ボタン（モーダル起動） -->
        <td>
          <button onclick="openEditModal({{ item.id }}, '{{ item.task|escape }}',
                                         `{{ item.description|escape }}`,
                                         '{{ item.due }}',
                                         '{{ item.submission_destination|escape }}')">
            編集
          </button>
        </td>

        <!-- 削除ボタン -->
        <td>
          <form method="POST" action="/delete/{{ item.id }}" style="display:inline;">
            <button type="submit" onclick="return confirm('削除しますか？');">削除</button>
          </form>
        </td>
      </tr>
      {% endfor %}
    </table>
  </div>

</div>

<!-- 編集モーダル -->
<div class="modal-overlay" id="editModal">
  <div class="modal">
    <span class="close-btn" onclick="closeEditModal()">✖</span>
    <h3>ToDo編集</h3>
    <form method="POST" id="editForm">
      <label>タスク
        <input type="text" name="task" id="edit_task">
      </label>

      <label>詳細説明
        <textarea name="description" id="edit_description"></textarea>
      </label>

      <label>期日
        <input type="date" name="due" id="edit_due">
      </label>

      <label>提出先
        <input type="text" name="submission_destination" id="edit_submission_destination">
      </label>

      <button type="submit">更新する</button>
    </form>
  </div>
</div>

<script>
function openEditModal(id, task, description, due, submission_destination) {
    document.getElementById("edit_task").value = task;
    document.getElementById("edit_description").value = description;
    document.getElementById("edit_due").value = due || "";
    document.getElementById("edit_submission_destination").value = submission_destination || "";

    document.getElementById("editForm").action = "/edit/" + id;
    document.getElementById("editModal").style.display = "flex";
}

function closeEditModal() {
    document.getElementById("editModal").style.display = "none";
}
</script>

</body>
</html>
"""

# ------------------------
# 一覧 + 新規登録
# ------------------------
@app.route("/", methods=["GET", "POST"])
def index():
    session = SessionLocal()
    form_data = {"task": "", "description": "", "due": "", "submission_destination": ""}
    errors = []

    try:
        if request.method == "POST":
            task = request.form.get("task", "").strip()
            description = request.form.get("description", "").strip()
            due_str = request.form.get("due", "").strip()
            submission_destination = request.form.get("submission_destination", "").strip()

            form_data.update({
                "task": task, "description": description,
                "due": due_str, "submission_destination": submission_destination,
            })

            if not task:
                errors.append("タスクは必須です。")

            due_date = None
            if due_str:
                try:
                    due_date = datetime.strptime(due_str, "%Y-%m-%d").date()
                except ValueError:
                    errors.append("日付形式が正しくありません。")

            if not errors:
                new = Todo(
                    task=task,
                    description=description,
                    due=due_date,
                    submission_destination=submission_destination or None,
                )
                session.add(new)
                session.commit()
                return redirect("/")

        todos = session.query(Todo).order_by(Todo.due.is_(None), Todo.due.asc()).all()
        return render_template_string(HTML, todos=todos, form=form_data, errors=errors)

    finally:
        session.close()

# ------------------------
# ToDo 削除
# ------------------------
@app.route("/delete/<int:todo_id>", methods=["POST"])
def delete(todo_id):
    session = SessionLocal()
    try:
        item = session.query(Todo).filter_by(id=todo_id).first()
        if item:
            session.delete(item)
            session.commit()
        return redirect("/")
    finally:
        session.close()

# ------------------------
# ToDo 編集（更新保存）
# ------------------------
@app.route("/edit/<int:todo_id>", methods=["POST"])
def edit(todo_id):
    session = SessionLocal()
    try:
        item = session.query(Todo).filter_by(id=todo_id).first()
        if not item:
            return redirect("/")

        task = request.form.get("task", "").strip()
        description = request.form.get("description", "").strip()
        due_str = request.form.get("due", "").strip()
        submission_destination = request.form.get("submission_destination", "").strip()

        if task:
            item.task = task
        item.description = description
        item.submission_destination = submission_destination or None

        item.due = None
        if due_str:
            try:
                item.due = datetime.strptime(due_str, "%Y-%m-%d").date()
            except:
                pass

        session.commit()
        return redirect("/")

    finally:
        session.close()

# ------------------------
# アプリ起動
# ------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    debug = os.environ.get("DEBUG", "false").lower() == "true"
    app.run(host="0.0.0.0", port=port, debug=debug)
