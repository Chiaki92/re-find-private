# ============================================
# 認証 Blueprint（ログイン・ログアウト・LIFF）
# ============================================

import os
import secrets
import requests as http_requests
from flask import Blueprint, request, session, redirect, render_template, current_app

from extensions import supabase_admin
from auth_utils import login_required

auth_bp = Blueprint("auth", __name__)

# --- LINE Login 設定（この Blueprint でのみ使用） ---
LINE_LOGIN_CHANNEL_ID = os.environ.get("LINE_LOGIN_CHANNEL_ID")
LINE_LOGIN_CHANNEL_SECRET = os.environ.get("LINE_LOGIN_CHANNEL_SECRET")
LIFF_ID = os.environ.get("LIFF_ID")
LINE_LOGIN_REDIRECT_URI = os.environ.get(
    "LINE_LOGIN_REDIRECT_URI",
    "https://re-find.onrender.com/login/callback"
)


# ============================================
# ヘルパー関数
# ============================================

def _create_default_data_if_needed(line_user_id):
    """
    初回ログイン時にデフォルトのカテゴリ・設定・通知ルールを作成する。
    すでにデータがある場合（2回目以降のログイン）は何もしない。
    """

    # --- 「未分類」カテゴリがなければ作成 ---
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

    # --- notification_rules がなければデフォルト作成 ---
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


# ============================================
# ルート
# ============================================

@auth_bp.route("/login")
def login_page():
    """ログイン画面を表示する"""
    if session.get("line_user_id"):
        return redirect("/")
    return render_template("login.html")


@auth_bp.route("/login/line")
def login_line():
    """LINEの認証ページにリダイレクトする"""
    state = secrets.token_urlsafe(32)
    session["oauth_state"] = state

    auth_url = (
        "https://access.line.me/oauth2/v2.1/authorize"
        f"?response_type=code"
        f"&client_id={LINE_LOGIN_CHANNEL_ID}"
        f"&redirect_uri={LINE_LOGIN_REDIRECT_URI}"
        f"&state={state}"
        f"&scope=profile%20openid"
    )
    return redirect(auth_url)


@auth_bp.route("/login/callback")
def login_callback():
    """LINEで認証した後のコールバック"""

    # --- エラーチェック ---
    error = request.args.get("error")
    if error:
        current_app.logger.error(f"LINE認証エラー: {error}")
        return redirect("/login")

    state = request.args.get("state")
    if state != session.get("oauth_state"):
        current_app.logger.error("stateが一致しません（CSRF攻撃の可能性）")
        return redirect("/login")

    code = request.args.get("code")
    if not code:
        current_app.logger.error("認証コードがありません")
        return redirect("/login")

    # --- 認証コードをアクセストークンに交換 ---
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
        current_app.logger.error(f"トークン取得失敗: {token_response.text}")
        return redirect("/login")

    access_token = token_response.json().get("access_token")

    # --- プロフィール取得 ---
    profile_response = http_requests.get(
        "https://api.line.me/v2/profile",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    if profile_response.status_code != 200:
        current_app.logger.error(f"プロフィール取得失敗: {profile_response.text}")
        return redirect("/login")

    profile = profile_response.json()
    line_user_id = profile.get("userId")
    display_name = profile.get("displayName")

    current_app.logger.info(f"ログイン成功: {display_name} ({line_user_id})")

    # --- DB保存（UPSERT） + デフォルトデータ作成 ---
    try:
        supabase_admin.table("users").upsert({
            "line_user_id": line_user_id,
            "display_name": display_name,
        }, on_conflict="line_user_id").execute()

        _create_default_data_if_needed(line_user_id)

    except Exception as e:
        current_app.logger.error(f"DB保存エラー: {e}")

    # --- セッション発行 ---
    session.permanent = True
    session["line_user_id"] = line_user_id
    session["display_name"] = display_name

    return redirect("/")


@auth_bp.route("/logout")
def logout():
    """セッションを全てクリアしてログイン画面に戻す"""
    session.clear()
    return redirect("/login")


@auth_bp.route("/liff")
def liff_entry():
    """LINEアプリ内からのエントリポイント"""
    if not LIFF_ID:
        current_app.logger.error("LIFF_ID が設定されていません")
        return redirect("/login")
    return render_template("liff.html", liff_id=LIFF_ID)


@auth_bp.route("/api/liff-login", methods=["POST"])
def liff_login():
    """LIFFから受け取ったユーザー情報でセッションを発行"""
    data = request.json
    line_user_id = data.get("userId")
    display_name = data.get("displayName")

    if not line_user_id:
        return {"error": "userId is required", "code": "VALIDATION_ERROR"}, 400

    try:
        supabase_admin.table("users").upsert({
            "line_user_id": line_user_id,
            "display_name": display_name,
        }, on_conflict="line_user_id").execute()

        _create_default_data_if_needed(line_user_id)
    except Exception as e:
        current_app.logger.error(f"LIFF DB保存エラー: {e}")

    session.permanent = True
    session["line_user_id"] = line_user_id
    session["display_name"] = display_name

    return {"ok": True}
