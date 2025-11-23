# db_init.py
from sqlalchemy import create_engine, text
import os

DATABASE_URL = os.environ.get("DATABASE_URL")
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+psycopg2://", 1)

if not DATABASE_URL:
    raise RuntimeError("環境変数 DATABASE_URL が設定されていません。")

engine = create_engine(DATABASE_URL, pool_pre_ping=True)

schema_sql = """
CREATE TABLE IF NOT EXISTS todolist (
  id SERIAL PRIMARY KEY,
  task VARCHAR(200) NOT NULL,
  description TEXT,
  due DATE,
  submission_destination VARCHAR(200),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
"""

seed_sql = """
INSERT INTO todolist (task, description, due, submission_destination)
VALUES
  ('Render設定', 'Render の DB と Web Service を連携する', '2025-01-01', NULL),
  ('Flaskデプロイ', 'Flask アプリを Render へ公開する', '2025-01-02', NULL);
"""

with engine.begin() as conn:
    conn.execute(text(schema_sql))
    count = conn.execute(text("SELECT COUNT(*) FROM todolist")).scalar_one()

    if count == 0:
        conn.execute(text(seed_sql))

print("OK: todolist テーブル作成 & 初期データ投入完了")
