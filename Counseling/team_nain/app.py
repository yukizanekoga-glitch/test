import os
from datetime import date as date_cls, datetime, time as time_cls, timedelta
from functools import wraps

from flask import Flask, render_template, redirect, url_for, request, session, flash
from sqlalchemy.exc import IntegrityError
#######################
import subprocess
from threading import Timer
########################

from models import db, User, AvailableSlot, Reservation

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
app.secret_key = 'dev-secret-key-change-in-production'
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(BASE_DIR, 'counseling.db')}"
# app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(BASE_DIR, 'my_dev.db')}"#####
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

# ロールごとのログイン後トップ画面
ROLE_TOP_ENDPOINT = {
    User.ROLE_STUDENT: 'top',
    User.ROLE_COUNSELOR: 'care_top',
    User.ROLE_TEACHER: 'teacher_student_top',
    User.ROLE_ADMIN: 'management_top',
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

        if user is None or not user.check_password(password):
            flash("ユーザー名またはパスワードが正しくありません。")
            return render_template("login.html")

        session.clear()
        session["user_id"] = user.id
        session["username"] = user.username
        session["display_name"] = user.display_name
        session["class_name"] = user.school_class.name if user.school_class else ""
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

WEEKDAYS_JP = '月火水木金土日'

# 面談可能日時として選択できる時間帯 (カウンセラー側の登録画面と同じ区切り)
RESERVATION_TIME_SLOTS = [
    (time_cls(hour, 0), time_cls(hour, 30))
    for hour in range(9, 17)
]


def _format_date_jp(target_date):
    return f"{target_date.year}年{target_date.month}月{target_date.day}日（{WEEKDAYS_JP[target_date.weekday()]}）"


def _format_slot_datetime(slot):
    return (
        f"{_format_date_jp(slot.date)} "
        f"{slot.start_time.strftime('%H:%M')} ～ {slot.end_time.strftime('%H:%M')}"
    )


@app.route("/reserva")
@role_required(User.ROLE_STUDENT)
def reserva():
    # カウンセラー一覧 (プルダウン用)
    counselors = (
        User.query
        .filter_by(role=User.ROLE_COUNSELOR)
        .order_by(User.display_name)
        .all()
    )

    raw_counselor_id = request.args.get("counselor_id", "").strip()
    selected_counselor_id = None
    if raw_counselor_id:
        try:
            selected_counselor_id = int(raw_counselor_id)
        except ValueError:
            selected_counselor_id = None
        if not any(c.id == selected_counselor_id for c in counselors):
            selected_counselor_id = None

    try:
        week_offset = int(request.args.get("week", 0))
    except ValueError:
        week_offset = 0
    week_offset = max(week_offset, 0)

    today = date_cls.today()
    monday = today - timedelta(days=today.weekday()) + timedelta(weeks=week_offset)
    week_dates = [monday + timedelta(days=i) for i in range(5)]  # 月～金

    # まだ予約が入っていない、今週表示分の面談可能日時
    query = (
        AvailableSlot.query
        .outerjoin(Reservation, Reservation.slot_id == AvailableSlot.id)
        .filter(Reservation.id.is_(None))
        .filter(AvailableSlot.date >= today)
        .filter(AvailableSlot.date >= week_dates[0])
        .filter(AvailableSlot.date <= week_dates[-1])
    )
    if selected_counselor_id is not None:
        query = query.filter(AvailableSlot.counselor_id == selected_counselor_id)

    week_slots = query.order_by(AvailableSlot.date, AvailableSlot.start_time).all()

    # 日付・時間帯ごとに1枠だけ表示する（「指定なし」の場合は最初に見つかった枠を使う）
    slot_by_cell = {}
    for slot in week_slots:
        slot_by_cell.setdefault((slot.date, slot.start_time), slot)

    grid_rows = [
        {
            "start_time": start_time,
            "end_time": end_time,
            "cells": [slot_by_cell.get((d, start_time)) for d in week_dates],
        }
        for start_time, end_time in RESERVATION_TIME_SLOTS
    ]

    return render_template(
        "Student/reserva.html",
        counselors=counselors,
        selected_counselor_id=selected_counselor_id,
        week_dates=week_dates,
        grid_rows=grid_rows,
        week_offset=week_offset,
        has_slots=bool(week_slots),
    )


# =========================
# 予約確認画面
# =========================

@app.route("/reserva_check", methods=["GET", "POST"])
@role_required(User.ROLE_STUDENT)
def reserva_check():
    if request.method == "POST":
        raw_slot_id = request.form.get("slot_id", "").strip()
        try:
            slot_id = int(raw_slot_id)
        except ValueError:
            flash("面談の日時を選択してください。")
            return redirect(url_for("reserva"))

        slot = db.session.get(AvailableSlot, slot_id)
        if slot is None or slot.is_booked or slot.date < date_cls.today():
            flash("選択した日時はすでに予約できません。もう一度お選びください。")
            return redirect(url_for("reserva"))

        session["pending_slot_id"] = slot_id
        return redirect(url_for("reserva_check"))

    slot_id = session.get("pending_slot_id")
    slot = db.session.get(AvailableSlot, slot_id) if slot_id else None
    if slot is None or slot.is_booked or slot.date < date_cls.today():
        flash("選択した日時が見つかりません。もう一度お選びください。")
        session.pop("pending_slot_id", None)
        return redirect(url_for("reserva"))

    return render_template(
        "Student/reserva_check.html",
        counselor_name=f"{slot.counselor.display_name} 先生",
        interview_datetime=_format_slot_datetime(slot),
        reservation_date=_format_date_jp(slot.date),
    )


# =========================
# 予約完了画面
# =========================

@app.route("/reserva_done", methods=["POST"])
@role_required(User.ROLE_STUDENT)
def reserva_done():
    slot_id = session.get("pending_slot_id")
    slot = db.session.get(AvailableSlot, slot_id) if slot_id else None
    if slot is None or slot.is_booked or slot.date < date_cls.today():
        flash("選択した日時は予約できませんでした。もう一度お選びください。")
        session.pop("pending_slot_id", None)
        return redirect(url_for("reserva"))

    db.session.add(Reservation(slot_id=slot.id, student_id=session["user_id"]))
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        flash("その日時はすでに他の人が予約しています。別の日時をお選びください。")
        session.pop("pending_slot_id", None)
        return redirect(url_for("reserva"))

    session.pop("pending_slot_id", None)

    return render_template(
        "Student/reserva_done.html",
        counselor_name=f"{slot.counselor.display_name} 先生",
        interview_datetime=_format_slot_datetime(slot),
        reservation_date=_format_date_jp(slot.date),
    )


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
# 面談予約確認画面 (面談予約を確認する)
# =========================

@app.route("/care_schedule")
@role_required(User.ROLE_COUNSELOR)
def care_schedule():
    reservations = (
        Reservation.query
        .join(AvailableSlot)
        .filter(AvailableSlot.counselor_id == session["user_id"])
        .order_by(AvailableSlot.date, AvailableSlot.start_time)
        .all()
    )
    return render_template("Counselor/care_schedule.html", reservations=reservations)


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


def _parse_slot_form(form):
    """日時登録・変更フォームの入力値を検証し、(値の辞書, エラーメッセージ) を返す"""
    raw_date = form.get("date", "").strip()
    raw_start = form.get("start_time", "").strip()
    raw_end = form.get("end_time", "").strip()

    try:
        slot_date = date_cls.fromisoformat(raw_date)
        start_time = time_cls.fromisoformat(raw_start)
        end_time = time_cls.fromisoformat(raw_end)
    except ValueError:
        return None, "日付・時刻の形式が正しくありません。"

    if slot_date < date_cls.today():
        return None, "過去の日付は登録できません。"

    if end_time <= start_time:
        return None, "終了時刻は開始時刻より後にしてください。"

    return {"date": raw_date, "start_time": raw_start, "end_time": raw_end}, None


def _has_overlap(counselor_id, slot_date, start_time, end_time, exclude_slot_id=None):
    query = AvailableSlot.query.filter(
        AvailableSlot.counselor_id == counselor_id,
        AvailableSlot.date == slot_date,
        AvailableSlot.start_time < end_time,
        AvailableSlot.end_time > start_time,
    )
    if exclude_slot_id is not None:
        query = query.filter(AvailableSlot.id != exclude_slot_id)
    return query.first() is not None

# =========================
# 面談可能日時トップ画面 (面談可能日一覧)
# =========================

@app.route("/care_reseva_top")
@role_required(User.ROLE_COUNSELOR)
def care_reseva_top():
    slots = (
        AvailableSlot.query
        .filter_by(counselor_id=session["user_id"])
        .order_by(AvailableSlot.date, AvailableSlot.start_time)
        .all()
    )
    return render_template("Counselor/care_reseva_top.html", slots=slots)


# =========================
# 面談可能日時登録画面 (面談可能日時を登録する)
# =========================

@app.route("/care_reseva", methods=["GET", "POST"])
@role_required(User.ROLE_COUNSELOR)
def care_reseva():
    slots = (
        AvailableSlot.query
        .filter_by(counselor_id=session["user_id"])
        .order_by(AvailableSlot.date, AvailableSlot.start_time)
        .all()
    )
    return render_template("Counselor/care_reseva.html", slots=slots)


# =========================
# 面談可能日時登録確認画面
# =========================

def _parse_bulk_slots(form):
    """一括登録フォームの slot ("YYYY-MM-DD|HH:MM|HH:MM") を検証し、(枠のリスト, エラーメッセージ) を返す"""
    slots = set()
    for raw in form.getlist("slot"):
        try:
            raw_date, raw_start, raw_end = raw.split("|")
            slot_date = date_cls.fromisoformat(raw_date)
            start_time = time_cls.fromisoformat(raw_start)
            end_time = time_cls.fromisoformat(raw_end)
        except ValueError:
            return None, "日付・時刻の形式が正しくありません。"

        if slot_date <= date_cls.today():
            return None, "明日以降の日付を選択してください。"

        if end_time <= start_time:
            return None, "終了時刻は開始時刻より後にしてください。"

        slots.add((slot_date, start_time, end_time))

    if not slots:
        return None, "登録する日時を選択してください。"

    return sorted(slots), None


@app.route("/care_reseva_check", methods=["GET", "POST"])
@role_required(User.ROLE_COUNSELOR)
def care_reseva_check():
    # 登録内容は care_reseva のフォームから POST で受け取る (件数が多くなるため session には保存しない)
    if request.method == "GET":
        return redirect(url_for("care_reseva"))

    slots, error = _parse_bulk_slots(request.form)
    if error:
        flash(error)
        return redirect(url_for("care_reseva"))

    # 既に登録済みの日時と重なる枠は登録しない
    new_slots = [
        s for s in slots
        if not _has_overlap(session["user_id"], *s)
    ]
    skipped_count = len(slots) - len(new_slots)

    if not new_slots:
        flash("選択した日時はすべて登録済みです。")
        return redirect(url_for("care_reseva"))

    if request.form.get("confirm") == "1":
        for slot_date, start_time, end_time in new_slots:
            db.session.add(AvailableSlot(
                counselor_id=session["user_id"],
                date=slot_date,
                start_time=start_time,
                end_time=end_time,
            ))
        db.session.commit()
        return redirect(url_for("care_reseva_complete"))

    # 確認画面用に日付ごとにまとめる
    grouped = {}
    for slot_date, start_time, end_time in new_slots:
        grouped.setdefault(slot_date, []).append((start_time, end_time))

    return render_template(
        "Counselor/care_reseva_check.html",
        grouped=grouped,
        new_slots=new_slots,
        skipped_count=skipped_count,
    )


# =========================
# 面談可能日時完了画面
# =========================

@app.route("/care_reseva_complete")
@role_required(User.ROLE_COUNSELOR)
def care_reseva_complete():
    return render_template("Counselor/care_reseva_complete.html")


def _get_own_slot(slot_id):
    return AvailableSlot.query.filter_by(id=slot_id, counselor_id=session["user_id"]).first()


# =========================
# 面談可能日時変更・削除画面 (面談可能日時を変更する/削除する)
# =========================

@app.route("/care_chadel", methods=["GET", "POST"])
@role_required(User.ROLE_COUNSELOR)
def care_chadel():
    if request.method == "POST":
        slot_id = request.form.get("slot_id", type=int)
        action = request.form.get("action")
        slot = _get_own_slot(slot_id)

        if slot is None:
            flash("対象の面談可能日時が見つかりません。")
            return redirect(url_for("care_chadel"))

        if slot.is_booked:
            flash("予約済みの日時は変更・削除できません。")
            return redirect(url_for("care_chadel"))

        if action == "delete":
            session["pending_chadel"] = {"action": "delete", "slot_id": slot_id}
            return redirect(url_for("care_chadel_check"))

        if action == "edit":
            values, error = _parse_slot_form(request.form)
            if error:
                flash(error)
                return redirect(url_for("care_chadel", edit=slot_id))
            session["pending_chadel"] = {"action": "edit", "slot_id": slot_id, **values}
            return redirect(url_for("care_chadel_check"))

        flash("不正な操作です。")
        return redirect(url_for("care_chadel"))

    slots = (
        AvailableSlot.query
        .filter_by(counselor_id=session["user_id"])
        .order_by(AvailableSlot.date, AvailableSlot.start_time)
        .all()
    )

    edit_slot = None
    edit_id = request.args.get("edit", type=int)
    if edit_id is not None:
        edit_slot = _get_own_slot(edit_id)
        if edit_slot is None:
            flash("対象の面談可能日時が見つかりません。")
        elif edit_slot.is_booked:
            flash("予約済みの日時は変更・削除できません。")
            edit_slot = None

    return render_template("Counselor/care_chadel.html", slots=slots, edit_slot=edit_slot)


# =========================
# 面談可能日時変更・削除確認画面
# =========================

@app.route("/care_chadel_check", methods=["GET", "POST"])
@role_required(User.ROLE_COUNSELOR)
def care_chadel_check():
    pending = session.get("pending_chadel") # 操作内容をセッションから取得
    if not pending:
        flash("変更・削除内容が見つかりません。もう一度操作してください。")
        return redirect(url_for("care_chadel"))

    slot = _get_own_slot(pending["slot_id"])# 対象の日時を取得
    if slot is None:
        session.pop("pending_chadel", None)
        flash("対象の面談可能日時が見つかりません。")
        return redirect(url_for("care_chadel"))

    if request.method == "POST":
        if pending["action"] == "delete":
            db.session.delete(slot)# POSTされたら確定処理
            db.session.commit()    # DBに反映して保留情報を削除 
            message = "面談可能日時を削除しました。"
        else:
            slot_date = date_cls.fromisoformat(pending["date"])
            start_time = time_cls.fromisoformat(pending["start_time"])
            end_time = time_cls.fromisoformat(pending["end_time"])

            if _has_overlap(session["user_id"], slot_date, start_time, end_time, exclude_slot_id=slot.id):
                session.pop("pending_chadel", None)
                flash("同じ日時に登録済みの面談可能日時があります。")
                return redirect(url_for("care_chadel"))

            slot.date = slot_date
            slot.start_time = start_time
            slot.end_time = end_time
            db.session.commit()
            message = "面談可能日時を変更しました。"

        session.pop("pending_chadel", None)
        flash(message)
        return redirect(url_for("care_chadel_complete"))

    return render_template("Counselor/care_chadel_check.html", pending=pending, slot=slot)


# =========================
# 面談可能日時変更・削除完了画面
# =========================

@app.route("/care_chadel_complete")
@role_required(User.ROLE_COUNSELOR)
def care_chadel_complete():
    return render_template("Counselor/care_chadel_complete.html")





# =========================
# 管理者トップ画面
# =========================

@app.route("/management_top")
@role_required(User.ROLE_ADMIN)
def management_top():
    return render_template("Management/management_top.html")


# =========================
# 生徒一覧画面 (管理者機能: 一覧・詳細・登録・編集・削除は今回は未対応)
# =========================

@app.route("/manage_student")
@role_required(User.ROLE_ADMIN)
def manage_student():
    return render_template("Management/ManageStudent/manage_student.html")


# =========================
# 生徒詳細画面
# =========================

@app.route("/manage_student_check")
@role_required(User.ROLE_ADMIN)
def manage_student_check():
    return render_template("Management/ManageStudent/manage_student_check.html")


# =========================
# 生徒新規登録画面
# =========================

@app.route("/manage_sturec")
@role_required(User.ROLE_ADMIN)
def manage_sturec():
    return render_template("Management/ManageStudent/manage_sturec.html")


# =========================
# 生徒新規登録確認画面
# =========================

@app.route("/manage_sturec_check")
@role_required(User.ROLE_ADMIN)
def manage_sturec_check():
    return render_template("Management/ManageStudent/manage_sturec_check.html")


# =========================
# 生徒新規登録完了画面
# =========================

@app.route("/manage_sturec_complete")
@role_required(User.ROLE_ADMIN)
def manage_sturec_complete():
    return render_template("Management/ManageStudent/manage_sturec_complete.html")


# =========================
# 生徒編集画面
# =========================

@app.route("/manage_stuedit")
@role_required(User.ROLE_ADMIN)
def manage_stuedit():
    return render_template("Management/ManageStudent/manage_stuedit.html")


# =========================
# 生徒編集確認画面
# =========================

@app.route("/manage_stuedit_check")
@role_required(User.ROLE_ADMIN)
def manage_stuedit_check():
    return render_template("Management/ManageStudent/manage_stuedit_check.html")


# =========================
# 生徒編集完了画面
# =========================

@app.route("/manage_stuedit_complete")
@role_required(User.ROLE_ADMIN)
def manage_stuedit_complete():
    return render_template("Management/ManageStudent/manage_stuedit_complete.html")


# =========================
# 生徒削除確認画面
# =========================

@app.route("/manage_studel_check")
@role_required(User.ROLE_ADMIN)
def manage_studel_check():
    return render_template("Management/ManageStudent/manage_studel_check.html")


# =========================
# 生徒削除完了画面
# =========================

@app.route("/manage_studel_complete")
@role_required(User.ROLE_ADMIN)
def manage_studel_complete():
    return render_template("Management/ManageStudent/manage_studel_complete.html")


# =========================
# カウンセラー管理画面
# =========================

@app.route("/manage_care")
@role_required(User.ROLE_ADMIN)
def manage_care():
    return render_template("Management/ManageCare/manage_care.html")


# =========================
# カウンセラー詳細画面
# =========================

@app.route("/manage_care_check")
@role_required(User.ROLE_ADMIN)
def manage_care_check():
    return render_template("Management/ManageCare/manage_care_check.html")


# =========================
# カウンセラー予約確認画面
# =========================

@app.route("/manage_schedule")
@role_required(User.ROLE_ADMIN)
def manage_schedule():
    return render_template("Management/ManageCare/manage_schedule.html")


# =========================
# カウンセラー新規登録画面
# =========================

@app.route("/manage_carereg")
@role_required(User.ROLE_ADMIN)
def manage_carereg():
    return render_template("Management/ManageCare/manage_carereg.html")


# =========================
# カウンセラー新規登録確認画面
# =========================

@app.route("/manage_carereg_check")
@role_required(User.ROLE_ADMIN)
def manage_carereg_check():
    return render_template("Management/ManageCare/manage_carereg_check.html")


# =========================
# カウンセラー新規登録完了画面
# =========================

@app.route("/manage_carereg_complete")
@role_required(User.ROLE_ADMIN)
def manage_carereg_complete():
    return render_template("Management/ManageCare/manage_carereg_complete.html")


# =========================
# カウンセラー編集画面
# =========================

@app.route("/manage_caredit")
@role_required(User.ROLE_ADMIN)
def manage_caredit():
    return render_template("Management/ManageCare/manage_caredit.html")


# =========================
# カウンセラー編集確認画面
# =========================

@app.route("/manage_caredit_check")
@role_required(User.ROLE_ADMIN)
def manage_caredit_check():
    return render_template("Management/ManageCare/manage_caredit_check.html")


# =========================
# カウンセラー編集完了画面
# =========================

@app.route("/manage_caredit_complete")
@role_required(User.ROLE_ADMIN)
def manage_caredit_complete():
    return render_template("Management/ManageCare/manage_caredit_complete.html")


# =========================
# カウンセラー削除確認画面
# =========================

@app.route("/manage_caredel_check")
@role_required(User.ROLE_ADMIN)
def manage_caredel_check():
    return render_template("Management/ManageCare/manage_caredel_check.html")


# =========================
# カウンセラー削除完了画面
# =========================

@app.route("/manage_caredel_complete")
@role_required(User.ROLE_ADMIN)
def manage_caredel_complete():
    return render_template("Management/ManageCare/manage_caredel_complete.html")




@app.route("/teacher_student_top")
@role_required(User.ROLE_TEACHER)
def teacher_student_top():
    return render_template("Teacher/teacher_student_top.html")

@app.route("/teacher_caretime")
@role_required(User.ROLE_TEACHER)
def teacher_caretime():
    return render_template("Teacher/teacher_caretime.html")

@app.route("/teacher_pass")
@role_required(User.ROLE_TEACHER)
def teacher_pass():
    return render_template("Teacher/teacher_pass.html")

@app.route("/teacher_pass_complete")
@role_required(User.ROLE_TEACHER)
def teacher_pass_complete():
    return render_template("Teacher/teacher_pass_complete.html")

@app.route("/manage_carepass")
@role_required(User.ROLE_ADMIN)
def manage_carepass():
    return render_template("Management/ManageCare/manage_carepass.html")

@app.route("/manage_carepass_complete")
@role_required(User.ROLE_ADMIN)
def manage_carepass_complete():
    return render_template("Management/ManageCare/manage_carepass_complete.html")

@app.route("/manage_class")
@role_required(User.ROLE_ADMIN)
def manage_class():
    return render_template("Management/ManageClass/manage_class.html")

@app.route("/manage_stuallo")
@role_required(User.ROLE_ADMIN)
def manage_stuallo():
    return render_template("Management/ManageClass/manage_stuallo.html")

@app.route("/manage_stuallo_check")
@role_required(User.ROLE_ADMIN)
def manage_stuallo_check():
    return render_template("Management/ManageClass/manage_stuallo_check.html")

@app.route("/manage_stuallo_complete")
@role_required(User.ROLE_ADMIN)
def manage_stuallo_complete():
    return render_template("Management/ManageClass/manage_stuallo_complete.html")

@app.route("/manage_stupass")
@role_required(User.ROLE_ADMIN)
def manage_stupass():
    return render_template("Management/ManageStudent/manage_stupass.html")

@app.route("/manage_stupass_complete")
@role_required(User.ROLE_ADMIN)
def manage_stupass_complete():
    return render_template("Management/ManageStudent/manage_stupass_complete.html")

@app.route("/manage_teacher")
@role_required(User.ROLE_ADMIN)
def manage_teacher():
    return render_template("Management/ManageTeacher/manage_teacher.html")

@app.route("/manage_teacher_check")
@role_required(User.ROLE_ADMIN)
def manage_teacher_check():
    return render_template("Management/ManageTeacher/manage_teacher_check.html")

@app.route("/manage_teadel_check")
@role_required(User.ROLE_ADMIN)
def manage_teadel_check():
    return render_template("Management/ManageTeacher/manage_teadel_check.html")

@app.route("/manage_teadel_complete")
@role_required(User.ROLE_ADMIN)
def manage_teadel_complete():
    return render_template("Management/ManageTeacher/manage_teadel_complete.html")

@app.route("/manage_teaedit")
@role_required(User.ROLE_ADMIN)
def manage_teaedit():
    return render_template("Management/ManageTeacher/manage_teaedit.html")

@app.route("/manage_teaedit_check")
@role_required(User.ROLE_ADMIN)
def manage_teaedit_check():
    return render_template("Management/ManageTeacher/manage_teaedit_check.html")

@app.route("/manage_teaedit_complete")
@role_required(User.ROLE_ADMIN)
def manage_teaedit_complete():
    return render_template("Management/ManageTeacher/manage_teaedit_complete.html")

@app.route("/manage_teallo")
@role_required(User.ROLE_ADMIN)
def manage_teallo():
    return render_template("Management/ManageClass/manage_teallo.html")

@app.route("/manage_teallo_check")
@role_required(User.ROLE_ADMIN)
def manage_teallo_check():
    return render_template("Management/ManageClass/manage_teallo_check.html")

@app.route("/manage_teallo_complete")
@role_required(User.ROLE_ADMIN)
def manage_teallo_complete():
    return render_template("Management/ManageClass/manage_teallo_complete.html")

@app.route("/manage_teapass")
@role_required(User.ROLE_ADMIN)
def manage_teapass():
    return render_template("Management/ManageTeacher/manage_teapass.html")

@app.route("/manage_teapass_complete")
@role_required(User.ROLE_ADMIN)
def manage_teapass_complete():
    return render_template("Management/ManageTeacher/manage_teapass_complete.html")

@app.route("/manage_tearec")
@role_required(User.ROLE_ADMIN)
def manage_tearec():
    return render_template("Management/ManageTeacher/manage_tearec.html")

@app.route("/manage_tearec_check")
@role_required(User.ROLE_ADMIN)
def manage_tearec_check():
    return render_template("Management/ManageTeacher/manage_tearec_check.html")

@app.route("/manage_tearec_complete")
@role_required(User.ROLE_ADMIN)
def manage_tearec_complete():
    return render_template("Management/ManageTeacher/manage_tearec_complete.html")


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
