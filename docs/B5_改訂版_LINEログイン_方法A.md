# B-5 改訂版：LINEログイン（方法A：Flask直接認証）

## 変更理由

SupabaseにはLINEプロバイダーが存在しないため、元のタスク（Supabase Auth経由）は実行不可。
Flask側で直接LINE Login OAuthを処理する方式に変更する。

---

## 変更の影響まとめ

| 項目 | 変更内容 |
|------|---------|
| B-5-1 | Supabase Auth設定 → **不要に**。LINE Loginチャネル作成 + Render環境変数のみ |
| B-5-2 | 変更なし（HTMLそのまま） |
| B-5-3 | Supabase Auth経由 → **Flask側で直接LINE OAuth処理** |
| B-5-4 | 変更なし（ログアウトそのまま） |
| RLSポリシー | 全テーブルのRLS → **不要に**（Flask + service_role_key で制御） |
| usersテーブル | id列が `auth.uid()` → **自動生成UUID**に変更 |
| C-1-3以降 | 変更なし（元から `supabase_admin`（service_role_key）を使う設計だった） |

---

## No.37 | B-5-1：LINE Loginチャネル作成 + 環境変数設定（30分）

**⚠️ LINE Login チャネルは Messaging API チャネルとは別物。新しく作る。**

### 手順

**① LINE Loginチャネルを作成する**

1. LINE Developers（https://developers.line.biz）にログイン
2. 既存のプロバイダー「Re:find」を開く
3. 「新規チャネル作成」→ **LINE Login** を選ぶ
4. 設定項目：
   - チャネル名：`Re:find Login`
   - チャネルの説明：`Re:findのWebアプリケーションにLINEアカウントでログインするための認証機能です。`
   - アプリタイプ：**Web app** ✅ にチェック
   - その他：Messaging APIチャネルと同じ内容でOK
5. 作成後、以下をメモ：
   - **Channel ID**（チャネル基本設定に表示される数字）
   - **Channel Secret**（チャネル基本設定の下の方）

**② コールバックURLを設定する**

1. LINE Login チャネルの設定画面を開く
2. 「LINE Login設定」タブを開く
3. 「コールバックURL」に以下を入力：
   ```
   https://re-find.onrender.com/login/callback
   ```
   ※ あなたのRender URLに合わせて変更してください

**③ Renderに環境変数を追加する**

Render ダッシュボード → re-find サービス → Environment タブに以下を追加：

| 変数名 | 値 |
|--------|-----|
| `LINE_LOGIN_CHANNEL_ID` | LINE Login の Channel ID |
| `LINE_LOGIN_CHANNEL_SECRET` | LINE Login の Channel Secret |
| `FLASK_SECRET_KEY` | ランダムな文字列（※下の説明参照） |

**FLASK_SECRET_KEY の作り方：**
Pythonで以下を実行して出てきた文字列をコピーする：
```python
import secrets
print(secrets.token_hex(32))
```
→ これはセッション（ログイン状態の記憶）を暗号化するための鍵。

### 完了チェック

- [ ] LINE Login チャネルが作成されている
- [ ] Channel ID と Channel Secret をメモした
- [ ] コールバックURL `https://re-find.onrender.com/login/callback` が設定されている
- [ ] Render に `LINE_LOGIN_CHANNEL_ID` を追加した
- [ ] Render に `LINE_LOGIN_CHANNEL_SECRET` を追加した
- [ ] Render に `FLASK_SECRET_KEY` を追加した

---

## No.38 | B-5-2：ログイン画面のHTMLを作成する（30分）

**※ 元のタスクから変更なし**

作成するファイル：`templates/login.html`

```html
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Re:find - ログイン</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body class="bg-light">
    <div class="container d-flex justify-content-center align-items-center min-vh-100">
        <div class="text-center">
            <h1 class="mb-4">Re:find</h1>
            <p class="text-muted mb-4">保存した情報を、もう一度見つける</p>
            <a href="/login/line" class="btn btn-success btn-lg px-5 py-3">
                LINEでログイン
            </a>
        </div>
    </div>
</body>
</html>
```

### 完了チェック

- [ ] ログイン画面がスマホで見やすいレイアウトになっている

---

## No.39 | B-5-3：Flaskにログイン処理を実装する（60分）

**⚠️ ここが一番の変更ポイント。元のタスクとはコードが違う。**
**⚠️ 認証まわりは躓きやすい。うまくいかなくても焦らない。**

**最悪の場合のプランB：** LINE user_id 直接入力で仮実装する（後述）。

### ログインの流れ（図解）

