/* ==========================================================
   Re:find — index.js
   一覧画面のJavaScript
   
   ■ このファイルの役割：
     1. カテゴリタブのフィルタリング処理
     2. カードクリック → モーダルを開く（modal.js の関数を呼ぶ）
   
   ■ 前提：
     - common.js が先に読み込まれていること
     - modal.js が後に読み込まれること
     - ITEMS_DATA が index.html の <script> で定義されていること
   ========================================================== */

document.addEventListener('DOMContentLoaded', function() {

    /* ----------------------------------------------------------
       1. カテゴリフィルタの処理
       
       タブをクリックすると、そのカテゴリのアイテムだけ表示する。
       「すべて」タブを押すと全アイテムを表示する。
       ---------------------------------------------------------- */

    // すべてのタブボタンを取得
    const tabs = document.querySelectorAll('.category-tab');
    
    // すべてのカードを取得
    const cards = document.querySelectorAll('.item-card');

    // 各タブにクリックイベントを設定
    tabs.forEach(function(tab) {
        tab.addEventListener('click', function() {

            // --- アクティブタブの切り替え ---
            // まず全タブから active を外す
            tabs.forEach(function(t) {
                t.classList.remove('active');
            });
            // クリックされたタブに active を付ける
            this.classList.add('active');

            // --- カードのフィルタリング ---
            // data-category 属性からカテゴリIDを取得
            const selectedCategory = this.getAttribute('data-category');

            cards.forEach(function(card) {
                // カードの data-category-id を取得
                const cardCategory = card.getAttribute('data-category-id');

                if (selectedCategory === 'all') {
                    // 「すべて」が選ばれた → 全カード表示
                    card.style.display = '';
                } else if (cardCategory === selectedCategory) {
                    // カテゴリが一致 → 表示
                    card.style.display = '';
                } else {
                    // カテゴリが不一致 → 非表示
                    card.style.display = 'none';
                }
            });

            // --- 空の状態の表示切り替え ---
            // フィルタ後に表示されているカードが0枚なら「空の状態」を表示
            updateEmptyState();
        });
    });


    /* ----------------------------------------------------------
       2. カードクリック → モーダルを開く
       
       各カードをクリックすると、そのアイテムの詳細を
       編集モーダルに表示する。
       実際のモーダル開閉処理は modal.js の openModal() で行う。
       ---------------------------------------------------------- */

    cards.forEach(function(card) {
        card.addEventListener('click', function() {
            // カードの data-item-id からアイテムIDを取得
            const itemId = this.getAttribute('data-item-id');

            // ITEMS_DATA（Flask から渡されたJSON）からアイテム情報を探す
            const item = ITEMS_DATA.find(function(i) {
                return String(i.id) === String(itemId);
            });

            if (item) {
                // modal.js の openModal() を呼ぶ
                // （modal.js がこの後に読み込まれるので、関数は存在する）
                openModal(item);
            }
        });
    });


    /* ----------------------------------------------------------
       3. ヘルパー関数
       ---------------------------------------------------------- */

    /**
     * フィルタ後に表示カードが0枚かチェックして、
     * 空の状態メッセージの表示/非表示を切り替える
     */
    function updateEmptyState() {
        const emptyState = document.querySelector('.empty-state');
        if (!emptyState) return;  // 空の状態がHTML上にない場合はスキップ

        // 表示されている（display: none でない）カードを数える
        let visibleCount = 0;
        cards.forEach(function(card) {
            if (card.style.display !== 'none') {
                visibleCount++;
            }
        });

        // 0枚なら空の状態を表示、1枚以上なら非表示
        emptyState.style.display = visibleCount === 0 ? '' : 'none';
    }
});