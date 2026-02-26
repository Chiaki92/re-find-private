# ============================================
# デモ通知 API Blueprint（発表用・一時的）
#
# ■ このファイルの役割：
#   - POST /api/demo/notify → ログインユーザーの pending アイテムのうち
#     今日が通知日のものを即座に LINE 通知する
#
# ■ 発表後の削除手順：
#   1. このファイルを削除
#   2. app.py の Blueprint 登録行を削除
#   3. settings.html のデモ通知ボタンを削除
# ============================================

import uuid
from datetime import datetime, time, timedelta, timezone
from collections import defaultdict

from flask import Blueprint, current_app, request

from extensions import supabase_admin, line_configuration
from auth_utils import login_required, get_current_user_line_id
from activity_logger import log_activity

from linebot.v3.messaging import ApiClient, MessagingApi
from linebot.v3.messaging.models import TextMessage, PushMessageRequest

api_demo_bp = Blueprint("api_demo", __name__)

# ── 定数 ──
JST = timezone(timedelta(hours=9))
BASE_URL = "https://re-find.onrender.com"
BASE_SHARE_URL = f"{BASE_URL}/share"
WEB_URL = f"{BASE_URL}/?openExternalBrowser=1"
NOTIFY_INTERVALS = {0: 1, 1: 3, 2: 7, 3: 14, 4: 30, 5: 60}
MAX_NOTIFY_COUNT = 6
NOTIFY_DETAIL_LIMIT = 5


# ============================================
# デモ通知送信
# ============================================

@api_demo_bp.route("/api/demo/notify", methods=["POST"])
@login_required
def demo_notify():
    """ログインユーザーの今日が通知日の pending アイテムを即座に通知する"""
    line_user_id = get_current_user_line_id()

    try:
        # 1. 対象日の pending アイテムを取得
        data = request.get_json(silent=True) or {}
        offset_days = int(data.get("offset_days", 0))

        now_jst = datetime.now(JST)
        today_start = now_jst.replace(hour=0, minute=0, second=0, microsecond=0)
        target_start = today_start + timedelta(days=offset_days)
        target_end = target_start + timedelta(days=1)

        res = supabase_admin.table("items") \
            .select("id, line_user_id, title, notify_count, next_notify_at, created_at, categories(name)") \
            .eq("line_user_id", line_user_id) \
            .eq("status", "pending") \
            .is_("deleted_at", "null") \
            .gte("next_notify_at", target_start.isoformat()) \
            .lt("next_notify_at", target_end.isoformat()) \
            .order("created_at", desc=True) \
            .execute()

        items = res.data or []
        if not items:
            msg = "今日が通知日のアイテムがありません" if offset_days == 0 \
                else "明日が通知日のアイテムがありません" if offset_days == 1 \
                else f"{offset_days}日後が通知日のアイテムがありません"
            return {"ok": False, "error": msg}, 404

        # カテゴリ名を整形
        for item in items:
            cat = item.pop("categories", None)
            item["category_name"] = cat["name"] if cat else "未分類"

        # 2. ユーザーの notify_time を取得
        settings = supabase_admin.table("user_settings") \
            .select("notify_time") \
            .eq("line_user_id", line_user_id) \
            .execute()
        notify_time = settings.data[0].get("notify_time", "21:00") if settings.data else "21:00"

        # 3. 共有リンクを取得/生成
        for item in items:
            try:
                token = _get_or_create_share_token(item["id"], line_user_id)
                item["share_url"] = f"{BASE_SHARE_URL}/{token}?openExternalBrowser=1"
            except Exception:
                item["share_url"] = ""

        # 4. メッセージ組み立て
        today_str = datetime.now(JST).strftime("%Y-%m-%d")
        message = _build_message(items, today_str)

        # 5. DB更新（notify_count を進める）
        updated_items = []
        for item in items:
            try:
                _update_item(item, notify_time)
                updated_items.append(item)
            except Exception as e:
                current_app.logger.error(f"デモ通知 DB更新失敗: item={item['id']} - {e}")

        if not updated_items:
            return {"ok": False, "error": "DB更新に失敗しました"}, 500

        # 6. LINE送信
        try:
            with ApiClient(line_configuration) as api_client:
                api = MessagingApi(api_client)
                api.push_message(
                    PushMessageRequest(
                        to=line_user_id,
                        messages=[TextMessage(text=message)],
                    )
                )
        except Exception as e:
            # 送信失敗 → DB巻き戻し
            current_app.logger.error(f"デモ通知 LINE送信失敗: {e}")
            for item in updated_items:
                try:
                    _revert_item(item)
                except Exception:
                    pass
            return {"ok": False, "error": "LINE送信に失敗しました"}, 500

        # 7. 通知ログ記録
        item_ids = [i["id"] for i in updated_items]
        log_activity(
            line_user_id,
            "notification_sent",
            metadata={"item_ids": item_ids, "count": len(item_ids)},
        )

        return {"ok": True, "count": len(updated_items)}

    except Exception as e:
        current_app.logger.error(f"デモ通知エラー: {e}")
        return {"ok": False, "error": "サーバーエラーが発生しました"}, 500


