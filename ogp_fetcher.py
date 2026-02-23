# ==============================================================
# ogp_fetcher.py
# ==============================================================
# 役割：URLからOGP情報（タイトル・説明・サムネイル画像）を取得する
#
# OGP（Open Graph Protocol）とは？
#   Webページに埋め込まれた「そのページの要約情報」のこと。
#   LINEやXでURLを貼ったときに表示されるプレビューの元データ。
#   HTMLの<head>内に以下のようなmetaタグとして記述される：
#     <meta property="og:title" content="ページのタイトル">
#     <meta property="og:description" content="ページの説明">
#     <meta property="og:image" content="サムネイル画像のURL">
#
# 使い方：
#   from ogp_fetcher import fetch_ogp
#   result = fetch_ogp("https://example.com/article")
#   print(result)
#   # → {"title": "記事タイトル", "description": "記事の説明", "image": "https://..."}
#
# 呼び出し元：
#   app.py の URL受信ハンドラ
# ==============================================================

import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse


def fetch_ogp(url):
    """
    URLからOGP情報（タイトル・説明・画像URL）を取得する。

    処理の流れ：
      1. XのURLだった場合は fxtwitter.com に差し替える
      2. URLにHTTPリクエストを送る
      3. 返ってきたHTMLをBeautifulSoupで解析する
      4. og:title, og:description, og:image のmetaタグを探す
      5. 見つかった情報を辞書で返す

    取得できなかった場合のフォールバック（代替処理）：
      - OGPタグがない → HTMLの<title>タグから取得を試みる
      - <title>もない → URLそのものをタイトルにする
      - リクエスト自体が失敗 → URLのドメイン名をタイトルにする

    引数:
        url (str): OGP情報を取得したいWebページのURL
                   例: "https://news.yahoo.co.jp/articles/xxxxx"

    戻り値:
        dict: 以下のキーを持つ辞書
            - "title" (str): ページのタイトル（必ず何かの値が入る）
            - "description" (str): ページの説明文（取得できない場合は空文字）
            - "image" (str or None): サムネイル画像のURL（取得できない場合はNone）
    """
    try:
        # -------------------------------------------------------
        # Step 1: XのURLは fxtwitter.com に差し替える
        # -------------------------------------------------------
        # XはBotからのOGP取得をブロックしているため、そのままアクセスすると
        # タイムアウトしてしまう。
        # fxtwitter.com はXの投稿内容をOGPとして返してくれる無料のプロキシサービス。
        # ドメインを差し替えるだけでURL構造はそのまま使えるため実装コストが低い。
        #
        # 例:
        #   https://x.com/user/status/123
        #   → https://fxtwitter.com/user/status/123
        #
        # 注意: fxtwitter.com はサードパーティのサービスのため、
        #       サービス停止時は取得できなくなるリスクがある。
        if "x.com" in url or "twitter.com" in url:
            url = url.replace("twitter.com", "fxtwitter.com") \
                     .replace("x.com", "fxtwitter.com")

        # -------------------------------------------------------
        # Step 2: URLにHTTPリクエストを送る
        # -------------------------------------------------------
        # fxtwitter.com はUser-Agentを見て動作を切り替える。
        # ブラウザのUser-AgentだとXに転送してしまうため、
        # XのURLの場合はDiscordボットのUser-Agentを使う。
        # それ以外の通常URLはブラウザのUser-Agentを使う。
        if "fxtwitter.com" in url:
            # Discordのボット用User-Agent（fxtwitter がOGPを返す条件）
            user_agent = "Mozilla/5.0 (compatible; Discordbot/2.0; +https://discordapp.com)"
        else:
            # 通常サイト用（ブラウザに見せかける）
            user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"

        response = requests.get(
            url,
            timeout=10,
            headers={"User-Agent": user_agent}
        )

        # -------------------------------------------------------
        # Step 3: HTMLをBeautifulSoupで解析する
        # -------------------------------------------------------
        # "html.parser" : Python標準のHTMLパーサー（追加インストール不要）
        soup = BeautifulSoup(response.text, "html.parser")

        # -------------------------------------------------------
        # Step 4: OGPのmetaタグを探す
        # -------------------------------------------------------
        # soup.find("meta", property="og:title") は以下のようなタグを探す：
        #   <meta property="og:title" content="ページのタイトル">
        #
        # 見つかった場合 → タグオブジェクトが返る → ["content"]で中身を取得
        # 見つからなかった場合 → None が返る
        og_title = soup.find("meta", property="og:title")
        og_desc  = soup.find("meta", property="og:description")
        og_image = soup.find("meta", property="og:image")

        # OGPタグが見つかった場合は content 属性の値を取得、なければ None
        title       = og_title["content"] if og_title else None
        description = og_desc["content"]  if og_desc  else None
        image       = og_image["content"] if og_image else None

        # -------------------------------------------------------
        # Step 5: フォールバック処理（OGPタイトルがない場合）
        # -------------------------------------------------------
        if not title:
            # OGPタイトルがない → HTMLの<title>タグを探す
            # 例: <title>Yahoo!ニュース - 国内最大級のニュースサイト</title>
            title_tag = soup.find("title")
            title = title_tag.string if title_tag else url
            # title_tag.string : <title>タグの中のテキストを取得
            # それもなければ URL そのものをタイトルにする

        # -------------------------------------------------------
        # Step 6: 結果を辞書で返す
        # -------------------------------------------------------
        return {
            "title":       title or url,          # Noneや空文字の場合はURLを使う
            "description": description or "",     # Noneの場合は空文字にする
            "image":       image                  # 画像URLはNoneのままでもOK
        }

    except Exception as e:
        # -------------------------------------------------------
        # エラー時のフォールバック処理
        # -------------------------------------------------------
        # どんなエラーでもアプリが落ちないようにキャッチする
        # - requests.exceptions.Timeout        : タイムアウト
        # - requests.exceptions.ConnectionError: 接続エラー
        # - requests.exceptions.HTTPError      : 404, 500等
        # - その他の予期しないエラー
        print(f"OGP取得エラー ({url}): {e}")

        # URLからドメイン名を抽出してタイトルの代わりにする
        # 例: "https://news.yahoo.co.jp/articles/xxx" → "news.yahoo.co.jp"
        domain = urlparse(url).netloc

        return {
            "title":       domain or url,  # ドメイン名が取れなければURLそのもの
            "description": "",
            "image":       None
        }


# ==============================================================
# 単体テスト用（このファイルを直接実行したときだけ動く）
# ==============================================================
# 実行方法:
#   python ogp_fetcher.py
if __name__ == "__main__":
    test_urls = [
        # XのURL（fxtwitter.comへの差し替えが動くか確認）
        "https://x.com/ai_hakase_/status/2025918986802651411?s=53",
        # 普通のURL（従来通り動くか確認）
        "https://qiita.com",
    ]

    for url in test_urls:
        print(f"\n--- テスト: {url} ---")
        result = fetch_ogp(url)
        print(f"title      : {result['title']}")
        print(f"description: {result['description']}")
        print(f"image      : {result['image']}")