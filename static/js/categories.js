/* ==========================================================
   Re:find — categories.js
   カテゴリ管理画面の JavaScript

   ■ このファイルの役割：
     1. 新規カテゴリの追加
     2. カテゴリ名のインライン編集（フォーカスが外れたら自動保存）
     3. カテゴリの削除（確認ダイアログ付き）
     4. カテゴリの並び替え（上下ボタン・一括ソート）

   ■ 前提：
     - common.js が先に読み込まれていること（apiPost, apiPut, apiDelete, showToast）
   ========================================================== */

document.addEventListener('DOMContentLoaded', function() {

    /* ----------------------------------------------------------
       1. 新規カテゴリの追加

       「+ 追加」ボタンを押すと、入力欄のテキストを
       新しいカテゴリとして Flask API に送信する。
       ---------------------------------------------------------- */

    const addBtn = document.getElementById('add-category-btn');
    const addInput = document.getElementById('new-category-input');

    addBtn.addEventListener('click', async function() {
        // 入力値を取得（前後の空白を除去）
        const name = addInput.value.trim();

        // 空欄チェック
        if (!name) {
            showToast('カテゴリ名を入力してください', 'error');
            return;
        }

        // Flask API にPOSTリクエスト
        const result = await apiPost('/api/categories', { name: name });

        if (result) {
            showToast(`「${name}」を追加しました`);
            // ページをリロードして最新状態を表示
            window.location.reload();
        }
    });

    // Enterキーでも追加できるようにする
    addInput.addEventListener('keydown', function(e) {
        if (e.key === 'Enter') {
            addBtn.click();
        }
    });


    /* ----------------------------------------------------------
       2. カテゴリ名のインライン編集

       カテゴリ名の input からフォーカスが外れたとき、
       元の名前と変わっていれば自動的に保存する。
       ---------------------------------------------------------- */

    // すべてのカテゴリ名 input を取得
    const nameInputs = document.querySelectorAll('.category-name-input');

    nameInputs.forEach(function(input) {
        // フォーカスが外れたとき（blur イベント）
        input.addEventListener('blur', async function() {
            const newName = this.value.trim();
            const originalName = this.getAttribute('data-original-name');

            // 名前が変わっていなければ何もしない
            if (newName === originalName) return;

            // 空欄チェック
            if (!newName) {
                // 空欄にされた場合は元の名前に戻す
                this.value = originalName;
                showToast('カテゴリ名は空にできません', 'error');
                return;
            }

            // カテゴリIDを取得（親要素の data-category-id）
            const categoryItem = this.closest('.category-item');
            const categoryId = categoryItem.getAttribute('data-category-id');

            // Flask API にPUTリクエスト
            const result = await apiPut(`/api/categories/${categoryId}`, { name: newName });

            if (result) {
                // 元の名前を更新（次回の比較用）
                this.setAttribute('data-original-name', newName);
                // data-category-name も更新（あいうえお順ソートで正しい名前を使うため）
                categoryItem.setAttribute('data-category-name', newName);
                showToast('カテゴリ名を変更しました');
            } else {
                // 失敗時は元に戻す
                this.value = originalName;
            }
        });

        // Enterキーでフォーカスを外す（＝保存をトリガー）
        input.addEventListener('keydown', function(e) {
            if (e.key === 'Enter') {
                this.blur();
            }
        });
    });


    /* ----------------------------------------------------------
       3. カテゴリの削除

       ゴミ箱ボタンを押すと確認ダイアログを出して、
       OKならカテゴリを削除する。
       アイテムは「未分類」に移動される（Flask API側で処理）。
       ---------------------------------------------------------- */

    const deleteBtns = document.querySelectorAll('.category-delete-btn');

    deleteBtns.forEach(function(btn) {
        btn.addEventListener('click', async function() {
            // 親要素からカテゴリIDと名前を取得
            const categoryItem = this.closest('.category-item');
            const categoryId = categoryItem.getAttribute('data-category-id');
            const categoryName = categoryItem.querySelector('.category-name-input').value;

            // 確認ダイアログ
            const confirmed = confirm(
                `「${categoryName}」を削除しますか？\n` +
                `このカテゴリのアイテムは「未分類」に移動されます。`
            );

            if (!confirmed) return;

            // Flask API にDELETEリクエスト
            const result = await apiDelete(`/api/categories/${categoryId}`);

            if (result) {
                showToast(`「${categoryName}」を削除しました`);
                // 画面からカテゴリ行を削除（リロードなし）
                categoryItem.remove();
                // 削除後に上下ボタンの状態を更新
                updateMoveButtonStates();
            }
        });
    });


    /* ----------------------------------------------------------
       4. AI分類カテゴリの開閉トグル
       ---------------------------------------------------------- */

    const aiToggle = document.getElementById('ai-categories-toggle');
    const aiBody = document.getElementById('ai-categories-body');
    const aiChevron = document.getElementById('ai-categories-chevron');

    if (aiToggle && aiBody && aiChevron) {
        aiToggle.addEventListener('click', function() {
            aiBody.classList.toggle('open');
            aiChevron.classList.toggle('open');
        });
    }


    /* ----------------------------------------------------------
       5. カテゴリの並び替え — 上下ボタン

       各カテゴリ行の ▲▼ ボタンでカテゴリを1つずつ移動する。
       「未分類」は常に一番下に固定され、移動対象にならない。
       ---------------------------------------------------------- */

    // カテゴリ一覧の親要素
    var categoryList = document.getElementById('category-list');

    /**
     * 「未分類」以外の .category-item を配列で返すヘルパー
     * （並び替えの対象となるカテゴリだけを取得する）
     */
    function getMovableItems() {
        var allItems = categoryList.querySelectorAll('.category-item');
        var movable = [];
        allItems.forEach(function(item) {
            // data-category-name が「未分類」でないものだけ対象
            if (item.getAttribute('data-category-name') !== '未分類') {
                movable.push(item);
            }
        });
        return movable;
    }

    /**
     * 指定アイテムの前にある移動可能なカテゴリを返す
     * （「未分類」はスキップする）
     */
    function getPreviousMovableItem(item) {
        var prev = item.previousElementSibling;
        while (prev) {
            // 「未分類」でなければそれが前の移動可能アイテム
            if (prev.classList.contains('category-item') &&
                prev.getAttribute('data-category-name') !== '未分類') {
                return prev;
            }
            prev = prev.previousElementSibling;
        }
        return null;
    }

    /**
     * 指定アイテムの後にある移動可能なカテゴリを返す
     * （「未分類」はスキップする）
     */
    function getNextMovableItem(item) {
        var next = item.nextElementSibling;
        while (next) {
            // 「未分類」でなければそれが次の移動可能アイテム
            if (next.classList.contains('category-item') &&
                next.getAttribute('data-category-name') !== '未分類') {
                return next;
            }
            next = next.nextElementSibling;
        }
        return null;
    }

    /**
     * 上下ボタンの enabled/disabled 状態を更新する
     * - 一番上のカテゴリの「▲」は disabled
     * - 一番下のカテゴリ（未分類の直前）の「▼」は disabled
     */
    function updateMoveButtonStates() {
        var movable = getMovableItems();

        movable.forEach(function(item, index) {
            var upBtn = item.querySelector('.move-up-btn');
            var downBtn = item.querySelector('.move-down-btn');
            if (upBtn) {
                // 最初のアイテムは上に移動できない
                upBtn.disabled = (index === 0);
            }
            if (downBtn) {
                // 最後のアイテムは下に移動できない
                downBtn.disabled = (index === movable.length - 1);
            }
        });
    }

    /**
     * 2つのカテゴリ要素のDOM位置を入れ替える
     * direction: 'up' または 'down'
     */
    function swapItems(item1, item2, direction) {
        // 移動中のハイライトを追加
        item1.classList.add('moving');

        if (direction === 'up') {
            // item1 を item2 の前に移動
            categoryList.insertBefore(item1, item2);
        } else {
            // item1 を item2 の後に移動
            categoryList.insertBefore(item1, item2.nextSibling);
        }

        // ハイライトを一定時間後に消す
        setTimeout(function() {
            item1.classList.remove('moving');
        }, 400);

        // 上下ボタンの状態を再計算
        updateMoveButtonStates();

        // サーバーに並び順を保存
        saveOrder();
    }

    /**
     * 全ての上下移動ボタンにクリックイベントを設定する
     */
    function setupMoveButtons() {
        // ▲ 上に移動ボタン
        var upBtns = document.querySelectorAll('.move-up-btn');
        upBtns.forEach(function(btn) {
            btn.addEventListener('click', function() {
                var item = this.closest('.category-item');
                var prevItem = getPreviousMovableItem(item);
                // 前のアイテムがあれば入れ替え
                if (prevItem) {
                    swapItems(item, prevItem, 'up');
                }
            });
        });

        // ▼ 下に移動ボタン
        var downBtns = document.querySelectorAll('.move-down-btn');
        downBtns.forEach(function(btn) {
            btn.addEventListener('click', function() {
                var item = this.closest('.category-item');
                var nextItem = getNextMovableItem(item);
                // 次のアイテムがあれば入れ替え
                if (nextItem) {
                    swapItems(item, nextItem, 'down');
                }
            });
        });
    }

    // 上下ボタンを初期化
    setupMoveButtons();
    // 初期状態で一番上/一番下のボタンを disabled に
    updateMoveButtonStates();


    /* ----------------------------------------------------------
       6. カテゴリの並び替え — 一括ソート

       「アイテム数順」「あいうえお順」「作成日順」ボタンで
       全カテゴリを一括で並べ替える。
       「未分類」は常に一番下に固定される。
       ---------------------------------------------------------- */

    /**
     * カテゴリを指定の比較関数でソートし、DOMに再配置する
     * compareFn: 標準の Array.sort() 用の比較関数
     */
    function sortCategories(compareFn) {
        var allItems = Array.from(categoryList.querySelectorAll('.category-item'));

        // 「未分類」を分離する
        var uncategorized = null;
        var sortable = [];

        allItems.forEach(function(item) {
            if (item.getAttribute('data-category-name') === '未分類') {
                uncategorized = item;
            } else {
                sortable.push(item);
            }
        });

        // 比較関数でソート
        sortable.sort(compareFn);

        // DOM に再配置（ソート済みの順番で appendChid）
        sortable.forEach(function(item) {
            categoryList.appendChild(item);
        });
        // 「未分類」は常に最後
        if (uncategorized) {
            categoryList.appendChild(uncategorized);
        }

        // フラッシュアニメーションを追加
        sortable.forEach(function(item) {
            item.classList.add('sorted');
        });
        // アニメーション終了後にクラスを除去
        setTimeout(function() {
            sortable.forEach(function(item) {
                item.classList.remove('sorted');
            });
        }, 500);

        // 上下ボタンの状態を再計算
        updateMoveButtonStates();

        // サーバーに並び順を保存
        saveOrder();
    }

    // --- アイテム数順ボタン（多い順 = 降順） ---
    var sortByCountBtn = document.getElementById('sort-by-count');
    if (sortByCountBtn) {
        sortByCountBtn.addEventListener('click', function() {
            sortCategories(function(a, b) {
                var countA = parseInt(a.getAttribute('data-item-count')) || 0;
                var countB = parseInt(b.getAttribute('data-item-count')) || 0;
                // 降順（多い順）
                return countB - countA;
            });
        });
    }

    // --- あいうえお順ボタン ---
    var sortByNameBtn = document.getElementById('sort-by-name');
    if (sortByNameBtn) {
        sortByNameBtn.addEventListener('click', function() {
            sortCategories(function(a, b) {
                var nameA = a.getAttribute('data-category-name');
                var nameB = b.getAttribute('data-category-name');
                // 日本語のあいうえお順で比較
                return nameA.localeCompare(nameB, 'ja');
            });
        });
    }

    // --- 作成日順ボタン（sort_order の昇順 = 元の作成順） ---
    var sortByCreatedBtn = document.getElementById('sort-by-created');
    if (sortByCreatedBtn) {
        sortByCreatedBtn.addEventListener('click', function() {
            sortCategories(function(a, b) {
                var orderA = parseInt(a.getAttribute('data-sort-order')) || 0;
                var orderB = parseInt(b.getAttribute('data-sort-order')) || 0;
                // 昇順（作成が古い順）
                return orderA - orderB;
            });
        });
    }


    /* ----------------------------------------------------------
       7. サーバーへの並び順保存

       DOM上のカテゴリ順序を読み取り、
       API にPOSTして sort_order を一括更新する。
       ---------------------------------------------------------- */

    /**
     * 現在のDOM順序をサーバーに保存する
     * - 「未分類」は sort_order: 999999 に固定
     * - それ以外は 1, 2, 3... の連番を振る
     */
    function saveOrder() {
        var allItems = categoryList.querySelectorAll('.category-item');
        var orderData = [];
        var sortIndex = 1;

        allItems.forEach(function(item) {
            var categoryId = item.getAttribute('data-category-id');
            var categoryName = item.getAttribute('data-category-name');

            if (categoryName === '未分類') {
                // 「未分類」は 999999 に固定
                orderData.push({ id: categoryId, sort_order: 999999 });
                item.setAttribute('data-sort-order', '999999');
            } else {
                // 通常カテゴリは連番を振る
                orderData.push({ id: categoryId, sort_order: sortIndex });
                item.setAttribute('data-sort-order', String(sortIndex));
                sortIndex++;
            }
        });

        // API にPOSTで送信
        apiPost('/api/categories/reorder', { order: orderData }).then(function(result) {
            if (!result) {
                // 保存失敗時はトーストを表示して1.5秒後にリロード
                showToast('並び替えの保存に失敗しました', 'error');
                setTimeout(function() {
                    window.location.reload();
                }, 1500);
            }
        });
    }

});
