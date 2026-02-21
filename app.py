# ============================================
# Re:find - LINE Bot Webhook サーバー
# ============================================
# LINEに送ったメッセージをFlaskで受け取り、
# AIで分類した結果を返信するコード

import os  # 環境変数を読み込むためのライブラリ
import re  # URL判定の正規表現に使用（B-4-2）
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