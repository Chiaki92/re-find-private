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

app.register_blueprint(auth_bp)
app.register_blueprint(api_items_bp)
app.register_blueprint(api_categories_bp)
app.register_blueprint(api_settings_bp)
app.register_blueprint(webhook_bp)

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

    return render_template("settings.html", settings=settings)


@app.route("/share/<token>")
def shared_item_page(token):
    """共有リンク閲覧ページ（ログイン不要）"""
    try:
        link = supabase_admin.table("shared_links") \
            .select("item_id") \
            .eq("token", token) \
            .execute()

        if not link.data:
            return render_template("shared_item.html", item=None)

        item_id = link.data[0]["item_id"]

        item = supabase_admin.table("items") \
            .select("*, categories(name)") \
            .eq("id", item_id) \
            .is_("deleted_at", "null") \
            .execute()

        if not item.data:
            return render_template("shared_item.html", item=None)

        item_data = item.data[0]
        cat = item_data.pop("categories", None)
        item_data["category_name"] = cat["name"] if cat else "未分類"

        return render_template("shared_item.html", item=item_data)

    except Exception as e:
        app.logger.error(f"共有リンクエラー: {e}")
        return render_template("shared_item.html", item=None)


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
