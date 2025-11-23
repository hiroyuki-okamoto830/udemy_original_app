# app.py
# -*- coding: utf-8 -*-

import os
from datetime import datetime
from flask import Flask, request, redirect, render_template
from sqlalchemy import Column, Integer, String, Text, Date, DateTime
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# =========================================================
#  DB 接続設定（Render / ローカル対応）
# =========================================================
DATABASE_URL = os.environ.get("DATABASE_URL")

if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+psycopg2://", 1)

engine = create_engine(DATABASE_URL, echo=False, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()


# =========================================================
#  モデル定義（提出先は任意）
# =========================================================
class Todo(Base):
    __tablename__ = "todolist"

    id = Column(Integer, primary_key=True, autoincrement=True)
    task = Column(String(200), nullable=False)
    description = Column(Text)
    due = Column(Date)
    submission_destination = Column(String(200))
    created_at = Column(DateTime, default=datetime.utcnow)


Base.metadata.create_all(engine)


# =========================================================
# 新規投稿 & 一覧
# =========================================================
@app.route("/", methods=["GET", "POST"])
def index():
    session = SessionLocal()
    try:
        if request.method == "POST":
            task = request.form.get("task", "").strip()
            description = request.form.get("description", "").strip()
            due_str = request.form.get("due", "").strip()
            submission_destination = request.form.get("submission_destination", "").strip()

            if task:
                due_date = None
                if due_str:
                    try:
                        due_date = datetime.strptime(due_str, "%Y-%m-%d").date()
                    except:
                        pass

                new = Todo(
                    task=task,
                    description=description,
                    due=due_date,
                    submission_destination=submission_destination or None,
                )
                session.add(new)
                session.commit()

        todos = session.query(Todo).order_by(Todo.due.is_(None), Todo.due.asc()).all()
        return render_template("index.html", todos=todos)

    finally:
        session.close()


# =========================================================
# 編集保存
# =========================================================
@app.route("/edit/<int:todo_id>", methods=["POST"])
def edit(todo_id):
    session = SessionLocal()
    try:
        item = session.query(Todo).filter_by(id=todo_id).first()
        if not item:
            return redirect("/")

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


# =========================================================
# 削除
# =========================================================
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


# =========================================================
# アプリ起動
# =========================================================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    debug = os.environ.get("DEBUG", "false").lower() == "true"
    app.run(host="0.0.0.0", port=port, debug=debug)
