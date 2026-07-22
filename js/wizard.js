/* ============================================================ */
/*  法律诊断向导引擎                                              */
/*  流程：选领域 → 选场景 → 回答问题 → 生成方案                   */
/* ============================================================ */

(function () {
    'use strict';

    window.knowledgeBase = null;    // 知识库数据（全局暴露，供其他模块使用）
    let selectedCategory = null;    // 当前选中的领域
    let selectedScenario = null;    // 当前选中的场景
    let userAnswers = {};           // 用户回答问题收集

    // DOM 元素
    const wizardSteps = document.getElementById('wizard-steps');
    const categoryGrid = document.getElementById('category-grid');
    const scenarioGrid = document.getElementById('scenario-grid');
    const questionsForm = document.getElementById('questions-form');
    const planResult = document.getElementById('plan-result');

    // Panel 元素
    const panel1 = document.getElementById('panel-step1');
    const panel2 = document.getElementById('panel-step2');
    const panel3 = document.getElementById('panel-step3');
    const panel4 = document.getElementById('panel-step4');

    // Step 标题
    const step2Title = document.getElementById('step2-title');

    // ============================================================
    //  初始化：加载知识库 → 渲染 Step 1 领域卡片
    // ============================================================
    async function init() {
        categoryGrid.innerHTML = '<p class="loading-hint">⏳ 正在加载知识库...</p>';

        try {
            // 优先使用 script 标签注入的全局变量（file:// 100%兼容）
            if (window.__knowledgeBaseData) {
                window.knowledgeBase = window.__knowledgeBaseData;
            } else {
                // 回退：fetch + XHR
                var response = await fetch('data/knowledge-base.json');
                if (!response.ok) throw new Error('HTTP ' + response.status);
                window.knowledgeBase = await response.json();
            }
            renderCategoryCards();
        } catch (err) {
            console.error('加载知识库失败:', err);
            // 最后一次尝试：XHR
            try {
                var xhr = new XMLHttpRequest();
                xhr.open('GET', 'data/knowledge-base.json', false);  // 同步
                xhr.overrideMimeType('application/json');
                xhr.send(null);
                if (xhr.status === 200 || xhr.status === 0) {
                    window.knowledgeBase = JSON.parse(xhr.responseText);
                    renderCategoryCards();
                    return;
                }
            } catch (e2) {}

            categoryGrid.innerHTML = `
                <div class="error-hint">
                    <p>⚠️ 知识库加载失败</p>
                    <p class="error-detail">${err.message || '未知错误'}</p>
                    <button class="btn btn-primary" onclick="location.reload()" style="margin-top:12px;">🔄 重新加载</button>
                </div>`;
        }
    }

    // ---------- 渲染 Step 1: 领域选择 ----------
    function renderCategoryCards() {
        if (!window.knowledgeBase) return;
        categoryGrid.innerHTML = '';

        Object.values(window.knowledgeBase.categories).forEach(function (cat) {
            const card = document.createElement('div');
            card.className = 'category-card';
            card.setAttribute('data-category-id', cat.id);
            card.innerHTML = `
                <div class="cat-icon">${cat.icon}</div>
                <div class="cat-name">${cat.name}</div>
                <div class="cat-desc">${cat.description}</div>
            `;
            card.addEventListener('click', function () {
                selectCategory(cat);
            });
            categoryGrid.appendChild(card);
        });
    }

    // ---------- 选择领域 → 进入 Step 2 ----------
    function selectCategory(cat) {
        selectedCategory = cat;

        // 通过 data 属性精确定位并标记选中
        document.querySelectorAll('.category-card').forEach(function (c) {
            c.classList.remove('selected');
        });
        var selectedCard = document.querySelector('.category-card[data-category-id="' + cat.id + '"]');
        if (selectedCard) selectedCard.classList.add('selected');

        // 延迟切换面板，让选中效果可见
        setTimeout(function () {
            switchPanel(2);
            renderScenarioCards(cat);
        }, 200);
    }

    // ---------- 渲染 Step 2: 场景选择 ----------
    function renderScenarioCards(cat) {
        step2Title.textContent = cat.name + ' - 具体是什么情况？';
        scenarioGrid.innerHTML = '';

        Object.values(cat.scenarios).forEach(function (scenario) {
            const card = document.createElement('div');
            card.className = 'scenario-card';
            card.innerHTML = `
                <h4>${scenario.name}</h4>
                <p>${scenario.description}</p>
            `;
            card.addEventListener('click', function () {
                selectScenario(scenario);
            });
            scenarioGrid.appendChild(card);
        });
    }

    // ---------- 选择场景 → 进入 Step 3 ----------
    function selectScenario(scenario) {
        selectedScenario = scenario;
        userAnswers = {};
        switchPanel(3);
        renderQuestions(scenario);
    }

    // ---------- 渲染 Step 3: 关键问题 ----------
    function renderQuestions(scenario) {
        questionsForm.innerHTML = '';

        scenario.questions.forEach(function (q, index) {
            const group = document.createElement('div');
            group.className = 'form-group';

            let labelHTML = '<label>' + q.label;
            if (q.hint) {
                labelHTML += '<span class="form-hint">（' + q.hint + '）</span>';
            }
            labelHTML += '</label>';
            group.innerHTML = labelHTML;

            if (q.type === 'select') {
                // 下拉选择
                const select = document.createElement('select');
                select.setAttribute('data-qid', q.id);
                select.innerHTML = '<option value="">-- 请选择 --</option>';
                q.options.forEach(function (opt) {
                    select.innerHTML += '<option value="' + opt.value + '">' + opt.label + '</option>';
                });
                select.addEventListener('change', function () {
                    userAnswers[q.id] = this.value;
                });
                group.appendChild(select);

            } else if (q.type === 'radio') {
                // 单选按钮组
                const radioGroup = document.createElement('div');
                radioGroup.className = 'radio-group';
                q.options.forEach(function (opt) {
                    const optEl = document.createElement('div');
                    optEl.className = 'radio-option';
                    optEl.textContent = opt.label;
                    optEl.setAttribute('data-value', opt.value);
                    optEl.addEventListener('click', function () {
                        // 移除同组其他选中
                        radioGroup.querySelectorAll('.radio-option').forEach(function (o) {
                            o.classList.remove('selected');
                        });
                        optEl.classList.add('selected');
                        userAnswers[q.id] = opt.value;
                    });
                    radioGroup.appendChild(optEl);
                });
                group.appendChild(radioGroup);

            } else if (q.type === 'checkbox') {
                // 多选
                userAnswers[q.id] = [];
                const checkboxGroup = document.createElement('div');
                checkboxGroup.className = 'radio-group';
                q.options.forEach(function (opt) {
                    const optEl = document.createElement('div');
                    optEl.className = 'radio-option';
                    optEl.textContent = opt.label;
                    optEl.setAttribute('data-value', opt.value);
                    optEl.addEventListener('click', function () {
                        optEl.classList.toggle('selected');
                        if (optEl.classList.contains('selected')) {
                            userAnswers[q.id].push(opt.value);
                        } else {
                            const arr = userAnswers[q.id];
                            const pos = arr.indexOf(opt.value);
                            if (pos > -1) arr.splice(pos, 1);
                        }
                    });
                    checkboxGroup.appendChild(optEl);
                });
                group.appendChild(checkboxGroup);
            }

            questionsForm.appendChild(group);
        });
    }

    // ============================================================
    //  生成应对方案 → Step 4
    // ============================================================
    document.getElementById('generate-plan').addEventListener('click', function () {
        if (!selectedScenario) return;

        // 简单校验：检查是否有未回答的必填问题
        const unanswered = selectedScenario.questions.filter(function (q) {
            const ans = userAnswers[q.id];
            if (q.type === 'checkbox') {
                return !ans || ans.length === 0;
            }
            return !ans;
        });

        if (unanswered.length > 0) {
            // 滚动到第一个未回答的问题
            const firstUnanswered = unanswered[0];
            const firstGroup = questionsForm.querySelector('[data-qid="' + firstUnanswered.id + '"]');
            if (firstGroup) {
                firstGroup.closest('.form-group').style.borderColor = '#ef4444';
                setTimeout(function () {
                    firstGroup.closest('.form-group').style.borderColor = '';
                }, 2000);
            }
            alert('请回答完所有问题后再生成方案');
            return;
        }

        switchPanel(4);
        renderPlan(selectedScenario);
    });

    // ---------- 渲染 Step 4: 应对方案 ----------
    function renderPlan(scenario) {
        const plan = scenario.plan;
        planResult.innerHTML = '';

        // 标题
        const titleEl = document.createElement('h3');
        titleEl.style.cssText = 'text-align:center;font-size:1.4rem;margin-bottom:28px;color:#fff;';
        titleEl.textContent = '📋 ' + plan.title;
        planResult.appendChild(titleEl);

        // 1. 行动步骤
        const stepsSection = document.createElement('div');
        stepsSection.className = 'plan-section';
        stepsSection.innerHTML = '<h4>📌 立即行动清单</h4>';
        const stepsList = document.createElement('ol');
        stepsList.className = 'plan-steps';
        plan.steps.forEach(function (step) {
            const li = document.createElement('li');
            li.setAttribute('data-step', step.order);
            li.innerHTML = '<strong>' + step.title + '</strong><br>' + step.detail;
            stepsList.appendChild(li);
        });
        stepsSection.appendChild(stepsList);
        planResult.appendChild(stepsSection);

        // 2. 涉及法律条文
        const lawsSection = document.createElement('div');
        lawsSection.className = 'plan-section';
        lawsSection.innerHTML = '<h4>📄 涉及法律条文（白话解读）</h4>';
        plan.laws.forEach(function (law) {
            const tag = document.createElement('span');
            tag.className = 'plan-tag law';
            tag.textContent = law.name;
            lawsSection.appendChild(tag);
            const explainP = document.createElement('p');
            explainP.style.cssText = 'color:#94a3b8;font-size:0.88rem;margin:8px 0 0 0;line-height:1.7;';
            explainP.textContent = '💡 ' + law.explain;
            lawsSection.appendChild(explainP);
            lawsSection.appendChild(document.createElement('br'));
        });
        planResult.appendChild(lawsSection);

        // 3. 常见陷阱
        const pitfallsSection = document.createElement('div');
        pitfallsSection.className = 'plan-section';
        pitfallsSection.innerHTML = '<h4>⚠️ 常见陷阱提醒</h4>';
        plan.pitfalls.forEach(function (pit) {
            const tag = document.createElement('span');
            tag.className = 'plan-tag warn';
            tag.textContent = '❌ ' + pit.title;
            pitfallsSection.appendChild(tag);
            const p = document.createElement('p');
            p.style.cssText = 'color:#94a3b8;font-size:0.88rem;margin:6px 0 0 0;line-height:1.7;';
            p.textContent = pit.detail;
            pitfallsSection.appendChild(p);
            pitfallsSection.appendChild(document.createElement('br'));
        });
        planResult.appendChild(pitfallsSection);

        // 4. 相关机构联系方式
        const contactsSection = document.createElement('div');
        contactsSection.className = 'plan-section';
        contactsSection.innerHTML = '<h4>🔗 相关机构联系方式</h4>';
        const contactsList = document.createElement('ul');
        contactsList.className = 'plan-contacts';
        plan.contacts.forEach(function (c) {
            const li = document.createElement('li');
            li.innerHTML = '<strong>' + c.name + '</strong>：' + c.detail;
            contactsList.appendChild(li);
        });
        contactsSection.appendChild(contactsList);
        planResult.appendChild(contactsSection);

        // 5. 推荐律师类型
        const lawyerSection = document.createElement('div');
        lawyerSection.className = 'plan-section';
        lawyerSection.innerHTML = '<h4>👨‍⚖️ 推荐律师类型</h4>';
        const lawyerTag = document.createElement('span');
        lawyerTag.className = 'plan-tag good';
        lawyerTag.textContent = '✅ ' + plan.lawyerType;
        lawyerSection.appendChild(lawyerTag);
        const lawyerP = document.createElement('p');
        lawyerP.style.cssText = 'color:#94a3b8;font-size:0.85rem;margin-top:10px;';
        lawyerP.innerHTML = '在 <a href="#lawyer-section" style="color:#3b82f6;">查找律师</a> 板块中搜索对应领域的律师。';
        lawyerSection.appendChild(lawyerP);
        planResult.appendChild(lawyerSection);

        // 6. 相关文书模板链接
        if (plan.templateIds && plan.templateIds.length > 0) {
            const tplSection = document.createElement('div');
            tplSection.className = 'plan-section';
            tplSection.innerHTML = '<h4>📝 推荐使用的文书模板</h4>';

            const tplList = document.createElement('div');
            tplList.style.cssText = 'display:flex;flex-wrap:wrap;gap:8px;margin-top:8px;';

            // 尝试从全局模板数据中查找模板名称
            const allTemplates = window.templatesData || [];
            plan.templateIds.forEach(function (tplId) {
                const tpl = allTemplates.find(function (t) { return t.id === tplId; });
                const tag = document.createElement('span');
                if (tpl) {
                    tag.className = 'plan-tag law';
                    tag.style.cssText = 'cursor:pointer;padding:8px 14px;font-size:0.82rem;';
                    tag.textContent = tpl.icon + ' ' + tpl.name;
                    tag.title = tpl.description;
                    tag.addEventListener('click', function () {
                        // 滚动到模板区并筛选该分类
                        document.getElementById('template-section').scrollIntoView({ behavior: 'smooth' });
                        // 触发对应分类按钮点击
                        setTimeout(function () {
                            const btns = document.querySelectorAll('#template-filters .filter-btn');
                            btns.forEach(function (btn) {
                                if (btn.getAttribute('data-filter') === tpl.category) {
                                    btn.click();
                                }
                            });
                        }, 400);
                    });
                } else {
                    tag.className = 'plan-tag law';
                    tag.textContent = '📋 ' + tplId;
                }
                tplList.appendChild(tag);
            });

            tplSection.appendChild(tplList);

            const tplHint = document.createElement('p');
            tplHint.style.cssText = 'color:#94a3b8;font-size:0.8rem;margin-top:12px;';
            tplHint.textContent = '👆 点击标签可跳转到文书模板区并自动筛选';
            tplSection.appendChild(tplHint);

            planResult.appendChild(tplSection);
        }

        // 滚动到方案顶部
        planResult.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }

    // ============================================================
    //  面板切换 + 步骤指示器更新
    // ============================================================
    function switchPanel(stepNum) {
        // 隐藏所有面板
        [panel1, panel2, panel3, panel4].forEach(function (p) { p.classList.remove('active'); });

        // 显示目标面板
        const targetPanel = document.getElementById('panel-step' + stepNum);
        if (targetPanel) targetPanel.classList.add('active');

        // 更新步骤指示器
        const steps = wizardSteps.querySelectorAll('.w-step');
        steps.forEach(function (step) {
            const s = parseInt(step.getAttribute('data-step'));
            step.classList.remove('active', 'done');
            if (s === stepNum) step.classList.add('active');
            if (s < stepNum) step.classList.add('done');
        });

        // 滚动到向导顶部
        document.getElementById('wizard-section').scrollIntoView({ behavior: 'smooth', block: 'start' });
    }

    // ============================================================
    //  返回按钮事件
    // ============================================================
    document.getElementById('back-to-step1').addEventListener('click', function () {
        selectedCategory = null;
        selectedScenario = null;
        userAnswers = {};
        document.querySelectorAll('.category-card').forEach(function (c) { c.classList.remove('selected'); });
        switchPanel(1);
    });

    document.getElementById('back-to-step2').addEventListener('click', function () {
        selectedScenario = null;
        userAnswers = {};
        switchPanel(2);
    });

    document.getElementById('back-to-step1-bottom').addEventListener('click', function () {
        selectedCategory = null;
        selectedScenario = null;
        userAnswers = {};
        document.querySelectorAll('.category-card').forEach(function (c) { c.classList.remove('selected'); });
        switchPanel(1);
    });

    // ============================================================
    //  启动
    // ============================================================
    init();

})();
