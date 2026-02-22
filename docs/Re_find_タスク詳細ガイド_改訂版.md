# Re:find — タスク詳細ガイド（改訂版）

> **最終更新：2/22（土）夜**
> B-5 まで全完了。フロントエンド（HTML/CSS/JS）を一括反映済み。
> このドキュメントは「**今から何をするか**」にフォーカスしています。

---

## 📍 現在地マップ

```
=== 完了済み ===================================================

  A（企画）       → 全完了 ✅
  B-1（DB構築）    → 全完了 ✅
  B-2（AI分類）    → 全完了 ✅
  B-3（画像処理）   → 全完了 ✅
  B-4（OGP・ログ）  → 全完了 ✅
  B-5（LINE Login） → 全完了 ✅
  レビュー①       → 全完了 ✅

  C-1 フロントエンド一括作成（HTML/CSS/JS 全15ファイル）→ 配置済み ✅

=== ★ 今ここ ===================================================

  C-1-3  Flask ルートにデータ受け渡しを接続   ← 次にやること
  C-1-4  カテゴリフィルタ（JS済み、動作確認のみ）

=== これから ===================================================

  C-2    編集モーダルの Flask API
  C-3    カテゴリ管理の Flask API
  C-4    共有リンク機能
  C-5    通知機能（notify.py）
  テスト＋発表準備
```

---

## ✅ 完了済み一覧（参照用・作業不要）

<details>
<summary>クリックで展開（A〜B-5 の全タスク）</summary>

| No. | タスクID | 内容 | 状態 |
|-----|---------|------|------|
| 1 | A-4-1 | DB設計ドキュメント読み合わせ | ✅ |
| 2 | A-4-2 | 技術スタック未決事項を決定 | ✅ |
| 3 | A-4-3 | 決定事項をドキュメントに反映 | ✅ |
| 4 | A-5-1 | タスク分解・担当決め | ✅ |
| 5 | A-5-2 | アカウント準備確認 | ✅ |
| 6 | A-6-1 | GitHubリポジトリ作成 | ✅ |
| 7 | A-6-2 | Flaskプロジェクト雛形 | ✅ |
| 8 | A-6-3 | Renderデプロイ | ✅ |
| 9 | A-6-4 | LINE Developers チャネル作成 | ✅ |
| 10 | A-6-5 | LINE Bot Webhook接続 | ✅ |
| 11 | B-1-1 | Supabaseプロジェクト作成 | ✅ |
| 12 | B-1-2 | usersテーブル作成 | ✅ |
| 13 | B-1-3 | categoriesテーブル作成 | ✅ |
| 14 | B-1-4 | itemsテーブル作成 | ✅ |
| 15 | B-1-5 | shared_links + activity_logsテーブル | ✅ |
| 16 | B-1-6 | user_settings + notification_rulesテーブル | ✅ |
| 17 | B-1-7 | トリガー設定 | ✅ |
| 18 | B-1-8 | RLS有効化（方法Aにより不要→完了扱い） | ✅ |
| 19 | B-1-9 | Storageバケット作成 | ✅ |
| 20 | B-1-10 | Python→Supabase接続テスト | ✅ |
| 21 | B-2-1 | OpenRouterアカウント + 動作確認 | ✅ |
| 22 | B-2-2 | AI分類プロンプト設計 | ✅ |
| 23 | B-2-3 | ai_classifier.py 作成 | ✅ |
| 24 | B-2-4 | app.pyにAI分類を統合 | ✅ |
| 25 | B-3-1 | 画像受信の基本処理 | ✅ |
| 26 | B-3-2 | 画像をStorageに保存 | ✅ |
| 27 | B-3-3 | 画像のAI分類 | ✅ |
| 28 | B-4-1 | URL判定処理 | ✅ |
| 29 | B-4-2 | OGP情報取得（ogp_fetcher.py） | ✅ |
| 30 | B-4-3 | URL処理の統合 | ✅ |
| 31 | B-4-4 | エラーハンドリング | ✅ |
| 32 | B-4-5 | 行動ログ記録（activity_logger.py） | ✅ |
| 34-36 | R①-1〜3 | レビュー① | ✅ |
| 37 | B-5-1 | LINE Loginチャネル作成 + 環境変数 | ✅ |
| 38 | B-5-2 | ログイン画面HTML | ✅ |
| 39 | B-5-3 | LINE OAuth処理（Flask側で直接処理） | ✅ |
| 40 | B-5-4 | ログアウト処理 | ✅ |
| — | 追加①② | usersテーブル修正 + RLS方針変更 | ✅ |
| — | 追加③ | ヘルパー関数（login_required等） | ✅ |

