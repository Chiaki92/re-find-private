"""
notify.py — re-find 通知バッチ
GitHub Actions で30分ごとに実行。
忘却曲線ベースの間隔で LINE Push Message を送信する。
各ユーザーの user_settings.notify_time に合わせて通知を送る。
"""

import os
import sys
import uuid
import logging
from datetime import datetime, timedelta, timezone
from collections import defaultdict

from dotenv import load_dotenv
from supabase import create_client
from linebot.v3.messaging import Configuration, ApiClient, MessagingApi
from linebot.v3.messaging.models import TextMessage, PushMessageRequest
from activity_logger import log_activity

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
BASE_URL = "https://re-find.onrender.com"
WEB_URL = f"{BASE_URL}/?openExternalBrowser=1"
BASE_SHARE_URL = f"{BASE_URL}/share"

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

# この件数以下なら詳細テキスト、超えたら目次形式でLINEに送る
NOTIFY_DETAIL_LIMIT = 5

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
log = logging.getLogger(__name__)


# ── 共有リンクの取得・生成 ─────────────────────────
def get_or_create_share_token(item_id, line_user_id):
    """既存の共有トークンを取得、なければ新規作成して返す"""
    res = (
        supabase.table("shared_links")
        .select("token")
        .eq("item_id", item_id)
        .limit(1)
        .execute()
    )
    if res.data:
        return res.data[0]["token"]

    token = str(uuid.uuid4()).replace("-", "")[:16]
    supabase.table("shared_links").insert({
        "line_user_id": line_user_id,
        "item_id": item_id,
        "token": token,
    }).execute()
    return token


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
        .select("id, line_user_id, title, notify_count, next_notify_at, created_at, categories(name)")
        .eq("status", "pending")
        .is_("deleted_at", "null")
        .lte("next_notify_at", now)
        .execute()
    )
    items = res.data or []

    # categories(name) の結果を category_name に整形
    for item in items:
        cat = item.pop("categories", None)
        item["category_name"] = cat["name"] if cat else "未分類"

    return items


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


# ── 経過日数の計算 ──────────────────────────────────
def calc_days_since(created_at_str):
    """保存日時から今日までの経過日数を計算する"""
    try:
        created_at = datetime.fromisoformat(created_at_str)
        if created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=JST)
        delta = datetime.now(JST) - created_at
        return delta.days
    except Exception:
        return "?"


# ── カテゴリ別グループ化 ─────────────────────────
def _group_by_category(items):
    """アイテムをカテゴリ名ごとにグループ化する（出現順を保持）"""
    grouped = defaultdict(list)
    for item in items:
        grouped[item["category_name"]].append(item)
    return grouped


# ── 通知メッセージの組み立て ───────────────────────
def build_message(items, notify_date_str=None):
    """
    ユーザーに送信する1通分のメッセージを組み立てる。
    - 通常通知（1〜5回目）:
      - NOTIFY_DETAIL_LIMIT 以下: カテゴリ×タイトル×共有URL（詳細形式）
      - NOTIFY_DETAIL_LIMIT 超:   番号×タイトルの目次形式
    - 最終通知（6回目）: 経過日数付きの特別な文面
    - 末尾に通知一覧ページURLを常に添付
    """
    if notify_date_str is None:
        notify_date_str = datetime.now(JST).strftime("%Y-%m-%d")

    # notify_count は送信前の値。MAX_NOTIFY_COUNT - 1 以上なら最終通知
    final_items  = [i for i in items if i["notify_count"] >= MAX_NOTIFY_COUNT - 1]
    normal_items = [i for i in items if i["notify_count"] <  MAX_NOTIFY_COUNT - 1]

    lines = []

    # ── 通常通知ブロック ──
    if normal_items:
        if len(normal_items) <= NOTIFY_DETAIL_LIMIT:
            # === 詳細形式（従来通り） ===
            lines.append(f"📬 {len(normal_items)}件の情報が待っています\n")

            for category, cat_items in _group_by_category(normal_items).items():
                lines.append(f"📁 {category}（{len(cat_items)}件）")
                for item in cat_items:
                    count     = item["notify_count"] + 1
                    title     = item.get("title") or "（タイトルなし）"
                    share_url = item.get("share_url", "")

                    lines.append(f"  ・{title}｜{count}回目")
                    if share_url:
                        lines.append(f"    {share_url}")
                lines.append("")
        else:
            # === 目次形式（件数が多い場合・カテゴリ別） ===
            lines.append(f"📬 {len(normal_items)}件の情報があります\n")
            num = 1
            for category, cat_items in _group_by_category(normal_items).items():
                lines.append(f"📁 {category}（{len(cat_items)}件）")
                for item in cat_items:
                    title = item.get("title") or "（タイトルなし）"
                    lines.append(f"  {num}. {title}")
                    num += 1
                lines.append("")

    # ── 最終通知ブロック ──
    if final_items:
        if normal_items:
            lines.append("─────────────────")

        lines.append("📌 最後のリマインドです\n")

        if len(final_items) > 1:
            lines.append("以下の情報への通知が今回で終わります。\n")

        for category, cat_items in _group_by_category(final_items).items():
            lines.append(f"📁 {category}（{len(cat_items)}件）")
            for item in cat_items:
                title     = item.get("title") or "（タイトルなし）"
                days_ago  = calc_days_since(item["created_at"])
                share_url = item.get("share_url", "")

                lines.append(f"  ・{title}（{days_ago}日前）")
                if share_url:
                    lines.append(f"    {share_url}")
            lines.append("")

        lines.append("まだ気になるものは「未対応」に戻せます。")

        if normal_items:
            lines.append("─────────────────")

    # ── 通知一覧ページへのリンク ──
    notify_list_url = f"{BASE_URL}/notify-list?date={notify_date_str}&openExternalBrowser=1"
    lines.append("")
    lines.append(f"▶ 今日の通知一覧を確認する\n{notify_list_url}")

    # ── Webアプリへのリンク ──
    lines.append(f"\n▶ Webアプリで確認する\n{WEB_URL}")
    return "\n".join(lines)