```
ユーザー                    Flask                     LINE
  │                         │                         │
  │ ① 「LINEでログイン」押す  │                         │
  │ ──────────────────────→ │                         │
  │                         │ ② LINE認証ページへ転送    │
  │                         │ ──────────────────────→ │
  │                         │                         │
  │ ③ LINEでログイン         │                         │
  │ ──────────────────────────────────────────────→  │
  │                         │                         │
  │                         │ ④ codeを持ってFlaskに戻る │
  │ ←────────────────────── │ ←────────────────────── │
  │                         │                         │
  │                         │ ⑤ codeでアクセストークン取得│
  │                         │ ──────────────────────→ │
  │                         │                         │
  │                         │ ⑥ トークンでプロフィール取得│
  │                         │ ──────────────────────→ │
  │                         │                         │
  │                         │ ⑦ DBに保存 + セッション作成│
  │                         │                         │
  │ ⑧ トップページ表示       │                         │
  │ ←────────────────────── │                         │
```

### 実装コード

**app.py に以下を追加：**

```python
import os
import secrets
import requests as http_requests  # Flask の request と名前が被るので別名にする
from flask import Flask, request, abort, session, redirect, url_for, render_template
from supabase import create_client

app = Flask(__name__)

# ============================================================
# セッション設定（ログイン状態をブラウザに覚えさせるための設定）
# ============================================================
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev-secret-key")
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["PERMANENT_SESSION_LIFETIME"] = 60 * 60 * 24 * 30  # 30日間

# ============================================================
# LINE Login の設定（Messaging API とは別のチャネル）
# ============================================================
LINE_LOGIN_CHANNEL_ID = os.environ.get("LINE_LOGIN_CHANNEL_ID")
LINE_LOGIN_CHANNEL_SECRET = os.environ.get("LINE_LOGIN_CHANNEL_SECRET")
LINE_LOGIN_REDIRECT_URI = os.environ.get(
    "LINE_LOGIN_REDIRECT_URI",
    "https://re-find.onrender.com/login/callback"
)

# ============================================================
# Supabase 管理者クライアント（service_role_key を使用）
# ============================================================
supabase_admin = create_client(
    os.environ.get("SUPABASE_URL"),
    os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
)


# ============================================================
# ログイン画面を表示する
# ============================================================
@app.route("/login")
def login_page():
    """ログイン画面を表示する"""
    # すでにログイン済みならトップページへ
    if session.get("line_user_id"):
        return redirect("/")
    return render_template("login.html")


# ============================================================
# 「LINEでログイン」ボタンを押したときの処理
# ============================================================
@app.route("/login/line")
def login_line():
    """LINEの認証ページにリダイレクトする"""

    # CSRF対策のランダム文字列（なりすまし防止）
    state = secrets.token_urlsafe(32)
    session["oauth_state"] = state

    # LINE の認証ページURL を組み立てる
    auth_url = (
        "https://access.line.me/oauth2/v2.1/authorize"
        f"?response_type=code"
        f"&client_id={LINE_LOGIN_CHANNEL_ID}"
        f"&redirect_uri={LINE_LOGIN_REDIRECT_URI}"
        f"&state={state}"
        f"&scope=profile%20openid"  # プロフィール情報とIDを要求
    )

    # LINEの認証ページへ飛ばす
    return redirect(auth_url)


# ============================================================
# LINEで認証した後、戻ってくる先（コールバック）
# ============================================================
@app.route("/login/callback")
def login_callback():
    """LINEからのコールバックを処理する"""

    # --- エラーチェック ---

    # LINE側でエラーが発生した場合
    error = request.args.get("error")
    if error:
        print(f"LINE認証エラー: {error}")
        return redirect("/login")

    # CSRF対策チェック（送ったstateと返ってきたstateが一致するか）
    state = request.args.get("state")
    if state != session.get("oauth_state"):
        print("stateが一致しません（CSRF攻撃の可能性）")
        return redirect("/login")

    # 認証コードを取得
    code = request.args.get("code")
    if not code:
        print("認証コードがありません")
        return redirect("/login")

    # --- ⑤ 認証コードをアクセストークンに交換する ---

    token_response = http_requests.post(
        "https://api.line.me/oauth2/v2.1/token",
        data={
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": LINE_LOGIN_REDIRECT_URI,
            "client_id": LINE_LOGIN_CHANNEL_ID,
            "client_secret": LINE_LOGIN_CHANNEL_SECRET,
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )

    if token_response.status_code != 200:
        print(f"トークン取得失敗: {token_response.text}")
        return redirect("/login")

    access_token = token_response.json().get("access_token")

    # --- ⑥ アクセストークンでユーザーのプロフィールを取得する ---

    profile_response = http_requests.get(
        "https://api.line.me/v2/profile",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    if profile_response.status_code != 200:
        print(f"プロフィール取得失敗: {profile_response.text}")
        return redirect("/login")

    profile = profile_response.json()
    line_user_id = profile.get("userId")       # 例："U1234abcdef..."
    display_name = profile.get("displayName")  # 例："ちあき"

    print(f"ログイン成功: {display_name} ({line_user_id})")

    # --- ⑦ DBに保存（UPSERT：あれば更新、なければ作成） ---

    try:
        supabase_admin.table("users").upsert({
            "line_user_id": line_user_id,
            "display_name": display_name,
        }, on_conflict="line_user_id").execute()

        # 初回ログイン時のデフォルトデータ作成
        _create_default_data_if_needed(line_user_id)

    except Exception as e:
        print(f"DB保存エラー: {e}")
        # DB保存に失敗してもログインは続行する

    # --- セッションにログイン情報を保存 ---

    session.permanent = True  # 30日間有効にする
    session["line_user_id"] = line_user_id
    session["display_name"] = display_name

    # --- ⑧ トップページへリダイレクト ---
    return redirect("/")


def _create_default_data_if_needed(line_user_id):
    """初回ログイン時にデフォルトのカテゴリ・設定・通知ルールを作成する"""

    # 「未分類」カテゴリがなければ作成
    existing = supabase_admin.table("categories") \
        .select("id") \
        .eq("line_user_id", line_user_id) \
        .eq("name", "未分類") \
        .execute()

    if not existing.data:
        supabase_admin.table("categories").insert({
            "line_user_id": line_user_id,
            "name": "未分類",
        }).execute()

    # user_settings がなければデフォルト作成
    existing_settings = supabase_admin.table("user_settings") \
        .select("id") \
        .eq("line_user_id", line_user_id) \
        .execute()

    if not existing_settings.data:
        supabase_admin.table("user_settings").insert({
            "line_user_id": line_user_id,
            "notify_time": "21:00",
            "notify_enabled": True,
        }).execute()

    # notification_rules がなければデフォルト作成
    existing_rules = supabase_admin.table("notification_rules") \
        .select("id") \
        .eq("line_user_id", line_user_id) \
        .execute()

    if not existing_rules.data:
        supabase_admin.table("notification_rules").insert({
            "line_user_id": line_user_id,
            "category_id": None,
            "item_id": None,
            "rule_type": "interval",
            "config": {"days": [1, 3, 7, 14, 30, 60]},
            "is_active": True,
            "priority": 10,
        }).execute()
```

