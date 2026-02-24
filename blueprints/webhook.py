# ============================================
# LINE Bot Webhook Blueprint
# ============================================

import re
import uuid
import logging
from datetime import datetime, timedelta
from flask import Blueprint, request, abort, current_app
from linebot.v3.messaging import (
    ApiClient, MessagingApi, MessagingApiBlob,
    ReplyMessageRequest, TextMessage,
)
from linebot.v3.webhooks import (
    MessageEvent, TextMessageContent, ImageMessageContent,
    StickerMessageContent, VideoMessageContent, AudioMessageContent,
    LocationMessageContent, FileMessageContent,
)
from linebot.v3.exceptions import InvalidSignatureError

from extensions import supabase_admin, line_configuration, line_handler, JST
from ai_classifier import classify_text, classify_image
from storage_handler import upload_image
from ogp_fetcher import fetch_ogp
from activity_logger import log_activity

logger = logging.getLogger(__name__)

webhook_bp = Blueprint("webhook", __name__)


# ============================================
# URL判定ユーティリティ
# ============================================

def is_url(text):
    """テキストにURLが含まれているか判定し、最初のURLを返す。"""
    url_pattern = r'https?://[^\s]+'
    match = re.search(url_pattern, text)
    return match.group() if match else None


# ============================================
# Webhook エンドポイント
# ============================================

@webhook_bp.route("/callback", methods=["POST"])
def callback():
    """LINEからのWebhookを受け取る入口"""
    signature = request.headers.get("X-Line-Signature", "")
    body = request.get_data(as_text=True)
    logger.info(f"[callback] body: {body}")

    try:
        line_handler.handle(body, signature)
    except InvalidSignatureError:
        logger.error("署名エラー: 不正なリクエスト")
        abort(400)
    except Exception as e:
        logger.error(f"その他エラー: {e}")
        abort(500)

    return "OK"


# ============================================
# テキストメッセージ受信
# ============================================

