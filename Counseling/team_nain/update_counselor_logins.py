"""今いるカウンセラーのログインID と初期パスワードを、新しい決め方に合わせるスクリプト。

実行方法:
    python update_counselor_logins.py

- ログインID: C + ふりがなのローマ字 (空白は _ 。例: わたなべ ゆうすけ → Cwatanabe_yuusuke)
- パスワード: ログインID と同じにする
- ふりがなが登録されていないカウンセラーは変えずにとばす
- すでに新しい決め方の ID になっている人はとばす (何回実行しても大丈夫)
"""
from app import app, _counselor_username, _kana_to_romaji
from models import db, User


def main():
    with app.app_context():
        counselors = User.query.filter_by(role=User.ROLE_COUNSELOR).order_by(User.id).all()
        changed = 0
        for counselor in counselors:
            profile = counselor.counselor_profile
            kana = profile.kana if profile else None
            if not kana or not _kana_to_romaji(kana):
                print(f"とばしました (ふりがな無し): {counselor.display_name} ({counselor.username})")
                continue

            base = "C" + _kana_to_romaji(kana)
            # 2人目以降に付く番号 (Cwatanabe_yuusuke2 など) も、すでに新しい ID とみなす
            rest = counselor.username[len(base):]
            if counselor.username.startswith(base) and (rest == "" or rest.isdigit()):
                print(f"変更なし: {counselor.display_name} ({counselor.username})")
                continue

            old = counselor.username
            counselor.username = _counselor_username(kana)
            counselor.set_password(counselor.username)
            db.session.flush()
            changed += 1
            print(f"変更しました: {counselor.display_name}  {old} → {counselor.username} (パスワードも同じ)")

        db.session.commit()
        print(f"{changed} 人のログインID とパスワードを変えました。")


if __name__ == "__main__":
    main()
