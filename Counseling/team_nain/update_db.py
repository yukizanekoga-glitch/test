"""
DBの構造を models.py に合わせる。

- 足りないテーブルを作る
- 足りない列を追加する(既存のデータは消えない・変えない)
- 実行前に counseling.db を自動でバックアップする

使い方 (Counseling/team_nain で):
    .venv/bin/python3 update_db.py

何度実行しても安全。変更がなければ何も起きない。
※ 列の「削除・型変更・名前変更」はしない。それは手作業で行う。
※ 追加した列の中身は空(NULL)。値を入れたい場合は別途UPDATEする。
"""
import os
import shutil
from datetime import datetime

from sqlalchemy import inspect, text

from datetime import timedelta

from app import app, BASE_DIR
from models import db, SurveyResponse


def main():
    with app.app_context():
        engine = db.engine

        # 1. バックアップ
        db_path = os.path.join(BASE_DIR, "counseling.db")
        if os.path.exists(db_path):
            backup = f"{db_path}.bak_{datetime.now():%Y%m%d_%H%M%S}"
            shutil.copy(db_path, backup)
            print("バックアップ:", os.path.basename(backup))

        # 2. 足りないテーブルを作る
        before = set(inspect(engine).get_table_names())
        db.create_all()
        after = set(inspect(engine).get_table_names())
        for name in sorted(after - before):
            print("テーブル追加:", name)

        # 3. 既存テーブルの足りない列を追加する
        insp = inspect(engine)
        added = 0
        for table in db.metadata.sorted_tables:
            if table.name not in before:
                continue  # 今作ったテーブルは列も揃っている
            have = {c["name"] for c in insp.get_columns(table.name)}
            for col in table.columns:
                if col.name in have:
                    continue
                col_type = col.type.compile(engine.dialect)
                with engine.begin() as conn:
                    conn.execute(
                        text(f'ALTER TABLE "{table.name}" ADD COLUMN "{col.name}" {col_type}')
                    )
                print("列追加:", table.name, col.name)
                added += 1

        # 4. アンケート回答の survey_date (その週の金曜日) を、空のものだけ created_at から埋める。
        #    同じ生徒・同じ週の回答が複数あるときは、いちばん新しい1件だけに入れる
        #    (残りは空のまま。1人1週1回の重複禁止を作れるようにするため)。
        filled = 0
        rows = SurveyResponse.query.order_by(SurveyResponse.created_at.desc()).all()
        used = {(r.student_id, r.survey_date) for r in rows if r.survey_date}
        for r in rows:
            if r.survey_date or not r.created_at:
                continue
            answered_on = (r.created_at + timedelta(hours=9)).date()  # created_at は UTC → 日本時間
            friday = answered_on - timedelta(days=answered_on.weekday()) + timedelta(days=4)
            if (r.student_id, friday) in used:
                continue
            r.survey_date = friday
            used.add((r.student_id, friday))
            filled += 1
        if filled:
            db.session.commit()
            print("survey_date を設定:", filled, "件")

        # 5. 足りないインデックス (1人1週1回の重複禁止など) を作る
        insp = inspect(engine)
        for table in db.metadata.sorted_tables:
            have_idx = {i["name"] for i in insp.get_indexes(table.name)}
            for index in table.indexes:
                if index.name and index.name not in have_idx:
                    index.create(bind=engine)
                    print("インデックス追加:", index.name)
                    added += 1

        if not (after - before) and not added and not filled:
            print("変更なし (DBはすでに最新)")
        else:
            print("完了")


if __name__ == "__main__":
    main()
