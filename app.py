# ============================================
# Re:find - LINE Bot Webhook サーバー
# ============================================
# LINEに送ったメッセージをFlaskで受け取り、
# AIで分類した結果を返信するコード

import os  # 環境変数を読み込むためのライブラリ
import re  # URL判定の正規表現に使用（B-4-2）
import uuid
import secrets  # CSRF対策用（B-5）
from functools import wraps  # login_required デコレータ用（B-5）
import requests as http_requests  # LINE Login API用（Flask の request と名前が被るので別名）
from dotenv import load_dotenv  # .env を読むため
from flask import Flask, request, abort, session, redirect, render_template  # Webサーバーの基本機能

from datetime import datetime, timedelta, timezone  # 日時用

from supabase import create_client  # Supabase接続

# --- LINE Bot SDK の必要なパーツを読み込む ---
from linebot.v3 import WebhookHandler  # LINEからの通知を処理する
from linebot.v3.messaging import (
    Configuration,          # LINE APIの設定情報を管理
    ApiClient,              # LINE APIと通信するためのクライアント
    MessagingApi,           # メッセージ送受信の機能
    MessagingApiBlob,       # 画像などのバイナリ取得用（B-3）
    ReplyMessageRequest,    # 返信メッセージのリクエスト
    TextMessage,            # テキストメッセージ
)
from linebot.v3.webhooks import (
    MessageEvent,           # 「メッセージが届いた」というイベント
    TextMessageContent,     # テキストメッセージの中身
    ImageMessageContent,    # 画像メッセージの中身（B-3）
    # --- 非対応メッセージタイプ（B-4-3）---
    StickerMessageContent,  # スタンプ
    VideoMessageContent,    # 動画
    AudioMessageContent,    # 音声
    LocationMessageContent, # 位置情報
    FileMessageContent,     # ファイル
)
from linebot.v3.exceptions import InvalidSignatureError  # 署名エラー用

from ai_classifier import classify_text, classify_image  # AI分類の共通関数
from storage_handler import upload_image  # 画像アップロード（B-3）
from ogp_fetcher import fetch_ogp  # OGP取得（B-4-2）
from activity_logger import log_activity  # 行動ログ記録（B-4-5）

# ============================================
# .env 読み込み（ローカル開発用）
# ============================================
load_dotenv()  # これで .env を読み込む（ローカル時のみ）

app = Flask(__name__)

# ============================================
# セッション設定（B-5：ログイン状態をブラウザに覚えさせる）
# ============================================
# secret_key: セッションデータを暗号化するための秘密鍵
#   → 本番では FLASK_SECRET_KEY 環境変数に secrets.token_hex(32) で生成した値を設定する
#   → "dev-secret-key" はローカル開発用のフォールバック
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev-secret-key")
# SameSite=Lax: 外部サイトからのリンク遷移時にCookieを送る（LINE認証コールバックで必要）
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
# セッションの有効期限: 30日間（秒単位で指定）
# → この設定がないとブラウザを閉じるたびにログアウトされてしまう
app.config["PERMANENT_SESSION_LIFETIME"] = 60 * 60 * 24 * 30  # 30日間

# JST
JST = timezone(timedelta(hours=9))

# ============================================
# Supabase 管理用クライアント（service_role 用）
# ============================================

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
    raise RuntimeError("SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY が設定されていません")

supabase_admin = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

# ============================================
# LINE Login の設定（B-5：Messaging API とは別のチャネル）
# ============================================
# ⚠️ LINE Login チャネルは Messaging API チャネルとは別物
#   → LINE Developers で「LINE Login」タイプのチャネルを新規作成して取得する
LINE_LOGIN_CHANNEL_ID = os.environ.get("LINE_LOGIN_CHANNEL_ID")        # LINE Login の Channel ID
LINE_LOGIN_CHANNEL_SECRET = os.environ.get("LINE_LOGIN_CHANNEL_SECRET")  # LINE Login の Channel Secret
# LIFF ID: LINE DevelopersのLIFFタブで作成したアプリのID
LIFF_ID = os.environ.get("LIFF_ID")
# コールバックURL: LINEで認証した後、ユーザーが戻ってくる先
#   → LINE Developers の「コールバックURL」にも同じURLを設定する必要がある
LINE_LOGIN_REDIRECT_URI = os.environ.get(
    "LINE_LOGIN_REDIRECT_URI",
    "https://re-find.onrender.com/login/callback"  # デフォルト値（Render のURL）
)