### ⚠️ /callback のURL衝突に注意！

元の `app.py` には LINE Bot Webhook 用の `/callback` ルートがすでにある。
LINE Login のコールバックは `/login/callback` なので **衝突しない**。

```
/callback         ← LINE Bot（Messaging API）のWebhook受信用。そのまま残す
/login/callback   ← LINE Login のコールバック用。今回新しく追加
```

### 完了チェック

- [ ] `/login` にアクセスするとログイン画面が表示される
- [ ] 「LINEでログイン」を押すとLINEの認証画面に飛ぶ
- [ ] LINEで認証後、トップページに戻ってくる
- [ ] Supabase の users テーブルにレコードが作成されている
- [ ] Supabase の categories テーブルに「未分類」が作成されている

---

## No.40 | B-5-4：ログアウト処理を実装する（15分）

**※ 元のタスクから変更なし**

```python
@app.route("/logout")
def logout():
    """セッションをクリアしてログイン画面に戻す"""
    session.clear()
    return redirect("/login")
```

### 完了チェック

- [ ] ログアウトボタンを押すとログイン画面に戻る
- [ ] ログアウト後にトップページにアクセスするとログイン画面にリダイレクトされる

---

## 追加変更①：usersテーブルの修正

**元の設計：**
```sql
CREATE TABLE users (
    id UUID PRIMARY KEY,  -- ← Supabase Auth の auth.uid()
    line_user_id TEXT NOT NULL UNIQUE,
    display_name TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);
```

**方法A用に変更：**
```sql
CREATE TABLE users (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,  -- ← 自動生成に変更
    line_user_id TEXT NOT NULL UNIQUE,
    display_name TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);
```

変更点は1行だけ：`id` に `DEFAULT gen_random_uuid()` を追加。
`auth.uid()` の代わりに自動でUUIDが生成される。

**⚠️ すでにテーブルを作成済みの場合：**
Supabase管理画面 → SQL Editor で以下を実行：
```sql
ALTER TABLE users ALTER COLUMN id SET DEFAULT gen_random_uuid();
```

