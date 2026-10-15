from datetime import datetime

from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


class User(db.Model):
    """ログイン可能な全ロール（生徒・スクールカウンセラー・先生）共通のユーザーテーブル。

    管理者(admin)ロールは今回のログイン機能では未対応（将来対応）。
    """
    __tablename__ = 'users'

    ROLE_STUDENT = 'student'
    ROLE_COUNSELOR = 'counselor'
    ROLE_TEACHER = 'teacher'
    ROLE_ADMIN = 'admin'
    ROLES = [ROLE_STUDENT, ROLE_COUNSELOR, ROLE_TEACHER, ROLE_ADMIN]

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    display_name = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(20), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, raw_password):
        self.password_hash = generate_password_hash(raw_password)

    def check_password(self, raw_password):
        return check_password_hash(self.password_hash, raw_password)

    def __repr__(self):
        return f"<User {self.username} ({self.role})>"
