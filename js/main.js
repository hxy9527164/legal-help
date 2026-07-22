/* ============================================================ */
/*  法律自助助手 - 通用交互                                        */
/*  导航、汉堡菜单、入口卡片、平滑滚动                             */
/* ============================================================ */

document.addEventListener('DOMContentLoaded', function () {

    // --- DOM 元素 ---
    const navbar = document.getElementById('navbar');
    const hamburger = document.getElementById('hamburger');
    const navLinksEl = document.querySelector('.nav-links');
    const navAnchors = document.querySelectorAll('.nav-links a');
    const entryCards = document.querySelectorAll('.entry-card');

    // ============================================================
    //  1. 导航栏滚动效果
    // ============================================================
    const allSections = document.querySelectorAll('section[id]');

    function updateNavOnScroll() {
        const scrollY = window.scrollY;

        // 背景加阴影
        if (scrollY > 30) {
            navbar.classList.add('scrolled');
        } else {
            navbar.classList.remove('scrolled');
        }

        // 高亮当前区块对应的导航
        let currentSection = '';
        allSections.forEach(function (section) {
            const sectionTop = section.offsetTop - 150;
            if (scrollY >= sectionTop) {
                currentSection = section.getAttribute('id');
            }
        });

        navAnchors.forEach(function (link) {
            link.classList.remove('active');
            if (link.getAttribute('href') === '#' + currentSection) {
                link.classList.add('active');
            }
        });
    }

    window.addEventListener('scroll', updateNavOnScroll, { passive: true });

    // ============================================================
    //  2. 导航链接平滑滚动
    // ============================================================
    navAnchors.forEach(function (anchor) {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const targetId = this.getAttribute('href').substring(1);
            const target = document.getElementById(targetId);
            if (target) {
                target.scrollIntoView({ behavior: 'smooth' });
                // 手机端关闭菜单
                navLinksEl.classList.remove('open');
                hamburger.classList.remove('active');
            }
        });
    });

    document.querySelector('.nav-logo').addEventListener('click', function (e) {
        e.preventDefault();
        window.scrollTo({ top: 0, behavior: 'smooth' });
    });

    // ============================================================
    //  3. 汉堡菜单
    // ============================================================
    hamburger.addEventListener('click', function () {
        this.classList.toggle('active');
        navLinksEl.classList.toggle('open');
    });

    document.addEventListener('click', function (e) {
        if (!hamburger.contains(e.target) && !navLinksEl.contains(e.target)) {
            navLinksEl.classList.remove('open');
            hamburger.classList.remove('active');
        }
    });

    // ============================================================
    //  4. 首页入口卡片 → 跳转到对应板块
    // ============================================================
    entryCards.forEach(function (card) {
        card.addEventListener('click', function () {
            const targetId = this.getAttribute('data-target');
            if (targetId) {
                const target = document.getElementById(targetId);
                if (target) {
                    target.scrollIntoView({ behavior: 'smooth' });
                }
            }
        });
    });

    // ============================================================
    //  5. 诉讼费计算器
    // ============================================================
    var calcAmount = document.getElementById('calc-amount');
    var calcBtn = document.getElementById('calc-btn');
    var calcFee = document.getElementById('calc-fee');
    var calcType = document.getElementById('calc-type');
    var calcTime = document.getElementById('calc-time');

    function calculateFee(amount) {
        if (!amount || amount <= 0) return { fee: 0, type: '', time: '' };
        var fee;
        if (amount <= 10000) fee = 50;
        else if (amount <= 100000) fee = Math.round(amount * 0.025 - 200);
        else if (amount <= 200000) fee = Math.round(amount * 0.02 + 300);
        else if (amount <= 500000) fee = Math.round(amount * 0.015 + 1300);
        else if (amount <= 1000000) fee = Math.round(amount * 0.01 + 3800);
        else fee = Math.round(amount * 0.005 + 8800);

        var type, time;
        if (amount <= 50000) { type = '小额诉讼'; time = '1-2个月'; }
        else if (amount <= 200000) { type = '简易程序'; time = '3-4个月'; }
        else { type = '普通程序'; time = '6个月左右'; }

        return { fee: fee, type: type, time: time };
    }

    if (calcBtn && calcAmount) {
        calcBtn.addEventListener('click', function () {
            var amount = parseFloat(calcAmount.value);
            if (isNaN(amount) || amount <= 0) {
                calcFee.textContent = '请输入金额';
                calcType.textContent = '—';
                calcTime.textContent = '—';
                return;
            }
            var result = calculateFee(amount);
            calcFee.textContent = result.fee.toLocaleString() + ' 元';
            calcType.textContent = result.type;
            calcTime.textContent = result.time;
        });

        // 回车触发计算
        calcAmount.addEventListener('keydown', function (e) {
            if (e.key === 'Enter') calcBtn.click();
        });
    }

    // ============================================================
    //  6. 法律术语词典渲染
    // ============================================================
    (function renderGlossary() {
        var glossaryGrid = document.getElementById('glossary-grid');
        if (!glossaryGrid) return;

        var terms = [
            { term: '小额诉讼', explain: '法院对5万元以下的简单案件适用的一种快速程序。一审终审（不能上诉），审理周期1-2个月，诉讼费低。非常适合押金、借款、简单合同等小额纠纷。' },
            { term: '仲裁 vs 诉讼', explain: '仲裁是双方约定好由仲裁委员会裁决（如合同中写了"提交XX仲裁委"），一裁终局。诉讼是去法院打官司，可上诉。劳动纠纷必须先仲裁才能诉讼。' },
            { term: '诉讼时效', explain: '你必须在规定时间内起诉，否则法院不再保护你的权利。一般民事纠纷3年，劳动纠纷1年。时效可以"中断"重新计算——每次催对方、对方部分履行，时效重新起算。' },
            { term: '强制执行', explain: '拿到胜诉判决但对方赖着不给钱时，向法院申请"强制执行"。法院可以冻结对方银行账户、查封房产车辆、限制高消费、列入失信名单（老赖）。' },
            { term: '财产保全', explain: '起诉前或起诉时申请法院查封/冻结对方的财产，防止对方转移财产让你赢了官司也拿不到钱。需要提供担保（通常保全金额的30%）。' },
            { term: '举证责任', explain: '谁主张谁举证——你说对方欠你钱，你就要拿出证据。但在某些情况下举证责任会倒置（如医疗纠纷中医院要证明自己无过错）。' },
            { term: '连带责任', explain: '多个责任人中的任何一个都有义务赔偿全部损失，赔了之后可以向其他责任人追偿。比如交通事故中肇事司机和车主可能承担连带责任。' },
            { term: '精神损害赔偿', explain: '人身受到严重伤害或名誉受到严重侵害时，除了赔医疗费/财产损失外，还可以要求赔偿精神损害。一般在几千到几万元不等，特别严重的可以更高。' },
            { term: '代位求偿', explain: '在保险中，如果你的损失是第三方造成的，你的保险公司可以先赔给你，然后保险公司取得你的权利去向第三方追偿。这样你不用自己去找第三方要钱。' },
            { term: '支付令', explain: '比起诉更快更便宜的讨债程序。债权债务清楚、无争议时，向法院申请支付令。法院15天内审查发出，对方15天内不异议就生效可直接强制执行。' },
            { term: 'LPR', explain: '贷款市场报价利率，由央行每月公布。目前1年期LPR约3.45%。法律上很多计算都和LPR挂钩——民间借贷利率上限为LPR的4倍（约13.8%），迟延履行利息按LPR计算。' },
            { term: '格式条款', explain: '商家/公司预先拟定好、你只能选择接受或拒绝的条款（如APP用户协议）。如果格式条款不合理地免除商家责任、加重你的责任、排除你的主要权利，该条款无效。' }
        ];

        terms.forEach(function (t) {
            var item = document.createElement('div');
            item.className = 'glossary-item';
            item.innerHTML = '<h4>' + t.term + '</h4><p>' + t.explain + '</p>';
            glossaryGrid.appendChild(item);
        });
    })();

    // ============================================================
    //  7. 初始状态
    // ============================================================
    updateNavOnScroll();

});