@line_handler.add(MessageEvent, message=TextMessageContent)
def handle_text_message(event):
    user_id = event.source.user_id
    text = event.message.text
    logger.info(f"[テキスト受信] user={user_id}, text={text}")

    reply_text = "⚠️ 保存中にエラーが発生しました。\nもう一度お試しください。"

    # 使い方ガイドのキーワードに反応する
    if "使い方" in text:
        usage_text = (
            "📌 Re:find の使い方\n\n"
            "送るだけで自動保存！\n"
            "🖼 画像（スクリーンショット）\n"
            "🔗 URL\n"
            "📝 テキスト（メモ）\n\n"
            "保存した情報は毎日リマインドが届きます。\n"
            "忘れてたことを再発見できますよ！"
        )
        with ApiClient(line_configuration) as api_client:
            line_bot_api = MessagingApi(api_client)
            line_bot_api.reply_message(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[TextMessage(text=usage_text)],
                )
            )
        return

    url = is_url(text)

    try:
        # ① ユーザーの既存カテゴリ一覧を取得
        cats = supabase_admin.table("categories") \
            .select("*") \
            .eq("line_user_id", user_id) \
            .execute()

        if getattr(cats, "error", None):
            logger.error(f"[supabase] categories error: {cats.error}")
            existing = {}
        else:
            existing = {c["name"]: c["id"] for c in (cats.data or [])}

        category_names = list(existing.keys())

        # ===== URL処理 =====
        if url:
            logger.info(f"[URL検出] url={url}")

            ogp = fetch_ogp(url)
            logger.info(f"[OGP取得結果] title={ogp['title']}, image={ogp['image']}")

            ai_input = f"{ogp['title']}。{ogp['description']}"
            result = classify_text(ai_input, category_names)
            title = result.get("title", ogp["title"][:30])
            category_name = result.get("category", "未分類")

            logger.info(f"[AI分類結果(URL)] title={title}, category={category_name}")

        # ===== テキスト処理 =====
        else:
            result = classify_text(text, category_names)
            title = result.get("title", text[:30])
            category_name = result.get("category", "未分類")

            logger.info(f"[AI分類結果] title={title}, category={category_name}")

        # ③ カテゴリなければ作成
        if category_name in existing:
            category_id = existing[category_name]
        else:
            new_cat = supabase_admin.table("categories") \
                .insert({"line_user_id": user_id, "name": category_name}) \
                .execute()

            if getattr(new_cat, "error", None):
                logger.error(f"[supabase] insert category error: {new_cat.error}")
                category_id = None
            else:
                category_id = new_cat.data[0]["id"]
                logger.info(f"[カテゴリ作成] {category_name} (id={category_id})")

        # ④ items に保存（ユーザー設定の通知時間で翌日通知）
        user_settings = supabase_admin.table("user_settings") \
            .select("notify_time") \
            .eq("line_user_id", user_id) \
            .execute()
        notify_time = user_settings.data[0].get("notify_time", "21:00") if user_settings.data else "21:00"
        nt_hour, nt_minute = map(int, notify_time.split(":"))
        first_notify_at = (datetime.now(JST) + timedelta(days=1)).replace(
            hour=nt_hour, minute=nt_minute, second=0, microsecond=0
        )

        if url:
            item_data = {
                "line_user_id": user_id,
                "type": "url",
                "original_url": url,
                "title": title,
                "description": ogp["description"],
                "ogp_image": ogp["image"],
                "status": "pending",
                "notify_count": 0,
                "next_notify_at": first_notify_at.isoformat(),
            }
        else:
            item_data = {
                "line_user_id": user_id,
                "type": "text",
                "title": title,
                "description": text,
                "status": "pending",
                "notify_count": 0,
                "next_notify_at": first_notify_at.isoformat(),
            }

        if category_id:
            item_data["category_id"] = category_id

        insert_res = supabase_admin.table("items").insert(item_data).execute()
        if getattr(insert_res, "error", None):
            logger.error(f"[supabase] insert item error: {insert_res.error}")

        # カテゴリ内の件数を取得
        item_count = 0
        if category_id:
            count_res = supabase_admin.table("items") \
                .select("id", count="exact") \
                .eq("line_user_id", user_id) \
                .eq("category_id", category_id) \
                .is_("deleted_at", "null") \
                .execute()
            item_count = count_res.count or 0

        count_label = f"（{item_count}件目）" if item_count else ""

        if url:
            reply_text = f"🔗 「{category_name}」に保存しました！{count_label}\nタイトル: {title}\n🌐 {url}"
        else:
            reply_text = f"📝 「{category_name}」に保存しました！{count_label}\nタイトル: {title}"

        msg_type = "url" if url else "text"
        log_activity(user_id, "bot_message", metadata={"message_type": msg_type})

    except Exception as e:
        logger.error(f"[handler] unexpected error (AI/DB): {e}")

    # --- LINEへの返信 ---
    try:
        with ApiClient(line_configuration) as api_client:
            line_bot_api = MessagingApi(api_client)
            line_bot_api.reply_message(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[TextMessage(text=reply_text)],
                )
            )

        logger.info("[handler] reply_message sent")

    except Exception as e:
        logger.error(f"[handler] unexpected error (reply): {e}")


# ============================================
# 画像メッセージ受信
# ============================================

