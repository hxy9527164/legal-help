/* ============================================================ */
/*  法律条文知识库 — 搜索/筛选/AI白话解释                          */
/* ============================================================ */
(function () {
    'use strict';

    var provisionsData = [];
    var currentPage = 1;
    var pageSize = 8;
    var currentFiltered = [];
    var currentCategory = 'all';
    var currentQuery = '';

    // DOM
    var searchInput, filterContainer, provisionGrid, paginationDiv, noResultsDiv;
    var API_KEY = 'sk-wbtzxngfywxeetfscvfqfjzlbdaiptwliceyqgnhmrslvlqd';

    // ============================================================
    //  初始化
    // ============================================================
    function init() {
        searchInput = document.getElementById('legal-search-input');
        filterContainer = document.getElementById('legal-filter-buttons');
        provisionGrid = document.getElementById('provision-grid');
        paginationDiv = document.getElementById('provision-pagination');
        noResultsDiv = document.getElementById('provision-no-results');

        // 加载数据
        if (window.__legalProvisionsData) {
            provisionsData = window.__legalProvisionsData;
        } else {
            provisionGrid.innerHTML = '<p class="no-results">条文数据加载失败，请刷新页面</p>';
            return;
        }

        // 恢复用户API Key
        try {
            var saved = localStorage.getItem('siliconflow_api_key');
            if (saved) API_KEY = saved;
        } catch (e) {}

        renderCategoryFilters();
        filterAndRender();

        // 搜索框事件
        if (searchInput) {
            searchInput.addEventListener('input', debounce(function () {
                currentQuery = this.value.trim().toLowerCase();
                currentPage = 1;
                filterAndRender();
            }, 300));
        }
    }

    // ============================================================
    //  防抖
    // ============================================================
    function debounce(fn, delay) {
        var timer;
        return function () {
            var ctx = this, args = arguments;
            clearTimeout(timer);
            timer = setTimeout(function () { fn.apply(ctx, args); }, delay);
        };
    }

    // ============================================================
    //  分类筛选按钮
    // ============================================================
    var catConfig = {
        'all': '全部',
        'consumer': '消费纠纷',
        'labor': '劳动雇佣',
        'housing': '住房邻里',
        'family': '婚姻家庭',
        'lending': '民间借贷',
        'tort': '侵权损害',
        'criminal': '刑事相关',
        'digital': '网络电商',
        'contract': '合同纠纷'
    };

    function renderCategoryFilters() {
        if (!filterContainer) return;

        Object.keys(catConfig).forEach(function (key) {
            var btn = document.createElement('button');
            btn.className = 'filter-btn' + (key === 'all' ? ' active' : '');
            btn.setAttribute('data-cat', key);
            btn.textContent = catConfig[key];
            btn.addEventListener('click', function () {
                currentCategory = key;
                currentPage = 1;
                // 更新活跃状态
                filterContainer.querySelectorAll('.filter-btn').forEach(function (b) {
                    b.classList.remove('active');
                });
                btn.classList.add('active');
                filterAndRender();
            });
            filterContainer.appendChild(btn);
        });
    }

    // ============================================================
    //  搜索+筛选+渲染
    // ============================================================
    function filterAndRender() {
        currentFiltered = provisionsData.filter(function (p) {
            var matchCat = currentCategory === 'all' || p.category === currentCategory;
            if (!matchCat) return false;

            if (!currentQuery) return true;

            // 搜索关键词、法律名、原文、白话解释
            var searchTarget = (p.keywords || '') + ' ' + p.lawName + ' ' + p.article + ' ' + p.original + ' ' + p.explanation;
            return searchTarget.toLowerCase().indexOf(currentQuery) > -1;
        });

        renderProvisionCards(currentFiltered);
    }

    // ============================================================
    //  渲染条文卡片
    // ============================================================
    function renderProvisionCards(provisions) {
        if (!provisionGrid) return;
        provisionGrid.innerHTML = '';

        if (provisions.length === 0) {
            if (noResultsDiv) noResultsDiv.style.display = 'block';
            if (paginationDiv) paginationDiv.style.display = 'none';
            return;
        }
        if (noResultsDiv) noResultsDiv.style.display = 'none';

        var totalPages = Math.ceil(provisions.length / pageSize);
        var start = (currentPage - 1) * pageSize;
        var end = Math.min(start + pageSize, provisions.length);
        var pageData = provisions.slice(start, end);

        // 分页按钮
        if (paginationDiv && totalPages > 1) {
            paginationDiv.style.display = 'flex';
            var prevBtn = paginationDiv.querySelector('#provision-page-prev');
            var nextBtn = paginationDiv.querySelector('#provision-page-next');
            var infoSpan = paginationDiv.querySelector('#provision-page-info');
            if (prevBtn) prevBtn.disabled = currentPage <= 1;
            if (nextBtn) nextBtn.disabled = currentPage >= totalPages;
            if (infoSpan) infoSpan.textContent = '共 ' + provisions.length + ' 条 · ' + currentPage + ' / ' + totalPages + ' 页';
        } else if (paginationDiv) {
            paginationDiv.style.display = 'flex';
            var infoSpan2 = paginationDiv.querySelector('#provision-page-info');
            if (infoSpan2) infoSpan2.textContent = '共 ' + provisions.length + ' 条';
            var prevBtn2 = paginationDiv.querySelector('#provision-page-prev');
            var nextBtn2 = paginationDiv.querySelector('#provision-page-next');
            if (prevBtn2) prevBtn2.style.display = 'none';
            if (nextBtn2) nextBtn2.style.display = 'none';
        }

        pageData.forEach(function (p) {
            var card = document.createElement('div');
            card.className = 'provision-card';

            var catName = catConfig[p.category] || p.category;
            var truncatedOriginal = p.original.length > 200 ? p.original.substring(0, 200) + '...' : p.original;

            card.innerHTML =
                '<div class="prov-header">' +
                    '<span class="prov-category-tag">' + catName + '</span>' +
                    '<span class="prov-law-name">' + p.lawName + ' ' + p.article + '</span>' +
                '</div>' +
                '<div class="prov-original-wrapper">' +
                    '<div class="prov-original-label">📜 法条原文</div>' +
                    '<div class="prov-original-text" id="prov-orig-' + p.id + '">' + escapeHTML(truncatedOriginal) + '</div>' +
                    (p.original.length > 200 ? '<button class="prov-expand-btn" data-pid="' + p.id + '">展开全文 ▼</button>' : '') +
                '</div>' +
                '<div class="prov-explanation-wrapper">' +
                    '<div class="prov-explain-label">💡 大白话解释</div>' +
                    '<div class="prov-explain-text" id="prov-explain-' + p.id + '">' + escapeHTML(p.explanation) + '</div>' +
                    '<button class="ai-explain-btn" data-pid="' + p.id + '">🤖 AI 换个说法解释</button>' +
                '</div>';

            provisionGrid.appendChild(card);
        });

        // 绑定展开/收起原文事件
        provisionGrid.querySelectorAll('.prov-expand-btn').forEach(function (btn) {
            btn.addEventListener('click', function () {
                var pid = parseInt(this.getAttribute('data-pid'));
                var origDiv = document.getElementById('prov-orig-' + pid);
                var prov = provisionsData.find(function (p) { return p.id === pid; });
                if (!prov) return;

                if (this.textContent.indexOf('展开') > -1) {
                    origDiv.textContent = prov.original;
                    this.textContent = '收起 ▲';
                } else {
                    origDiv.textContent = prov.original.length > 200 ? prov.original.substring(0, 200) + '...' : prov.original;
                    this.textContent = '展开全文 ▼';
                }
            });
        });

        // 绑定AI解释事件
        provisionGrid.querySelectorAll('.ai-explain-btn').forEach(function (btn) {
            btn.addEventListener('click', function () {
                var pid = parseInt(this.getAttribute('data-pid'));
                var prov = provisionsData.find(function (p) { return p.id === pid; });
                if (!prov) return;
                aiExplain(prov, this);
            });
        });
    }

    // ============================================================
    //  AI解释某一条文
    // ============================================================
    function aiExplain(provision, btn) {
        var explainDiv = document.getElementById('prov-explain-' + provision.id);
        if (!explainDiv) return;

        btn.disabled = true;
        btn.textContent = '⏳ AI正在生成解释...';
        explainDiv.innerHTML = '<span style="color:var(--text-secondary);">⏳ 正在生成中，请稍候...</span>';

        var systemPrompt = '请用大白话解释以下法律条文，让完全不懂法律的人也能听懂。用生活中的例子来说明，控制在200字以内，不要用法律套话。';
        var userPrompt = '【法律名称】' + provision.lawName + '\n【条款】' + provision.article + '\n【原文】' + provision.original;

        callSiliconFlow(systemPrompt, userPrompt, function (error, result) {
            btn.disabled = false;
            btn.textContent = '🤖 AI 换个说法解释';
            if (error) {
                explainDiv.innerHTML = '<span style="color:#c97a6a;">⚠️ AI解释失败：' + error + '。请检查网络后重试。</span>';
            } else if (result) {
                explainDiv.textContent = result;
            }
        });
    }

    // ============================================================
    //  调用硅基流动API（非流式，用于条文解释）
    // ============================================================
    function callSiliconFlow(systemPrompt, userPrompt, callback) {
        var apiKey = API_KEY;
        try {
            var saved = localStorage.getItem('siliconflow_api_key');
            if (saved) apiKey = saved;
        } catch (e) {}

        var xhr = new XMLHttpRequest();
        xhr.open('POST', 'https://api.siliconflow.cn/v1/chat/completions', true);
        xhr.setRequestHeader('Content-Type', 'application/json');
        xhr.setRequestHeader('Authorization', 'Bearer ' + apiKey);
        xhr.timeout = 30000;
        xhr.responseType = 'text';

        xhr.onload = function () {
            if (xhr.status === 200) {
                try {
                    var data = JSON.parse(xhr.responseText);
                    var text = data.choices && data.choices[0] && data.choices[0].message
                        ? data.choices[0].message.content
                        : '';
                    callback(null, (text || '').trim());
                } catch (e) {
                    callback('解析响应失败', null);
                }
            } else if (xhr.status === 0) {
                // file:// 或其他导致 status=0 的场景
                callback('请求被阻止（可能是跨域或file协议限制）', null);
            } else {
                var errMsg = 'HTTP ' + xhr.status;
                try {
                    var errData = JSON.parse(xhr.responseText);
                    if (errData.error && errData.error.message) errMsg = errData.error.message;
                } catch (e) {}
                callback(errMsg, null);
            }
        };

        xhr.onerror = function () { callback('网络连接失败，请检查网络', null); };
        xhr.ontimeout = function () { callback('请求超时（30秒），请重试', null); };

        xhr.send(JSON.stringify({
            model: 'deepseek-ai/DeepSeek-V3',
            messages: [
                { role: 'system', content: systemPrompt },
                { role: 'user', content: userPrompt }
            ],
            temperature: 0.7,
            max_tokens: 600,
            stream: false
        }));
    }

    // ============================================================
    //  HTML转义
    // ============================================================
    function escapeHTML(str) {
        var div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    }

    // ============================================================
    //  分页事件绑定
    // ============================================================
    function bindPagination() {
        var prevBtn = document.getElementById('provision-page-prev');
        var nextBtn = document.getElementById('provision-page-next');
        if (prevBtn) {
            prevBtn.addEventListener('click', function () {
                if (currentPage > 1) {
                    currentPage--;
                    renderProvisionCards(currentFiltered);
                    document.getElementById('legal-db-section').scrollIntoView({ behavior: 'smooth', block: 'start' });
                }
            });
        }
        if (nextBtn) {
            nextBtn.addEventListener('click', function () {
                var totalPages = Math.ceil(currentFiltered.length / pageSize);
                if (currentPage < totalPages) {
                    currentPage++;
                    renderProvisionCards(currentFiltered);
                    document.getElementById('legal-db-section').scrollIntoView({ behavior: 'smooth', block: 'start' });
                }
            });
        }
    }

    // ============================================================
    //  启动
    // ============================================================
    document.addEventListener('DOMContentLoaded', function () {
        init();
        bindPagination();
    });

})();