# ── ヘルパー関数（notify.py のロジックを再利用） ──

def _get_or_create_share_token(item_id, line_user_id):
    res = supabase_admin.table("shared_links") \
        .select("token").eq("item_id", item_id).limit(1).execute()
    if res.data:
        return res.data[0]["token"]
    token = str(uuid.uuid4()).replace("-", "")[:16]
    supabase_admin.table("shared_links").insert({
        "line_user_id": line_user_id,
        "item_id": item_id,
        "token": token,
    }).execute()
    return token


def _calc_days_since(created_at_str):
    try:
        created_at = datetime.fromisoformat(created_at_str)
        if created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=JST)
        return (datetime.now(JST) - created_at).days
    except Exception:
        return "?"


def _group_by_category(items):
    grouped = defaultdict(list)
    for item in items:
        grouped[item["category_name"]].append(item)
    return grouped


def _build_message(items, notify_date_str):
    final_items = [i for i in items if i["notify_count"] >= MAX_NOTIFY_COUNT - 1]
    normal_items = [i for i in items if i["notify_count"] < MAX_NOTIFY_COUNT - 1]
    lines = []

    if normal_items:
        if len(normal_items) <= NOTIFY_DETAIL_LIMIT:
            lines.append(f"\U0001f4ec {len(normal_items)}件の情報が待っています\n")
            for category, cat_items in _group_by_category(normal_items).items():
                lines.append(f"\U0001f4c1 {category}（{len(cat_items)}件）")
                for item in cat_items:
                    count = item["notify_count"] + 1
                    title = item.get("title") or "（タイトルなし）"
                    share_url = item.get("share_url", "")
                    lines.append(f"  ・{title}｜{count}回目")
                    if share_url:
                        lines.append(f"    {share_url}")
                lines.append("")
        else:
            lines.append(f"\U0001f4ec {len(normal_items)}件の情報があります\n")
            lines.append("＜目次＞")
            for i, item in enumerate(normal_items, 1):
                title = item.get("title") or "（タイトルなし）"
                lines.append(f"{i}. {title}")
            lines.append("")

    if final_items:
        if normal_items:
            lines.append("─────────────────")
        lines.append("\U0001f4cc 最後のリマインドです\n")
        if len(final_items) > 1:
            lines.append("以下の情報への通知が今回で終わります。\n")
        for category, cat_items in _group_by_category(final_items).items():
            lines.append(f"\U0001f4c1 {category}（{len(cat_items)}件）")
            for item in cat_items:
                title = item.get("title") or "（タイトルなし）"
                days_ago = _calc_days_since(item["created_at"])
                share_url = item.get("share_url", "")
                lines.append(f"  ・{title}（{days_ago}日前）")
                if share_url:
                    lines.append(f"    {share_url}")
            lines.append("")
        lines.append("まだ気になるものは「未対応」に戻せます。")
        if normal_items:
            lines.append("─────────────────")

    notify_list_url = f"{BASE_URL}/notify-list?date={notify_date_str}&openExternalBrowser=1"
    lines.append("")
    lines.append(f"▶ 今日の通知一覧を確認する\n{notify_list_url}")
    lines.append(f"\n▶ Webアプリで確認する\n{WEB_URL}")
    return "\n".join(lines)


def _update_item(item, notify_time="21:00"):
    new_count = item["notify_count"] + 1
    if new_count >= MAX_NOTIFY_COUNT:
        supabase_admin.table("items").update({
            "notify_count": new_count,
            "status": "archived",
            "next_notify_at": None,
            "updated_at": datetime.now(JST).isoformat(),
        }).eq("id", item["id"]).execute()
    else:
        hour, minute = map(int, notify_time.split(":")[:2])
        days = NOTIFY_INTERVALS.get(new_count, 60)
        now = datetime.now(JST)
        next_at = datetime.combine(
            now.date() + timedelta(days=days), time(hour, minute), tzinfo=JST
        )
        if next_at <= now:
            next_at += timedelta(days=1)
        supabase_admin.table("items").update({
            "notify_count": new_count,
            "next_notify_at": next_at.isoformat(),
            "updated_at": datetime.now(JST).isoformat(),
        }).eq("id", item["id"]).execute()


def _revert_item(item):
    supabase_admin.table("items").update({
        "notify_count": item["notify_count"],
        "next_notify_at": item["next_notify_at"],
        "status": "pending",
        "updated_at": datetime.now(JST).isoformat(),
    }).eq("id", item["id"]).execute()
