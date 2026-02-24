# ============================================
# ユーザー設定 API Blueprint（通知時間・通知ON/OFF）
#
# ■ このファイルの役割：
#   - GET /api/settings  → ログインユーザーの設定を取得
#   - PUT /api/settings  → ログインユーザーの設定を更新
#
# ■ 対象テーブル：user_settings
#   - notify_time    : TIME型（"HH:MM" 形式、30分刻み）
#   - notify_enabled : BOOLEAN型（通知の有効/無効）
#
# ■ 使われ方：
#   settings.js から apiGet / apiPut で呼ばれる
# ============================================

from flask import Blueprint, request, current_app

from extensions import supabase_admin
from auth_utils import login_required, get_current_user_line_id

api_settings_bp = Blueprint("api_settings", __name__)


# ============================================
# 設定取得
# ============================================

@api_settings_bp.route("/api/settings", methods=["GET"])
@login_required
def get_settings():
    """ユーザー設定を取得する"""
    line_user_id = get_current_user_line_id()

    try:
        res = supabase_admin.table("user_settings") \
            .select("notify_time, notify_enabled") \
            .eq("line_user_id", line_user_id) \
            .execute()

        if res.data:
            return {"ok": True, "settings": res.data[0]}
        else:
            # user_settings レコードがない場合はデフォルト値を返す
            # （通常は初回ログイン時に auth.py で作成されている）
            return {"ok": True, "settings": {"notify_time": "21:00", "notify_enabled": True}}
    except Exception as e:
        current_app.logger.error(f"設定取得エラー: {e}")
        return {"error": "サーバーエラーが発生しました", "code": "INTERNAL_ERROR"}, 500


# ============================================
# 設定更新
# ============================================

@api_settings_bp.route("/api/settings", methods=["PUT"])
@login_required
def update_settings():
    """ユーザー設定を更新する"""
    line_user_id = get_current_user_line_id()
    data = request.json

    # ── ホワイトリスト方式で許可フィールドのみ受け付ける ──
    # 意図しないカラム（line_user_id 等）を上書きされないようにする
    allowed_fields = {"notify_time", "notify_enabled"}
    update_data = {k: v for k, v in data.items() if k in allowed_fields}

    if not update_data:
        return {"error": "更新するデータがありません", "code": "VALIDATION_ERROR"}, 400

    # ── notify_time のバリデーション ──
    # "HH:MM" 形式で、分は 00 か 30 のみ許可（30分刻み）
    # 例: "07:00", "21:30" → OK / "25:00", "09:15" → NG
    if "notify_time" in update_data:
        nt = update_data["notify_time"]
        try:
            h, m = map(int, nt.split(":"))
            if not (0 <= h <= 23 and m in (0, 30)):
                raise ValueError
        except (ValueError, AttributeError):
            return {"error": "通知時間の形式が正しくありません", "code": "VALIDATION_ERROR"}, 400

    try:
        supabase_admin.table("user_settings") \
            .update(update_data) \
            .eq("line_user_id", line_user_id) \
            .execute()
        return {"ok": True}
    except Exception as e:
        current_app.logger.error(f"設定更新エラー: {e}")
        return {"error": "サーバーエラーが発生しました", "code": "INTERNAL_ERROR"}, 500
