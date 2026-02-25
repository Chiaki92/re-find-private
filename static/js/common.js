/* ==========================================================
   Re:find — common.js
   全ページ共通の JavaScript

   ■ このファイルの役割：
     1. API通信の共通関数（apiGet, apiPost, apiPut, apiDelete）
     2. トースト通知の表示関数（showToast）
     3. ログアウト処理
   
   ■ 使い方（他のJSファイルから呼ぶ）：
     const data = await apiGet('/api/items');
     showToast('保存しました');
   ========================================================== */


/* ----------------------------------------------------------
   1. API通信の共通関数

   Flask の API エンドポイントにリクエストを送る。
   全ページで同じ書き方ができるように、ここにまとめる。
   
   ■ 使い方：
     // GETリクエスト（データ取得）
     const items = await apiGet('/api/items');
   
     // POSTリクエスト（データ作成）
     const result = await apiPost('/api/items', { title: '新しいアイテム' });
   
     // PUTリクエスト（データ更新）
     await apiPut('/api/items/123', { memo: 'メモを更新' });
   
     // DELETEリクエスト（データ削除）
     await apiDelete('/api/items/123');
   ---------------------------------------------------------- */

/**
 * GETリクエストを送る（データを取得する）
 * @param {string} url - APIのURL（例：'/api/items'）
 * @returns {object} レスポンスのJSON
 */
async function apiGet(url) {
    try {
        // fetch でサーバーにGETリクエストを送信
        const response = await fetch(url);

        // ステータスコードが200番台でなければエラー
        if (!response.ok) {
            throw new Error(`API Error: ${response.status}`);
        }

        // JSON形式でレスポンスを返す
        return await response.json();

    } catch (error) {
        // エラーが起きたらコンソールに表示して、トーストで通知
        console.error('apiGet エラー:', error);
        showToast('データの取得に失敗しました', 'error');
        return null;
    }
}

/**
 * POSTリクエストを送る（新しいデータを作成する）
 * @param {string} url - APIのURL
 * @param {object} data - 送信するデータ
 * @returns {object} レスポンスのJSON
 */
async function apiPost(url, data) {
    try {
        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',  // JSON形式で送ることを宣言
            },
            body: JSON.stringify(data),  // JavaScriptオブジェクトをJSON文字列に変換
        });

        if (!response.ok) {
            throw new Error(`API Error: ${response.status}`);
        }

        return await response.json();

    } catch (error) {
        console.error('apiPost エラー:', error);
        showToast('操作に失敗しました', 'error');
        return null;
    }
}

/**
 * PUTリクエストを送る（既存データを更新する）
 * @param {string} url - APIのURL（例：'/api/items/123'）
 * @param {object} data - 更新するデータ
 * @returns {object} レスポンスのJSON
 */
async function apiPut(url, data) {
    try {
        const response = await fetch(url, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data),
        });

        if (!response.ok) {
            throw new Error(`API Error: ${response.status}`);
        }

        return await response.json();

    } catch (error) {
        console.error('apiPut エラー:', error);
        showToast('更新に失敗しました', 'error');
        return null;
    }
}

/**
 * DELETEリクエストを送る（データを削除する）
 * @param {string} url - APIのURL（例：'/api/items/123'）
 * @returns {object} レスポンスのJSON
 */
async function apiDelete(url) {
    try {
        const response = await fetch(url, {
            method: 'DELETE',
        });

        if (!response.ok) {
            throw new Error(`API Error: ${response.status}`);
        }

        return await response.json();

    } catch (error) {
        console.error('apiDelete エラー:', error);
        showToast('削除に失敗しました', 'error');
        return null;
    }
}


/* ----------------------------------------------------------
   2. トースト通知の表示

   画面上部に一時的なメッセージを表示する。
   3秒後に自動で消える。
   
   ■ 使い方：
     showToast('保存しました');           // 通常メッセージ
     showToast('削除に失敗しました', 'error');  // エラーメッセージ
   ---------------------------------------------------------- */

/**
 * トースト通知を表示する
 * @param {string} message - 表示するメッセージ
 * @param {string} type - 'success'（デフォルト）or 'error'
 */
