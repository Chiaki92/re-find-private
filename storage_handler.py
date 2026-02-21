# storage_handler.py

import os
from supabase import create_client, Client

# ===============================
# 環境変数から Supabase 情報を取得
# ===============================
SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_SERVICE_ROLE_KEY = os.environ["SUPABASE_SERVICE_ROLE_KEY"]

# 管理者権限で接続（Storageアップロード用）
supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

# 保存先のバケット名（Supabaseで作成済みのもの）
BUCKET_NAME = "screenshots"


def upload_image(user_id: str, item_id: str, image_bytes: bytes) -> str:
    """
    画像を Supabase Storage にアップロードして
    公開URLを返す関数

    Parameters:
        user_id: LINEのユーザーID
        item_id: DBに保存するアイテムID（UUID）
        image_bytes: LINEから取得した画像データ（バイト列）

    Returns:
        public_url (str)
    """

    # ファイル保存パス
    # 例: Uxxxxxxxx/550e8400-e29b-41d4-a716-446655440000.png
    file_path = f"{user_id}/{item_id}.png"

    # ===============================
    # Storageへアップロード
    # ===============================
    supabase.storage.from_(BUCKET_NAME).upload(
        path=file_path,              # 旧SDK では file= だった
        file=image_bytes,            # 旧SDK では file_content= だった
        file_options={
            "content-type": "image/png",  # 画像形式
            "upsert": "true"  # 同名なら上書き
        },
    )

    # ===============================
    # 公開URL取得
    # ===============================
    public_url = supabase.storage.from_(BUCKET_NAME).get_public_url(file_path)

    # バージョン差異対策
    if isinstance(public_url, dict):
        public_url = public_url.get("publicUrl")

    return public_url