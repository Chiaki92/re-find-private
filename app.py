# ============================================
# Re:find - LINE Bot Webhook サーバー
# ============================================
# LINEに送ったメッセージをFlaskで受け取り、
# AIで分類した結果を返信するコード

import os  # 環境変数を読み込むためのライブラリ
import uuid
from dotenv import load_dotenv  # .env を読むため
from flask import Flask, request, abort  # Webサーバーの基本機能

from datetime import datetime, timedelta, timezone  # 日時用

from supabase import create_client  # Supabase接続

# --- LINE Bot SDK の必要なパーツを読み込む ---
from linebot.v3 import WebhookHandler  # LINEからの通知を処理する
from linebot.v3.messaging import (
    Configuration,          # LINE APIの設定情報を管理
    ApiClient,              # LINE APIと通信するためのクライアント
    MessagingApi,           # メッセージ送受信の機能
    ReplyMessageRequest,    # 返信メッセージのリクエスト
    TextMessage,            # テキストメッセージ
)
from linebot.v3.webhooks import (
    MessageEvent,           # 「メッセージが届いた」というイベント
    TextMessageContent,     # テキストメッセージの中身
)
from linebot.v3.exceptions import InvalidSignatureError  # 署名エラー用

from ai_classifier import classify_text  # AI分類の共通関数

# ============================================
# .env 読み込み（ローカル開発用）
# ============================================
load_dotenv()  # これで .env を読み込む（ローカル時のみ）

app = Flask(__name__)

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
# ルート（URL）の設定
# ============================================

@app.route("/")
def index():
    """
    トップページ（動作確認用）
    """
    return "Re:find is running."


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
# メッセージ受信時の処理（ここでAI分類）
# ============================================

@handler.add(MessageEvent, message=TextMessageContent)
def handle_text_message(event):
    user_id = event.source.user_id
    text = event.message.text
    app.logger.info(f"[テキスト受信] user={user_id}, text={text}")

    # デフォルトの返信（どこかで失敗しても、最低これだけは返す）
    reply_text = f"メッセージを受信しました：{text}"

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

        # ② AI分類
        result = classify_text(text, category_names)
        title = result.get("title", text[:30])
        category_name = result.get("category", "未分類")

        app.logger.info(f"[AI分類結果] title={title}, category={category_name}")

        # ③ カテゴリなければ作成
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
        reply_text = f"📝 「{category_name}」に保存しました！\nタイトル: {title}"

    except Exception as e:
        # AI or Supabase で失敗したとき
        app.logger.error(f"[handler] unexpected error (AI/DB): {e}")
        # reply_text はデフォルトのまま（「メッセージ受信しました」）

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
# サーバー起動（ローカル実行用）
# ============================================
if __name__ == "__main__":
    # ローカルで python app.py を実行したときだけ動く
    app.run(debug=True)

from linebot import LineBotApi, WebhookHandler
from linebot.models import MessageEvent, ImageMessage, TextSendMessage
from linebot.exceptions import InvalidSignatureError

from storage_handler import upload_image
from ai_classifier import classify_image

app = Flask(__name__)

# ===============================
# LINE設定
# ===============================
line_bot_api = LineBotApi(os.environ["LINE_CHANNEL_ACCESS_TOKEN"])
handler = WebhookHandler(os.environ["LINE_CHANNEL_SECRET"])

# ===============================
# Supabase接続
# ===============================
supabase = create_client(
    os.environ["SUPABASE_URL"],
    os.environ["SUPABASE_SERVICE_ROLE_KEY"]
)


# ===============================
# LINE Webhook
# ===============================
@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers["X-Line-Signature"]
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return "OK"


# ===============================
# 画像受信処理
# ===============================
@handler.add(MessageEvent, message=ImageMessage)
def handle_image(event):

    user_id = event.source.user_id
    message_id = event.message.id

    try:
        # -------------------------------
        # ① LINEから画像を取得
        # -------------------------------
        message_content = line_bot_api.get_message_content(message_id)
        image_bytes = b"".join(chunk for chunk in message_content.iter_content())

        # -------------------------------
        # ② UUID発行（DB用）
        # -------------------------------
        item_id = str(uuid.uuid4())

        # -------------------------------
        # ③ Storageへ保存
        # -------------------------------
        image_url = upload_image(user_id, item_id, image_bytes)

        # -------------------------------
        # ④ 既存カテゴリ取得
        # -------------------------------
        res = supabase.table("categories") \
            .select("id,name") \
            .eq("user_id", user_id) \
            .execute()

        category_map = {row["name"]: row["id"] for row in res.data} if res.data else {}

        # -------------------------------
        # ⑤ AI解析
        # -------------------------------
        ai_result = classify_image(image_bytes, list(category_map.keys()))
        title = ai_result["title"]
        category_name = ai_result["category"]

        # -------------------------------
        # ⑥ カテゴリID確定
        # -------------------------------
        if category_name in category_map:
            category_id = category_map[category_name]
        else:
            new_cat = supabase.table("categories").insert({
                "user_id": user_id,
                "name": category_name
            }).execute()
            category_id = new_cat.data[0]["id"]

        # -------------------------------
        # ⑦ itemsテーブルに保存
        # -------------------------------
        supabase.table("items").insert({
            "id": item_id,
            "user_id": user_id,
            "title": title,
            "category_id": category_id,
            "type": "image",
            "image_url": image_url,
            "status": "pending",
            "next_notify_at": (
                datetime.datetime.utcnow()
                + datetime.timedelta(days=1)
            ).isoformat()
        }).execute()

        reply_text = f"📷 {category_name} に保存しました！"

    except Exception as e:
        print("画像処理エラー:", e)
        reply_text = "保存に失敗しました。もう一度試してください。"

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply_text)
    )


if __name__ == "__main__":
    app.run()