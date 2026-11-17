"""カウンセラーのプロフィール用テーブル (counselor_profiles) を作るスクリプト。

実行方法:
    python migrate_counselor_profiles.py              # counseling.db を更新
    python migrate_counselor_profiles.py my_dev.db    # 別のDBを更新する場合

- テーブルがまだ無ければ作る (何回実行しても大丈夫)
- すでにテーブルがあって年齢 (age)・ふりがな (kana) の列が無ければ、列を足す
- 列: counselor_id (主キー。カウンセラーの users.id) / image (画像) / kana (ふりがな) / gender (性別)
      / age (年齢) / comment (コメント) / updated_at (更新日時)
- 中身は空のまま (既存のカウンセラーの行は作らない)
"""
import os
import sqlite3
import sys

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


def main():
    db_name = sys.argv[1] if len(sys.argv) > 1 else "counseling.db"
    db_path = db_name if os.path.isabs(db_name) else os.path.join(BASE_DIR, db_name)
    if not os.path.exists(db_path):
        print(f"DBが見つかりません: {db_path}")
        sys.exit(1)

    conn = sqlite3.connect(db_path)
    try:
        if not conn.execute("PRAGMA table_info(users)").fetchall():
            print("users テーブルがありません。先に python seed.py を実行してください。")
            sys.exit(1)

        exists = conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'counselor_profiles'"
        ).fetchone()
        if exists:
            print("counselor_profiles テーブルはすでにあります。")
            # 先にテーブルだけ作った人向け: 後から増えた列が無ければ足す
            columns = [row[1] for row in conn.execute("PRAGMA table_info(counselor_profiles)")]
            for name, column_type, label in [("age", "INTEGER", "年齢"), ("kana", "VARCHAR(100)", "ふりがな")]:
                if name not in columns:
                    conn.execute(f"ALTER TABLE counselor_profiles ADD COLUMN {name} {column_type}")
                    conn.commit()
                    print(f"{name} ({label}) の列を追加しました。")
            return

        conn.execute(
            """
            CREATE TABLE counselor_profiles (
                counselor_id INTEGER NOT NULL PRIMARY KEY,
                image VARCHAR(255),
                kana VARCHAR(100),
                gender VARCHAR(10),
                age INTEGER,
                comment TEXT,
                updated_at DATETIME,
                FOREIGN KEY (counselor_id) REFERENCES users (id)
            )
            """
        )
        conn.commit()
        print("counselor_profiles テーブルを作りました。")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
