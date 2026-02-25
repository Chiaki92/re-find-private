/* ==========================================================
   Re:find — index.js
   一覧画面のJavaScript

   ■ このファイルの役割：
     1. カテゴリタブのフィルタリング処理
     2. キーワード検索のフィルタリング処理
     3. ソート（並び替え）処理
     4. セクション分け（pending → archived → done）
     5. 選択モード・一括操作
     6. カードクリック → モーダルを開く（modal.js の関数を呼ぶ）

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
    var currentCategory = 'all';
    var currentSearchQuery = '';

    // セクションの折りたたみ状態（初期: 折りたたみ）
    var sectionCollapsed = { archived: true, done: true };


    /* ----------------------------------------------------------
       1. カテゴリタブのクリック処理
       ---------------------------------------------------------- */

    tabs.forEach(function(tab) {
        tab.addEventListener('click', function() {
            tabs.forEach(function(t) { t.classList.remove('active'); });
            this.classList.add('active');
            currentCategory = this.getAttribute('data-category');
            applyFiltersAndSort();
        });
    });


    /* ----------------------------------------------------------
       2. 検索ボックスの入力処理
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
       ---------------------------------------------------------- */

    function applyFiltersAndSort() {

        // --- Step A: フィルタリング ---
        cards.forEach(function(card) {
            var cardCategory = card.getAttribute('data-category-id');
            var cardTitle = (card.getAttribute('data-title') || '').toLowerCase();

            var matchesCategory =
                currentCategory === 'all' || cardCategory === currentCategory;
            var matchesSearch =
                currentSearchQuery === '' || cardTitle.indexOf(currentSearchQuery) !== -1;

            // フィルタの結果を data 属性にも記録（セクション分けで使う）
            if (matchesCategory && matchesSearch) {
                card.style.display = '';
                card.removeAttribute('data-filtered-out');
            } else {
                card.style.display = 'none';
                card.setAttribute('data-filtered-out', 'true');
            }
            // セクション非表示フラグをリセット
            card.removeAttribute('data-section-hidden');
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
                    return compareDates(b, a);
                case 'title':
                    var titleA = a.getAttribute('data-title') || '';
                    var titleB = b.getAttribute('data-title') || '';
                    return titleA.localeCompare(titleB, 'ja');
                case 'notify':
                    var notifyA = a.getAttribute('data-next-notify-at') || '';
                    var notifyB = b.getAttribute('data-next-notify-at') || '';
                    if (!notifyA && !notifyB) return compareDates(b, a);
                    if (!notifyA) return 1;
                    if (!notifyB) return -1;
                    if (notifyA < notifyB) return -1;
                    if (notifyA > notifyB) return 1;
                    return compareDates(b, a);
                default:
                    return 0;
            }
        });

        // ソート順でDOMに再配置
        cardArray.forEach(function(card) {
            itemGrid.appendChild(card);
        });

        // --- Step C: セクション分けを挿入 ---
        insertSectionDividers();

        // --- Step D: 空の状態を更新 ---
        updateEmptyState();
    }


    function compareDates(a, b) {
        var dateA = a.getAttribute('data-created-at') || '';
        var dateB = b.getAttribute('data-created-at') || '';
        if (dateA < dateB) return -1;
        if (dateA > dateB) return 1;
        return 0;
    }


    /* ----------------------------------------------------------
       4.5. セクション分け表示
       ---------------------------------------------------------- */

    function insertSectionDividers() {
        // 既存のセクションヘッダーを削除
        itemGrid.querySelectorAll('.section-divider').forEach(function(el) { el.remove(); });

        // フィルタ済み（表示対象）のカードを、現在のDOM順序で取得
        // ※ cards (静的NodeList) ではなく itemGrid から取得することで、ソート順を維持する
        var visibleCards = Array.from(itemGrid.querySelectorAll('.item-card')).filter(function(c) {
            return !c.hasAttribute('data-filtered-out');
        });

        // ステータスごとにグルーピング（ソート順を維持）
        var pendingCards = visibleCards.filter(function(c) { return c.getAttribute('data-status') === 'pending'; });
        var archivedCards = visibleCards.filter(function(c) { return c.getAttribute('data-status') === 'archived'; });
        var doneCards = visibleCards.filter(function(c) { return c.getAttribute('data-status') === 'done'; });

        // DOM再配置: pending → archivedヘッダー → archived → doneヘッダー → done
        pendingCards.forEach(function(card) { itemGrid.appendChild(card); });

        var archivedDivider = createSectionDivider('archived', '通知停止', archivedCards.length);
        itemGrid.appendChild(archivedDivider);

        archivedCards.forEach(function(card) { itemGrid.appendChild(card); });

        var doneDivider = createSectionDivider('done', '対応済み', doneCards.length);
        itemGrid.appendChild(doneDivider);

        doneCards.forEach(function(card) { itemGrid.appendChild(card); });

        // 検索中は全セクション強制展開、それ以外は折りたたみ状態を適用
        var isSearching = currentSearchQuery !== '';
        applySectionCollapse('archived', archivedCards, isSearching ? false : sectionCollapsed.archived);
        applySectionCollapse('done', doneCards, isSearching ? false : sectionCollapsed.done);
    }


    function createSectionDivider(sectionId, label, count) {
        var div = document.createElement('div');
        div.className = 'section-divider';
        div.setAttribute('data-section', sectionId);

        var isCollapsed = currentSearchQuery !== '' ? false : sectionCollapsed[sectionId];
        var iconChar = isCollapsed ? '▶' : '▼';

        div.innerHTML = '<button class="section-toggle" data-target="' + sectionId + '">' +
            '<span class="section-toggle-icon">' + iconChar + '</span> ' +
            label + ' <span class="section-count">(' + count + ')</span>' +
            '</button>';

        div.querySelector('.section-toggle').addEventListener('click', function() {
            toggleSection(sectionId);
        });

        return div;
    }


    function toggleSection(sectionId) {
        sectionCollapsed[sectionId] = !sectionCollapsed[sectionId];

        var sectionCards = Array.from(cards).filter(function(c) {
            return c.getAttribute('data-status') === sectionId && !c.hasAttribute('data-filtered-out');
        });

        applySectionCollapse(sectionId, sectionCards, sectionCollapsed[sectionId]);
    }


    function applySectionCollapse(sectionId, sectionCards, collapsed) {
        var divider = itemGrid.querySelector('.section-divider[data-section="' + sectionId + '"]');
        if (!divider) return;

        var icon = divider.querySelector('.section-toggle-icon');
        icon.textContent = collapsed ? '▶' : '▼';

        sectionCards.forEach(function(card) {
            if (collapsed) {
                card.style.display = 'none';
                card.setAttribute('data-section-hidden', 'true');
            } else {
                card.style.display = '';
                card.removeAttribute('data-section-hidden');
            }
        });
    }


    /* ----------------------------------------------------------
       5. カードクリック → モーダル or 選択トグル
       ---------------------------------------------------------- */

    cards.forEach(function(card) {
        card.addEventListener('click', function() {
            if (isSelectMode) {
                // 選択モード: 選択/解除をトグル
                var itemId = this.getAttribute('data-item-id');
                if (selectedItems.has(itemId)) {
                    selectedItems.delete(itemId);
                    this.classList.remove('selected');
                } else {
                    selectedItems.add(itemId);
                    this.classList.add('selected');
                }
                updateBulkCount();
                return;
            }

            // 通常モード: モーダルを開く
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

    function updateEmptyState() {
        var emptyState = document.querySelector('.empty-state');
        if (!emptyState) return;

        var visibleCount = 0;
        cards.forEach(function(card) {
            // フィルタで非表示 → カウントしない
            // セクション折りたたみで非表示 → カウントする（存在はしている）
            if (!card.hasAttribute('data-filtered-out')) {
                visibleCount++;
            }
        });

        emptyState.style.display = visibleCount === 0 ? '' : 'none';
    }


    /* ----------------------------------------------------------
       7. 選択モード・一括操作
       ---------------------------------------------------------- */

    var isSelectMode = false;
    var selectedItems = new Set();
    var selectModeBtn = document.getElementById('select-mode-btn');
    var bulkBar = document.getElementById('bulk-bar');
    var bulkCount = document.getElementById('bulk-count');

    // 選択モードの切り替え
    if (selectModeBtn) {
        selectModeBtn.addEventListener('click', function() {
            isSelectMode = !isSelectMode;
            document.body.classList.toggle('select-mode', isSelectMode);
            selectModeBtn.classList.toggle('active', isSelectMode);
            bulkBar.style.display = isSelectMode ? 'flex' : 'none';

            if (!isSelectMode) {
                selectedItems.clear();
                cards.forEach(function(card) { card.classList.remove('selected'); });
                updateBulkCount();
            }
        });
    }

    function exitSelectMode() {
        isSelectMode = false;
        document.body.classList.remove('select-mode');
        if (selectModeBtn) selectModeBtn.classList.remove('active');
        if (bulkBar) bulkBar.style.display = 'none';
        selectedItems.clear();
        cards.forEach(function(card) { card.classList.remove('selected'); });
        updateBulkCount();
    }

    function updateBulkCount() {
        if (bulkCount) bulkCount.textContent = selectedItems.size;
    }

    // キャンセルボタン
    var bulkCancelBtn = document.getElementById('bulk-cancel-btn');
    if (bulkCancelBtn) {
        bulkCancelBtn.addEventListener('click', exitSelectMode);
    }

    // 全選択ボタン
    var bulkSelectAllBtn = document.getElementById('bulk-select-all-btn');
    if (bulkSelectAllBtn) {
        bulkSelectAllBtn.addEventListener('click', function() {
            // 表示中のカード（フィルタOK & セクション非表示でない）を取得
            var visibleCards = Array.from(cards).filter(function(c) {
                return !c.hasAttribute('data-filtered-out') && !c.hasAttribute('data-section-hidden');
            });

            // 全部選択済みなら全解除、そうでなければ全選択
            var allSelected = visibleCards.every(function(c) {
                return selectedItems.has(c.getAttribute('data-item-id'));
            });

            if (allSelected) {
                visibleCards.forEach(function(c) {
                    var id = c.getAttribute('data-item-id');
                    selectedItems.delete(id);
                    c.classList.remove('selected');
                });
            } else {
                visibleCards.forEach(function(c) {
                    var id = c.getAttribute('data-item-id');
                    selectedItems.add(id);
                    c.classList.add('selected');
                });
            }
            updateBulkCount();
        });
    }

    // 一括削除
    var bulkDeleteBtn = document.getElementById('bulk-delete-btn');
    if (bulkDeleteBtn) {
        bulkDeleteBtn.addEventListener('click', async function() {
            if (selectedItems.size === 0) return;
            if (!confirm(selectedItems.size + '件のアイテムを削除しますか？')) return;

            var result = await apiPost('/api/items/bulk-action', {
                item_ids: Array.from(selectedItems),
                action: 'delete'
            });
            if (result) {
                showToast(selectedItems.size + '件を削除しました');
                window.location.reload();
            }
        });
    }

    // 一括通知停止
    var bulkArchiveBtn = document.getElementById('bulk-archive-btn');
    if (bulkArchiveBtn) {
        bulkArchiveBtn.addEventListener('click', async function() {
            if (selectedItems.size === 0) return;

            var result = await apiPost('/api/items/bulk-action', {
                item_ids: Array.from(selectedItems),
                action: 'archive'
            });
            if (result) {
                showToast(selectedItems.size + '件の通知を停止しました');
                window.location.reload();
            }
        });
    }

    // 一括対応済み
    var bulkDoneBtn = document.getElementById('bulk-done-btn');
    if (bulkDoneBtn) {
        bulkDoneBtn.addEventListener('click', async function() {
            if (selectedItems.size === 0) return;

            var result = await apiPost('/api/items/bulk-action', {
                item_ids: Array.from(selectedItems),
                action: 'done'
            });
            if (result) {
                showToast(selectedItems.size + '件を対応済みにしました');
                window.location.reload();
            }
        });
    }


    /* ----------------------------------------------------------
       8. カテゴリタブの横スクロール補助（PC向け）
       ---------------------------------------------------------- */

    var categoryTabs = document.querySelector('.category-tabs');

    if (categoryTabs) {
        categoryTabs.addEventListener('wheel', function(e) {
            if (Math.abs(e.deltaY) > 0) {
                e.preventDefault();
                categoryTabs.scrollLeft += e.deltaY;
            }
        }, { passive: false });
    }

    var scrollLeftBtn = document.querySelector('.tab-scroll-left');
    var scrollRightBtn = document.querySelector('.tab-scroll-right');
    var scrollAmount = 120;

    if (scrollLeftBtn) {
        scrollLeftBtn.addEventListener('click', function() {
            categoryTabs.scrollBy({ left: -scrollAmount, behavior: 'smooth' });
        });
    }
    if (scrollRightBtn) {
        scrollRightBtn.addEventListener('click', function() {
            categoryTabs.scrollBy({ left: scrollAmount, behavior: 'smooth' });
        });
    }


    /* ----------------------------------------------------------
       9. URLハッシュによるカテゴリ自動選択
       ---------------------------------------------------------- */

    var hash = decodeURIComponent(location.hash);
    if (hash.startsWith('#cat-')) {
        var catName = hash.substring(5);
        var targetTab = document.querySelector('[data-category="' + catName + '"]');
        if (targetTab) {
            targetTab.click();
        }
    }

    // 初期表示でセクション分けを適用
    applyFiltersAndSort();
});
