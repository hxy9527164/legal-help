/* ============================================================ */
/*  法律条文百科 — 树形目录 / 高级筛选 / 面包屑 / AI白话解释         */
/* ============================================================ */
(function () {
    'use strict';

    var provisionsData = [];
    var currentPage = 1, pageSize = 8;
    var currentFiltered = [];
    var currentBranch = 'all', currentSubcategory = 'all';
    var currentCountry = 'all', currentHierarchy = 'all';
    var currentQuery = '';
    var highlightedId = null;

    // DOM
    var searchInput, sidebarTree, provisionGrid, paginationDiv, noResultsDiv, breadcrumbEl;
    var countryFilter, hierarchyFilter, resultCountEl;
    var API_KEY = 'sk-wbtzxngfywxeetfscvfqfjzlbdaiptwliceyqgnhmrslvlqd';

    // ============================================================
    //  分类配置
    // ============================================================
    var branchConfig = {
        'constitution': { name: '宪法及宪法相关法', icon: '📜', children: {
            'rights': '公民权利', 'organs': '国家机构', 'election': '选举制度'
        }},
        'civil': { name: '民法商法', icon: '⚖️', children: {
            'general': '总则', 'property': '物权', 'contract': '合同',
            'family': '婚姻家庭', 'inheritance': '继承', 'tort': '侵权责任',
            'company': '公司企业', 'ip': '知识产权'
        }},
        'admin': { name: '行政法', icon: '🏛️', children: {
            'publicorder': '治安管理', 'traffic': '交通管理', 'foodsafety': '食品安全'
        }},
        'economic': { name: '经济法', icon: '💰', children: {
            'consumer': '消费者保护', 'competition': '竞争法', 'tax': '税收',
            'realestate': '房地产'
        }},
        'social': { name: '社会法', icon: '🤝', children: {
            'labor': '劳动法', 'insurance': '社会保障', 'elderly': '老年人权益',
            'children': '未成年人保护', 'women': '妇女权益'
        }},
        'criminal': { name: '刑法', icon: '🔒', children: {
            'personal': '侵犯人身权利', 'property': '侵犯财产', 'economic': '经济犯罪'
        }},
        'procedure': { name: '诉讼与非诉讼程序法', icon: '📋', children: {
            'civil': '民事诉讼', 'criminal': '刑事诉讼', 'admin': '行政诉讼',
            'arbitration': '仲裁', 'mediation': '调解'
        }}
    };

    var countryConfig = {
        'all': '🌐 全部国家', 'CN': '🇨🇳 中国', 'US': '🇺🇸 美国',
        'EU': '🇪🇺 欧盟', 'JP': '🇯🇵 日本', 'KR': '🇰🇷 韩国'
    };

    var hierarchyConfig = {
        'all': '全部层级', 'constitution': '宪法',
        'law': '法律', 'regulation': '行政法规',
        'judicial': '司法解释', 'directive': '指令/规章'
    };

    // ============================================================
    //  初始化
    // ============================================================
    function init() {
        searchInput = document.getElementById('legal-search-input');
        sidebarTree = document.getElementById('legal-sidebar-tree');
        provisionGrid = document.getElementById('provision-grid');
        paginationDiv = document.getElementById('provision-pagination');
        noResultsDiv = document.getElementById('provision-no-results');
        breadcrumbEl = document.getElementById('legal-breadcrumb');
        countryFilter = document.getElementById('filter-country');
        hierarchyFilter = document.getElementById('filter-hierarchy');
        resultCountEl = document.getElementById('legal-result-count');

        if (window.__legalProvisionsData) {
            provisionsData = window.__legalProvisionsData;
        } else {
            if (provisionGrid) provisionGrid.innerHTML = '<p class="no-results">条文数据加载失败，请刷新页面</p>';
            return;
        }

        try { var saved = localStorage.getItem('siliconflow_api_key'); if (saved) API_KEY = saved; } catch (e) {}

        renderCategoryTree();
        renderCountryFilter();
        renderHierarchyFilter();
        filterAndRender();

        if (searchInput) searchInput.addEventListener('input', debounce(function () {
            currentQuery = this.value.trim().toLowerCase();
            currentPage = 1;
            filterAndRender();
        }, 300));

        if (countryFilter) countryFilter.addEventListener('change', function () {
            currentCountry = this.value; currentPage = 1; filterAndRender();
        });
        if (hierarchyFilter) hierarchyFilter.addEventListener('change', function () {
            currentHierarchy = this.value; currentPage = 1; filterAndRender();
        });
    }

    // ============================================================
    //  防抖
    // ============================================================
    function debounce(fn, delay) {
        var timer;
        return function () { var ctx = this, args = arguments; clearTimeout(timer); timer = setTimeout(function () { fn.apply(ctx, args); }, delay); };
    }

    // ============================================================
    //  树形目录
    // ============================================================
    function renderCategoryTree() {
        if (!sidebarTree) return;
        sidebarTree.innerHTML = '';

        // "全部" 节点
        var allNode = createTreeNode('all', 'all', '📚 全部法律条文', true);
        sidebarTree.appendChild(allNode);

        // 中国法节点
        var cnNode = createTreeParent('cn-group', '🇨🇳 中国法律');
        sidebarTree.appendChild(cnNode);

        Object.keys(branchConfig).forEach(function (branchKey) {
            var cfg = branchConfig[branchKey];
            var branchNode = createTreeParent('branch-' + branchKey, cfg.icon + ' ' + cfg.name, true);

            Object.keys(cfg.children).forEach(function (subKey) {
                var subName = cfg.children[subKey];
                var subNode = createTreeNode(branchKey, subKey, subName, true);
                branchNode.querySelector('.tree-children').appendChild(subNode);
            });

            cnNode.querySelector('.tree-children').appendChild(branchNode);
        });

        // 国际对比节点
        var intlNode = createTreeParent('intl-group', '🌍 国际法律对比');
        sidebarTree.appendChild(intlNode);

        ['US','EU','JP','KR'].forEach(function (cc) {
            var name = countryConfig[cc].replace(/[🇺🇸🇪🇺🇯🇵🇰🇷]\s*/, '');
            var intlChild = createTreeNode('intl', cc, countryConfig[cc].split(' ')[0] + ' ' + name, true);
            intlNode.querySelector('.tree-children').appendChild(intlChild);
        });
    }

    function createTreeNode(branch, subcategory, label, indent) {
        var node = document.createElement('div');
        node.className = 'tree-node' + (indent ? ' tree-indent' : '');
        node.setAttribute('data-branch', branch);
        node.setAttribute('data-subcat', subcategory);

        var count = countProvisions(branch, subcategory);
        var countStr = count > 0 ? ' <span class="tree-count">' + count + '</span>' : '';

        node.innerHTML = '<span class="tree-label">' + label + countStr + '</span>';
        node.addEventListener('click', function (e) {
            e.stopPropagation();
            currentBranch = branch;
            currentSubcategory = subcategory;
            currentPage = 1;
            highlightedId = null;
            sidebarTree.querySelectorAll('.tree-node.active').forEach(function (n) { n.classList.remove('active'); });
            node.classList.add('active');
            updateBreadcrumb();
            filterAndRender();
        });
        return node;
    }

    function createTreeParent(id, label) {
        var container = document.createElement('div');
        container.className = 'tree-parent';
        container.id = id;

        var header = document.createElement('div');
        header.className = 'tree-parent-header';
        header.innerHTML = '<span class="tree-toggle">▶</span> <span class="tree-parent-label">' + label + '</span>';
        header.addEventListener('click', function () {
            var children = container.querySelector('.tree-children');
            var toggle = container.querySelector('.tree-toggle');
            if (children.style.display === 'none') {
                children.style.display = 'block';
                toggle.textContent = '▼';
            } else {
                children.style.display = 'none';
                toggle.textContent = '▶';
            }
        });

        var children = document.createElement('div');
        children.className = 'tree-children';

        container.appendChild(header);
        container.appendChild(children);
        return container;
    }

    function countProvisions(branch, subcategory) {
        return provisionsData.filter(function (p) {
            if (branch === 'all') return true;
            if (branch === 'intl') return p.country !== 'CN';
            if (subcategory === 'all') return p.branch === branch;
            return p.branch === branch && p.subcategory === subcategory;
        }).length;
    }

    // ============================================================
    //  高级筛选
    // ============================================================
    function renderCountryFilter() {
        if (!countryFilter) return;
        Object.keys(countryConfig).forEach(function (key) {
            var opt = document.createElement('option');
            opt.value = key; opt.textContent = countryConfig[key];
            countryFilter.appendChild(opt);
        });
    }

    function renderHierarchyFilter() {
        if (!hierarchyFilter) return;
        Object.keys(hierarchyConfig).forEach(function (key) {
            var opt = document.createElement('option');
            opt.value = key; opt.textContent = hierarchyConfig[key];
            hierarchyFilter.appendChild(opt);
        });
    }

    // ============================================================
    //  面包屑
    // ============================================================
    function updateBreadcrumb() {
        if (!breadcrumbEl) return;
        var parts = ['📚 法律条文百科'];
        if (currentBranch !== 'all' && currentBranch !== 'intl') {
            var bcfg = branchConfig[currentBranch];
            parts.push(bcfg ? bcfg.name : currentBranch);
        }
        if (currentBranch === 'intl') parts.push('🌍 国际法律对比');
        if (currentSubcategory !== 'all') {
            var bcfg = branchConfig[currentBranch];
            if (bcfg && bcfg.children[currentSubcategory]) {
                parts.push(bcfg.children[currentSubcategory]);
            } else if (countryConfig[currentSubcategory]) {
                parts.push(countryConfig[currentSubcategory].replace(/[^一-龥a-zA-Z]/g, '').trim());
            }
        }
        breadcrumbEl.innerHTML = parts.join(' <span class="breadcrumb-sep">›</span> ');
    }

    // ============================================================
    //  搜索+筛选+渲染
    // ============================================================
    function filterAndRender() {
        currentFiltered = provisionsData.filter(function (p) {
            if (currentBranch !== 'all') {
                if (currentBranch === 'intl') {
                    if (p.country === 'CN') return false;
                    if (currentSubcategory !== 'all' && p.country !== currentSubcategory) return false;
                } else {
                    if (p.branch !== currentBranch) return false;
                    if (currentSubcategory !== 'all' && p.subcategory !== currentSubcategory) return false;
                }
            }
            if (currentCountry !== 'all' && p.country !== currentCountry) return false;
            if (currentHierarchy !== 'all' && p.hierarchy !== currentHierarchy) return false;
            if (currentQuery) {
                var target = (p.keywords||'') + ' ' + p.lawName + ' ' + p.article + ' ' + p.original + ' ' + p.explanation;
                if (target.toLowerCase().indexOf(currentQuery) === -1) return false;
            }
            return true;
        });

        if (resultCountEl) resultCountEl.textContent = '共 ' + currentFiltered.length + ' 条';
        renderProvisionCards(currentFiltered);
    }

    // ============================================================
    //  渲染条文卡片（增强版：元信息、关联、层级标签）
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

        renderPagination(provisions.length, totalPages);

        pageData.forEach(function (p) {
            var card = document.createElement('div');
            card.className = 'provision-card';
            card.id = 'prov-card-' + p.id;

            if (highlightedId === p.id) {
                card.classList.add('highlighted');
                setTimeout(function () { card.classList.remove('highlighted'); highlightedId = null; }, 2000);
            }

            var branchName = (branchConfig[p.branch] && branchConfig[p.branch].name) || p.branch;
            var subName = (branchConfig[p.branch] && branchConfig[p.branch].children[p.subcategory]) || p.subcategory;
            var hierarchyLabel = (hierarchyConfig[p.hierarchy] || p.hierarchy);
            var countryLabel = (countryConfig[p.country] || p.country);
            var truncatedOriginal = p.original.length > 200 ? p.original.substring(0, 200) + '...' : p.original;

            // 关联条文链接
            var relatedHTML = '';
            if (p.related && p.related.length > 0) {
                var relatedLinks = p.related.map(function (rid) {
                    var rel = provisionsData.find(function (x) { return x.id === rid; });
                    if (rel) {
                        return '<span class="prov-related-link" data-rid="' + rid + '">' + escapeHTML(rel.lawName) + ' ' + escapeHTML(rel.article) + '</span>';
                    }
                    return '';
                }).filter(Boolean).join(', ');
                if (relatedLinks) relatedHTML = '<div class="prov-related">🔗 关联条文：' + relatedLinks + '</div>';
            }

            // 国家标签（非中国时显示）
            var countryTagHTML = p.country !== 'CN'
                ? '<span class="prov-country-tag" title="' + escapeHTML(countryLabel) + '">' + countryLabel + '</span>'
                : '';

            card.innerHTML =
                '<div class="prov-header">' +
                    '<span class="prov-category-tag">' + escapeHTML(branchName) + ' › ' + escapeHTML(subName) + '</span>' +
                    countryTagHTML +
                    '<span class="prov-hierarchy-tag">' + escapeHTML(hierarchyLabel) + '</span>' +
                '</div>' +
                '<div class="prov-law-name">' + escapeHTML(p.lawName) + ' ' + escapeHTML(p.article) + '</div>' +
                '<div class="prov-meta-row">' +
                    (p.effectiveDate ? '<span class="prov-date">📅 施行：' + p.effectiveDate + '</span>' : '') +
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
                '</div>' +
                relatedHTML;

            provisionGrid.appendChild(card);
        });

        // 绑定事件
        bindCardEvents();
    }

    function renderPagination(total, totalPages) {
        if (!paginationDiv) return;
        paginationDiv.style.display = 'flex';
        var prevBtn = paginationDiv.querySelector('#provision-page-prev');
        var nextBtn = paginationDiv.querySelector('#provision-page-next');
        var infoSpan = paginationDiv.querySelector('#provision-page-info');
        if (totalPages > 1) {
            if (prevBtn) { prevBtn.disabled = currentPage <= 1; prevBtn.style.display = ''; }
            if (nextBtn) { nextBtn.disabled = currentPage >= totalPages; nextBtn.style.display = ''; }
            if (infoSpan) infoSpan.textContent = currentPage + ' / ' + totalPages + ' 页';
        } else {
            if (prevBtn) prevBtn.style.display = 'none';
            if (nextBtn) nextBtn.style.display = 'none';
            if (infoSpan) infoSpan.textContent = '共 ' + total + ' 条';
        }
    }

    function bindCardEvents() {
        provisionGrid.querySelectorAll('.prov-expand-btn').forEach(function (btn) {
            btn.addEventListener('click', function () {
                var pid = parseInt(this.getAttribute('data-pid'), 10);
                var origDiv = document.getElementById('prov-orig-' + pid);
                var prov = provisionsData.find(function (p) { return p.id === pid; });
                if (!prov || !origDiv) return;
                if (this.textContent.indexOf('展开') > -1) {
                    origDiv.textContent = prov.original;
                    this.textContent = '收起 ▲';
                } else {
                    origDiv.textContent = prov.original.length > 200 ? prov.original.substring(0, 200) + '...' : prov.original;
                    this.textContent = '展开全文 ▼';
                }
            });
        });

        provisionGrid.querySelectorAll('.ai-explain-btn').forEach(function (btn) {
            btn.addEventListener('click', function () {
                var pid = parseInt(this.getAttribute('data-pid'), 10);
                var prov = provisionsData.find(function (p) { return p.id === pid; });
                if (!prov) return;
                aiExplain(prov, this);
            });
        });

        // 关联条文跳转
        provisionGrid.querySelectorAll('.prov-related-link').forEach(function (link) {
            link.addEventListener('click', function () {
                var rid = parseInt(this.getAttribute('data-rid'), 10);
                // 重置筛选以显示目标条文
                currentBranch = 'all'; currentSubcategory = 'all';
                currentCountry = 'all'; currentHierarchy = 'all'; currentQuery = '';
                if (searchInput) searchInput.value = '';
                if (countryFilter) countryFilter.value = 'all';
                if (hierarchyFilter) hierarchyFilter.value = 'all';
                highlightedId = rid;
                currentPage = 1;
                // 找到目标条文所在的页码
                currentFiltered = provisionsData.slice();
                var idx = currentFiltered.findIndex(function (p) { return p.id === rid; });
                if (idx >= 0) currentPage = Math.floor(idx / pageSize) + 1;
                sidebarTree.querySelectorAll('.tree-node.active').forEach(function (n) { n.classList.remove('active'); });
                updateBreadcrumb();
                filterAndRender();
                // 滚动到卡片
                setTimeout(function () {
                    var targetCard = document.getElementById('prov-card-' + rid);
                    if (targetCard) targetCard.scrollIntoView({ behavior: 'smooth', block: 'center' });
                }, 200);
            });
        });
    }

    // ============================================================
    //  AI解释
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
                explainDiv.innerHTML = '<span style="color:#c97a6a;">⚠️ AI解释失败：' + escapeHTML(error) + '。请检查网络后重试。</span>';
            } else if (result) {
                explainDiv.textContent = result;
            }
        });
    }

    function callSiliconFlow(systemPrompt, userPrompt, callback) {
        var apiKey = API_KEY;
        try { var saved = localStorage.getItem('siliconflow_api_key'); if (saved) apiKey = saved; } catch (e) {}
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
                    var text = data.choices && data.choices[0] && data.choices[0].message ? data.choices[0].message.content : '';
                    callback(null, (text || '').trim());
                } catch (e) { callback('解析响应失败', null); }
            } else if (xhr.status === 0) {
                callback('请求被阻止（可能是跨域或file协议限制）', null);
            } else {
                var errMsg = 'HTTP ' + xhr.status;
                try { var errData = JSON.parse(xhr.responseText); if (errData.error && errData.error.message) errMsg = errData.error.message; } catch (e) {}
                callback(errMsg, null);
            }
        };
        xhr.onerror = function () { callback('网络连接失败，请检查网络', null); };
        xhr.ontimeout = function () { callback('请求超时（30秒），请重试', null); };
        xhr.send(JSON.stringify({ model: 'deepseek-ai/DeepSeek-V3', messages: [{ role: 'system', content: systemPrompt }, { role: 'user', content: userPrompt }], temperature: 0.7, max_tokens: 600, stream: false }));
    }

    // ============================================================
    //  分页事件
    // ============================================================
    function bindPagination() {
        var prevBtn = document.getElementById('provision-page-prev');
        var nextBtn = document.getElementById('provision-page-next');
        if (prevBtn) prevBtn.addEventListener('click', function () {
            if (currentPage > 1) { currentPage--; renderProvisionCards(currentFiltered); document.getElementById('legal-db-section').scrollIntoView({ behavior: 'smooth', block: 'start' }); }
        });
        if (nextBtn) nextBtn.addEventListener('click', function () {
            if (currentPage < Math.ceil(currentFiltered.length / pageSize)) { currentPage++; renderProvisionCards(currentFiltered); document.getElementById('legal-db-section').scrollIntoView({ behavior: 'smooth', block: 'start' }); }
        });
    }

    // ============================================================
    //  工具函数
    // ============================================================
    function escapeHTML(str) {
        var div = document.createElement('div');
        div.textContent = str || '';
        return div.innerHTML;
    }

    // ============================================================
    //  启动
    // ============================================================
    document.addEventListener('DOMContentLoaded', function () { init(); bindPagination(); updateBreadcrumb(); });
})();
