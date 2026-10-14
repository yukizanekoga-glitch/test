from flask import Flask, render_template, redirect, url_for
#######################
import subprocess
from threading import Timer
########################

app = Flask(__name__)


# =========================
# ログイン画面
# =========================

@app.route("/")
def index():
    return redirect(url_for("login"))


@app.route("/login")
def login():
    return render_template("login.html")


@app.route("/logout")
def logout():
    return redirect(url_for("login"))


# =========================
# 職員ログイン画面
# =========================

@app.route("/management_login")
def management_login():
    return render_template("management_login.html")


# =========================
# 職員トップ画面
# =========================

@app.route("/management_top")
def management_top():
    return render_template("Management/management_top.html")


# =========================
# 生徒トップ画面
# =========================

@app.route("/top")
def top():
    return render_template("Student/top.html")


# =========================
# 予約画面
# =========================

@app.route("/reserva")
def reserva():
    return render_template("Student/reserva.html")


# =========================
# 予約確認画面
# =========================

@app.route("/reservacheck")
def reservacheck():
    return render_template("Student/reservacheck.html")


# =========================
# 予約完了画面
# =========================

@app.route("/reservadone")
def reservadone():
    return render_template("Student/reservadone.html")


# =========================
# 予約一覧画面
# =========================

@app.route("/schedule")
def schedule():
    return render_template("Student/schedule.html")


# =========================
# 予約取消画面
# =========================

@app.route("/reserva_delete")
def reserva_delete():
    return render_template("Student/reserva_delete.html")


# =========================
# 予約取消完了画面
# =========================

@app.route("/reserva_delete_complete")
def reserva_delete_complete():
    return render_template("Student/reserva_delete_complete.html")


# =========================
# 履歴画面
# =========================

@app.route("/history")
def history():
    return render_template("Student/history.html")


# =========================
# カウンセラートップ画面
# =========================

@app.route("/care_top")
def care_top():
    return render_template("Counselor/care_top.html")


# =========================
# 面談予約確認画面
# =========================

@app.route("/care_schedule")
def care_schedule():
    return render_template("Counselor/care_schedule.html")


# =========================
# 面談内容確認画面
# =========================

@app.route("/care_contents")
def care_contents():
    return render_template("Counselor/care_contents.html")


# =========================
# 詳細一覧画面
# =========================

@app.route("/care_contents_check")
def care_contents_check():
    return render_template("Counselor/care_contents_check.html")


# =========================
# 面談履歴画面
# =========================

@app.route("/care_history")
def care_history():
    return render_template("Counselor/care_history.html")


# =========================
# 生徒画面
# =========================

@app.route("/care_student")
def care_student():
    return render_template("Counselor/care_student.html")


# =========================
# 記録新規登録画面
# =========================

@app.route("/care_record")
def care_record():
    return render_template("Counselor/care_record.html")


# =========================
# 記録確認画面
# =========================

@app.route("/care_record_check")
def care_record_check():
    return render_template("Counselor/care_record_check.html")


# =========================
# 記録完了画面
# =========================

@app.route("/care_record_complete")
def care_record_complete():
    return render_template("Counselor/care_record_complete.html")


# =========================
# 記録変更画面
# =========================

@app.route("/care_charec")
def care_charec():
    return render_template("Counselor/care_charec.html")


# =========================
# 記録変更確認画面
# =========================

@app.route("/care_charec_check")
def care_charec_check():
    return render_template("Counselor/care_charec_check.html")


# =========================
# 記録変更完了画面
# =========================

@app.route("/care_charec_complete")
def care_charec_complete():
    return render_template("Counselor/care_charec_complete.html")


# =========================
# 面談可能日時登録画面
# =========================

@app.route("/care_reseva")
def care_reseva():
    return render_template("Counselor/care_reseva.html")


# =========================
# 面談可能日時登録確認画面
# =========================

@app.route("/care_reseva_check")
def care_reseva_check():
    return render_template("Counselor/care_reseva_check.html")


# =========================
# 面談可能日時完了画面
# =========================

@app.route("/care_reseva_complete")
def care_reseva_complete():
    return render_template("Counselor/care_reseva_complete.html")


# =========================
# 面談可能日時変更・削除画面
# =========================

@app.route("/care_chadel")
def care_chadel():
    return render_template("Counselor/care_chadel.html")


# =========================
# 面談可能日時変更・削除確認画面
# =========================

@app.route("/care_chadel_check")
def care_chadel_check():
    return render_template("Counselor/care_chadel_check.html")


# =========================
# 面談可能日時変更・削除完了画面
# =========================

@app.route("/care_chadel_complete")
def care_chadel_complete():
    return render_template("Counselor/care_chadel_complete.html")


# =========================
# 生徒一覧画面
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
    