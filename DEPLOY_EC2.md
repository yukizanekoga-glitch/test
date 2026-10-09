# EC2 デプロイ手順（TrainAlertApp）

Amazon Linux の EC2 に、Django + gunicorn + Nginx で公開するための手順です。

- リポジトリのフォルダ: `/home/ec2-user/TrainAlertApp`
- Django のプロジェクト名（settings.py があるフォルダ）: `trainSupport`

---

## 0. EC2 に接続する（手元の PowerShell で）

```
ssh -i <鍵ファイル.pem> ec2-user@<EC2のIPアドレス>
```

プロンプトが `[ec2-user@ip-... ]$` になっていれば EC2 の中にいます。
`PS C:\電車>` のままなら、まだ手元の Windows です（ここで manage.py を動かすと `No module named 'django'` になります）。

---

## 1. 必要なソフトを入れる（初回のみ）

```
sudo dnf install -y python3.12 python3.12-pip nginx git
```

## 2. コードを取ってくる（初回のみ）

```
cd ~
git clone https://github.com/<アカウント名>/TrainAlertApp
cd TrainAlertApp
```

※ すでに `TrainAlertApp` の中にいるときに `cd TrainAlertApp` すると
  「does not exist」になります。迷ったら `cd /home/ec2-user/TrainAlertApp`。

## 3. 仮想環境とライブラリ

```
python3.12 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install gunicorn
```

※ requirements.txt に gunicorn が入っていないので、別途インストールが必要。
  プロンプトの先頭に `(venv)` が付いていることを確認。

## 4. settings.py を本番用に直す

`trainSupport/settings.py` に次の2点が必要。

```
STATIC_ROOT = BASE_DIR / 'staticfiles'   # STATIC_URL の下に追加
ALLOWED_HOSTS = ['*']                    # [] のままだと 400 Bad Request
```

EC2 上でコマンドで直す場合:

```
sed -i "/^STATIC_URL/a STATIC_ROOT = BASE_DIR / 'staticfiles'" trainSupport/settings.py
sed -i "s/^ALLOWED_HOSTS = \[\]/ALLOWED_HOSTS = ['*']/" trainSupport/settings.py
grep -n "STATIC\|ALLOWED_HOSTS" trainSupport/settings.py
```

※ STATIC_ROOT と STATICFILES_DIRS（`static`）は別のフォルダにすること。
※ 手元の C:\電車 の settings.py にも同じ変更を入れてコミットしておけば、次回からこの手順は不要。

## 5. 静的ファイル・DB・駅データ

```
python manage.py collectstatic --noinput
python manage.py migrate
python manage.py import_stations 'data/3!stations.csv' 'data/2!lines.csv'
```

※ ファイル名に `!` があるので必ずシングルクォート `'...'` で囲む。
※ 引数の順番は「駅CSV → 路線CSV」。

## 6. gunicorn の動作テスト

```
gunicorn --bind 127.0.0.1:8000 trainSupport.wsgi:application
```

`Listening at: http://127.0.0.1:8000` が出れば OK。Ctrl+C で止める。

---

## 7. gunicorn を常駐させる（systemd）

```
sudo nano /etc/systemd/system/django.service
```

中身:

```
[Unit]
Description=TrainAlertApp gunicorn
After=network.target

[Service]
User=ec2-user
Group=ec2-user
WorkingDirectory=/home/ec2-user/TrainAlertApp
ExecStart=/home/ec2-user/TrainAlertApp/venv/bin/gunicorn --workers 2 --bind 127.0.0.1:8000 trainSupport.wsgi:application
Restart=always

[Install]
WantedBy=multi-user.target
```

nano の保存: Ctrl+O → Enter → Ctrl+X

```
sudo systemctl daemon-reload
sudo systemctl enable --now django
sudo systemctl status django      # active (running) なら OK（q で閉じる）
```

---

## 8. Nginx の設定

```
sudo nano /etc/nginx/conf.d/trainSupport.conf
```

※ `sudo cat` ではファイルは作れない（表示するだけ）。作るのは `nano`。

中身:

```
server {
    listen 80 default_server;
    server_name _;

    location /static/ {
        alias /home/ec2-user/TrainAlertApp/staticfiles/;
    }

    location /media/ {
        alias /home/ec2-user/TrainAlertApp/media/;
    }

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Nginx 本体の初期ページ（Welcome to nginx!）が優先されないようにする:

```
sudo sed -i 's/ default_server//' /etc/nginx/nginx.conf
```

Nginx が /home/ec2-user の中の CSS を読めるようにする:

```
chmod 711 /home/ec2-user
```

反映:

```
sudo nginx -t                     # syntax is ok を確認
sudo systemctl enable --now nginx
sudo systemctl restart nginx
sudo systemctl restart django
```

## 9. ブラウザで確認

`http://<EC2のパブリックIP>/` を開く。

つながらない場合は、AWS コンソールで EC2 のセキュリティグループのインバウンドルールに
**HTTP（ポート 80）** があるか確認。

---

## コードを更新したとき（2回目以降）

```
cd /home/ec2-user/TrainAlertApp
source venv/bin/activate
git pull
pip install -r requirements.txt
python manage.py collectstatic --noinput
python manage.py migrate
sudo systemctl restart django
```

※ EC2 上で settings.py を直接直していると、`git pull` でぶつかることがある。
  手元で同じ修正をコミットしておくのが安全。

---

## よくあるエラーと対処

| 症状 | 原因 | 対処 |
|---|---|---|
| `You're using the staticfiles app without having set the STATIC_ROOT` | STATIC_ROOT がない | 手順4 |
| `No module named 'django'` | 手元の Windows で実行している / venv が無効 | EC2 に接続し `source venv/bin/activate` |
| `Directory 'TrainAlertApp' does not exist` | すでにそのフォルダの中にいる | `cd /home/ec2-user/TrainAlertApp` |
| `gunicorn: command not found` | gunicorn 未インストール | `pip install gunicorn` |
| `client_loop: send disconnect` | SSH が切れた | 手順0で再接続 |
| Welcome to nginx! が出る | Nginx 初期設定が優先されている / 再起動忘れ | 手順8の default_server と restart |
| Bad Request (400) | ALLOWED_HOSTS が空 | 手順4 |
| 502 Bad Gateway | gunicorn が動いていない | `sudo systemctl status django` |
| CSS が当たらない / 403 | STATIC_ROOT・alias・権限 | collectstatic、alias のパス、`chmod 711 /home/ec2-user` |

ログの見方:

```
sudo journalctl -u django -n 30 --no-pager     # Django / gunicorn のログ
sudo tail -n 30 /var/log/nginx/error.log       # Nginx のエラーログ
```
