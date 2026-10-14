"""初期ユーザーデータ投入スクリプト。

実行方法:
    python seed.py

テーブルが無ければ作成し、検証用アカウント（生徒・スクールカウンセラー・先生）を登録する。
"""
from app import app
from models import db, User

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


if __name__ == '__main__':
    run()
