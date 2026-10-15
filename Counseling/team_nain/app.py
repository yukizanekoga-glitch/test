import os
from functools import wraps

from flask import Flask, render_template, redirect, url_for, request, session, flash
#######################
import subprocess
from threading import Timer
########################

from models import db, User

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
app.secret_key = 'dev-secret-key-change-in-production'
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(BASE_DIR, 'counseling.db')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

# ロールごとのログイン後トップ画面
ROLE_TOP_ENDPOINT = {
    User.ROLE_STUDENT: 'top',
    User.ROLE_COUNSELOR: 'care_top',
    User.ROLE_TEACHER: 'teacher_top',
}


def login_required(view):
    """ログイン済みでなければログイン画面へ戻す"""
    @wraps(view)
    def wrapped(*args, **kwargs):
        if 'user_id' not in session:
            flash('ログインしてください。')
            return redirect(url_for('login', next=request.path))
        return view(*args, **kwargs)
    return wrapped


def role_required(role):
    """指定ロール以外のユーザーはアクセスできないようにする"""
    def decorator(view):
        @wraps(view)
        @login_required
        def wrapped(*args, **kwargs):
            if session.get('role') != role:
                flash('このページへのアクセス権限がありません。')
                return redirect(url_for('login'))
            return view(*args, **kwargs)
        return wrapped
    return decorator


# =========================
# ログイン画面
# =========================

@app.route("/")
def index():
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        user = User.query.filter_by(username=username).first()

        if user is None or not user.check_password(password) or user.role == User.ROLE_ADMIN:
            flash("ユーザー名またはパスワードが正しくありません。")
            return render_template("login.html")

        session.clear()
        session["user_id"] = user.id
        session["username"] = user.username
        session["display_name"] = user.display_name
        session["role"] = user.role

        next_endpoint = ROLE_TOP_ENDPOINT.get(user.role, "login")
        return redirect(url_for(next_endpoint))

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# =========================
# 生徒トップ画面
# =========================

@app.route("/top")
@role_required(User.ROLE_STUDENT)
def top():
    return render_template("Student/top.html")


# =========================
# 予約画面
# =========================

@app.route("/reserva")
@role_required(User.ROLE_STUDENT)
def reserva():
    return render_template("Student/reserva.html")


# =========================
# 予約確認画面
# =========================

@app.route("/reservacheck")
@role_required(User.ROLE_STUDENT)
def reservacheck():
    return render_template("Student/reservacheck.html")


# =========================
# 予約完了画面
# =========================

@app.route("/reservadone")
@role_required(User.ROLE_STUDENT)
def reservadone():
    return render_template("Student/reservadone.html")


# =========================
# 予約一覧画面
# =========================

@app.route("/schedule")
@role_required(User.ROLE_STUDENT)
def schedule():
    return render_template("Student/schedule.html")


# =========================
# 予約取消画面
# =========================

@app.route("/reserva_delete")
@role_required(User.ROLE_STUDENT)
def reserva_delete():
    return render_template("Student/reserva_delete.html")


# =========================
# 予約取消完了画面
# =========================

@app.route("/reserva_delete_complete")
@role_required(User.ROLE_STUDENT)
def reserva_delete_complete():
    return render_template("Student/reserva_delete_complete.html")


# =========================
# 履歴画面
# =========================

@app.route("/history")
@role_required(User.ROLE_STUDENT)
def history():
    return render_template("Student/history.html")


# =========================
# カウンセラートップ画面
# =========================

@app.route("/care_top")
@role_required(User.ROLE_COUNSELOR)
def care_top():
    return render_template("Counselor/care_top.html")


# =========================
# 面談予約確認画面
# =========================

@app.route("/care_schedule")
@role_required(User.ROLE_COUNSELOR)
def care_schedule():
    return render_template("Counselor/care_schedule.html")


# =========================
# 面談内容確認画面
# =========================

@app.route("/care_contents")
@role_required(User.ROLE_COUNSELOR)
def care_contents():
    return render_template("Counselor/care_contents.html")


