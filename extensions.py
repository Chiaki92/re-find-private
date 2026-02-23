# ============================================
# 共有シングルトン（Blueprint から import して使う）
# ============================================
# app.py → blueprints → extensions.py の一方向依存にすることで
# 循環 import を防止する。

import os
from datetime import timedelta, timezone
from supabase import create_client
from linebot.v3 import WebhookHandler
from linebot.v3.messaging import Configuration

# --- タイムゾーン ---
JST = timezone(timedelta(hours=9))

# --- Supabase 管理用クライアント（service_role） ---
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
    raise RuntimeError("SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY が設定されていません")

supabase_admin = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

# --- LINE Bot SDK ---
_channel_access_token = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")
_channel_secret = os.environ.get("LINE_CHANNEL_SECRET")

if not _channel_access_token or not _channel_secret:
    raise RuntimeError(
        "LINE_CHANNEL_SECRET / LINE_CHANNEL_ACCESS_TOKEN が設定されていません"
    )

line_configuration = Configuration(access_token=_channel_access_token)
line_handler = WebhookHandler(_channel_secret)