# ── アイテムの更新（notify_count・次回通知日時） ───
def update_item(item, notify_time="21:00"):
    """
    送信成功後に呼び出す。
    - notify_count を +1
    - NOTIFY_INTERVALS に従って次回 next_notify_at を設定（ユーザー設定時間）
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
        # ── 次回通知日時を計算（ユーザー設定時間を使用） ──
        hour, minute = map(int, notify_time.split(":")[:2])
        days = NOTIFY_INTERVALS.get(new_count, 60)
        next_at = (datetime.now(JST) + timedelta(days=days)).replace(
            hour=hour, minute=minute, second=0, microsecond=0
        )
        supabase.table("items").update({
            "notify_count": new_count,
            "next_notify_at": next_at.isoformat(),
            "updated_at": datetime.now(JST).isoformat(),
        }).eq("id", item["id"]).execute()


# ── アイテムの巻き戻し（送信失敗時） ─────────────────
def revert_item(item):
    """
    LINE送信が失敗した場合に update_item() の変更を元に戻す。
    next_notify_at と notify_count を送信前の値に復元する。
    """
    supabase.table("items").update({
        "notify_count": item["notify_count"],
        "next_notify_at": item["next_notify_at"],
        "status": "pending",
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
    dry_run = "--dry-run" in sys.argv

    if dry_run:
        log.info("DRY RUN モード（送信・DB更新はしません）")

    log.info("=== notify.py 開始 ===")

    # 1. 通知対象を取得
    items = fetch_pending_items()
    if not items:
        log.info("通知対象なし")
        return

    log.info(f"通知対象: {len(items)} 件")

    # 2. ユーザーごとにまとめる（1ユーザー = 1通）
    grouped = group_by_user(items)
    log.info(f"通知対象ユーザー: {len(grouped)} 人")

    success_count = 0
    fail_count = 0

    for line_user_id, user_items in grouped.items():

        # 3. user_settings で通知が無効なユーザーはスキップ、notify_time を取得
        settings = (
            supabase.table("user_settings")
            .select("notify_enabled, notify_time")
            .eq("line_user_id", line_user_id)
            .execute()
        )
        if settings.data and not settings.data[0].get("notify_enabled", True):
            log.info(f"通知OFF: {line_user_id}")
            continue

        notify_time = settings.data[0].get("notify_time", "21:00") if settings.data else "21:00"

        # 4. 共有リンクを取得/生成してアイテムに付与
        for item in user_items:
            try:
                token = get_or_create_share_token(item["id"], line_user_id)
                item["share_url"] = f"{BASE_SHARE_URL}/{token}?openExternalBrowser=1"
            except Exception as e:
                log.warning(f"共有リンク生成失敗: item={item['id']} - {e}")
                item["share_url"] = ""

        # 5. メッセージを組み立てて送信
        today_str = datetime.now(JST).strftime("%Y-%m-%d")
        message = build_message(user_items, notify_date_str=today_str)

        if dry_run:
            log.info(f"[DRY RUN] 送信先: {line_user_id} ({len(user_items)}件)")
            log.info(f"メッセージ内容:\n{message}")
            success_count += 1
            continue

        # 6. DB更新を先に行う（再送防止）
        #    LINE送信前に next_notify_at を未来に設定しておくことで、
        #    送信後にスクリプトがクラッシュしても同じ通知が再送されない
        updated_items = []
        for item in user_items:
            try:
                update_item(item, notify_time)
                updated_items.append(item)
            except Exception as e:
                log.error(f"DB更新失敗: item={item['id']} - {e}")

        if not updated_items:
            log.error(f"全アイテムのDB更新失敗、送信スキップ: {line_user_id}")
            fail_count += 1
            continue

        # 7. LINE送信（失敗したらDB更新を巻き戻す）
        try:
            send_line_message(line_user_id, message)
            log.info(f"送信OK: {line_user_id} ({len(updated_items)}件)")
            success_count += 1
        except Exception as e:
            log.error(f"送信失敗: {line_user_id} - {e}")
            fail_count += 1
            for item in updated_items:
                try:
                    revert_item(item)
                    log.info(f"DB巻き戻しOK: item={item['id']}")
                except Exception as re_err:
                    log.error(f"DB巻き戻し失敗: item={item['id']} - {re_err}")
            continue

        # 8. 通知ログを記録
        item_ids = [i["id"] for i in user_items]
        log_activity(
            line_user_id,
            "notification_sent",
            metadata={"item_ids": item_ids, "count": len(item_ids)},
        )

    # ── 結果サマリー ──
    log.info(
        f"=== notify.py 完了 === "
        f"成功: {success_count}人 / 失敗: {fail_count}人 / "
        f"処理アイテム合計: {len(items)}件"
    )


if __name__ == "__main__":
    main()
