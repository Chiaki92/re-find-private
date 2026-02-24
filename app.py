# ============================================
# Re:find - メインアプリケーション
# ============================================
# Flask 初期化、テンプレートフィルタ、エラーハンドラ、
# Blueprint 登録、および少数のルート（index / health / share）を管理する。

import os
import sys
import json
import logging
from datetime import datetime, timedelta, timezone

from dotenv import load_dotenv
from flask import Flask, request, session, redirect, render_template

load_dotenv()

# --- タイムゾーン ---
JST = timezone(timedelta(hours=9))

# --- 開発モード設定 ---
DEV_MODE = os.environ.get("DEV_MODE", "").lower() == "true"
DEV_USER_ID = os.environ.get("DEV_USER_ID")
DEV_DISPLAY_NAME = os.environ.get("DEV_DISPLAY_NAME", "開発ユーザー")

if DEV_MODE:
    print("\n" + "!" * 60)
    print("!!! DEV_MODE が有効です - LINE Login をスキップします !!!")
    print("!!! 本番環境では絶対に DEV_MODE=true を設定しないでください !!!")
    print("!" * 60 + "\n")

app = Flask(__name__)

# ============================================
# ロガー設定
# ============================================
_log_handler = logging.StreamHandler(sys.stdout)
_log_handler.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s] %(message)s'))
_log_handler.setLevel(logging.DEBUG)
app.logger.addHandler(_log_handler)
app.logger.setLevel(logging.DEBUG if DEV_MODE else logging.INFO)
app.logger.propagate = False

# ============================================
# セッション設定
# ============================================
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev-secret-key")
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["PERMANENT_SESSION_LIFETIME"] = 60 * 60 * 24 * 30  # 30日間

# ============================================
# Jinja2 カスタムフィルタ
# ============================================

@app.template_filter('timeago')
def timeago_filter(value):
    """日時を「3日前」のような相対表示に変換する"""
    if not value:
        return ""
    if isinstance(value, str):
        value = datetime.fromisoformat(value.replace("Z", "+00:00"))
    now = datetime.now(timezone.utc)
    diff = now - value
    minutes = int(diff.total_seconds() / 60)
    hours = int(diff.total_seconds() / 3600)
    days = diff.days

    if minutes < 1:
        return "たった今"
    elif minutes < 60:
        return f"{minutes}分前"
    elif hours < 24:
        return f"{hours}時間前"
    elif days < 30:
        return f"{days}日前"
    elif days < 365:
        return f"{days // 30}ヶ月前"
    else:
        return f"{days // 365}年前"


@app.template_filter('timeuntil')
def timeuntil_filter(value):
    """未来の日時を「3日後」のような相対表示に変換する"""
    if not value:
        return ""
    if isinstance(value, str):
        value = datetime.fromisoformat(value.replace("Z", "+00:00"))

    JST = timezone(timedelta(hours=9))
    today = datetime.now(JST).date()
    target_date = value.astimezone(JST).date()
    days = (target_date - today).days

    if days <= 0:
        return "今日"
    elif days == 1:
        return "明日"
    elif days < 30:
        return f"{days}日後"
    elif days < 365:
        return f"{days // 30}ヶ月後"
    else:
        return f"{days // 365}年後"


@app.template_filter('dateformat')
def dateformat_filter(value):
    """日時を「2026/02/20」形式（JST）に変換する"""
    if not value:
        return ""
    if isinstance(value, str):
        value = datetime.fromisoformat(value.replace("Z", "+00:00"))
    jst_time = value.astimezone(JST)
    return jst_time.strftime("%Y/%m/%d")


# ============================================
# 開発モード: 自動ログイン
# ============================================
if DEV_MODE:
    @app.before_request
    def dev_auto_login():
        """DEV_MODE 時に LINE Login をスキップして自動的にセッションを設定する"""
        if not session.get("line_user_id"):
            session.permanent = True
            session["line_user_id"] = DEV_USER_ID
            session["display_name"] = DEV_DISPLAY_NAME
            app.logger.info(f"[DEV_MODE] 自動ログイン: {DEV_DISPLAY_NAME} ({DEV_USER_ID})")

# ============================================
# Blueprint 登録
# ============================================
from blueprints.auth import auth_bp
from blueprints.api_items import api_items_bp
from blueprints.api_categories import api_categories_bp
from blueprints.api_settings import api_settings_bp
from blueprints.webhook import webhook_bp
from blueprints.api_demo import api_demo_bp  # デモ通知（発表後に削除）

app.register_blueprint(auth_bp)
app.register_blueprint(api_items_bp)
app.register_blueprint(api_categories_bp)
app.register_blueprint(api_settings_bp)
app.register_blueprint(webhook_bp)
app.register_blueprint(api_demo_bp)  # デモ通知（発表後に削除）

# ============================================
# ルート（app.py に残すもの）
# ============================================
from extensions import supabase_admin
from auth_utils import login_required, get_current_user_line_id


@app.route("/health")
def health_check():
    """UptimeRobot等の監視サービス用。認証不要・軽量。"""
    return {"status": "ok", "message": "Re:find is running"}, 200


