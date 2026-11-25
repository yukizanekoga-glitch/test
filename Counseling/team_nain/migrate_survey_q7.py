"""今週のアンケートの回答テーブル (survey_responses) を、10問 (q1〜q10) から 7問 (q1〜q7) にするスクリプト。

実行方法:
    python migrate_survey_q7.py              # counseling.db を更新
    python migrate_survey_q7.py my_dev.db    # 別のDBを更新する場合

- q8〜q10 の列があれば、q1〜q7 だけの表に作り直す (何回実行しても大丈夫)
- 今ある回答は q1〜q7 と回答日時をそのまま残す (q8〜q10 の回答は消える)
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
        columns = [row[1] for row in conn.execute("PRAGMA table_info(survey_responses)")]
        if not columns:
            print("survey_responses テーブルがありません。先に python seed.py を実行してください。")
            sys.exit(1)
        if not {"q8", "q9", "q10"} & set(columns):
            print("survey_responses はすでに q1〜q7 です。")
            return

        count = conn.execute("SELECT COUNT(*) FROM survey_responses").fetchone()[0]
        kept = "id, student_id, q1, q2, q3, q4, q5, q6, q7, created_at"
        with conn:
            conn.execute("ALTER TABLE survey_responses RENAME TO survey_responses_old")
            conn.execute(
                """
                CREATE TABLE survey_responses (
                    id INTEGER NOT NULL,
                    student_id INTEGER NOT NULL,
                    q1 VARCHAR(50) NOT NULL,
                    q2 VARCHAR(50) NOT NULL,
                    q3 VARCHAR(50) NOT NULL,
                    q4 VARCHAR(50) NOT NULL,
                    q5 VARCHAR(50) NOT NULL,
                    q6 VARCHAR(50) NOT NULL,
                    q7 VARCHAR(50) NOT NULL,
                    created_at DATETIME,
                    PRIMARY KEY (id),
                    FOREIGN KEY(student_id) REFERENCES users (id)
                )
                """
            )
            conn.execute(f"INSERT INTO survey_responses ({kept}) SELECT {kept} FROM survey_responses_old")
            conn.execute("DROP TABLE survey_responses_old")
        print(f"survey_responses を q1〜q7 に作り直しました (回答 {count} 件はそのまま)。")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