**フロントエンド一括作成（Claudeで作成・配置済み）：**
| ファイル | 状態 |
|---------|------|
| templates/base.html | ✅ 配置済み |
| templates/login.html | ✅ 配置済み |
| templates/index.html | ✅ 配置済み |
| templates/categories.html | ✅ 配置済み |
| templates/shared_item.html | ✅ 配置済み |
| static/css/common.css | ✅ 配置済み |
| static/css/login.css | ✅ 配置済み |
| static/css/index.css | ✅ 配置済み |
| static/css/modal.css | ✅ 配置済み |
| static/css/categories.css | ✅ 配置済み |
| static/css/shared.css | ✅ 配置済み |
| static/js/common.js | ✅ 配置済み |
| static/js/index.js | ✅ 配置済み |
| static/js/modal.js | ✅ 配置済み |
| static/js/categories.js | ✅ 配置済み |

</details>

---
---

# 🔨 ここから先の作業

---

## STEP 1 — 一覧画面をデータで動かす（C-1-3, C-1-4）

### 🎯 ゴール
ログイン → Supabase からアイテム＋カテゴリを取得 → 一覧画面に表示される

### やること

**HTML/CSS/JS はすべて配置済み。** app.py の `/` ルートを修正して、テンプレートに正しいデータを渡すだけ。

#### ① app.py の `/` ルートを修正

```python
import json

@app.route("/")
@login_required
def index():
    """一覧画面：ログインユーザーのアイテムをタイル表示"""
    line_user_id = get_current_user_line_id()

    # --- カテゴリ一覧を取得 ---
    categories = supabase_admin.table("categories") \
        .select("id, name") \
        .eq("line_user_id", line_user_id) \
        .order("created_at") \
        .execute()

    # --- アイテム一覧を取得 ---
    # ⚠️ deleted_at IS NULL を忘れると削除済みも表示される
    items = supabase_admin.table("items") \
        .select("*, categories(name)") \
        .eq("line_user_id", line_user_id) \
        .is_("deleted_at", "null") \
        .order("created_at", desc=True) \
        .execute()

    # --- カテゴリ名をアイテムに追加 ---
    # Supabase のリレーション結果を整形する
    items_list = []
    for item in items.data:
        # categories(name) の結果を取り出す
        cat = item.pop("categories", None)
        item["category_name"] = cat["name"] if cat else "未分類"
        items_list.append(item)

    # --- テンプレートにデータを渡す ---
    return render_template("index.html",
        categories=categories.data,    # カテゴリタブ用
        items=items_list,              # カード表示用
        items_json=json.dumps(items_list, default=str),  # JS用（モーダル）
    )
```

#### ② Jinja2 カスタムフィルタを追加

index.html で使っている `timeago` フィルタと、shared_item.html で使う `dateformat` フィルタを app.py に追加する。

```python
from datetime import datetime, timezone, timedelta

# 日本時間
JST = timezone(timedelta(hours=9))

@app.template_filter('timeago')
def timeago_filter(value):
    """日時を「3日前」のような相対表示に変換する Jinja2 フィルタ"""
    if not value:
        return ""
    # 文字列なら datetime に変換
    if isinstance(value, str):
        # ISO形式の文字列を datetime に変換
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
    """日時を「2026/02/20」形式に変換する Jinja2 フィルタ"""
    if not value:
        return ""
    if isinstance(value, str):
        value = datetime.fromisoformat(value.replace("Z", "+00:00"))
    jst_time = value.astimezone(JST)
    return jst_time.strftime("%Y/%m/%d")
```