@app.route("/")
@login_required
def index():
    """一覧画面：ログインユーザーのアイテムをタイル表示"""
    line_user_id = get_current_user_line_id()

    categories = supabase_admin.table("categories") \
        .select("id, name") \
        .eq("line_user_id", line_user_id) \
        .order("created_at") \
        .execute()

    items = supabase_admin.table("items") \
        .select("*, categories(name)") \
        .eq("line_user_id", line_user_id) \
        .is_("deleted_at", "null") \
        .order("created_at", desc=True) \
        .execute()

    items_list = []
    for item in items.data:
        cat = item.pop("categories", None)
        item["category_name"] = cat["name"] if cat else "未分類"
        items_list.append(item)

    return render_template("index.html",
        categories=categories.data,
        items=items_list,
        items_json=json.dumps(items_list, default=str),
    )


@app.route("/settings")
@login_required
def settings_page():
    """通知設定画面"""
    line_user_id = get_current_user_line_id()

    res = supabase_admin.table("user_settings") \
        .select("notify_time, notify_enabled") \
        .eq("line_user_id", line_user_id) \
        .execute()

    settings = res.data[0] if res.data else {"notify_time": "21:00", "notify_enabled": True}

    # DB の time 型は "21:00:00" のように秒付きで返る場合があるため
    # テンプレートの "HH:MM" 形式と一致するよう先頭5文字に切り詰める
    raw_time = settings.get("notify_time", "21:00")
    settings["notify_time"] = raw_time[:5] if raw_time else "21:00"

    return render_template("settings.html", settings=settings)


@app.route("/share/<token>")
def shared_item_page(token):
    """共有リンク閲覧ページ（ログイン不要）"""
    try:
        link = supabase_admin.table("shared_links") \
            .select("item_id, line_user_id") \
            .eq("token", token) \
            .execute()

        if not link.data:
            return render_template("shared_item.html", item=None, is_owner=False)

        item_id = link.data[0]["item_id"]
        owner_id = link.data[0]["line_user_id"]

        item = supabase_admin.table("items") \
            .select("*, categories(name)") \
            .eq("id", item_id) \
            .is_("deleted_at", "null") \
            .execute()

        if not item.data:
            return render_template("shared_item.html", item=None, is_owner=False)

        item_data = item.data[0]
        cat = item_data.pop("categories", None)
        item_data["category_name"] = cat["name"] if cat else "未分類"

        # ログイン中ユーザーがアイテムのオーナーか判定
        current_user = session.get("line_user_id")
        is_owner = current_user is not None and current_user == owner_id

        return render_template("shared_item.html", item=item_data, is_owner=is_owner)

    except Exception as e:
        app.logger.error(f"共有リンクエラー: {e}")
        return render_template("shared_item.html", item=None, is_owner=False)


@app.route("/notify-list")
@login_required
def notify_list():
    """
    通知一覧ページ。
    LINEの通知メッセージ末尾のURLから遷移する。
    指定日に通知したアイテムをタイル表示する。

    クエリパラメータ:
        date: 表示する日付（YYYY-MM-DD形式）。省略時は今日（JST）
    """
    line_user_id = get_current_user_line_id()

    # ---- 日付パラメータの取得 ----
    date_str = request.args.get("date")
    if date_str:
        try:
            target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            target_date = datetime.now(JST).date()
    else:
        target_date = datetime.now(JST).date()

    date_display = target_date.strftime("%Y-%m-%d")
    next_date_str = (target_date + timedelta(days=1)).strftime("%Y-%m-%d")

    # ---- user_activity_logs から notification_sent を検索 ----
    items_list = []
    try:
        logs_res = supabase_admin.table("user_activity_logs") \
            .select("metadata") \
            .eq("line_user_id", line_user_id) \
            .eq("action_type", "notification_sent") \
            .gte("created_at", f"{date_display}T00:00:00+09:00") \
            .lt("created_at", f"{next_date_str}T00:00:00+09:00") \
            .execute()

        # metadata JSON から item_ids を収集
        all_item_ids = []
        for log_row in (logs_res.data or []):
            meta = log_row.get("metadata")
            if isinstance(meta, str):
                import json as _json
                meta = _json.loads(meta)
            if meta and isinstance(meta, dict):
                all_item_ids.extend(meta.get("item_ids", []))

        unique_ids = list(set(all_item_ids))

        if unique_ids:
            items_res = supabase_admin.table("items") \
                .select("*, categories(name)") \
                .eq("line_user_id", line_user_id) \
                .in_("id", unique_ids) \
                .is_("deleted_at", "null") \
                .execute()

            for item in (items_res.data or []):
                cat = item.pop("categories", None)
                item["category_name"] = cat["name"] if cat else "未分類"
                items_list.append(item)

    except Exception as e:
        app.logger.error(f"通知一覧取得エラー: {e}")

    # ---- カテゴリ一覧を取得（モーダルで使用） ----
    categories = supabase_admin.table("categories") \
        .select("id, name") \
        .eq("line_user_id", line_user_id) \
        .order("created_at") \
        .execute()

    return render_template(
        "notify_list.html",
        items=items_list,
        items_json=json.dumps(items_list, default=str),
        categories=categories.data,
        date_str=date_display,
        item_count=len(items_list),
    )


# ============================================
# グローバルエラーハンドラ
# ============================================

@app.errorhandler(400)
def bad_request(e):
    return {"error": "Bad request", "code": "BAD_REQUEST"}, 400


@app.errorhandler(404)
def not_found(e):
    return {"error": "Not found", "code": "NOT_FOUND"}, 404


@app.errorhandler(500)
def server_error(e):
    app.logger.error(f"Unhandled error: {e}")
    return {"error": "Internal server error", "code": "INTERNAL_ERROR"}, 500


# ============================================
# サーバー起動（ローカル実行用）
# ============================================
if __name__ == "__main__":
    app.run(debug=True)
