# ============================================
# 認証ヘルパー（複数 Blueprint から import して使う）
# ============================================

from functools import wraps
from flask import session, redirect


def get_current_user_line_id():
    """
    現在ログイン中のユーザーの line_user_id を返す。未ログインなら None。
    """
    return session.get("line_user_id")


def login_required(f):
    """
    ログインしていないユーザーをログイン画面にリダイレクトするデコレータ。
    使い方:
        @bp.route("/protected")
        @login_required
        def protected_page():
            ...
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("line_user_id"):
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function
