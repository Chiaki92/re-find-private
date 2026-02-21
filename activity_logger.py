# ============================================
# activity_logger.py
# ============================================
# 役割：ユーザーの行動ログを user_activity_logs テーブルに記録する
#
# ログ記録はアプリの主機能ではないため、
# 失敗してもアプリ全体に影響させない（サイレントキャッチ）。
#
# 使い方：
#   from activity_logger import log_activity
#   log_activity("U1234...", "bot_message", metadata={"message_type": "text"})
#
# 呼び出し元：
#   app.py の各メッセージハンドラ（保存成功後に呼ぶ）
# ============================================

import os
from dotenv import load_dotenv
from supabase import create_client

# ローカル開発時は .env を読み込む
load_dotenv()

# Supabase 管理用クライアント（service_role でRLSバイパス）
supabase_admin = create_client(
    os.environ.get("SUPABASE_URL"),
    os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
)


def log_activity(line_user_id, action_type, item_id=None, metadata=None):
    """
    行動ログを user_activity_logs テーブルに記録する。

    引数:
        line_user_id (str): LINEのユーザーID（例: "U1234..."）
        action_type (str): 行動の種類（例: "bot_message"）
        item_id (str, optional): 関連するアイテムのID
        metadata (dict, optional): 追加情報（例: {"message_type": "text"}）

    戻り値: なし（失敗してもエラーを出さない）
    """
    try:
        # 必須フィールドを設定
        data = {
            "line_user_id": line_user_id,
            "action_type": action_type,
        }

        # オプションフィールドがあれば追加
        if item_id:
            data["item_id"] = item_id
        if metadata:
            data["metadata"] = metadata

        # user_activity_logs テーブルにINSERT
        supabase_admin.table("user_activity_logs").insert(data).execute()

    except Exception as e:
        # ログ記録失敗はアプリ全体に影響させない
        print(f"ログ記録エラー: {e}")
