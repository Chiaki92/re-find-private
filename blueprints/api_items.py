# ============================================
# アイテム API Blueprint（更新・削除・共有・コピー）
# ============================================

import uuid
from datetime import datetime, timedelta
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


@api_items_bp.route("/api/items/copy", methods=["POST"])
@login_required
def copy_item():
    """共有アイテムを自分のアイテムとしてコピーする"""
    line_user_id = get_current_user_line_id()
    data = request.json or {}
    source_item_id = data.get("item_id")

    if not source_item_id:
        return {"error": "コピー元のアイテムIDが必要です", "code": "VALIDATION_ERROR"}, 400

    try:
        # 1. コピー元アイテムを取得
        source = supabase_admin.table("items") \
            .select("*, categories(name)") \
            .eq("id", source_item_id) \
            .is_("deleted_at", "null") \
            .execute()

        if not source.data:
            return {"error": "アイテムが見つかりません", "code": "NOT_FOUND"}, 404

        source_item = source.data[0]

        # 2. 自分のアイテムでないことを確認
        if source_item["line_user_id"] == line_user_id:
            return {"error": "自分のアイテムはコピーできません", "code": "SELF_COPY"}, 400

        # 3. コピー先ユーザーの通知時間設定を取得
        settings_res = supabase_admin.table("user_settings") \
            .select("notify_time") \
            .eq("line_user_id", line_user_id) \
            .execute()
        notify_time = settings_res.data[0].get("notify_time", "21:00") if settings_res.data else "21:00"
        parts = notify_time.split(":")
        nt_hour, nt_minute = int(parts[0]), int(parts[1])

        first_notify_at = (datetime.now(JST) + timedelta(days=1)).replace(
            hour=nt_hour, minute=nt_minute, second=0, microsecond=0
        )

        # 4. カテゴリ名でマッチング
        category_id = None
        source_cat = source_item.pop("categories", None)
        source_cat_name = source_cat["name"] if source_cat else None

        if source_cat_name:
            cat_res = supabase_admin.table("categories") \
                .select("id") \
                .eq("line_user_id", line_user_id) \
                .eq("name", source_cat_name) \
                .limit(1) \
                .execute()
            if cat_res.data:
                category_id = cat_res.data[0]["id"]

        # 5. 新しいアイテムを作成
        new_item_id = str(uuid.uuid4())
        new_item = {
            "id": new_item_id,
            "line_user_id": line_user_id,
            "type": source_item.get("type"),
            "title": source_item.get("title"),
            "description": source_item.get("description"),
            "original_url": source_item.get("original_url"),
            "ogp_image": source_item.get("ogp_image"),
            "image_url": source_item.get("image_url"),
            "memo": source_item.get("memo"),
            "status": "pending",
            "notify_count": 0,
            "next_notify_at": first_notify_at.isoformat(),
            "category_id": category_id,
        }
        supabase_admin.table("items").insert(new_item).execute()

        # 6. コピー履歴を記録
        supabase_admin.table("item_copies").insert({
            "source_item_id": source_item_id,
            "copied_by": line_user_id,
            "copied_item_id": new_item_id,
        }).execute()

        return {"ok": True, "new_item_id": new_item_id}

    except Exception as e:
        current_app.logger.error(f"アイテムコピーエラー: {e}")
        return {"error": "サーバーエラーが発生しました", "code": "INTERNAL_ERROR"}, 500