# ============================================
# LINE Bot の設定
# ============================================
channel_access_token = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")
channel_secret = os.environ.get("LINE_CHANNEL_SECRET")

if not channel_access_token or not channel_secret:
    raise RuntimeError(
        "LINE_CHANNEL_SECRET / LINE_CHANNEL_ACCESS_TOKEN が設定されていません"
    )

configuration = Configuration(access_token=channel_access_token)
handler = WebhookHandler(channel_secret)

# ============================================
# ヘルパー関数（B-5：認証まわり）
# ============================================

def get_current_user_line_id():
    """
    現在ログイン中のユーザーの line_user_id を返す。未ログインなら None。
    使い方: line_user_id = get_current_user_line_id()
    """
    return session.get("line_user_id")


def login_required(f):
    """
    ログインしていないユーザーをログイン画面にリダイレクトするデコレータ。
    使い方:
        @app.route("/protected")
        @login_required
        def protected_page():
            ...
    """
    @wraps(f)  # 元の関数名やdocstringを保持する
    def decorated_function(*args, **kwargs):
        if not session.get("line_user_id"):
            return redirect("/login")  # 未ログイン → ログイン画面へ
        return f(*args, **kwargs)  # ログイン済み → 元の関数を実行
    return decorated_function


# ============================================
# ルート（URL）の設定
# ============================================

@app.route("/")
@login_required
def index():
    """トップページ（ログイン必須）"""
    return "Re:find is running."


# ============================================
# ログイン・ログアウト（B-5）
# ============================================

@app.route("/login")
def login_page():
    """ログイン画面を表示する"""
    # すでにログイン済みならトップページへ飛ばす（二重ログイン防止）
    if session.get("line_user_id"):
        return redirect("/")
    return render_template("login.html")


@app.route("/login/line")
def login_line():
    """
    「LINEでログイン」ボタンを押したときの処理。
    LINEの認証ページ（authorize URL）にリダイレクトする。
    """
    # CSRF対策: ランダムな文字列を生成してセッションに保存
    # → コールバック時に同じ値が返ってくるか検証する（なりすまし防止）
    state = secrets.token_urlsafe(32)
    session["oauth_state"] = state

    # LINE の認証ページURL を組み立てる
    # response_type=code → 認証コードフローを使用
    # scope=profile openid → プロフィール情報とIDを要求
    auth_url = (
        "https://access.line.me/oauth2/v2.1/authorize"
        f"?response_type=code"
        f"&client_id={LINE_LOGIN_CHANNEL_ID}"
        f"&redirect_uri={LINE_LOGIN_REDIRECT_URI}"
        f"&state={state}"
        f"&scope=profile%20openid"
    )
    # LINEの認証ページへ飛ばす
    return redirect(auth_url)


