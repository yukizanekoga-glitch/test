// ログアウトの確認ポップアップ (全画面共通)
// /logout へのリンクやフォームを押したとき、画面の上から確認を出し、
// 「はい」でログアウト、「いいえ」で何もしない。
(function () {
    const LOGOUT_PATH = "/logout";

    // ---------- 見た目 ----------
    const style = document.createElement("style");
    style.textContent = `
        .logout-confirm-backdrop {
            position: fixed;
            inset: 0;
            z-index: 2000;
            background: rgba(20, 30, 50, 0.35);
            opacity: 0;
            transition: opacity 0.2s;
        }
        .logout-confirm-backdrop.show { opacity: 1; }

        .logout-confirm {
            position: fixed;
            top: 24px;
            left: 50%;
            z-index: 2001;
            width: calc(100% - 32px);
            max-width: 380px;
            padding: 24px 24px 20px;
            border-radius: 10px;
            background: #ffffff;
            box-shadow: 0 12px 32px rgba(20, 30, 50, 0.22);
            font-family: inherit;
            text-align: center;
            transform: translate(-50%, -140%);
            transition: transform 0.25s ease-out;
        }
        .logout-confirm.show { transform: translate(-50%, 0); }

        .logout-confirm-message {
            margin: 0 0 20px;
            color: #1f2d44;
            font-size: 16px;
            font-weight: 700;
        }

        .logout-confirm-buttons {
            display: flex;
            gap: 12px;
        }

        .logout-confirm-buttons button {
            flex: 1 1 0;
            height: 40px;
            border-radius: 6px;
            font-family: inherit;
            font-size: 14px;
            font-weight: 600;
            cursor: pointer;
            transition: background 0.2s, border-color 0.2s;
        }

        .logout-confirm-yes {
            border: 1px solid #1476f5;
            background: #1476f5;
            color: #ffffff;
        }
        .logout-confirm-yes:hover { border-color: #0b5ed7; background: #0b5ed7; }

        .logout-confirm-no {
            border: 1px solid #c8ced9;
            background: #ffffff;
            color: #46536c;
        }
        .logout-confirm-no:hover { background: #f3f5f8; }
    `;
    document.head.appendChild(style);

    // ---------- 確認ポップアップ ----------
    let pendingAction = null;
    let backdrop = null;
    let dialog = null;

    function build() {
        backdrop = document.createElement("div");
        backdrop.className = "logout-confirm-backdrop";

        dialog = document.createElement("div");
        dialog.className = "logout-confirm";
        dialog.setAttribute("role", "alertdialog");
        dialog.setAttribute("aria-modal", "true");
        dialog.setAttribute("aria-labelledby", "logoutConfirmMessage");
        dialog.innerHTML = `
            <p class="logout-confirm-message" id="logoutConfirmMessage">ログアウトしますか？</p>
            <div class="logout-confirm-buttons">
                <button type="button" class="logout-confirm-yes">はい</button>
                <button type="button" class="logout-confirm-no">いいえ</button>
            </div>
        `;

        dialog.querySelector(".logout-confirm-yes").addEventListener("click", function () {
            const action = pendingAction;
            close();
            if (action) action();
        });
        dialog.querySelector(".logout-confirm-no").addEventListener("click", close);
        backdrop.addEventListener("click", close);

        document.body.appendChild(backdrop);
        document.body.appendChild(dialog);
    }

    function open(action) {
        if (!dialog) build();
        pendingAction = action;
        backdrop.hidden = false;
        dialog.hidden = false;
        // 表示してから class を付けると、上から下りてくる動きになる
        requestAnimationFrame(function () {
            backdrop.classList.add("show");
            dialog.classList.add("show");
            dialog.querySelector(".logout-confirm-no").focus();
        });
    }

    function close() {
        pendingAction = null;
        if (!dialog) return;
        backdrop.classList.remove("show");
        dialog.classList.remove("show");
        setTimeout(function () {
            if (!dialog.classList.contains("show")) {
                backdrop.hidden = true;
                dialog.hidden = true;
            }
        }, 250);
    }

    function isOpen() {
        return dialog && dialog.classList.contains("show");
    }

    // ---------- /logout へのリンク・フォームを横取りする ----------
    function isLogoutUrl(url) {
        try {
            return new URL(url, location.href).pathname === LOGOUT_PATH;
        } catch (e) {
            return false;
        }
    }

    document.addEventListener("click", function (event) {
        const link = event.target.closest("a[href]");
        if (!link || !isLogoutUrl(link.getAttribute("href"))) return;

        event.preventDefault();
        open(function () { location.href = link.href; });
    });

    document.addEventListener("submit", function (event) {
        const form = event.target;
        if (!isLogoutUrl(form.getAttribute("action") || "")) return;

        event.preventDefault();
        open(function () { form.submit(); });
    });

    // Esc キーで「いいえ」と同じ動き
    document.addEventListener("keydown", function (event) {
        if (event.key === "Escape" && isOpen()) close();
    });
})();