#### ③ ログイン画面のルート確認

```python
@app.route("/login")
def login_page():
    """ログイン画面を表示"""
    # すでにログイン済みならトップへリダイレクト
    if session.get("line_user_id"):
        return redirect("/")
    return render_template("login.html")
```

#### ④ 動作確認

1. ローカルで `python app.py` を起動
2. ブラウザで `http://127.0.0.1:5000/login` → ログイン画面が表示される
3. LINEログイン → トップページにリダイレクト
4. LINEで事前に送ったアイテムがカード表示されている
5. カテゴリタブをタップ → フィルタリングが動く

**完了チェック：**
- [ ] `/login` でログイン画面が表示される（デザインが反映されている）
- [ ] LINEログイン後、一覧画面にアイテムが表示される
- [ ] カテゴリタブで絞り込みができる
- [ ] アイテムがないときは「まだアイテムがありません」と表示される

---

## STEP 2 — 編集モーダルの Flask API を作る（C-2）

### 🎯 ゴール
カードをタップ → モーダルが開く → カテゴリ変更・メモ追加・対応済み・削除がすべて動く

### やること

**modal.js（フロントエンド）は配置済み。** Flask 側に API エンドポイントを追加するだけ。

modal.js は以下の API を呼んでいる：

| JS の呼び出し | Flask に必要なルート | HTTPメソッド |
|-------------|-------------------|------------|
| `apiPut('/api/items/123', data)` | `/api/items/<item_id>` | PUT |
| `apiDelete('/api/items/123')` | `/api/items/<item_id>` | DELETE |
| `apiPut('/api/items/123', {status: 'done'})` | （↑ と同じ） | PUT |
| `apiPost('/api/items/123/share', {})` | `/api/items/<item_id>/share` | POST |

#### ① アイテム更新 API

```python
@app.route("/api/items/<item_id>", methods=["PUT"])
@login_required
def update_item(item_id):
    """アイテムを更新する（カテゴリ変更、メモ追加、対応済みなど）"""
    line_user_id = get_current_user_line_id()
    data = request.json

    # 更新できるフィールドだけ抽出（不正なフィールドを弾く）
    allowed_fields = {"title", "category_id", "memo", "status"}
    update_data = {k: v for k, v in data.items() if k in allowed_fields}

    if not update_data:
        return {"error": "更新するデータがありません"}, 400

    try:
        supabase_admin.table("items") \
            .update(update_data) \
            .eq("id", item_id) \
            .eq("line_user_id", line_user_id) \
            .execute()
        return {"ok": True}
    except Exception as e:
        print(f"アイテム更新エラー: {e}")
        return {"error": str(e)}, 500
```

#### ② アイテム削除 API（ソフトデリート）

```python
@app.route("/api/items/<item_id>", methods=["DELETE"])
@login_required
def delete_item(item_id):
    """アイテムを削除する（ソフトデリート：deleted_at に日時を入れる）"""
    line_user_id = get_current_user_line_id()

    try:
        supabase_admin.table("items") \
            .update({"deleted_at": datetime.now(JST).isoformat()}) \
            .eq("id", item_id) \
            .eq("line_user_id", line_user_id) \
            .execute()
        return {"ok": True}
    except Exception as e:
        print(f"アイテム削除エラー: {e}")
        return {"error": str(e)}, 500
```

#### ③ 共有リンク作成 API

```python
import uuid

@app.route("/api/items/<item_id>/share", methods=["POST"])
@login_required
def create_share_link(item_id):
    """共有リンクを作成する"""
    line_user_id = get_current_user_line_id()

    # ランダムなトークンを生成
    token = str(uuid.uuid4()).replace("-", "")[:16]

    try:
        supabase_admin.table("shared_links").insert({
            "line_user_id": line_user_id,
            "item_id": item_id,
            "token": token,
        }).execute()

        # 共有URLを返す
        base_url = request.host_url.rstrip("/")
        share_url = f"{base_url}/share/{token}"

        return {"ok": True, "share_url": share_url}
    except Exception as e:
        print(f"共有リンク作成エラー: {e}")
        return {"error": str(e)}, 500
```

#### ④ 動作確認

1. 一覧画面でカードをタップ → モーダルが開く
2. タイトルを変更して「保存する」→ リロード後に反映されている
3. メモを追加して「保存する」→ 反映
4. 「✓ 対応済みにする」→ カードが薄くなる
5. 「🗑 削除」→ カードが消える
6. 「🔗 共有リンクを作成」→ クリップボードにURLがコピーされる

**完了チェック：**
- [ ] モーダルでカテゴリ変更ができる
- [ ] メモを追加して保存できる
- [ ] 「対応済み」にできる（カードが薄くなる）
- [ ] 削除ができる（一覧から消える）
- [ ] 共有リンクが作成できる（URLがコピーされる）

---

## STEP 3 — カテゴリ管理の Flask API を作る（C-3）

### 🎯 ゴール
カテゴリ管理画面で新規作成・名前変更・削除がすべて動く

### やること

**categories.html / categories.css / categories.js は配置済み。** Flask 側に API とページルートを追加する。

categories.js は以下の API を呼んでいる：

| JS の呼び出し | Flask に必要なルート | HTTPメソッド |
|-------------|-------------------|------------|
| `apiPost('/api/categories', {name})` | `/api/categories` | POST |
| `apiPut('/api/categories/123', {name})` | `/api/categories/<id>` | PUT |
| `apiDelete('/api/categories/123')` | `/api/categories/<id>` | DELETE |

#### ① カテゴリ管理ページのルート

```python
@app.route("/categories")
@login_required
def categories_page():
    """カテゴリ管理画面を表示"""
    line_user_id = get_current_user_line_id()

    # カテゴリ一覧を取得（アイテム件数付き）
    categories = supabase_admin.table("categories") \
        .select("id, name") \
        .eq("line_user_id", line_user_id) \
        .order("created_at") \
        .execute()

    # 各カテゴリのアイテム件数を取得
    for cat in categories.data:
        count_result = supabase_admin.table("items") \
            .select("id", count="exact") \
            .eq("category_id", cat["id"]) \
            .is_("deleted_at", "null") \
            .execute()
        cat["item_count"] = count_result.count if hasattr(count_result, 'count') else 0

    return render_template("categories.html", categories=categories.data)
```

#### ② カテゴリ追加 API

```python
@app.route("/api/categories", methods=["POST"])
@login_required
def create_category():
    """新しいカテゴリを作成する"""
    line_user_id = get_current_user_line_id()
    name = request.json.get("name", "").strip()

    if not name:
        return {"error": "カテゴリ名を入力してください"}, 400

    try:
        result = supabase_admin.table("categories").insert({
            "line_user_id": line_user_id,
            "name": name,
        }).execute()
        return {"ok": True, "category": result.data[0]}
    except Exception as e:
        # 重複エラーの場合
        if "duplicate" in str(e).lower():
            return {"error": "同じ名前のカテゴリが既にあります"}, 400
        return {"error": str(e)}, 500
```

#### ③ カテゴリ名変更 API

```python
@app.route("/api/categories/<category_id>", methods=["PUT"])
@login_required
def update_category(category_id):
    """カテゴリ名を変更する"""
    line_user_id = get_current_user_line_id()
    name = request.json.get("name", "").strip()

    if not name:
        return {"error": "カテゴリ名を入力してください"}, 400

    try:
        supabase_admin.table("categories") \
            .update({"name": name}) \
            .eq("id", category_id) \
            .eq("line_user_id", line_user_id) \
            .execute()
        return {"ok": True}
    except Exception as e:
        return {"error": str(e)}, 500
```