---

## 追加変更②：RLSポリシーについて

**方法Aでは、全テーブルのRLSポリシーは設定不要。**

元の設計では `auth.uid()` を使ってRLSで制御していたが、
方法Aでは Supabase Auth を使わないため `auth.uid()` が存在しない。

代わりに、全てのDBアクセスを `service_role_key`（管理者権限）で行い、
Flask側で `session["line_user_id"]` を使ってユーザーを判別する。

```
元の設計：
  ブラウザ → Supabase（RLSが自動でフィルタ）

方法A：
  ブラウザ → Flask（line_user_idでフィルタ）→ Supabase（管理者権限でアクセス）
```

**すでにRLSを有効化している場合：**
そのままでOK。`service_role_key` はRLSをバイパスするので影響なし。

---

## 追加変更③：ヘルパー関数（他のルートで使う）

B-5-3のコードと一緒に、以下のヘルパー関数も追加しておくと便利：

```python
def get_current_user_line_id():
    """現在ログイン中のユーザーの line_user_id を返す。未ログインなら None"""
    return session.get("line_user_id")

def login_required(f):
    """ログインしていないユーザーをログイン画面にリダイレクトするデコレータ"""
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("line_user_id"):
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function
```

使い方：
```python
@app.route("/")
@login_required
def index():
    line_user_id = get_current_user_line_id()
    # ... 一覧データ取得 ...
```

---

## 最悪のプランB：LINE user_id 直接入力で仮実装

もしLINE Login の設定がうまくいかない場合、
開発を止めないために以下の仮実装を使う：

```python
@app.route("/login", methods=["GET", "POST"])
def login_page():
    if request.method == "POST":
        # フォームから line_user_id を手入力して仮ログイン
        line_user_id = request.form.get("line_user_id")
        if line_user_id:
            session.permanent = True
            session["line_user_id"] = line_user_id
            session["display_name"] = "テストユーザー"
            return redirect("/")
    return render_template("login.html")
```

これで LINE Bot 側で表示される user_id をコピペして仮ログインできる。
**本番リリース前に必ずLINE Login に切り替えること。**

---

## 環境変数チェックリスト（更新版）

| 変数名 | 入手場所 | 設定タイミング |
|--------|---------|-------------|
| LINE_CHANNEL_SECRET | LINE Developers → Messaging API | No.10（設定済み） |
| LINE_CHANNEL_ACCESS_TOKEN | LINE Developers → Messaging API | No.10（設定済み） |
| SUPABASE_URL | Supabase → Settings → API | No.20（設定済み） |
| SUPABASE_KEY | Supabase → Settings → API（anon key） | No.20（設定済み） |
| SUPABASE_SERVICE_ROLE_KEY | Supabase → Settings → API（service_role） | No.20（設定済み） |
| OPENROUTER_API_KEY | OpenRouter → Keys | No.21（設定済み） |
| **LINE_LOGIN_CHANNEL_ID** | **LINE Developers → LINE Login** | **No.37（今回追加）** |
| **LINE_LOGIN_CHANNEL_SECRET** | **LINE Developers → LINE Login** | **No.37（今回追加）** |
| **FLASK_SECRET_KEY** | **Pythonで生成** | **No.37（今回追加）** |

---

## データの流れ：初回LINEログイン時（改訂版）

```
① Webアプリで「LINEでログイン」をタップ

② Flask が LINE Login の認証URLにリダイレクト

③ ユーザーが LINE でログイン（ID/パスワード or 自動認証）

④ LINE が認証コード付きで Flask の /login/callback に戻す

⑤ Flask が認証コードをアクセストークンに交換

⑥ Flask がアクセストークンでプロフィール（line_user_id, display_name）を取得

⑦ users テーブルに UPSERT
   line_user_id='U1234...', display_name='ちあき'

⑧ user_settings テーブルにデフォルト設定を INSERT
   line_user_id='U1234...', notify_time='21:00', notify_enabled=TRUE

⑨ categories テーブルに「未分類」カテゴリを INSERT
   line_user_id='U1234...', name='未分類'

⑩ notification_rules テーブルにデフォルトルールを INSERT
   line_user_id='U1234...', config={"days": [1, 3, 7, 14, 30, 60]}

⑪ セッションに line_user_id と display_name を保存

⑫ ログイン完了 → Webアプリのトップページを表示
```

**元の設計との違い：** ②〜⑥ が「Supabase Auth経由」から「Flask直接処理」に変わっただけ。
⑦以降のDB操作は元の設計とほぼ同じ。