# =========================
# 詳細一覧画面
# =========================

@app.route("/care_contents_check")
@role_required(User.ROLE_COUNSELOR)
def care_contents_check():
    return render_template("Counselor/care_contents_check.html")


# =========================
# 面談履歴画面
# =========================

@app.route("/care_history")
@role_required(User.ROLE_COUNSELOR)
def care_history():
    return render_template("Counselor/care_history.html")


# =========================
# 生徒画面
# =========================

@app.route("/care_student")
@role_required(User.ROLE_COUNSELOR)
def care_student():
    return render_template("Counselor/care_student.html")


# =========================
# 記録新規登録画面
# =========================

@app.route("/care_record")
@role_required(User.ROLE_COUNSELOR)
def care_record():
    return render_template("Counselor/care_record.html")


# =========================
# 記録確認画面
# =========================

@app.route("/care_record_check")
@role_required(User.ROLE_COUNSELOR)
def care_record_check():
    return render_template("Counselor/care_record_check.html")


# =========================
# 記録完了画面
# =========================

@app.route("/care_record_complete")
@role_required(User.ROLE_COUNSELOR)
def care_record_complete():
    return render_template("Counselor/care_record_complete.html")


# =========================
# 記録変更画面
# =========================

@app.route("/care_charec")
@role_required(User.ROLE_COUNSELOR)
def care_charec():
    return render_template("Counselor/care_charec.html")


# =========================
# 記録変更確認画面
# =========================

@app.route("/care_charec_check")
@role_required(User.ROLE_COUNSELOR)
def care_charec_check():
    return render_template("Counselor/care_charec_check.html")


# =========================
# 記録変更完了画面
# =========================

@app.route("/care_charec_complete")
@role_required(User.ROLE_COUNSELOR)
def care_charec_complete():
    return render_template("Counselor/care_charec_complete.html")


# =========================
# 面談可能日時登録画面
# =========================

@app.route("/care_reseva")
@role_required(User.ROLE_COUNSELOR)
def care_reseva():
    return render_template("Counselor/care_reseva.html")


# =========================
# 面談可能日時登録確認画面
# =========================

@app.route("/care_reseva_check")
@role_required(User.ROLE_COUNSELOR)
def care_reseva_check():
    return render_template("Counselor/care_reseva_check.html")


# =========================
# 面談可能日時完了画面
# =========================

@app.route("/care_reseva_complete")
@role_required(User.ROLE_COUNSELOR)
def care_reseva_complete():
    return render_template("Counselor/care_reseva_complete.html")


# =========================
# 面談可能日時変更・削除画面
# =========================

@app.route("/care_chadel")
@role_required(User.ROLE_COUNSELOR)
def care_chadel():
    return render_template("Counselor/care_chadel.html")


# =========================
# 面談可能日時変更・削除確認画面
# =========================

@app.route("/care_chadel_check")
@role_required(User.ROLE_COUNSELOR)
def care_chadel_check():
    return render_template("Counselor/care_chadel_check.html")


# =========================
# 面談可能日時変更・削除完了画面
# =========================

@app.route("/care_chadel_complete")
@role_required(User.ROLE_COUNSELOR)
def care_chadel_complete():
    return render_template("Counselor/care_chadel_complete.html")


# =========================
# 先生トップ画面 (担当クラス管理機能)
# =========================

@app.route("/teacher_top")
@role_required(User.ROLE_TEACHER)
def teacher_top():
    return render_template("Teacher/teacher_top.html")


# =========================
# クラスの生徒一覧を表示する
# =========================

@app.route("/teacher_class_students")
@role_required(User.ROLE_TEACHER)
def teacher_class_students():
    return render_template("Teacher/teacher_class_students.html")


# =========================
# クラスの生徒の面談予約日時を表示する
# =========================

@app.route("/teacher_class_schedule")
@role_required(User.ROLE_TEACHER)
def teacher_class_schedule():
    return render_template("Teacher/teacher_class_schedule.html")