@line_handler.add(MessageEvent, message=ImageMessageContent)
def handle_image_message(event):
    user_id = event.source.user_id
    message_id = event.message.id
    logger.info(f"[画像受信] user={user_id}, message_id={message_id}")

    reply_text = "⚠️ 保存中にエラーが発生しました。\nもう一度お試しください。"

    try:
        # ① LINEから画像データをダウンロード
        try:
            with ApiClient(line_configuration) as api_client:
                blob_api = MessagingApiBlob(api_client)
                image_bytes = blob_api.get_message_content(message_id)
        except Exception as e:
            logger.error(f"[handler] 画像ダウンロード失敗: {e}")
            reply_text = "⚠️ 画像を取得できませんでした。\nもう一度送信してみてください。"
            raise

        # ② UUID発行
        item_id = str(uuid.uuid4())

        # ③ Supabase Storageへ保存
        image_url = upload_image(user_id, item_id, image_bytes)

        # ④ 既存カテゴリ取得
        cats = supabase_admin.table("categories") \
            .select("*") \
            .eq("line_user_id", user_id) \
            .execute()

        if getattr(cats, "error", None):
            logger.error(f"[supabase] categories error: {cats.error}")
            existing = {}
        else:
            existing = {c["name"]: c["id"] for c in (cats.data or [])}

        # ⑤ AI解析
        ai_result = classify_image(image_bytes, list(existing.keys()))
        title = ai_result.get("title", "画像メモ")
        category_name = ai_result.get("category", "未分類")

        logger.info(f"[AI画像分類結果] title={title}, category={category_name}")

        # ⑥ カテゴリなければ作成
        if category_name in existing:
            category_id = existing[category_name]
        else:
            new_cat = supabase_admin.table("categories") \
                .insert({"line_user_id": user_id, "name": category_name}) \
                .execute()

            if getattr(new_cat, "error", None):
                logger.error(f"[supabase] insert category error: {new_cat.error}")
                category_id = None
            else:
                category_id = new_cat.data[0]["id"]
                logger.info(f"[カテゴリ作成] {category_name} (id={category_id})")

        # ⑦ items に保存（ユーザー設定の通知時間で翌日通知）
        user_settings = supabase_admin.table("user_settings") \
            .select("notify_time") \
            .eq("line_user_id", user_id) \
            .execute()
        notify_time = user_settings.data[0].get("notify_time", "21:00") if user_settings.data else "21:00"
        nt_hour, nt_minute = map(int, notify_time.split(":"))
        first_notify_at = (datetime.now(JST) + timedelta(days=1)).replace(
            hour=nt_hour, minute=nt_minute, second=0, microsecond=0
        )

        item_data = {
            "id": item_id,
            "line_user_id": user_id,
            "type": "image",
            "title": title,
            "image_url": image_url,
            "status": "pending",
            "notify_count": 0,
            "next_notify_at": first_notify_at.isoformat(),
        }
        if category_id:
            item_data["category_id"] = category_id

        insert_res = supabase_admin.table("items").insert(item_data).execute()
        if getattr(insert_res, "error", None):
            logger.error(f"[supabase] insert item error: {insert_res.error}")

        # カテゴリ内の件数を取得
        item_count = 0
        if category_id:
            count_res = supabase_admin.table("items") \
                .select("id", count="exact") \
                .eq("line_user_id", user_id) \
                .eq("category_id", category_id) \
                .is_("deleted_at", "null") \
                .execute()
            item_count = count_res.count or 0

        count_label = f"（{item_count}件目）" if item_count else ""
        reply_text = f"📷 「{category_name}」に保存しました！{count_label}\nタイトル: {title}"

        log_activity(user_id, "bot_message", metadata={"message_type": "image"})

    except Exception as e:
        logger.error(f"[handler] unexpected error (画像処理): {e}")
        if "画像を取得できませんでした" not in reply_text:
            reply_text = "⚠️ 保存に失敗しました。\nもう一度お試しください。"

    # --- LINEへの返信 ---
    try:
        with ApiClient(line_configuration) as api_client:
            line_bot_api = MessagingApi(api_client)
            line_bot_api.reply_message(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[TextMessage(text=reply_text)],
                )
            )

        logger.info("[handler] reply_message sent (画像)")

    except Exception as e:
        logger.error(f"[handler] unexpected error (reply): {e}")


# ============================================
# 非対応メッセージの共通ハンドラ
# ============================================

for _msg_type in [StickerMessageContent, VideoMessageContent,
                  AudioMessageContent, LocationMessageContent,
                  FileMessageContent]:
    @line_handler.add(MessageEvent, message=_msg_type)
    def handle_unsupported(event):
        """非対応メッセージを受信したときの共通ハンドラ"""
        try:
            with ApiClient(line_configuration) as api_client:
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
            logger.error(f"[handler] 非対応メッセージ返信エラー: {e}")