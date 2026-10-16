"""初期ユーザーデータ投入スクリプト。

実行方法:
    python seed.py

テーブルが無ければ作成し、検証用アカウント（生徒・スクールカウンセラー・先生）を登録する。
"""
from datetime import date, time, timedelta

from app import app
from models import db, User, AvailableSlot, Reservation, Class

SAMPLE_USERS = [
    {
        'username': 'student01',
        'password': 'student123',
        'display_name': '山田 太郎',
        'role': User.ROLE_STUDENT,
    },
    {
        'username': 'counselor01',
        'password': 'counselor123',
        'display_name': '佐藤 花子',
        'role': User.ROLE_COUNSELOR,
    },
    {
        'username': 'teacher01',
        'password': 'teacher123',
        'display_name': '鈴木 一郎',
        'role': User.ROLE_TEACHER,
    },
]


def run():
    with app.app_context():
        db.create_all()

        for data in SAMPLE_USERS:
            if User.query.filter_by(username=data['username']).first():
                continue
            user = User(
                username=data['username'],
                display_name=data['display_name'],
                role=data['role'],
            )
            user.set_password(data['password'])
            db.session.add(user)

        db.session.commit()
        print("初期ユーザーを登録しました:")
        for data in SAMPLE_USERS:
            print(f"  - {data['role']}: {data['username']} / {data['password']}")

        counselor = User.query.filter_by(username='counselor01').first()
        student = User.query.filter_by(username='student01').first()
        teacher = User.query.filter_by(username='teacher01').first()

        if not Class.query.filter_by(name='1年A組').first():
            school_class = Class(name='1年A組')
            db.session.add(school_class)
            db.session.flush()

            if teacher:
                teacher.class_id = school_class.id
            if student:
                student.class_id = school_class.id

            db.session.commit()
            print("クラスのサンプルデータを登録しました。")

        if counselor and not AvailableSlot.query.filter_by(counselor_id=counselor.id).first():
            today = date.today()
            booked_slot = AvailableSlot(
                counselor_id=counselor.id,
                date=today + timedelta(days=2),
                start_time=time(10, 0),
                end_time=time(10, 30),
            )
            free_slot = AvailableSlot(
                counselor_id=counselor.id,
                date=today + timedelta(days=3),
                start_time=time(13, 0),
                end_time=time(13, 30),
            )
            db.session.add_all([booked_slot, free_slot])
            db.session.flush()

            if student:
                db.session.add(Reservation(slot_id=booked_slot.id, student_id=student.id))

            db.session.commit()
            print("面談可能日時のサンプルデータを登録しました。")


if __name__ == '__main__':
    run()