# =========================
# 生徒一覧画面 (管理者機能: 今回は未対応)
# =========================

@app.route("/manage_student")
def manage_student():
    return render_template("Management/manage_student.html")


# =========================
# 生徒詳細画面
# =========================

@app.route("/manage_student_check")
def manage_student_check():
    return render_template("Management/manage_student_check.html")


# =========================
# 生徒新規登録画面
# =========================

@app.route("/manage_sturec")
def manage_sturec():
    return render_template("Management/manage_sturec.html")


# =========================
# 生徒新規登録確認画面
# =========================

@app.route("/manage_sturec_check")
def manage_sturec_check():
    return render_template("Management/manage_sturec_check.html")


# =========================
# 生徒新規登録完了画面
# =========================

@app.route("/manage_sturec_complete")
def manage_sturec_complete():
    return render_template("Management/manage_sturec_complete.html")


# =========================
# 生徒編集画面
# =========================

@app.route("/manage_stuedit")
def manage_stuedit():
    return render_template("Management/manage_stuedit.html")


# =========================
# 生徒編集確認画面
# =========================

@app.route("/manage_stuedit_check")
def manage_stuedit_check():
    return render_template("Management/manage_stuedit_check.html")


# =========================
# 生徒編集完了画面
# =========================

@app.route("/manage_stuedit_complete")
def manage_stuedit_complete():
    return render_template("Management/manage_stuedit_complete.html")


# =========================
# 生徒削除確認画面
# =========================

@app.route("/manage_studel_check")
def manage_studel_check():
    return render_template("Management/manage_studel_check.html")


# =========================
# 生徒削除完了画面
# =========================

@app.route("/manage_studel_complete")
def manage_studel_complete():
    return render_template("Management/manage_studel_complete.html")


# =========================
# カウンセラー管理画面
# =========================

@app.route("/manage_care")
def manage_care():
    return render_template("Management/manage_care.html")


# =========================
# カウンセラー詳細画面
# =========================

@app.route("/manage_care_check")
def manage_care_check():
    return render_template("Management/manage_care_check.html")


# =========================
# カウンセラー予約確認画面
# =========================

@app.route("/manage_schedule")
def manage_schedule():
    return render_template("Management/manage_schedule.html")


# =========================
# カウンセラー新規登録画面
# =========================

@app.route("/manage_carereg")
def manage_carereg():
    return render_template("Management/manage_carereg.html")


# =========================
# カウンセラー新規登録確認画面
# =========================

@app.route("/manage_carereg_check")
def manage_carereg_check():
    return render_template("Management/manage_carereg_check.html")


# =========================
# カウンセラー新規登録完了画面
# =========================

@app.route("/manage_carereg_complete")
def manage_carereg_complete():
    return render_template("Management/manage_carereg_complete.html")


# =========================
# カウンセラー編集画面
# =========================

@app.route("/manage_caredit")
def manage_caredit():
    return render_template("Management/manage_caredit.html")


# =========================
# カウンセラー編集確認画面
# =========================

@app.route("/manage_caredit_check")
def manage_caredit_check():
    return render_template("Management/manage_caredit_check.html")


# =========================
# カウンセラー編集完了画面
# =========================

@app.route("/manage_caredit_complete")
def manage_caredit_complete():
    return render_template("Management/manage_caredit_complete.html")


# =========================
# カウンセラー削除確認画面
# =========================

@app.route("/manage_caredel_check")
def manage_caredel_check():
    return render_template("Management/manage_caredel_check.html")


# =========================
# カウンセラー削除完了画面
# =========================

@app.route("/manage_caredel_complete")
def manage_caredel_complete():
    return render_template("Management/manage_caredel_complete.html")


if __name__ == "__main__":
    ##################
    Timer(
        1,
        lambda: subprocess.Popen([
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            "http://127.0.0.1:5000"
        ])
    ).start()
    ##################

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )
