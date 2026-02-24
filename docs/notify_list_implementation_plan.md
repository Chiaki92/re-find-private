# Re:find 実装指示書 — 通知一覧ページ＆件数分岐メッセージ

## ゴール（何を作るか）

現在のLINE通知は件数が多いと視認性が悪い（例：13件を全部テキストで送ると長すぎる）。
これを解決するために以下の2つを実装する。

1. **通知一覧ページ**（`/notify-list`） → LINEから飛べるWebページ。今日の通知対象アイテムをタイル表示
2. **LINEメッセージの件数分岐** → 少ない件数はこれまで通り詳細テキスト、多い件数は目次＋URLのみ

---

## 変更するファイル一覧

| ファイル | 変更種別 | 内容 |
|---------|---------|------|
| `notify.py` | 修正 | メッセージ組み立て関数を追加、件数分岐ロジックを追加 |
| `app.py` | 修正 | `/notify-list` ルートを追加 |
| `templates/notify_list.html` | 新規作成 | 通知一覧ページのHTMLテンプレート |

---

## ① notify.py の修正

### 追加する定数

```python
# ===== 通知メッセージのしきい値 =====
# この件数を超えたら、詳細テキストではなく目次形式でLINEに送る
NOTIFY_DETAIL_LIMIT = 5
```

### 追加する関数

既存の通知送信処理の前に、以下の関数を追加する。

```python
def build_notify_message(items, line_user_id, notify_date_str):
    """
    LINEに送るメッセージ文字列を組み立てる関数。

    件数が NOTIFY_DETAIL_LIMIT 以下 → 詳細テキスト形式（カテゴリ名 + タイトル + 共有URL）
    件数が NOTIFY_DETAIL_LIMIT 超   → 目次形式（番号 + タイトルだけ）

    どちらの場合も、末尾に通知一覧ページのURLを添付する。

    Args:
        items (list): 通知対象のアイテムリスト。各アイテムは辞書形式。
                      必要なキー: title, category_name（カテゴリ名）, share_token（共有リンクのトークン）
        line_user_id (str): LINEユーザーID（将来のパーソナライズ用に引数として受け取る）
        notify_date_str (str): 通知日付の文字列（例: "2026-02-24"）。一覧ページURLに使う

    Returns:
        str: LINEに送るメッセージ全文
    """

    # ---- 一覧ページのURL（末尾に必ず添付する） ----
    # 環境変数からアプリのベースURLを取得する（Renderのドメインを想定）
    import os
    base_url = os.environ.get("APP_BASE_URL", "https://re-find.onrender.com")
    notify_list_url = f"{base_url}/notify-list?date={notify_date_str}"

    lines = []  # メッセージの行を格納するリスト

    # ---- 件数によってメッセージ形式を切り替える ----
    if len(items) <= NOTIFY_DETAIL_LIMIT:
        # ===== 少ない場合：詳細テキスト形式 =====
        lines.append(f"📬 {len(items)}件の情報を思い出してください！\n")

        for item in items:
            # カテゴリ名（Noneの場合は「未分類」と表示）
            category_name = item.get("category_name") or "未分類"
            title = item.get("title") or "タイトルなし"

            # 共有URLを組み立てる（share_tokenがあれば共有リンクを使う）
            share_token = item.get("share_token")
            if share_token:
                item_url = f"{base_url}/share/{share_token}"
            else:
                # 共有リンクがない場合は一覧ページに誘導
                item_url = notify_list_url

            lines.append(f"📁 {category_name}")
            lines.append(f"・{title}")
            lines.append(f"  {item_url}\n")

    else:
        # ===== 多い場合：目次形式 =====
        lines.append(f"📬 {len(items)}件の情報があります\n")
        lines.append("＜目次＞")

        for i, item in enumerate(items, 1):
            title = item.get("title") or "タイトルなし"
            lines.append(f"{i}. {title}")

    # ---- 末尾に一覧ページURLを添付（件数にかかわらず常に） ----
    lines.append(f"\n▶ 今日の通知一覧を確認する")
    lines.append(notify_list_url)

    return "\n".join(lines)
```

### 既存の通知送信ループへの組み込み

既存の「ユーザーごとにメッセージを組み立ててLINEに送る」部分を、上記の関数を使う形に書き換える。

```python
# ===== 変更前（イメージ）=====
# message = "\n".join([f"・{item['title']}" for item in user_items])

# ===== 変更後 =====
from datetime import datetime, timezone, timedelta

# 今日の日付文字列（日本時間）
jst = timezone(timedelta(hours=9))
today_str = datetime.now(jst).strftime("%Y-%m-%d")

# 関数を呼び出してメッセージを組み立てる
message = build_notify_message(
    items=user_items,
    line_user_id=line_user_id,
    notify_date_str=today_str
)

# LINEにプッシュ送信（既存の処理をそのまま使う）
line_bot_api.push_message(line_user_id, TextSendMessage(text=message))
```

---

## ② app.py の修正

### 追加するルート

```python
@app.route("/notify-list")
def notify_list():
    """
    今日の通知一覧ページ。
    LINEの通知メッセージ末尾のURLから飛んでくる。

    クエリパラメータ:
        date: 表示する日付（YYYY-MM-DD形式）。省略時は今日

    ログインしていない場合はログインページにリダイレクト。
    """

    # ---- ログインチェック ----
    # セッションからLINEユーザーIDを取得（ログインしていなければリダイレクト）
    line_user_id = session.get("line_user_id")
    if not line_user_id:
        return redirect(url_for("login"))

    # ---- 日付パラメータの取得 ----
    from datetime import datetime, timezone, timedelta

    date_str = request.args.get("date")  # クエリパラメータから取得（例: ?date=2026-02-24）

    if date_str:
        # パラメータが指定されている場合はそれを使う
        try:
            target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            # 不正な日付形式の場合は今日にフォールバック
            jst = timezone(timedelta(hours=9))
            target_date = datetime.now(jst).date()
    else:
        # パラメータなしなら今日の日付
        jst = timezone(timedelta(hours=9))
        target_date = datetime.now(jst).date()

    # 表示用の日付文字列（YYYY-MM-DD）
    date_str_display = target_date.strftime("%Y-%m-%d")

    # ---- 該当日に通知したアイテムを取得 ----
    # user_activity_logs テーブルの notification_sent レコードを使って
    # その日に通知したアイテムのIDを取得し、items テーブルと結合する
    #
    # ⚠️ 注意: user_activity_logs を使う方法と、
    #          items の next_notify_at を使う方法の2通りがある。
    #          プロジェクトの実装状況に合わせて選択すること。

    try:
        # 方法A: user_activity_logs から notification_sent を検索（推奨）
        # この日にどのアイテムに通知を送ったかのログが残っている前提
        logs_response = supabase.table("user_activity_logs") \
            .select("item_id") \
            .eq("line_user_id", line_user_id) \
            .eq("action_type", "notification_sent") \
            .gte("created_at", f"{date_str_display}T00:00:00+09:00") \
            .lt("created_at", f"{date_str_display}T23:59:59+09:00") \
            .execute()

        # ログから item_id のリストを作る（重複を除去）
        notified_item_ids = list(set([
            log["item_id"] for log in logs_response.data
            if log.get("item_id")
        ]))

        if notified_item_ids:
            # item_id リストに一致するアイテムを取得
            items_response = supabase.table("items") \
                .select("*, categories(name)") \
                .eq("line_user_id", line_user_id) \
                .in_("id", notified_item_ids) \
                .is_("deleted_at", "null") \
                .execute()
            items = items_response.data
        else:
            items = []

    except Exception as e:
        # エラーが起きた場合は空リストで表示（ページはクラッシュさせない）
        print(f"[notify_list] DBエラー: {e}")
        items = []

    # ---- HTMLテンプレートにデータを渡してレンダリング ----
    return render_template(
        "notify_list.html",
        items=items,
        date_str=date_str_display,
        item_count=len(items)
    )
```

---

## ③ templates/notify_list.html の新規作成

既存の `index.html` のタイルカード表示を流用して作る。
`base.html` を継承する（`{% extends "base.html" %}` を使う）。

