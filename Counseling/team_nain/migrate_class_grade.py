"""classes テーブルに「年 (grade)」「組 (section)」の列を追加するスクリプト。

実行方法:
    python migrate_class_grade.py              # counseling.db を更新
    python migrate_class_grade.py my_dev.db    # 別のDBを更新する場合

- 列がまだ無ければ追加する (何回実行しても大丈夫)
- 既存のクラスは name から年・組を入れる
    例: 1年A組 → 年 = 1、組 = A
        2年3組 → 年 = 2、組 = 3
- 「○年○組」の形でない name のクラスは、年・組を空 (NULL) のままにして表示する
"""
import os
import re
import sqlite3
import sys

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# 「数字 + 年 + (組の文字) + 組」の形
CLASS_NAME_PATTERN = re.compile(r"^\s*(\d+)\s*年\s*(.+?)\s*組\s*$")


def parse_class_name(name):
    """クラス名から (年, 組) を取り出す。形が合わなければ (None, None)"""
    match = CLASS_NAME_PATTERN.match(name or "")
    if not match:
        return None, None
    return int(match.group(1)), match.group(2)


def main():
    db_name = sys.argv[1] if len(sys.argv) > 1 else "counseling.db"
    db_path = db_name if os.path.isabs(db_name) else os.path.join(BASE_DIR, db_name)
    if not os.path.exists(db_path):
        print(f"DBが見つかりません: {db_path}")
        sys.exit(1)

    conn = sqlite3.connect(db_path)
    try:
        columns = [row[1] for row in conn.execute("PRAGMA table_info(classes)")]
        if not columns:
            print("classes テーブルがありません。先に python seed.py を実行してください。")
            sys.exit(1)

        if "grade" not in columns:
            conn.execute("ALTER TABLE classes ADD COLUMN grade INTEGER")
            print("grade (年) の列を追加しました。")
        if "section" not in columns:
            conn.execute("ALTER TABLE classes ADD COLUMN section VARCHAR(20)")
            print("section (組) の列を追加しました。")

        # 年・組がまだ入っていないクラスに、name から値を入れる
        rows = conn.execute(
            "SELECT id, name FROM classes WHERE grade IS NULL OR section IS NULL"
        ).fetchall()
        for class_id, name in rows:
            grade, section = parse_class_name(name)
            if grade is None:
                print(f"  そのまま (○年○組の形ではない): {name}")
                continue
            conn.execute(
                "UPDATE classes SET grade = ?, section = ? WHERE id = ?",
                (grade, section, class_id),
            )
            print(f"  {name} → 年: {grade} / 組: {section}")

        conn.commit()
        print("完了しました。")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