#### ④ カテゴリ削除 API（アイテムを「未分類」に移動）

```python
@app.route("/api/categories/<category_id>", methods=["DELETE"])
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
        print(f"カテゴリ削除エラー: {e}")
        return {"error": str(e)}, 500
```

**完了チェック：**
- [ ] `/categories` でカテゴリ管理画面が表示される
- [ ] 新しいカテゴリを追加できる
- [ ] カテゴリ名を変更できる（入力欄を編集して外をクリック）
- [ ] カテゴリを削除できる（アイテムが「未分類」に移動する）
- [ ] 「未分類」は削除できない（🔒 固定 と表示される）

---

## STEP 4 — 共有リンク閲覧ページ（C-4）

### 🎯 ゴール
共有リンクをブラウザで開くと、ログイン不要でアイテムが1つ表示される

### やること

**shared_item.html / shared.css は配置済み。** Flask ルートを追加するだけ。

```python
@app.route("/share/<token>")
def shared_item_page(token):
    """共有リンク閲覧ページ（ログイン不要）"""

    # service_role_key でRLSバイパスしてデータ取得
    try:
        # トークンから共有リンク情報を取得
        link = supabase_admin.table("shared_links") \
            .select("item_id") \
            .eq("token", token) \
            .execute()

        if not link.data:
            # トークンが見つからない → 無効なリンク
            return render_template("shared_item.html", item=None)

        item_id = link.data[0]["item_id"]

        # アイテム情報を取得
        item = supabase_admin.table("items") \
            .select("*, categories(name)") \
            .eq("id", item_id) \
            .is_("deleted_at", "null") \
            .execute()

        if not item.data:
            return render_template("shared_item.html", item=None)

        # カテゴリ名を整形
        item_data = item.data[0]
        cat = item_data.pop("categories", None)
        item_data["category_name"] = cat["name"] if cat else "未分類"

        return render_template("shared_item.html", item=item_data)

    except Exception as e:
        print(f"共有リンクエラー: {e}")
        return render_template("shared_item.html", item=None)
```

**完了チェック：**
- [ ] 共有リンク（`/share/xxxx`）にアクセスするとアイテムが表示される
- [ ] ログインしていなくても表示される
- [ ] 存在しないトークンだと「このリンクは無効です」と表示される

---

## STEP 5 — 通知機能（C-5）

### 🎯 ゴール
Render Cron Job で毎日21時（JST）に、通知対象アイテムをLINEで送信

### やること

`notify.py` を新規作成する。

#### ① 通知ロジック

```
next_notify_at ≤ 現在時刻
AND status = 'pending'
AND deleted_at IS NULL
→ ユーザーごとにまとめて1通LINE送信
→ notify_count +1、次の通知日時を計算
```

#### ② 通知間隔

```
notify_count 0 → 1日後に通知
notify_count 1 → 3日後に通知
notify_count 2 → 7日後に通知
notify_count 3 → 14日後に通知
notify_count 4 → 30日後に通知
notify_count 5 → 60日後に通知（最終通知）
notify_count 6 → status を 'archived' に変更（通知終了）
```

#### ③ 重要ポイント

**通知内URLは外部ブラウザで開く：**
```python
# ✅ URLに ?openExternalBrowser=1 を付ける
web_url = "https://re-find.onrender.com/?openExternalBrowser=1"
```

LINEアプリ内ブラウザだとCookieが不安定でセッションが切れるため。

**最終通知（6通目）のメッセージ：**
```
📌 最後のお知らせです
🎹 ピアノ教室の情報
この情報は 60日前 に保存され、これまでに 6回 お知らせしました。
今回が最後の通知です。
まだ気になるなら、Webアプリで「未対応」に戻せます。
[Webアプリで確認する]
```

#### ④ Render Cron Job 設定

1. Render ダッシュボード → 「New +」→「Cron Job」
2. GitHubリポジトリを選択
3. 設定：
   - **Name**: `re-find-notify`
   - **Schedule**: `0 12 * * *`（UTC 12:00 = JST 21:00）
   - **Build Command**: `pip install -r requirements.txt`
   - **Command**: `python notify.py`
4. 環境変数を re-find サービスと同じものを設定

**完了チェック：**
- [ ] `python notify.py` を手動実行してLINE通知が届く
- [ ] 通知メッセージにアイテムのタイトルが含まれている
- [ ] 通知内のURLに `?openExternalBrowser=1` が付いている
- [ ] 通知リンクタップ → 外部ブラウザ → ログインなしで一覧表示
- [ ] Render Cron Job が設定されている

---

## STEP 6 — 最終テスト＋レビュー②（2/26）

### 通しテスト 4シナリオ

| # | シナリオ | 確認ポイント |
|---|---------|------------|
| 1 | LINE でスクショ送信 → AI分類 → Web一覧に表示 → 通知 → 対応済み | 画像→DB→表示→通知→ステータス変更 |
| 2 | LINE で URL 送信 → OGP取得 → AI分類 → カテゴリ変更 → 共有リンク発行 | URL→OGP→分類→モーダル→共有 |
| 3 | LINE でテキスト送信 → AI分類 → メモ追加 → 削除 | テキスト→分類→モーダル→ソフトデリート |
| 4 | カテゴリ管理（新規作成 → 名前変更 → 削除） | CRUD全操作 |

### 多人数テスト

チーム3人が**別アカウント**でログイン → 他の人のデータが見えないことを確認

**完了チェック：**
- [ ] 4シナリオすべて正常動作
- [ ] 他ユーザーのデータが見えない
- [ ] スマホ実機で表示崩れがない

---

## STEP 7 — デモ準備＋発表（2/27）

- [ ] デモ用データを投入（各カテゴリ3〜5件）
- [ ] **デモ前にRenderにアクセスしてウォームアップ**（スリープ対策）
- [ ] 万が一の画面キャプチャを用意
- [ ] デモの流れを決めておく（LINE入力→一覧表示→モーダル操作→通知）

---

## 推奨スケジュール

```
2/23（月）
  午前：STEP 1 — 一覧画面のデータ接続
  午後：STEP 2 — 編集モーダル API
  　　　STEP 3 — カテゴリ管理 API
  夕方：動作確認＋バグ修正

2/24（火）
  午前：STEP 4 — 共有リンク機能
  午後：STEP 5 — 通知機能（notify.py）
  夕方：通しテスト＋バグ修正

2/25（水）
  終日：バグ修正＋UI微調整＋予備日

2/26（木）
  午前：STEP 6 — 最終テスト＋レビュー②
  午後：修正対応

2/27（金）
  STEP 7 — デモ準備＋発表
```

---

## 環境変数チェックリスト（Renderに設定済みのはず）

| 変数名 | 設定済み？ |
|--------|----------|
| LINE_CHANNEL_SECRET | ✅ |
| LINE_CHANNEL_ACCESS_TOKEN | ✅ |
| SUPABASE_URL | ✅ |
| SUPABASE_KEY | ✅ |
| SUPABASE_SERVICE_ROLE_KEY | ✅ |
| OPENROUTER_API_KEY | ✅ |
| LINE_LOGIN_CHANNEL_ID | ✅ |
| LINE_LOGIN_CHANNEL_SECRET | ✅ |

---

## 困ったときのチェック順序

1. **画面が真っ白** → Render のログを確認（Pythonエラーが出ているはず）
2. **テンプレートエラー** → block の二重定義がないか確認（headerブロック注意）
3. **データが表示されない** → Supabase Table Editor で実際にデータがあるか確認
4. **API が 500 エラー** → app.py の print 出力を Render ログで確認
5. **CSSが効かない** → ブラウザのDevTools(F12)でファイルが読み込まれているか確認
6. **ログインできない** → LINE Login のコールバックURL設定を再確認