```html
{% extends "base.html" %}

{% block title %}通知一覧 - {{ date_str }} - Re:find{% endblock %}

{% block content %}
<div class="container py-4">

    <!-- ===== ページヘッダー ===== -->
    <div class="d-flex align-items-center mb-3">
        <!-- 戻るボタン（一覧ページに戻る） -->
        <a href="/" class="btn btn-outline-secondary btn-sm me-3">← 戻る</a>

        <div>
            <h2 class="mb-0" style="font-size: 1.2rem;">📬 通知一覧</h2>
            <!-- 通知日付と件数を表示 -->
            <small class="text-muted">{{ date_str }} ／ {{ item_count }}件</small>
        </div>
    </div>

    <!-- ===== アイテムがない場合のメッセージ ===== -->
    {% if item_count == 0 %}
    <div class="text-center text-muted py-5">
        <p>この日の通知はありません</p>
        <a href="/" class="btn btn-primary">一覧に戻る</a>
    </div>

    {% else %}
    <!-- ===== タイルグリッド（index.html と同じスタイルを流用） ===== -->
    <!-- Bootstrap の grid を使って2〜4列のタイル表示 -->
    <div class="row row-cols-2 row-cols-sm-3 row-cols-lg-4 g-3">

        {% for item in items %}
        <div class="col">
            <!-- アイテムカード -->
            <!-- 共有リンクがあればそこに飛ぶ、なければ一覧ページ -->
            <a href="{{ item.share_url if item.share_url else '/' }}"
               class="text-decoration-none"
               target="_blank">

                <div class="card h-100 item-card
                            {% if item.status == 'done' %}opacity-50{% endif %}">

                    <!-- サムネイル画像（画像がある場合のみ表示） -->
                    {% if item.image_url %}
                    <img src="{{ item.image_url }}"
                         class="card-img-top"
                         style="height: 120px; object-fit: cover;"
                         alt="サムネイル">
                    {% elif item.ogp_image %}
                    <img src="{{ item.ogp_image }}"
                         class="card-img-top"
                         style="height: 120px; object-fit: cover;"
                         alt="OGP画像">
                    {% endif %}

                    <div class="card-body p-2">
                        <!-- カテゴリ名バッジ -->
                        <span class="badge bg-secondary mb-1" style="font-size: 0.65rem;">
                            {{ item.categories.name if item.categories else "未分類" }}
                        </span>

                        <!-- タイトル -->
                        <p class="card-text mb-0"
                           style="font-size: 0.8rem; line-height: 1.3;
                                  overflow: hidden; display: -webkit-box;
                                  -webkit-line-clamp: 3; -webkit-box-orient: vertical;">
                            {{ item.title or "タイトルなし" }}
                        </p>
                    </div>

                    <!-- ステータスバッジ（対応済みなら表示） -->
                    {% if item.status == 'done' %}
                    <div class="card-footer p-1 text-center">
                        <small class="text-muted">✅ 対応済み</small>
                    </div>
                    {% endif %}

                </div>
            </a>
        </div>
        {% endfor %}

    </div><!-- /.row -->
    {% endif %}

</div><!-- /.container -->
{% endblock %}
```

---

## 環境変数の追加

`.env` と Render のダッシュボードに以下を追加する。

```
APP_BASE_URL=https://re-find.onrender.com
```

ローカル開発時は：
```
APP_BASE_URL=http://localhost:5000
```

---

---

## ④ index.html の修正（カテゴリタブ横にボタン追加）

### ボタン色の選定理由

既存の `common.css` で定義されているカラーパレットは以下の通り：

```
--color-primary: #4A90D9   → フィルタータブのアクティブ色（青）
--color-secondary:          → フィルタータブの非アクティブ色（グレー）
--color-success: #06C755   → LINE緑 / 成功
--color-danger:  #DC3545   → 削除・エラー
--color-warning: #FFC107   → 注意
```

**「📬 今日」ボタンには `btn-outline-success`（LINE緑）を採用する。**

理由：
- フィルタータブ（青・グレー）と明確に色が異なり、「フィルターじゃない別の機能」と視覚的に区別できる
- `--color-success` はコメントに「LINE緑」と書かれており、**LINEからの通知**というコンセプトと意味的に一致する
- `btn-outline-danger`（赤）や `btn-outline-warning`（黄）は警告・エラーの印象を与えるため不適

---

### 変更箇所（index.html のカテゴリフィルタ部分）

