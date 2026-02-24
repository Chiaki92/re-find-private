/* ==========================================================
   Re:find — index.js
   一覧画面のJavaScript

   ■ このファイルの役割：
     1. カテゴリタブのフィルタリング処理
     2. キーワード検索のフィルタリング処理
     3. ソート（並び替え）処理
     4. カードクリック → モーダルを開く（modal.js の関数を呼ぶ）

   ■ 前提：
     - common.js が先に読み込まれていること
     - modal.js が後に読み込まれること
     - ITEMS_DATA が index.html の <script> で定義されていること
   ========================================================== */

document.addEventListener('DOMContentLoaded', function() {

    /* ----------------------------------------------------------
       0. 要素の取得
       ---------------------------------------------------------- */

    var tabs = document.querySelectorAll('.category-tab');
    var cards = document.querySelectorAll('.item-card');
    var itemGrid = document.querySelector('.item-grid');
    var searchInput = document.getElementById('search-input');
    var sortSelect = document.getElementById('sort-select');

    // 現在のフィルタ状態を保持する変数
    var currentCategory = 'all';      // 選択中のカテゴリ（'all' = すべて）
    var currentSearchQuery = '';       // 検索クエリ（小文字化済み）


    /* ----------------------------------------------------------
       1. カテゴリタブのクリック処理
       ---------------------------------------------------------- */

    tabs.forEach(function(tab) {
        tab.addEventListener('click', function() {
            // アクティブタブの切り替え
            tabs.forEach(function(t) {
                t.classList.remove('active');
            });
            this.classList.add('active');

            // 現在のカテゴリを更新
            currentCategory = this.getAttribute('data-category');

            // フィルタ＆ソートを再適用
            applyFiltersAndSort();
        });
    });


    /* ----------------------------------------------------------
       2. 検索ボックスの入力処理

       input イベントで1文字ごとにフィルタする（リアルタイム検索）。
       DOM操作のみでAPIコールなし、カード数も限定的なのでデバウンス不要。
       ---------------------------------------------------------- */

    if (searchInput) {
        searchInput.addEventListener('input', function() {
            currentSearchQuery = this.value.trim().toLowerCase();
            applyFiltersAndSort();
        });
    }


    /* ----------------------------------------------------------
       3. ソートドロップダウンの変更処理
       ---------------------------------------------------------- */

    if (sortSelect) {
        sortSelect.addEventListener('change', function() {
            applyFiltersAndSort();
        });
    }


    /* ----------------------------------------------------------
       4. フィルタ＆ソートの統合処理（中核ロジック）

       カテゴリフィルタ、検索フィルタ、ソートの3つを
       まとめて処理する。どのコントロールが変更されても
       この関数が呼ばれる。
       ---------------------------------------------------------- */

    function applyFiltersAndSort() {

        // --- Step A: フィルタリング ---
        cards.forEach(function(card) {
            var cardCategory = card.getAttribute('data-category-id');
            var cardTitle = (card.getAttribute('data-title') || '').toLowerCase();

            // カテゴリ条件：「すべて」なら常にtrue
            var matchesCategory =
                currentCategory === 'all' || cardCategory === currentCategory;

            // 検索条件：クエリが空なら常にtrue
            var matchesSearch =
                currentSearchQuery === '' || cardTitle.indexOf(currentSearchQuery) !== -1;

            // 両方の条件を満たすカードだけ表示
            card.style.display = (matchesCategory && matchesSearch) ? '' : 'none';
        });

        // --- Step B: ソート ---
        var sortKey = sortSelect ? sortSelect.value : 'newest';
        var cardArray = Array.from(cards);

        cardArray.sort(function(a, b) {
            switch (sortKey) {
                case 'newest':
                    return compareDates(b, a);

                case 'oldest':
                    return compareDates(a, b);

                case 'category':
                    var catA = a.getAttribute('data-category-name') || '';
                    var catB = b.getAttribute('data-category-name') || '';
                    var catCompare = catA.localeCompare(catB, 'ja');
                    if (catCompare !== 0) return catCompare;
                    return compareDates(b, a);  // 同カテゴリ内は新しい順

                case 'title':
                    var titleA = a.getAttribute('data-title') || '';
                    var titleB = b.getAttribute('data-title') || '';
                    return titleA.localeCompare(titleB, 'ja');

                default:
                    return 0;
            }
        });

        // ソート順でDOMに再配置
        cardArray.forEach(function(card) {
            itemGrid.appendChild(card);
        });

        // --- Step C: 空の状態を更新 ---
        updateEmptyState();
    }


    /**
     * 2つのカードのcreated_at日時を比較するヘルパー
     * ISO 8601 文字列は辞書順で比較可能
     */
    function compareDates(a, b) {
        var dateA = a.getAttribute('data-created-at') || '';
        var dateB = b.getAttribute('data-created-at') || '';
        if (dateA < dateB) return -1;
        if (dateA > dateB) return 1;
        return 0;
    }


    /* ----------------------------------------------------------
       5. カードクリック → モーダルを開く
       ---------------------------------------------------------- */

    cards.forEach(function(card) {
        card.addEventListener('click', function() {
            var itemId = this.getAttribute('data-item-id');

            var item = ITEMS_DATA.find(function(i) {
                return String(i.id) === String(itemId);
            });

            if (item) {
                openModal(item);
            }
        });
    });


    /* ----------------------------------------------------------
       6. ヘルパー関数
       ---------------------------------------------------------- */

    /**
     * フィルタ後に表示カードが0枚かチェックして、
     * 空の状態メッセージの表示/非表示を切り替える
     */
    function updateEmptyState() {
        var emptyState = document.querySelector('.empty-state');
        if (!emptyState) return;

        var visibleCount = 0;
        cards.forEach(function(card) {
            if (card.style.display !== 'none') {
                visibleCount++;
            }
        });

        emptyState.style.display = visibleCount === 0 ? '' : 'none';
    }
});
