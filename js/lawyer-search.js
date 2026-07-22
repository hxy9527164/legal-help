/* ============================================================ */
/*  律师检索 + 文书模板渲染                                       */
/* ============================================================ */

(function () {
    'use strict';

    let lawyersData = [];
    let templatesData = [];

    // DOM
    const lawyerGrid = document.getElementById('lawyer-grid');
    const lawyerCount = document.getElementById('lawyer-count');
    const lawyerSearch = document.getElementById('lawyer-search');
    const filterProvince = document.getElementById('filter-province');
    const filterCity = document.getElementById('filter-city');
    const filterDistrict = document.getElementById('filter-district');
    const filterFirm = document.getElementById('filter-firm');
    const filterField = document.getElementById('filter-field');
    const lawyerNoResults = document.getElementById('lawyer-no-results');

    const templateList = document.getElementById('template-list');
    const templateFilters = document.getElementById('template-filters');

    // ============================================================
    //  初始化：加载数据
    // ============================================================
    var initRetryCount = 0;
    var MAX_RETRIES = 3;

    function showLawyerLoading() {
        if (lawyerGrid) {
            lawyerGrid.innerHTML = '<div class="loading-box"><span class="loading-spinner"></span><p>正在加载律师数据...</p></div>';
        }
        if (lawyerCount) lawyerCount.textContent = '';
    }

    function showLawyerError(errMsg) {
        if (lawyerGrid) {
            lawyerGrid.innerHTML = `
                <div class="error-banner">
                    <div class="error-banner-icon">⚠️</div>
                    <h4>律师数据加载失败</h4>
                    <p class="error-reason">${errMsg}</p>
                    <p class="error-detail">请确认 <code>data/lawyers.json</code> 文件未被移动或损坏。</p>
                    <div class="error-actions">
                        <button class="btn btn-retry" onclick="location.reload()">🔄 刷新页面</button>
                        ${initRetryCount < MAX_RETRIES ? '<button class="btn btn-retry-secondary" id="retry-lawyer-load">🔁 重试加载</button>' : ''}
                    </div>
                </div>`;
            var retryBtn = document.getElementById('retry-lawyer-load');
            if (retryBtn) {
                retryBtn.addEventListener('click', function () {
                    initRetryCount++;
                    init();
                });
            }
        }
        if (lawyerCount) lawyerCount.textContent = '加载失败';
    }

    // ---------- 数据加载（优先使用 script 标签注入的全局变量）----------
    function loadDataOrFallback(globalVar, jsonPath) {
        return new Promise(function (resolve, reject) {
            // 方案1: script 标签已注入全局变量（file:// 100%兼容，最快）
            if (globalVar) {
                resolve(globalVar);
                return;
            }
            // 方案2: fetch（HTTP 服务器场景）
            fetch(jsonPath).then(function (res) {
                if (!res.ok) throw new Error('HTTP ' + res.status);
                return res.json();
            }).then(resolve).catch(function () {
                // 方案3: XHR 回退
                var xhr = new XMLHttpRequest();
                xhr.open('GET', jsonPath, true);
                xhr.overrideMimeType('application/json');
                xhr.onload = function () {
                    if (xhr.status === 200 || xhr.status === 0) {
                        try { resolve(JSON.parse(xhr.responseText)); }
                        catch (e) { reject(new Error('JSON 格式错误: ' + e.message)); }
                    } else {
                        reject(new Error('所有加载方式均失败 (HTTP ' + xhr.status + ')'));
                    }
                };
                xhr.onerror = function () {
                    reject(new Error('无法读取 ' + jsonPath + ' — 请确认文件存在'));
                };
                xhr.send(null);
            });
        });
    }

    async function init() {
        // 诊断日志
        var hasLawyersGlobal = !!window.__lawyersData;
        var hasTemplatesGlobal = !!window.__templatesData;
        var diagMsg = '[法律自助助手] script标签数据: lawyers=' + hasLawyersGlobal + ' templates=' + hasTemplatesGlobal;
        console.log(diagMsg);

        showLawyerLoading();
        if (templateList) templateList.innerHTML = '<p class="loading-hint">⏳ 正在加载文书模板...</p>';

        try {
            // 首选: script 标签注入的全局变量
            if (window.__lawyersData) {
                console.log('[法律自助助手] 使用 script 标签数据 (lawyers: ' + window.__lawyersData.length + ' 条)');
                lawyersData = window.__lawyersData;
            } else {
                console.log('[法律自助助手] script 标签数据不可用，尝试 fetch/XHR...');
                lawyersData = await loadDataOrFallback(null, 'data/lawyers.json');
            }

            if (window.__templatesData) {
                templatesData = window.__templatesData;
            } else {
                templatesData = await loadDataOrFallback(null, 'data/templates.json');
            }
            window.templatesData = templatesData;

            initRetryCount = 0;

            // 合并用户上传的律师数据（localStorage）
            try {
                var uploaded = JSON.parse(localStorage.getItem('user_uploaded_lawyers') || '[]');
                var existingKeys = new Set();
                lawyersData.forEach(function (l) { existingKeys.add(l.name + '|' + l.firm); });
                uploaded.forEach(function (l) {
                    if (!existingKeys.has(l.name + '|' + l.firm)) {
                        lawyersData.push(l);
                        existingKeys.add(l.name + '|' + l.firm);
                    }
                });
                if (uploaded.length > 0) console.log('[法律自助助手] 加载用户上传律师: ' + uploaded.length + ' 位');
            } catch (e) {}

            console.log('[法律自助助手] 数据就绪，开始渲染...');
            populateFilters();
            renderLawyers(lawyersData);
            renderTemplateCategories();
            renderTemplates(templatesData);
            renderFAQs();
            console.log('[法律自助助手] 渲染完成！律师: ' + lawyersData.length + ' 模板: ' + templatesData.length);
        } catch (err) {
            console.error('[法律自助助手] 加载失败:', err);
            showLawyerError(err.message || '未知错误');
            if (templateList) {
                templateList.innerHTML = '<p class="no-results">模板数据暂不可用</p>';
            }
        }
    }

    // ============================================================
    //  律师搜索
    // ============================================================

    // 填充筛选下拉框（省→市→区三级联动）
    function populateFilters() {
        // 省份（始终显示全部）
        if (filterProvince) {
            var provinces = [...new Set(lawyersData.map(function (l) { return l.province; }).filter(Boolean))].sort();
            provinces.forEach(function (p) {
                var opt = document.createElement('option'); opt.value = p; opt.textContent = p;
                filterProvince.appendChild(opt);
            });
        }

        // 律所
        if (filterFirm) {
            var firms = [...new Set(lawyersData.map(function (l) { return l.firm; }).filter(Boolean))].sort();
            firms.forEach(function (f) {
                var opt = document.createElement('option'); opt.value = f;
                opt.textContent = f.length > 25 ? f.substring(0, 25) + '...' : f;
                filterFirm.appendChild(opt);
            });
        }

        // 领域
        if (filterField) {
            var allFields = [];
            lawyersData.forEach(function (l) { allFields.push.apply(allFields, l.fields); });
            var uniqueFields = [...new Set(allFields)].sort();
            uniqueFields.forEach(function (f) {
                var opt = document.createElement('option'); opt.value = f; opt.textContent = f;
                filterField.appendChild(opt);
            });
        }

        // 初始填充城市和区县（显示全部）
        populateCityDropdown();
        populateDistrictDropdown();
    }

    // 根据选中省份填充城市
    function populateCityDropdown() {
        if (!filterCity) return;
        var province = filterProvince ? filterProvince.value : '';
        var cities = [...new Set(lawyersData
            .filter(function (l) { return !province || l.province === province; })
            .map(function (l) { return l.city; })
            .filter(Boolean))].sort();
        filterCity.innerHTML = '<option value="">全部城市</option>';
        cities.forEach(function (c) {
            var opt = document.createElement('option'); opt.value = c; opt.textContent = c;
            filterCity.appendChild(opt);
        });
    }

    // 根据选中省份+城市填充区县
    function populateDistrictDropdown() {
        if (!filterDistrict) return;
        var province = filterProvince ? filterProvince.value : '';
        var city = filterCity ? filterCity.value : '';
        var districts = [...new Set(lawyersData
            .filter(function (l) {
                return (!province || l.province === province) && (!city || l.city === city);
            })
            .map(function (l) { return l.district; })
            .filter(Boolean))].sort();
        filterDistrict.innerHTML = '<option value="">全部区县</option>';
        districts.forEach(function (d) {
            var opt = document.createElement('option'); opt.value = d; opt.textContent = d;
            filterDistrict.appendChild(opt);
        });
    }

    // 省份变更 → 重新填充城市 + 区县
    if (filterProvince) {
        filterProvince.addEventListener('change', function () {
            populateCityDropdown();
            populateDistrictDropdown();
            filterLawyers();
        });
    }
    // 城市变更 → 重新填充区县
    if (filterCity) {
        filterCity.addEventListener('change', function () {
            populateDistrictDropdown();
            filterLawyers();
        });
    }

    // 渲染律师卡片（带照片缩略图 + 点击查看详情）
    function renderLawyers(lawyers) {
        lawyerGrid.innerHTML = '';

        if (lawyerCount) {
            lawyerCount.textContent = '共找到 ' + lawyers.length + ' 位律师（点击卡片查看详情）';
        }

        if (lawyers.length === 0) {
            lawyerNoResults.style.display = 'block';
            return;
        }
        lawyerNoResults.style.display = 'none';

        lawyers.forEach(function (lawyer) {
            var card = document.createElement('div');
            card.className = 'lawyer-card';
            card.setAttribute('data-id', lawyer.id);
            card.addEventListener('click', function () {
                openLawyerDetail(lawyer);
            });

            var fieldsHTML = lawyer.fields.slice(0, 5).map(function (f) {
                return '<span class="lawyer-field-tag">' + f + '</span>';
            }).join('');

            var hasPhoto = lawyer.photo && lawyer.photo.startsWith('http');
            var photoHTML = hasPhoto
                ? '<img class="lawyer-photo-thumb" src="' + lawyer.photo + '" alt="' + lawyer.name + '" loading="lazy" onerror="this.style.display=\'none\';this.nextElementSibling.style.display=\'flex\';">'
                : '';
            var placeholderHTML = '<div class="lawyer-photo-placeholder"' + (hasPhoto ? ' style="display:none"' : '') + '>' + lawyer.name.charAt(0) + '</div>';

            var hasRealProfile = lawyer.profile_url && lawyer.profile_url.startsWith('http');
            var verifiedBadge = hasRealProfile
                ? '<span class="lawyer-verified" title="数据来自律所官网/法律平台采集">✅ 已验证</span>'
                : '';

            var expYears = lawyer.experience || 0;
            var expBadge = expYears > 0
                ? '<span class="lawyer-badge">' + expYears + '年经验</span>'
                : '';

            var districtInfo = [lawyer.city, lawyer.district].filter(Boolean).join(' ');

            card.innerHTML = `
                <div class="lawyer-header">
                    <div class="lawyer-card-left">
                        ${photoHTML}${placeholderHTML}
                        <div>
                            <div class="lawyer-name">${lawyer.name} ${verifiedBadge}</div>
                            <div class="lawyer-firm">${lawyer.firm}</div>
                        </div>
                    </div>
                    <div>
                        ${expBadge}
                        <div style="color:#94a3b8;font-size:0.75rem;text-align:right;margin-top:4px;">${districtInfo}</div>
                    </div>
                </div>
                <div class="lawyer-fields">${fieldsHTML}</div>
                <div class="lawyer-cases">📂 ${(lawyer.cases || '').substring(0, 80)}${(lawyer.cases || '').length > 80 ? '...' : ''}</div>
                <div class="lawyer-card-hint">点击查看详情 →</div>
            `;
            lawyerGrid.appendChild(card);
        });
    }

    // ============================================================
    //  律师详情弹窗
    // ============================================================
    function openLawyerDetail(lawyer) {
        var overlay = document.getElementById('lawyer-modal-overlay');
        var content = document.getElementById('lawyer-modal-content');
        if (!overlay || !content) return;

        var hasPhoto = lawyer.photo && lawyer.photo.startsWith('http');
        var photoEl = hasPhoto
            ? '<img class="modal-photo" src="' + lawyer.photo + '" alt="' + lawyer.name + '" onerror="this.style.display=\'none\';this.nextElementSibling.style.display=\'flex\';">'
            : '';
        var placeholderEl = '<div class="modal-photo-placeholder"' + (hasPhoto ? ' style="display:none"' : '') + '>' + lawyer.name.charAt(0) + '</div>';

        var position = lawyer.position || '';
        var fieldsAll = (lawyer.fields || []).map(function (f) {
            return '<span class="modal-field-tag">' + f + '</span>';
        }).join('');

        // Calculate analysis scores based on available data
        var expScore = Math.min(100, (lawyer.experience || 0) * 4);
        var fieldScore = Math.min(100, (lawyer.fields || []).length * 15 + 20);
        var eduScore = lawyer.education && lawyer.education.indexOf('博士') > -1 ? 95
            : lawyer.education && lawyer.education.indexOf('硕士') > -1 ? 80
            : lawyer.education && lawyer.education.indexOf('学士') > -1 ? 60
            : lawyer.education && lawyer.education !== '暂无学历信息' ? 70 : 30;
        var hasRealProfile = lawyer.profile_url && lawyer.profile_url.startsWith('http');
        var verifyScore = hasRealProfile ? 90 : 40;
        var caseScore = (lawyer.cases && lawyer.cases.length > 20 && lawyer.cases !== '暂无案例信息') ? 70 : 25;
        var overall = Math.round((expScore * 0.25 + fieldScore * 0.25 + eduScore * 0.2 + verifyScore * 0.15 + caseScore * 0.15));

        content.innerHTML = `
            <div class="modal-header">
                ${photoEl}${placeholderEl}
                <div class="modal-name">${lawyer.name}</div>
                ${position ? '<div class="modal-position">' + position + '</div>' : ''}
                <div class="modal-firm">${lawyer.firm}</div>
            </div>
            <div class="modal-body">
                <div class="modal-section">
                    <h4>📋 基本信息</h4>
                    <div class="modal-info-row"><span class="modal-info-label">执业地区</span><span class="modal-info-value">${lawyer.province} ${lawyer.city} ${lawyer.district || ''}</span></div>
                    <div class="modal-info-row"><span class="modal-info-label">执业年限</span><span class="modal-info-value">${lawyer.experience || '暂无'} 年</span></div>
                    <div class="modal-info-row"><span class="modal-info-label">学历背景</span><span class="modal-info-value">${lawyer.education || '暂无学历信息'}</span></div>
                    <div class="modal-info-row"><span class="modal-info-label">执业证号</span><span class="modal-info-value">${lawyer.license || '暂无'}</span></div>
                    <div class="modal-info-row"><span class="modal-info-label">联系方式</span><span class="modal-info-value">${lawyer.contact || '暂无联系方式'}</span></div>
                    ${lawyer.languages ? '<div class="modal-info-row"><span class="modal-info-label">工作语言</span><span class="modal-info-value">' + lawyer.languages + '</span></div>' : ''}
                    ${lawyer.service_count ? '<div class="modal-info-row"><span class="modal-info-label">服务次数</span><span class="modal-info-value">' + lawyer.service_count + ' 次</span></div>' : ''}
                </div>

                <div class="modal-section">
                    <h4>🏷️ 擅长领域</h4>
                    <div class="modal-fields">${fieldsAll || '<span style="color:#94a3b8;font-size:0.82rem;">暂无数据</span>'}</div>
                </div>

                <div class="modal-section">
                    <h4>📂 经手案件 / 执业经验</h4>
                    <div class="modal-cases"><p>${lawyer.cases || '暂无案例信息'}</p></div>
                </div>

                ${lawyer.awards ? '<div class="modal-section"><h4>🏆 荣誉奖项</h4><div class="modal-cases"><p>' + lawyer.awards + '</p></div></div>' : ''}

                <div class="modal-section">
                    <h4>📊 律师专业度分析</h4>
                    <div class="modal-analysis">
                        <div class="analysis-bars">
                            <div class="analysis-bar-row">
                                <span class="analysis-bar-label">执业经验</span>
                                <div class="analysis-bar-track"><div class="analysis-bar-fill" style="width:${expScore}%"></div></div>
                                <span class="analysis-bar-score">${expScore}</span>
                            </div>
                            <div class="analysis-bar-row">
                                <span class="analysis-bar-label">专业广度</span>
                                <div class="analysis-bar-track"><div class="analysis-bar-fill" style="width:${fieldScore}%"></div></div>
                                <span class="analysis-bar-score">${fieldScore}</span>
                            </div>
                            <div class="analysis-bar-row">
                                <span class="analysis-bar-label">学历层次</span>
                                <div class="analysis-bar-track"><div class="analysis-bar-fill" style="width:${eduScore}%"></div></div>
                                <span class="analysis-bar-score">${eduScore}</span>
                            </div>
                            <div class="analysis-bar-row">
                                <span class="analysis-bar-label">数据可信度</span>
                                <div class="analysis-bar-track"><div class="analysis-bar-fill" style="width:${verifyScore}%"></div></div>
                                <span class="analysis-bar-score">${verifyScore}</span>
                            </div>
                            <div class="analysis-bar-row">
                                <span class="analysis-bar-label">案例丰富度</span>
                                <div class="analysis-bar-track"><div class="analysis-bar-fill" style="width:${caseScore}%"></div></div>
                                <span class="analysis-bar-score">${caseScore}</span>
                            </div>
                        </div>
                        <div style="text-align:center;margin-top:14px;font-size:0.85rem;color:var(--accent);font-weight:600;">
                            综合评分：${overall}/100
                        </div>
                    </div>
                </div>

                <div class="modal-section" style="text-align:center;padding-top:8px;">
                    <span style="font-size:0.72rem;color:#ccc;">数据来源：${lawyer.source || '数据库'} | ${hasRealProfile ? '<a href="' + lawyer.profile_url + '" target="_blank" style="color:var(--accent);">查看原始页面 →</a>' : '模拟数据'}</span>
                </div>
            </div>
        `;

        overlay.classList.add('open');
        document.body.style.overflow = 'hidden';
    }

    // 关闭弹窗
    document.addEventListener('DOMContentLoaded', function () {
        var overlay = document.getElementById('lawyer-modal-overlay');
        var closeBtn = document.getElementById('lawyer-modal-close');
        if (!overlay) return;

        function closeModal() {
            overlay.classList.remove('open');
            document.body.style.overflow = '';
        }

        if (closeBtn) closeBtn.addEventListener('click', closeModal);
        overlay.addEventListener('click', function (e) {
            if (e.target === overlay) closeModal();
        });
        document.addEventListener('keydown', function (e) {
            if (e.key === 'Escape') closeModal();
        });
    });

    // 搜索和筛选
    function filterLawyers() {
        var searchTerm = lawyerSearch ? lawyerSearch.value.trim().toLowerCase() : '';
        var province = filterProvince ? filterProvince.value : '';
        var city = filterCity ? filterCity.value : '';
        var district = filterDistrict ? filterDistrict.value : '';
        var firm = filterFirm ? filterFirm.value : '';
        var field = filterField ? filterField.value : '';

        var filtered = lawyersData.filter(function (l) {
            var matchSearch = !searchTerm ||
                l.name.toLowerCase().indexOf(searchTerm) > -1 ||
                (l.firm || '').toLowerCase().indexOf(searchTerm) > -1 ||
                l.fields.some(function (f) { return f.toLowerCase().indexOf(searchTerm) > -1; }) ||
                (l.cases || '').toLowerCase().indexOf(searchTerm) > -1;

            var matchProvince = !province || l.province === province;
            var matchCity = !city || l.city === city;
            var matchDistrict = !district || l.district === district;
            var matchFirm = !firm || l.firm === firm;
            var matchField = !field || l.fields.indexOf(field) > -1;

            return matchSearch && matchProvince && matchCity && matchDistrict && matchFirm && matchField;
        });

        renderLawyers(filtered);
    }

    // 搜索框带防抖，下拉框即时响应
    var searchDebounceTimer = null;
    function debouncedFilterLawyers() {
        if (searchDebounceTimer) clearTimeout(searchDebounceTimer);
        searchDebounceTimer = setTimeout(filterLawyers, 250);
    }

    if (lawyerSearch) lawyerSearch.addEventListener('input', debouncedFilterLawyers);
    if (filterDistrict) filterDistrict.addEventListener('change', filterLawyers);
    if (filterFirm) filterFirm.addEventListener('change', filterLawyers);
    if (filterField) filterField.addEventListener('change', filterLawyers);

    // ============================================================
    //  文书模板
    // ============================================================

    function renderTemplateCategories() {
        const categories = [...new Set(templatesData.map(function (t) { return t.category; }))];
        const catNames = { 'consumer': '消费纠纷', 'labor': '劳动纠纷', 'housing': '住房邻里', 'family': '婚姻家庭' };

        // "全部"按钮
        const allBtn = document.createElement('button');
        allBtn.className = 'filter-btn active';
        allBtn.textContent = '全部';
        allBtn.setAttribute('data-filter', 'all');
        allBtn.addEventListener('click', function () {
            updateFilterActive(this);
            renderTemplates(templatesData);
        });
        templateFilters.appendChild(allBtn);

        // 分类按钮
        categories.forEach(function (cat) {
            const btn = document.createElement('button');
            btn.className = 'filter-btn';
            btn.textContent = catNames[cat] || cat;
            btn.setAttribute('data-filter', cat);
            btn.addEventListener('click', function () {
                updateFilterActive(this);
                const filtered = templatesData.filter(function (t) { return t.category === cat; });
                renderTemplates(filtered);
            });
            templateFilters.appendChild(btn);
        });
    }

    function updateFilterActive(activeBtn) {
        templateFilters.querySelectorAll('.filter-btn').forEach(function (b) { b.classList.remove('active'); });
        activeBtn.classList.add('active');
    }

    function renderTemplates(templates) {
        templateList.innerHTML = '';

        if (templates.length === 0) {
            templateList.innerHTML = '<p class="no-results">暂无该分类的模板</p>';
            return;
        }

        templates.forEach(function (tpl) {
            const card = document.createElement('div');
            card.className = 'template-card';
            card.innerHTML = `
                <span class="tpl-category">${tpl.categoryName}</span>
                <div class="tpl-icon">${tpl.icon}</div>
                <h4>${tpl.name}</h4>
                <p>${tpl.description}</p>
            `;

            card.addEventListener('click', function () {
                // 展开/收起
                const wasExpanded = card.classList.contains('expanded');

                // 收起所有已展开的
                templateList.querySelectorAll('.template-card.expanded').forEach(function (c) {
                    c.classList.remove('expanded');
                    const existingContent = c.querySelector('.template-content-wrapper');
                    if (existingContent) existingContent.remove();
                });

                if (!wasExpanded) {
                    card.classList.add('expanded');

                    const wrapper = document.createElement('div');
                    wrapper.className = 'template-content-wrapper';

                    const content = document.createElement('div');
                    content.className = 'template-content';
                    content.textContent = tpl.content;

                    const copyBtn = document.createElement('button');
                    copyBtn.className = 'copy-btn';
                    copyBtn.textContent = '📋 一键复制全文';
                    copyBtn.addEventListener('click', function (e) {
                        e.stopPropagation();
                        navigator.clipboard.writeText(tpl.content).then(function () {
                            copyBtn.textContent = '✅ 已复制！';
                            copyBtn.classList.add('copied');
                            setTimeout(function () {
                                copyBtn.textContent = '📋 一键复制全文';
                                copyBtn.classList.remove('copied');
                            }, 2000);
                        }).catch(function () {
                            // 降级方案：选中文本
                            const range = document.createRange();
                            range.selectNodeContents(content);
                            const selection = window.getSelection();
                            selection.removeAllRanges();
                            selection.addRange(range);
                            copyBtn.textContent = '⚠️ 请手动 Ctrl+C 复制（已选中全文）';
                        });
                    });

                    wrapper.appendChild(copyBtn);
                    wrapper.appendChild(content);
                    card.appendChild(wrapper);

                    // 滚动到展开的卡片
                    setTimeout(function () {
                        card.scrollIntoView({ behavior: 'smooth', block: 'center' });
                    }, 100);
                }
            });

            templateList.appendChild(card);
        });
    }

    // ============================================================
    //  FAQ 渲染
    // ============================================================
    function renderFAQs() {
        const faqList = document.getElementById('faq-list');
        if (!faqList) return;

        // 使用全局的 knowledgeBase（在 wizard.js 加载后可用）
        // 如果 knowledgeBase 还没加载好，等一会再试
        if (!window.knowledgeBase) {
            // wizard.js 负责加载，这里延迟检测（最多重试5次，共2.5秒）
            if (!renderFAQs._retryCount) renderFAQs._retryCount = 0;
            if (renderFAQs._retryCount < 5) {
                renderFAQs._retryCount++;
                setTimeout(renderFAQs, 500);
            } else {
                faqList.innerHTML = '<p class="no-results">常见问题加载超时，请刷新页面重试</p>';
            }
            return;
        }
        renderFAQs._retryCount = 0;

        const faqs = window.knowledgeBase.faqs;
        if (!faqs || faqs.length === 0) return;

        const catNames = {
            'consumer': '🛒 消费纠纷',
            'labor': '💼 劳动雇佣',
            'housing': '🏠 住房邻里',
            'family': '👨‍👩‍👧 婚姻家庭'
        };

        faqs.forEach(function (faq, index) {
            const item = document.createElement('div');
            item.className = 'faq-item';

            const question = document.createElement('button');
            question.className = 'faq-question';
            question.innerHTML = '<span>' + (catNames[faq.category] || '') + ' | ' + faq.question + '</span>';

            const answer = document.createElement('div');
            answer.className = 'faq-answer';
            answer.innerHTML = '<p>' + faq.answer + '</p>';

            question.addEventListener('click', function () {
                const isOpen = item.classList.contains('open');
                // 关闭其他
                faqList.querySelectorAll('.faq-item.open').forEach(function (f) {
                    f.classList.remove('open');
                });
                if (!isOpen) {
                    item.classList.add('open');
                }
            });

            item.appendChild(question);
            item.appendChild(answer);
            faqList.appendChild(item);
        });
    }

    // ============================================================
    //  律师上传功能（localStorage 持久化）
    // ============================================================
    (function setupUploadFeature() {
        var btnAdd = document.getElementById('btn-add-lawyer');
        var addOverlay = document.getElementById('add-lawyer-overlay');
        var addClose = document.getElementById('add-lawyer-close');
        var addForm = document.getElementById('add-lawyer-form');
        var addMsg = document.getElementById('add-lawyer-msg');

        if (!btnAdd || !addOverlay) return;

        btnAdd.addEventListener('click', function () {
            addOverlay.classList.add('open');
            document.body.style.overflow = 'hidden';
        });

        function closeUpload() {
            addOverlay.classList.remove('open');
            document.body.style.overflow = '';
        }

        if (addClose) addClose.addEventListener('click', closeUpload);
        addOverlay.addEventListener('click', function (e) { if (e.target === addOverlay) closeUpload(); });

        if (addForm) {
            addForm.addEventListener('submit', function (e) {
                e.preventDefault();
                var fd = new FormData(addForm);
                var name = (fd.get('name') || '').trim();
                if (!name) {
                    if (addMsg) { addMsg.style.display = 'block'; addMsg.style.color = '#ef4444'; addMsg.textContent = '请填写律师姓名'; }
                    return;
                }

                var fieldsRaw = (fd.get('fields') || '').trim();
                var fields = fieldsRaw ? fieldsRaw.split(/[,，、]/).map(function (s) { return s.trim(); }).filter(Boolean) : ['民商事'];

                var newLawyer = {
                    id: 0,
                    name: name,
                    firm: (fd.get('firm') || '').trim() || '个体律师',
                    city: (fd.get('city') || '').trim() || '广州',
                    province: '广东',
                    district: (fd.get('district') || '').trim() || '天河区',
                    experience: parseInt(fd.get('experience')) || 0,
                    education: (fd.get('education') || '').trim() || '暂无学历信息',
                    fields: fields,
                    cases: (fd.get('cases') || '').trim() || '暂无案例信息',
                    contact: (fd.get('contact') || '').trim() || '暂无联系方式',
                    photo: (fd.get('photo') || '').trim(),
                    source: (fd.get('source') || '').trim() || '用户上传',
                    profile_url: '', license: '', position: '', languages: '', awards: '',
                };

                // Save to localStorage
                var uploaded = [];
                try { uploaded = JSON.parse(localStorage.getItem('user_uploaded_lawyers') || '[]'); } catch (ex) {}
                uploaded.push(newLawyer);
                try { localStorage.setItem('user_uploaded_lawyers', JSON.stringify(uploaded)); } catch (ex) {}

                // Add to live data + re-render
                lawyersData.push(newLawyer);
                for (var i = 0; i < lawyersData.length; i++) lawyersData[i].id = i + 1;
                renderLawyers(lawyersData);

                addForm.reset();
                if (addMsg) { addMsg.style.display = 'block'; addMsg.style.color = '#6a9b7a'; addMsg.textContent = '✅ ' + name + ' 已成功添加！'; }
                setTimeout(function () { closeUpload(); if (addMsg) addMsg.style.display = 'none'; }, 1500);
            });
        }
    })();

    // ============================================================
    //  启动
    // ============================================================
    init();

})();
