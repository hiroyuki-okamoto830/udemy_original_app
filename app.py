# app.py
# -*- coding: utf-8 -*-
"""
ToDo 管理アプリ（Render 用）
- 新規追加（UI縦揃え）
- 一覧表示
- 削除
- 編集（モーダルウインドウ UI縦揃え）
"""

import os
from datetime import datetime
from flask import Flask, request, redirect, render_template_string
from sqlalchemy import Column, Integer, String, Text, Date, DateTime
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)

# -------------------------------------------------
# DB URL（あなたの固定URL）
# -------------------------------------------------
DATABASE_URL = (
    "postgresql+psycopg2://"
    "todolist_mvpv_user:BwWye7JQp52RkMDAe0BJYKJYL35QGVjm@"
    "dpg-d4h8ai2dbo4c73bafql0-a.singapore-postgres.render.com/"
    "todolist_mvpv"
    "?sslmode=require"
)

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()

# -----------------------------
# モデル
# -----------------------------
class Todo(Base):
    __tablename__ = "todolist"

    id = Column(Integer, primary_key=True, autoincrement=True)
    task = Column(String(200), nullable=False)
    description = Column(Text)
    due = Column(Date)
    submission_destination = Column(String(200))
    created_at = Column(DateTime, default=datetime.utcnow)

Base.metadata.create_all(engine)


# -----------------------------
# HTML（モーダルUIも縦揃えに修正）
# -----------------------------
HTML = """
<!doctype html>
<html lang="ja">
<head>
<meta charset="utf-8">
<title>ToDo管理アプリ</title>
<style>
body { font-family: sans-serif; margin: 30px; }
.container { display: flex; gap: 40px; }

/* 左カラム：縦揃えフォーム */
.form-box form {
  display: flex;
  flex-direction: column;
  width: 100%;
}
.form-box label {
  display: block;
  margin-bottom: 15px;
}
.form-box label span {
  display: inline-block;
  margin-bottom: 6px;
  font-weight: bold;
}
.form-box input[type=text],
.form-box input[type=date],
.form-box textarea {
  width: 100%;
  padding: 8px;
  box-sizing: border-box;
}

/* モーダル（縦揃えフォーム） */
.modal-overlay {
  position: fixed; top:0; left:0; right:0; bottom:0;
  background: rgba(0,0,0,0.4);
  display:none; justify-content:center; align-items:center;
}
.modal {
  background:#fff; padding:20px; width:400px; border-radius:8px;
}
.modal form {
  display: flex;
  flex-direction: column;
}
.modal label {
  display: block;
  margin-bottom: 15px;
}
.modal label span {
  display: inline-block;
  margin-bottom: 6px;
  font-weight: bold;
}
.modal input[type=text],
.modal input[type=date],
.modal textarea {
  width: 100%;
  padding: 8px;
  box-sizing: border-box;
}
.close-btn { float:right; cursor:pointer; font-size:18px; }

/* 一覧 */
table { border-collapse: collapse; width: 100%; }
th, td { border: 1px solid #ccc; padding: 6px; }
th { background: #f0f0f0; }

</style>
</head>
<body>

<h1>ToDo管理アプリ</h1>

<div class="container">

  <!-- 新規登録フォーム -->
  <div class="form-box">
    <h2>新規ToDo追加</h2>
    <form method="POST">
      <label>
        <span>タスク</span>
        <input type="text" name="task">
      </label>

      <label>
        <span>詳細説明</span>
        <textarea name="description"></textarea>
      </label>

      <label>
        <span>期日</span>
        <input type="date" name="due">
      </label>

      <label>
        <span>提出先</span>
        <input type="text" name="submission_destination">
      </label>

      <button type="submit">登録</button>
    </form>
  </div>


  <!-- 一覧 -->
  <div class="list-box">
    <h2>ToDo一覧</h2>
    <table>
      <tr>
        <th>ID</th><th>タスク</th><th>説明</th><th>期日</th><th>提出先</th><th>編集</th><th>削除</th>
      </tr>

      {% for item in todos %}
      <tr>
        <td>{{ item.id }}</td>
        <td>{{ item.task }}</td>
        <td>{{ item.description or "" }}</td>
        <td>{{ item.due }}</td>
        <td>{{ item.submission_destination or "" }}</td>

        <!-- 編集（モーダル） -->
        <td>
          <button onclick='openEditModal(
            {{ {
              "id": item.id,
              "task": item.task,
              "description": item.description,
              "due": item.due|string if item.due else "",
              "submission_destination": item.submission_destination
            } | tojson }}
          )'>編集</button>
        </td>

        <!-- 削除 -->
        <td>
          <form method="POST" action="/delete/{{ item.id }}">
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

      <label>
        <span>タスク</span>
        <input type="text" name="task" id="edit_task">
      </label>

      <label>
        <span>詳細説明</span>
        <textarea name="description" id="edit_description"></textarea>
      </label>

      <label>
        <span>期日</span>
        <input type="date" name="due" id="edit_due">
      </label>

      <label>
        <span>提出先</span>
        <input type="text" name="submission_destination" id="edit_submission_destination">
      </label>

      <button type="submit">更新</button>
    </form>

  </div>
</div>

<script>
// --- 編集モーダル ---
function openEditModal(data) {
    document.getElementById("edit_task").value = data.task || "";
    document.getElementById("edit_description").value = data.description || "";
    document.getElementById("edit_due").value = data.due || "";
    document.getElementById("edit_submission_destination").value = data.submission_destination || "";

    document.getElementById("editForm").action = "/edit/" + data.id;
    document.getElementById("editModal").style.display = "flex";
}
function closeEditModal() {
    document.getElementById("editModal").style.display = "none";
}
</script>

</body>
</html>
"""


# -----------------------------
# 新規作成・一覧
# -----------------------------
@app.route("/", methods=["GET", "POST"])
def index():
    session = SessionLocal()
    try:
        if request.method == "POST":
            task = request.form.get("task", "").strip()
            description = request.form.get("description", "").strip()
            due_str = request.form.get("due", "").strip()
            sub = request.form.get("submission_destination", "").strip()

            if task:
                due = None
                if due_str:
                    try:
                        due = datetime.strptime(due_str, "%Y-%m-%d").date()
                    except:
                        pass

                session.add(Todo(
                    task=task,
                    description=description,
                    due=due,
                    submission_destination=sub or None
                ))
                session.commit()

        todos = session.query(Todo).order_by(Todo.due.is_(None), Todo.due.asc()).all()
        return render_template_string(HTML, todos=todos)

    finally:
        session.close()


# -----------------------------
# 編集
# -----------------------------
@app.route("/edit/<int:todo_id>", methods=["POST"])
def edit(todo_id):
    session = SessionLocal()
    try:
        item = session.query(Todo).filter_by(id=todo_id).first()
        if item:
            item.task = request.form.get("task", "").strip()
            item.description = request.form.get("description", "").strip()

            due_str = request.form.get("due", "").strip()
            item.due = None
            if due_str:
                try:
                    item.due = datetime.strptime(due_str, "%Y-%m-%d").date()
                except:
                    pass

            sub = request.form.get("submission_destination", "").strip()
            item.submission_destination = sub or None

            session.commit()
        return redirect("/")
    finally:
        session.close()


# -----------------------------
# 削除
# -----------------------------
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


# -----------------------------
# 起動
# -----------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    debug = os.environ.get("DEBUG", "false").lower() == "true"
    app.run(host="0.0.0.0", port=port, debug=debug)