function showToast(message, type = 'success') {
    // トーストを入れるコンテナを取得
    const container = document.getElementById('toast-container');
    if (!container) return;

    // トースト要素を作成
    const toast = document.createElement('div');
    toast.className = 'toast-message';
    toast.textContent = message;

    // エラーの場合は背景を赤くする
    if (type === 'error') {
        toast.style.backgroundColor = '#D94F4F';
    }

    // コンテナに追加して表示
    container.appendChild(toast);

    // 3秒後にトーストを削除
    setTimeout(() => {
        toast.remove();
    }, 3000);
}


/* ----------------------------------------------------------
   3. ログアウト処理

   ヘッダーの「ログアウト」ボタンを押したときの処理。
   Flask の /logout エンドポイントにリダイレクトする。
   ---------------------------------------------------------- */

// ページ読み込み完了後に実行
document.addEventListener('DOMContentLoaded', function() {

    // ----------------------------------------------------------
    // 3-1. ハンバーガーメニューの開閉処理
    // ----------------------------------------------------------

    const hamburgerBtn = document.getElementById('hamburger-btn');
    const hamburgerMenu = document.getElementById('hamburger-menu');
    const hamburgerIcon = document.getElementById('hamburger-icon');

    if (hamburgerBtn && hamburgerMenu && hamburgerIcon) {

        // ヘッダーの実際の高さに合わせてメニュー位置を設定
        const header = document.querySelector('.refind-header');
        const lineAddBtn = document.querySelector('.btn-line-add');

        function closeMenu() {
            hamburgerMenu.style.display = 'none';
            hamburgerIcon.className = 'bi bi-list';
            hamburgerBtn.setAttribute('aria-label', 'メニューを開く');
            if (lineAddBtn) lineAddBtn.classList.remove('btn-line-add-hidden');
        }

        function openMenu() {
            // ヘッダー高さを動的に取得してメニュー位置を合わせる
            if (header) {
                hamburgerMenu.style.top = header.offsetHeight + 'px';
            }
            hamburgerMenu.style.display = 'block';
            hamburgerIcon.className = 'bi bi-x-lg';
            hamburgerBtn.setAttribute('aria-label', 'メニューを閉じる');
            if (lineAddBtn) lineAddBtn.classList.add('btn-line-add-hidden');
        }

        hamburgerBtn.addEventListener('click', function(e) {
            e.stopPropagation();
            const isOpen = hamburgerMenu.style.display !== 'none';
            if (isOpen) {
                closeMenu();
            } else {
                openMenu();
            }
        });

        document.addEventListener('click', function(e) {
            if (!hamburgerMenu.contains(e.target) && !hamburgerBtn.contains(e.target)) {
                closeMenu();
            }
        });
    }

    // ----------------------------------------------------------
    // 3-2. ログアウト処理
    // ----------------------------------------------------------

    const logoutBtn = document.getElementById('logout-btn');

    if (logoutBtn) {
        logoutBtn.addEventListener('click', function() {
            // 確認ダイアログを表示
            if (confirm('ログアウトしますか？')) {
                // Flask のログアウトURLに遷移
                window.location.href = '/logout';
            }
        });
    }
});


/* ----------------------------------------------------------
   4. 相対時間の表示ヘルパー（オプション）
   
   「3日前」「1時間前」のような表示を作る。
   Flask側のJinja2フィルタで処理する場合はこの関数は不要。
   
   ■ 使い方：
     const text = timeAgo('2026-02-20T10:00:00');
     // → "2日前"
   ---------------------------------------------------------- */

/**
 * ISO日時文字列を「〇日前」のような相対表示に変換する
 * @param {string} dateString - ISO 8601 形式の日時文字列
 * @returns {string} 相対時間の文字列
 */
function timeAgo(dateString) {
    const now = new Date();
    const date = new Date(dateString);
    const diffMs = now - date;                    // ミリ秒の差
    const diffMinutes = Math.floor(diffMs / 60000);       // 分
    const diffHours = Math.floor(diffMs / 3600000);       // 時間
    const diffDays = Math.floor(diffMs / 86400000);       // 日

    if (diffMinutes < 1) return 'たった今';
    if (diffMinutes < 60) return `${diffMinutes}分前`;
    if (diffHours < 24) return `${diffHours}時間前`;
    if (diffDays < 30) return `${diffDays}日前`;
    if (diffDays < 365) return `${Math.floor(diffDays / 30)}ヶ月前`;
    return `${Math.floor(diffDays / 365)}年前`;
}