```html
<!-- ===== カテゴリフィルタ + 今日の通知一覧ボタン ===== -->
<!--
    d-flex: 横並びにする
    align-items-center: 縦方向に中央揃え
-->
<div class="d-flex align-items-center mb-3">

    <!-- 左側：カテゴリフィルタ（横スクロール可能なタブ群） -->
    <!--
        flex-grow-1: 残りの横幅をすべてこちらが占める
        overflow-auto: タブが多いときは横スクロールできるようにする
        flex-nowrap: タブが折り返さないようにする
        pb-2: スクロールバー分の下余白
    -->
    <div class="category-tabs d-flex gap-2 overflow-auto flex-nowrap pb-2 flex-grow-1">
        <button class="btn btn-sm btn-primary rounded-pill category-tab active"
                data-category="all">全て</button>
        {% for category in categories %}
        <button class="btn btn-sm btn-outline-secondary rounded-pill category-tab"
                data-category="{{ category.id }}">
            {{ category.name }}
        </button>
        {% endfor %}
    </div>

    <!-- 右側：今日の通知一覧ボタン -->
    <!--
        border-start: 左に区切り線を入れて、フィルタータブと視覚的に分離する
        ms-2 ps-2: 区切り線の左右に少し余白
        flex-shrink-0: 横幅が狭くなってもこのボタンは縮まず常に表示される
        pb-2: 左側タブの pb-2 に高さを揃える
    -->
    <div class="border-start ms-2 ps-2 flex-shrink-0 pb-2">
        <a href="/notify-list"
           class="btn btn-sm btn-outline-success rounded-pill"
           title="今日の通知一覧">
            📬 今日
        </a>
    </div>

</div>
```

### 完成イメージ

```
┌──────────────────────────────────────────────────┐
│ [全て] [習い事] [記事] [返信] ・・・  │ [📬 今日] │
│  ←─── 青・グレーのタブ ─────────── ↑  ← 緑ボタン │
│                                  区切り線          │
└──────────────────────────────────────────────────┘
```

タブが多くて横スクロールになっても、「📬 今日」ボタンは右端に固定で常に見える。

---

## 動作確認チェックリスト

- [ ] `.env` に `APP_BASE_URL` を追加した
- [ ] `notify.py` に `NOTIFY_DETAIL_LIMIT = 5` 定数を追加した
- [ ] `notify.py` に `build_notify_message()` 関数を追加した
- [ ] `notify.py` の既存の送信ループを `build_notify_message()` を呼ぶ形に書き換えた
- [ ] `app.py` に `/notify-list` ルートを追加した
- [ ] `templates/notify_list.html` を新規作成した
- [ ] `index.html` のカテゴリタブ行に「📬 今日」ボタンを追加した
- [ ] スマホ幅でタブが横スクロールしても「📬 今日」ボタンが右端に固定で表示されることを確認した
- [ ] ローカルでnotify.pyを手動実行し、LINEに届くメッセージを確認した
- [ ] 5件以下の時：詳細テキスト＋一覧URLが届くことを確認
- [ ] 6件以上の時：目次形式＋一覧URLが届くことを確認
- [ ] 一覧URLをブラウザで開いてタイル表示されることを確認
- [ ] ログインしていない状態でアクセスしたらログインページにリダイレクトされることを確認

---

## 注意事項・前提確認

実装前に、現在の `notify.py` の以下を確認すること：

1. **Supabaseクライアントの変数名** — `supabase` という名前で使っているか
2. **LINEへの送信方法** — `line_bot_api.push_message()` を使っているか、別の方法か
3. **アイテムの取得方法** — ユーザーごとのループがどのように書かれているか
4. **`user_activity_logs` への記録** — `notification_sent` のログが現在記録されているか
   → 記録されていない場合、`/notify-list` のデータ取得を「itemsの `next_notify_at` が今日」という条件に変更する必要がある

---

## 実装の優先順位（時間がない場合）

| 優先度 | 内容 | 工数 |
|-------|------|-----|
| ★★★ 最優先 | notify.py に一覧URLを末尾追加するだけ | 10分 |
| ★★★ 最優先 | notify.py に件数分岐ロジック追加 | 30分 |
| ★★☆ 次に | `/notify-list` ページ作成 | 2〜3時間 |
