# db_init.py
from sqlalchemy import create_engine, text
import os

# --- app.py と同じ構造の DATABASE_URL を利用 ---
DATABASE_URL = os.environ.get("DATABASE_URL")
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+psycopg2://", 1)

if not DATABASE_URL:
    raise RuntimeError("環境変数 DATABASE_URL が設定されていません。")

engine = create_engine(DATABASE_URL, pool_pre_ping=True)

# --- ToDo アプリ用テーブル構造 ---
schema_sql = """
CREATE TABLE IF NOT EXISTS todolist (
  id SERIAL PRIMARY KEY,
  task VARCHAR(200) NOT NULL,
  description TEXT,
  due DATE,
  submission_destination VARCHAR(200) NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
"""

# --- 初期データ（任意） ---
seed_sql = """
INSERT INTO todolist (task, description, due, submission_destination)
VALUES
  (:t1, :d1, :due1, :sub1),
  (:t2, :d2, :due2, :sub2);
"""

with engine.begin() as conn:
    # テーブル作成
    conn.execute(text(schema_sql))

    # 件数確認
    count = conn.execute(text("SELECT COUNT(*) FROM todolist;")).scalar_one()

    # 初期データ投入（空のときだけ）
    if count == 0:
        conn.execute(
            text(seed_sql),
            dict(
                t1="初期タスク：Render設定",
                d1="Render の PostgreSQL と Web Service を連携する",
                due1="2025-01-01",
                sub1="自分",

                t2="初期タスク：Flaskデプロイ",
                d2="Flask アプリを Render の無料プランで公開",
                due2="2025-01-02",
                sub2="自分",
            ),
        )

print("OK: todolist テーブル作成と初期データ投入が完了しました。")