@app.route("/login/callback")
def login_callback():
    """
    LINEで認証した後、戻ってくる先（コールバック）。
    ⚠️ /callback（LINE Bot Webhook）とは別のルート。衝突しない。

    処理の流れ:
      ④ LINEからcodeを受け取る
      ⑤ codeをアクセストークンに交換する
      ⑥ アクセストークンでプロフィールを取得する
      ⑦ DBに保存（UPSERT） + デフォルトデータ作成
      ⑧ セッションに保存してトップページへリダイレクト
    """

    # --- エラーチェック ---

    # LINE側でエラーが発生した場合（ユーザーがキャンセルした等）
    error = request.args.get("error")
    if error:
        app.logger.error(f"LINE認証エラー: {error}")
        return redirect("/login")

    # CSRF対策チェック（送ったstateと返ってきたstateが一致するか）
    state = request.args.get("state")
    if state != session.get("oauth_state"):
        app.logger.error("stateが一致しません（CSRF攻撃の可能性）")
        return redirect("/login")

    # ④ LINEから認証コードを取得
    code = request.args.get("code")
    if not code:
        app.logger.error("認証コードがありません")
        return redirect("/login")

    # --- ⑤ 認証コードをアクセストークンに交換する ---
    # LINE の token API に POST リクエストを送る
    token_response = http_requests.post(
        "https://api.line.me/oauth2/v2.1/token",
        data={
            "grant_type": "authorization_code",  # 認証コードフロー
            "code": code,                          # LINEからもらった認証コード
            "redirect_uri": LINE_LOGIN_REDIRECT_URI,  # コールバックURL（一致必須）
            "client_id": LINE_LOGIN_CHANNEL_ID,        # LINE Login の Channel ID
            "client_secret": LINE_LOGIN_CHANNEL_SECRET,  # LINE Login の Channel Secret
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )

    if token_response.status_code != 200:
        app.logger.error(f"トークン取得失敗: {token_response.text}")
        return redirect("/login")

    # レスポンスからアクセストークンを取り出す
    access_token = token_response.json().get("access_token")

    # --- ⑥ アクセストークンでユーザーのプロフィールを取得する ---
    # LINE の profile API に GET リクエストを送る
    profile_response = http_requests.get(
        "https://api.line.me/v2/profile",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    if profile_response.status_code != 200:
        app.logger.error(f"プロフィール取得失敗: {profile_response.text}")
        return redirect("/login")

    profile = profile_response.json()
    line_user_id = profile.get("userId")       # 例："U1234abcdef..."
    display_name = profile.get("displayName")  # 例："ちあき"

    app.logger.info(f"ログイン成功: {display_name} ({line_user_id})")

    # --- ⑦ DBに保存（UPSERT：あれば更新、なければ作成） ---
    try:
        # users テーブルに line_user_id と display_name を保存
        # on_conflict="line_user_id" → 同じユーザーが再ログインしたら display_name を更新
        supabase_admin.table("users").upsert({
            "line_user_id": line_user_id,
            "display_name": display_name,
        }, on_conflict="line_user_id").execute()

        # 初回ログイン時のみ: デフォルトのカテゴリ・設定・通知ルールを作成
        _create_default_data_if_needed(line_user_id)

    except Exception as e:
        app.logger.error(f"DB保存エラー: {e}")
        # DB保存に失敗してもログインは続行する（ユーザー体験を優先）

    # --- ⑧ セッションにログイン情報を保存 ---
    session.permanent = True  # 30日間有効にする（PERMANENT_SESSION_LIFETIME で設定した期間）
    session["line_user_id"] = line_user_id    # 他のルートでユーザー判別に使う
    session["display_name"] = display_name    # 画面表示用

    # トップページへリダイレクト
    return redirect("/")


@app.route("/logout")
def logout():
    """セッションを全てクリアしてログイン画面に戻す"""
    session.clear()  # line_user_id, display_name, oauth_state などを全削除
    return redirect("/login")


# ============================================
# LIFF（LINEアプリ内シームレスログイン）
# ============================================

@app.route("/liff")
def liff_entry():
    """
    LINEアプリ内から開いた場合のエントリポイント。
    LIFF SDKを使ってLINEのプロフィール情報を自動取得し、
    セッションを発行してから一覧画面へリダイレクトする。
    外部ブラウザからアクセスした場合は通常のログインフローにフォールバック。
    """
    if not LIFF_ID:
        app.logger.error("LIFF_ID が設定されていません")
        return redirect("/login")
    return render_template("liff.html", liff_id=LIFF_ID)


@app.route("/api/liff-login", methods=["POST"])
def liff_login():
    """LIFFから受け取ったユーザー情報でセッションを発行"""
    data = request.json
    line_user_id = data.get("userId")
    display_name = data.get("displayName")

    if not line_user_id:
        return {"error": "userId is required"}, 400

    # DB保存（通常ログインと同じ処理）
    try:
        supabase_admin.table("users").upsert({
            "line_user_id": line_user_id,
            "display_name": display_name,
        }, on_conflict="line_user_id").execute()

        _create_default_data_if_needed(line_user_id)
    except Exception as e:
        app.logger.error(f"LIFF DB保存エラー: {e}")

    # セッション発行（通常のログインと同じ状態にする）
    session.permanent = True
    session["line_user_id"] = line_user_id
    session["display_name"] = display_name

    return {"ok": True}


def _create_default_data_if_needed(line_user_id):
    """
    初回ログイン時にデフォルトのカテゴリ・設定・通知ルールを作成する。
    すでにデータがある場合（2回目以降のログイン）は何もしない。
    """

    # --- 「未分類」カテゴリがなければ作成 ---
    # LINE Bot でメッセージを送ったとき、カテゴリが判定できなかった場合に使われる
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

    # --- user_settings がなければデフォルト作成 ---
    # 通知時間のデフォルト: 21:00（夜9時）
    existing_settings = supabase_admin.table("user_settings") \
        .select("id") \
        .eq("line_user_id", line_user_id) \
        .execute()

    if not existing_settings.data:
        supabase_admin.table("user_settings").insert({
            "line_user_id": line_user_id,
            "notify_time": "21:00",      # デフォルトの通知時刻
            "notify_enabled": True,       # 通知ON
        }).execute()

    # --- notification_rules がなければデフォルト作成 ---
    # 忘却曲線ベースの通知間隔: 1日後、3日後、7日後、14日後、30日後、60日後
    existing_rules = supabase_admin.table("notification_rules") \
        .select("id") \
        .eq("line_user_id", line_user_id) \
        .execute()

    if not existing_rules.data:
        supabase_admin.table("notification_rules").insert({
            "line_user_id": line_user_id,
            "category_id": None,      # 全カテゴリ共通のルール
            "item_id": None,          # 全アイテム共通のルール
            "rule_type": "interval",  # 間隔ベースの通知
            "config": {"days": [1, 3, 7, 14, 30, 60]},  # 忘却曲線に基づく日数
            "is_active": True,        # ルール有効
            "priority": 10,           # 優先度（数値が大きいほど優先）
        }).execute()


# ============================================
# LINE Bot Webhook（Messaging API）
# ============================================

@app.route("/callback", methods=["POST"])
def callback():
    """
    LINEからのWebhook（通知）を受け取る入口
    """
    # ① リクエストヘッダーから署名を取得
    signature = request.headers.get("X-Line-Signature", "")

    # ② リクエストの本文（メッセージデータ）を取得
    body = request.get_data(as_text=True)
    print("受信:", body)  # ログに表示（デバッグ用）
    app.logger.info(f"[callback] body: {body}")

    # ③ 署名を検証して、メッセージを処理する
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        app.logger.error("署名エラー: 不正なリクエスト")
        abort(400)
    except Exception as e:
        app.logger.error(f"その他エラー: {e}")
        abort(500)

    return "OK"


# ============================================
# URL判定ユーティリティ（B-4-2）
# ============================================

def is_url(text):
    """
    テキストにURLが含まれているか判定し、最初のURLを返す。
    URLが見つからなければ None を返す。

    例:
        is_url("https://example.com の記事")  → "https://example.com"
        is_url("今日は天気がいい")              → None
    """
    url_pattern = r'https?://[^\s]+'
    match = re.search(url_pattern, text)
    return match.group() if match else None


# ============================================
# メッセージ受信時の処理（ここでAI分類）
# ============================================

@handler.add(MessageEvent, message=TextMessageContent)
def handle_text_message(event):
    user_id = event.source.user_id
    text = event.message.text
    app.logger.info(f"[テキスト受信] user={user_id}, text={text}")

    # デフォルトの返信（エラー時にユーザーへ返すメッセージ）（B-4-4）
    reply_text = "⚠️ 保存中にエラーが発生しました。\nもう一度お試しください。"

    # --- URL判定（B-4-2）---
    # テキストにURLが含まれていれば URL処理、なければ従来のテキスト処理
    url = is_url(text)

    # --- AI & DB 部分 ---
    try:
        # ① ユーザーの既存カテゴリ一覧を取得
        cats = supabase_admin.table("categories") \
            .select("*") \
            .eq("line_user_id", user_id) \
            .execute()

        if getattr(cats, "error", None):
            app.logger.error(f"[supabase] categories error: {cats.error}")
            existing = {}
        else:
            existing = {c["name"]: c["id"] for c in (cats.data or [])}

        category_names = list(existing.keys())

        # ===== URL処理（B-4-2）=====
        if url:
            app.logger.info(f"[URL検出] url={url}")

            # ② OGP情報を取得（タイトル・説明・サムネイル）
            ogp = fetch_ogp(url)
            app.logger.info(f"[OGP取得結果] title={ogp['title']}, image={ogp['image']}")

            # ③ OGPのタイトル＋説明文を結合してAI分類に渡す
            ai_input = f"{ogp['title']}。{ogp['description']}"
            result = classify_text(ai_input, category_names)
            title = result.get("title", ogp["title"][:30])
            category_name = result.get("category", "未分類")

            app.logger.info(f"[AI分類結果(URL)] title={title}, category={category_name}")

        # ===== テキスト処理（従来のロジック）=====
        else:
            # ② AI分類（テキストをそのまま渡す）
            result = classify_text(text, category_names)
            title = result.get("title", text[:30])
            category_name = result.get("category", "未分類")

            app.logger.info(f"[AI分類結果] title={title}, category={category_name}")

        # ③ カテゴリなければ作成（URL・テキスト共通）
        if category_name in existing:
            category_id = existing[category_name]
        else:
            new_cat = supabase_admin.table("categories") \
                .insert({"line_user_id": user_id, "name": category_name}) \
                .execute()

            if getattr(new_cat, "error", None):
                app.logger.error(f"[supabase] insert category error: {new_cat.error}")
                category_id = None
            else:
                category_id = new_cat.data[0]["id"]
                app.logger.info(f"[カテゴリ作成] {category_name} (id={category_id})")

        # ④ items に保存（明日21時に通知）
        tomorrow_9pm = (datetime.now(JST) + timedelta(days=1)).replace(
            hour=21, minute=0, second=0, microsecond=0
        )

        # URL と テキストで保存するデータを分ける
        if url:
            # URL用：original_url, description(OGP説明文), ogp_image を保存
            item_data = {
                "line_user_id": user_id,
                "type": "url",
                "original_url": url,
                "title": title,
                "description": ogp["description"],
                "ogp_image": ogp["image"],
                "status": "pending",
                "next_notify_at": tomorrow_9pm.isoformat(),
            }
        else:
            # テキスト用：従来通り
            item_data = {
                "line_user_id": user_id,
                "type": "text",
                "title": title,
                "description": text,
                "status": "pending",
                "next_notify_at": tomorrow_9pm.isoformat(),
            }

        if category_id:
            item_data["category_id"] = category_id

        insert_res = supabase_admin.table("items").insert(item_data).execute()
        if getattr(insert_res, "error", None):
            app.logger.error(f"[supabase] insert item error: {insert_res.error}")

        # ここまで全部成功したときだけ、AI結果ベースの返信文に上書き
        if url:
            reply_text = f"🔗 「{category_name}」に保存しました！\nタイトル: {title}"
        else:
            reply_text = f"📝 「{category_name}」に保存しました！\nタイトル: {title}"

        # 行動ログを記録（B-4-5）
        msg_type = "url" if url else "text"
        log_activity(user_id, "bot_message", metadata={"message_type": msg_type})

    except Exception as e:
        # AI or Supabase で失敗したとき
        app.logger.error(f"[handler] unexpected error (AI/DB): {e}")

    # --- LINEへの返信 ---
    try:
        with ApiClient(configuration) as api_client:
            line_bot_api = MessagingApi(api_client)
            line_bot_api.reply_message(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[TextMessage(text=reply_text)],
                )
            )

        app.logger.info("[handler] reply_message sent")

    except Exception as e:
        app.logger.error(f"[handler] unexpected error (reply): {e}")


# ============================================
# 画像受信時の処理（B-3 で追加）
# ============================================

@handler.add(MessageEvent, message=ImageMessageContent)
def handle_image_message(event):
    user_id = event.source.user_id
    message_id = event.message.id
    app.logger.info(f"[画像受信] user={user_id}, message_id={message_id}")

    # デフォルトの返信（エラー時にユーザーへ返すメッセージ）（B-4-4）
    reply_text = "⚠️ 保存中にエラーが発生しました。\nもう一度お試しください。"

    # --- 画像取得 → Storage → AI解析 → DB保存 ---
    try:
        # ① LINEから画像データをダウンロード（v3 SDK の MessagingApiBlob を使用）
        try:
            with ApiClient(configuration) as api_client:
                blob_api = MessagingApiBlob(api_client)
                image_bytes = blob_api.get_message_content(message_id)
        except Exception as e:
            # 画像ダウンロード失敗は専用メッセージで返す（B-4-4）
            app.logger.error(f"[handler] 画像ダウンロード失敗: {e}")
            reply_text = "⚠️ 画像を取得できませんでした。\nもう一度送信してみてください。"
            raise  # 外側の except に伝搬して処理を中断する

        # ② UUID発行（DB用）
        item_id = str(uuid.uuid4())

        # ③ Supabase Storageへ保存
        image_url = upload_image(user_id, item_id, image_bytes)

        # ④ 既存カテゴリ取得
        cats = supabase_admin.table("categories") \
            .select("*") \
            .eq("line_user_id", user_id) \
            .execute()

        if getattr(cats, "error", None):
            app.logger.error(f"[supabase] categories error: {cats.error}")
            existing = {}
        else:
            existing = {c["name"]: c["id"] for c in (cats.data or [])}

        # ⑤ AI解析（画像からタイトル・カテゴリを生成）
        ai_result = classify_image(image_bytes, list(existing.keys()))
        title = ai_result.get("title", "画像メモ")
        category_name = ai_result.get("category", "未分類")

        app.logger.info(f"[AI画像分類結果] title={title}, category={category_name}")

        # ⑥ カテゴリなければ作成
        if category_name in existing:
            category_id = existing[category_name]
        else:
            new_cat = supabase_admin.table("categories") \
                .insert({"line_user_id": user_id, "name": category_name}) \
                .execute()

            if getattr(new_cat, "error", None):
                app.logger.error(f"[supabase] insert category error: {new_cat.error}")
                category_id = None
            else:
                category_id = new_cat.data[0]["id"]
                app.logger.info(f"[カテゴリ作成] {category_name} (id={category_id})")

        # ⑦ items に保存（明日21時に通知）
        tomorrow_9pm = (datetime.now(JST) + timedelta(days=1)).replace(
            hour=21, minute=0, second=0, microsecond=0
        )

        item_data = {
            "id": item_id,
            "line_user_id": user_id,
            "type": "image",
            "title": title,
            "image_url": image_url,
            "status": "pending",
            "next_notify_at": tomorrow_9pm.isoformat(),
        }
        if category_id:
            item_data["category_id"] = category_id

        insert_res = supabase_admin.table("items").insert(item_data).execute()
        if getattr(insert_res, "error", None):
            app.logger.error(f"[supabase] insert item error: {insert_res.error}")

        # ここまで全部成功したときだけ、AI結果ベースの返信文に上書き
        reply_text = f"📷 「{category_name}」に保存しました！\nタイトル: {title}"

        # 行動ログを記録（B-4-5）
        log_activity(user_id, "bot_message", metadata={"message_type": "image"})

    except Exception as e:
        # 画像処理で失敗したとき（B-4-4）
        # 画像ダウンロード失敗の場合は既に専用メッセージがセットされているので
        # それ以外のエラー（Storage・AI・DB等）の場合のみ上書きする
        app.logger.error(f"[handler] unexpected error (画像処理): {e}")
        if "画像を取得できませんでした" not in reply_text:
            reply_text = "⚠️ 保存に失敗しました。\nもう一度お試しください。"

    # --- LINEへの返信 ---
    try:
        with ApiClient(configuration) as api_client:
            line_bot_api = MessagingApi(api_client)
            line_bot_api.reply_message(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[TextMessage(text=reply_text)],
                )
            )

        app.logger.info("[handler] reply_message sent (画像)")

    except Exception as e:
        app.logger.error(f"[handler] unexpected error (reply): {e}")


# ============================================
# 非対応メッセージの共通ハンドラ（B-4-3）
# ============================================
# スタンプ・動画・音声・位置情報・ファイルは現在非対応。
# 対応していないメッセージが送られたとき、案内メッセージを返す。

for msg_type in [StickerMessageContent, VideoMessageContent,
                 AudioMessageContent, LocationMessageContent,
                 FileMessageContent]:
    @handler.add(MessageEvent, message=msg_type)
    def handle_unsupported(event):
        """非対応メッセージを受信したときの共通ハンドラ"""
        try:
            with ApiClient(configuration) as api_client:
                line_bot_api = MessagingApi(api_client)
                line_bot_api.reply_message(
                    ReplyMessageRequest(
                        reply_token=event.reply_token,
                        messages=[TextMessage(
                            text="📌 現在は画像・URL・テキストに対応しています。\nスクショやURLを送ってみてください！"
                        )]
                    )
                )
        except Exception as e:
            app.logger.error(f"[handler] 非対応メッセージ返信エラー: {e}")


# ============================================
# サーバー起動（ローカル実行用）
# ============================================
if __name__ == "__main__":
    # ローカルで python app.py を実行したときだけ動く
    app.run(debug=True)