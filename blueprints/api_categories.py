# ============================================
# カテゴリ管理 Blueprint（ページ + API）
# ============================================

from flask import Blueprint, request, render_template, current_app

from extensions import supabase_admin
from auth_utils import login_required, get_current_user_line_id
from ai_classifier import CATEGORY_DESCRIPTIONS

api_categories_bp = Blueprint("api_categories", __name__)


@api_categories_bp.route("/categories")
@login_required
def categories_page():
    """カテゴリ管理画面を表示"""
    line_user_id = get_current_user_line_id()

    # sort_order → created_at の順でソート（並び替え機能対応）
    categories = supabase_admin.table("categories") \
        .select("id, name, sort_order") \
        .eq("line_user_id", line_user_id) \
        .order("sort_order") \
        .order("created_at") \
        .execute()

    for cat in categories.data:
        count_result = supabase_admin.table("items") \
            .select("id", count="exact") \
            .eq("category_id", cat["id"]) \
            .eq("status", "pending") \
            .is_("deleted_at", "null") \
            .execute()
        cat["item_count"] = count_result.count if hasattr(count_result, 'count') else 0

    return render_template("categories.html", categories=categories.data,
                           ai_categories=CATEGORY_DESCRIPTIONS)


@api_categories_bp.route("/api/categories", methods=["POST"])
@login_required
def create_category():
    """新しいカテゴリを作成する"""
    line_user_id = get_current_user_line_id()
    name = request.json.get("name", "").strip()

    if not name:
        return {"error": "カテゴリ名を入力してください", "code": "VALIDATION_ERROR"}, 400

    try:
        # 現在の最大 sort_order を取得（未分類の 999999 は除く）
        existing = supabase_admin.table("categories") \
            .select("sort_order") \
            .eq("line_user_id", line_user_id) \
            .lt("sort_order", 999999) \
            .order("sort_order", desc=True) \
            .limit(1) \
            .execute()

        # 新しいカテゴリは末尾（未分類の直前）に配置
        new_sort_order = (existing.data[0]["sort_order"] + 1) if existing.data else 1

        # insert に sort_order を追加
        result = supabase_admin.table("categories").insert({
            "line_user_id": line_user_id,
            "name": name,
            "sort_order": new_sort_order,
        }).execute()
        return {"ok": True, "category": result.data[0]}
    except Exception as e:
        if "duplicate" in str(e).lower():
            return {"error": "同じ名前のカテゴリが既にあります", "code": "DUPLICATE_ERROR"}, 400
        current_app.logger.error(f"カテゴリ作成エラー: {e}")
        return {"error": "サーバーエラーが発生しました", "code": "INTERNAL_ERROR"}, 500


@api_categories_bp.route("/api/categories/<category_id>", methods=["PUT"])
@login_required
def update_category(category_id):
    """カテゴリ名を変更する"""
    line_user_id = get_current_user_line_id()
    name = request.json.get("name", "").strip()

    if not name:
        return {"error": "カテゴリ名を入力してください", "code": "VALIDATION_ERROR"}, 400

    try:
        supabase_admin.table("categories") \
            .update({"name": name}) \
            .eq("id", category_id) \
            .eq("line_user_id", line_user_id) \
            .execute()
        return {"ok": True}
    except Exception as e:
        current_app.logger.error(f"カテゴリ更新エラー: {e}")
        return {"error": "サーバーエラーが発生しました", "code": "INTERNAL_ERROR"}, 500


@api_categories_bp.route("/api/categories/<category_id>", methods=["DELETE"])
@login_required
def delete_category(category_id):
    """カテゴリを削除する（アイテムは「未分類」に移動）"""
    line_user_id = get_current_user_line_id()

    try:
        # 「未分類」カテゴリのIDを取得
        uncategorized = supabase_admin.table("categories") \
            .select("id") \
            .eq("line_user_id", line_user_id) \
            .eq("name", "未分類") \
            .execute()

        uncategorized_id = uncategorized.data[0]["id"] if uncategorized.data else None

        # このカテゴリのアイテムを「未分類」に移動
        if uncategorized_id:
            supabase_admin.table("items") \
                .update({"category_id": uncategorized_id}) \
                .eq("category_id", category_id) \
                .eq("line_user_id", line_user_id) \
                .execute()

        # カテゴリを削除
        supabase_admin.table("categories") \
            .delete() \
            .eq("id", category_id) \
            .eq("line_user_id", line_user_id) \
            .execute()

        return {"ok": True}
    except Exception as e:
        current_app.logger.error(f"カテゴリ削除エラー: {e}")
        return {"error": "サーバーエラーが発生しました", "code": "INTERNAL_ERROR"}, 500


@api_categories_bp.route("/api/categories/reorder", methods=["POST"])
@login_required
def reorder_categories():
    """カテゴリの並び順を一括更新する"""
    line_user_id = get_current_user_line_id()
    order_list = request.json.get("order", [])

    # バリデーション: 並び順データが空の場合はエラー
    if not order_list:
        return {"error": "並び順データがありません", "code": "VALIDATION_ERROR"}, 400

    try:
        # 各カテゴリの sort_order を更新
        for item in order_list:
            category_id = item.get("id")
            sort_order = item.get("sort_order")
            if not category_id or sort_order is None:
                continue

            # line_user_id で絞り込んで他ユーザーのデータを変更できないようにする
            supabase_admin.table("categories") \
                .update({"sort_order": sort_order}) \
                .eq("id", category_id) \
                .eq("line_user_id", line_user_id) \
                .execute()

        return {"ok": True}
    except Exception as e:
        current_app.logger.error(f"カテゴリ並び替えエラー: {e}")
        return {"error": "サーバーエラーが発生しました", "code": "INTERNAL_ERROR"}, 500
