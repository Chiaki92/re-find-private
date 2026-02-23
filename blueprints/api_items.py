# ============================================
# アイテム API Blueprint（更新・削除・共有）
# ============================================

import uuid
from datetime import datetime
from flask import Blueprint, request, current_app

from extensions import supabase_admin, JST
from auth_utils import login_required, get_current_user_line_id

api_items_bp = Blueprint("api_items", __name__)


@api_items_bp.route("/api/items/<item_id>", methods=["PUT"])
@login_required
def update_item(item_id):
    """アイテムを更新する（カテゴリ変更、メモ追加、対応済みなど）"""
    line_user_id = get_current_user_line_id()
    data = request.json

    allowed_fields = {"title", "category_id", "memo", "status"}
    update_data = {k: v for k, v in data.items() if k in allowed_fields}

    if not update_data:
        return {"error": "更新するデータがありません", "code": "VALIDATION_ERROR"}, 400

    try:
        supabase_admin.table("items") \
            .update(update_data) \
            .eq("id", item_id) \
            .eq("line_user_id", line_user_id) \
            .execute()
        return {"ok": True}
    except Exception as e:
        current_app.logger.error(f"アイテム更新エラー: {e}")
        return {"error": "サーバーエラーが発生しました", "code": "INTERNAL_ERROR"}, 500


@api_items_bp.route("/api/items/<item_id>", methods=["DELETE"])
@login_required
def delete_item(item_id):
    """アイテムを削除する（ソフトデリート）"""
    line_user_id = get_current_user_line_id()

    try:
        supabase_admin.table("items") \
            .update({"deleted_at": datetime.now(JST).isoformat()}) \
            .eq("id", item_id) \
            .eq("line_user_id", line_user_id) \
            .execute()
        return {"ok": True}
    except Exception as e:
        current_app.logger.error(f"アイテム削除エラー: {e}")
        return {"error": "サーバーエラーが発生しました", "code": "INTERNAL_ERROR"}, 500


@api_items_bp.route("/api/items/<item_id>/share", methods=["POST"])
@login_required
def create_share_link(item_id):
    """共有リンクを作成する"""
    line_user_id = get_current_user_line_id()

    token = str(uuid.uuid4()).replace("-", "")[:16]

    try:
        supabase_admin.table("shared_links").insert({
            "line_user_id": line_user_id,
            "item_id": item_id,
            "token": token,
        }).execute()

        base_url = request.host_url.rstrip("/")
        share_url = f"{base_url}/share/{token}"

        return {"ok": True, "share_url": share_url}
    except Exception as e:
        current_app.logger.error(f"共有リンク作成エラー: {e}")
        return {"error": "サーバーエラーが発生しました", "code": "INTERNAL_ERROR"}, 500
