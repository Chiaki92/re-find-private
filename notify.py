"""
notify.py — re-find 通知バッチ
GitHub Actions で毎日 UTC 12:00（JST 21:00）に実行。
忘却曲線ベースの間隔で LINE Push Message を送信する。
"""

import os
import logging
from datetime import datetime, timedelta, timezone
from collections import defaultdict

from dotenv import load_dotenv
from supabase import create_client
from linebot.v3.messaging import Configuration, ApiClient, MessagingApi
from linebot.v3.messaging.models import TextMessage, PushMessageRequest

load_dotenv()

# ── 環境変数から接続情報を取得 ─────────────────────
SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_SERVICE_ROLE_KEY"]  # RLS バイパス用
LINE_CHANNEL_ACCESS_TOKEN = os.environ["LINE_CHANNEL_ACCESS_TOKEN"]

# ── クライアント初期化 ─────────────────────────────
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
configuration = Configuration(access_token=LINE_CHANNEL_ACCESS_TOKEN)

# ── 定数 ───────────────────────────────────────────
JST = timezone(timedelta(hours=9))

# LINEアプリ内ブラウザだと Cookie が不安定でセッションが切れるため
# ?openExternalBrowser=1 を付けて外部ブラウザで開かせる
WEB_URL = "https://re-find.onrender.com/?openExternalBrowser=1"

# 忘却曲線に基づく通知間隔（notify_count → 次回通知までの日数）
# count 0: 保存翌日  → count 1: 3日後 → count 2: 7日後
# → count 3: 14日後 → count 4: 30日後 → count 5: 60日後（最終通知）
NOTIFY_INTERVALS = {
    0: 1,    # 1日後
    1: 3,    # 3日後
    2: 7,    # 7日後
    3: 14,   # 14日後
    4: 30,   # 30日後
    5: 60,   # 60日後（最終通知）
}
MAX_NOTIFY_COUNT = 6  # この回数に達したら status を 'archived' に変更

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
log = logging.getLogger(__name__)


# ── 通知対象アイテムの取得 ─────────────────────────
def fetch_pending_items():
    """
    通知条件:
      - next_notify_at ≤ 現在時刻（通知時刻が来ている）
      - status = 'pending'（未対応のもの）
      - deleted_at IS NULL（削除されていない）
    """
    now = datetime.now(JST).isoformat()
    res = (
        supabase.table("items")
        .select("id, line_user_id, title, notify_count, category_id")
        .eq("status", "pending")
        .is_("deleted_at", "null")
        .lte("next_notify_at", now)
        .execute()
    )
    return res.data


# ── ユーザーごとにグループ化 ───────────────────────
def group_by_user(items):
    """
    1ユーザーに対して複数アイテムがあっても
    LINE メッセージは1通にまとめて送信するためグループ化する
    """
    grouped = defaultdict(list)
    for item in items:
        grouped[item["line_user_id"]].append(item)
    return grouped


# ── 通知メッセージの組み立て ───────────────────────
def build_message(items):
    """
    ユーザーに送信する1通分のメッセージを組み立てる。
    - 通常通知: タイトルと通知回数を表示
    - 最終通知（6回目）: 特別な文面でアーカイブされることを案内
    """
    lines = ["📬 re-find からのお知らせ\n"]

    for item in items:
        title = item.get("title") or "（タイトルなし）"
        count = item["notify_count"] + 1  # 今回の通知で +1 した回数
        is_last = count >= MAX_NOTIFY_COUNT

        if is_last:
            # ── 最終通知（6回目）：特別な文面 ──
            lines.append("📌 最後のお知らせです")
            lines.append(f"🔖 {title}")
            lines.append(
                f"この情報は保存され、これまでに {count}回 お知らせしました。"
            )
            lines.append("今回が最後の通知です。")
            lines.append("まだ気になるなら、Webアプリで「未対応」に戻せます。")
            lines.append("")
        else:
            # ── 通常通知 ──
            lines.append(f"🔖 {title}（{count}回目）")
            lines.append("")

    # 全アイテム共通のリンク（外部ブラウザで開く）
    lines.append(f"▶ Webアプリで確認する\n{WEB_URL}")
    return "\n".join(lines)


# ── アイテムの更新（notify_count・次回通知日時） ───
def update_item(item):
    """
    送信成功後に呼び出す。
    - notify_count を +1
    - NOTIFY_INTERVALS に従って次回 next_notify_at を設定（21:00 JST 固定）
    - MAX_NOTIFY_COUNT に達したら status='archived', next_notify_at=NULL
    """
    new_count = item["notify_count"] + 1

    if new_count >= MAX_NOTIFY_COUNT:
        # ── 最終通知済み → これ以上通知しない ──
        supabase.table("items").update({
            "notify_count": new_count,
            "status": "archived",
            "next_notify_at": None,
            "updated_at": datetime.now(JST).isoformat(),
        }).eq("id", item["id"]).execute()
    else:
        # ── 次回通知日時を計算（JST 21:00 に固定） ──
        days = NOTIFY_INTERVALS.get(new_count, 60)
        next_at = (datetime.now(JST) + timedelta(days=days)).replace(
            hour=21, minute=0, second=0, microsecond=0
        )
        supabase.table("items").update({
            "notify_count": new_count,
            "next_notify_at": next_at.isoformat(),
            "updated_at": datetime.now(JST).isoformat(),
        }).eq("id", item["id"]).execute()


# ── LINE Push Message 送信 ─────────────────────────
def send_line_message(line_user_id, text):
    """
    LINE Messaging API の Push Message で送信する。
    ※ reply_message と違い、reply_token 不要で能動的に送れる。
    """
    with ApiClient(configuration) as api_client:
        api = MessagingApi(api_client)
        api.push_message(
            PushMessageRequest(
                to=line_user_id,
                messages=[TextMessage(text=text)],
            )
        )


# ── メイン処理 ─────────────────────────────────────
def main():
    log.info("=== notify.py 開始 ===")

    # 1. 通知対象を取得
    items = fetch_pending_items()
    if not items:
        log.info("通知対象なし")
        return

    log.info(f"通知対象: {len(items)} 件")

    # 2. ユーザーごとにまとめる（1ユーザー = 1通）
    grouped = group_by_user(items)

    for line_user_id, user_items in grouped.items():

        # 3. user_settings で通知が無効なユーザーはスキップ
        settings = (
            supabase.table("user_settings")
            .select("notify_enabled")
            .eq("line_user_id", line_user_id)
            .execute()
        )
        if settings.data and not settings.data[0].get("notify_enabled", True):
            log.info(f"通知OFF: {line_user_id}")
            continue

        # 4. メッセージを組み立てて送信
        message = build_message(user_items)
        try:
            send_line_message(line_user_id, message)
            log.info(f"送信OK: {line_user_id} ({len(user_items)}件)")
        except Exception as e:
            log.error(f"送信失敗: {line_user_id} - {e}")
            continue  # 送信失敗したユーザーのアイテムは更新しない

        # 5. 送信成功 → notify_count と next_notify_at を更新
        for item in user_items:
            update_item(item)

    log.info("=== notify.py 完了 ===")


if __name__ == "__main__":
    main()
