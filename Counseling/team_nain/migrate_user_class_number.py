"""users テーブルに「出席番号 (class_number)」の列を追加するスクリプト。

実行方法:
    python migrate_user_class_number.py              # counseling.db を更新
    python migrate_user_class_number.py my_dev.db    # 別のDBを更新する場合

- 列がまだ無ければ追加する (何回実行しても大丈夫)
- 出席番号は重複ありなので、一意制約は付けない
- 既存のユーザーの出席番号は空 (NULL) のまま
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
        columns = [row[1] for row in conn.execute("PRAGMA table_info(users)")]
        if not columns:
            print("users テーブルがありません。先に python seed.py を実行してください。")
            sys.exit(1)

        if "class_number" in columns:
            print("class_number (出席番号) の列はすでにあります。")
        else:
            conn.execute("ALTER TABLE users ADD COLUMN class_number INTEGER")
            conn.commit()
            print("class_number (出席番号) の列を追加しました。")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
