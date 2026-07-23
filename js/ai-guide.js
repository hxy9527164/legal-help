/* ============================================================ */
/*  AI维权指导 — 用户描述案件 → AI大白话维权步骤                     */
/*  使用硅基流动 DeepSeek-V3，支持流式输出（打字机效果）             */
/* ============================================================ */
(function () {
    'use strict';

    var API_KEY = 'sk-wbtzxngfywxeetfscvfqfjzlbdaiptwliceyqgnhmrslvlqd';
    var API_URL = 'https://api.siliconflow.cn/v1/chat/completions';

    // DOM
    var caseInput, analyzeBtn, outputArea, outputFooter, keyModal, keyInput, keySaveBtn, copyBtn;
    var isGenerating = false;
    var abortController = null;

    // ============================================================
    //  System Prompt
    // ============================================================
    var SYSTEM_PROMPT = [
        '你是一位资深的法律顾问，擅长用通俗易懂的大白话为普通人解释法律问题和维权方法。',
        '用户会描述他们遇到的法律纠纷，请严格按照以下结构给出分析：',
        '',
        '## 📋 案情梳理',
        '用一两句话概括用户遇到的情况，让用户确认你理解对了。',
        '',
        '## ⚖️ 涉及的法律问题',
        '列出可能涉及的法律关系（合同纠纷、侵权、劳动纠纷、消费维权等），每种用一句话说明。',
        '',
        '## 🔢 维权步骤（按先后顺序编号）',
        '每个步骤包含：做什么 → 找谁 → 怎么说/怎么做 → 预期结果',
        '优先推荐协商、投诉等低成本方式，诉讼作为最后手段',
        '每个步骤要给出具体可操作的做法，比如"拨打12315时说：我在XX超市买了过期食品……"',
        '',
        '## 📸 需要准备的证据',
        '列出所有需要收集的证据类型，标注哪些是最关键的、哪些是辅助的',
        '说明每种证据的收集方法和注意事项',
        '',
        '## ⚠️ 注意事项和常见陷阱',
        '提醒用户维权过程中容易犯的错误、对方可能用的套路、时效问题等',
        '',
        '## 📖 相关法律条文',
        '列出适用的法律名称和条款编号，简要说明每条如何适用到这个案件',
        '',
        '重要原则：',
        '- 全程使用口语化中文，像朋友在帮你分析问题，不要用"贵方""兹""鉴于"等文书用语',
        '- 每个建议都要给出具体可操作的做法，不要说"建议咨询律师"这种空话',
        '- 如果你对某些细节不确定，要诚实说明并建议就该点咨询当地律师',
        '- 开头先写"根据你的描述，我帮你分析如下："作为过渡',
        '- 使用 Markdown 格式组织内容，让排版清晰易读'
    ].join('\n');

    // ============================================================
    //  初始化
    // ============================================================
    function init() {
        caseInput = document.getElementById('ai-case-input');
        analyzeBtn = document.getElementById('ai-analyze-btn');
        outputArea = document.getElementById('ai-output-area');
        keyModal = document.getElementById('ai-key-modal');
        keyInput = document.getElementById('ai-key-input');
        keySaveBtn = document.getElementById('ai-key-save');
        copyBtn = document.getElementById('ai-copy-btn');
        outputFooter = document.getElementById('ai-output-footer');

        // 恢复已保存的API Key
        try {
            var saved = localStorage.getItem('siliconflow_api_key');
            if (saved) API_KEY = saved;
        } catch (e) {}

        // 首次使用引导
        if (keyModal && !localStorage.getItem('ai_key_confirmed')) {
            setTimeout(function () {
                keyModal.classList.add('open');
                if (keyInput) keyInput.value = API_KEY;
            }, 800);
        }

        // 绑定事件
        if (analyzeBtn) analyzeBtn.addEventListener('click', handleAnalyze);
        if (keySaveBtn) keySaveBtn.addEventListener('click', saveApiKey);
        if (copyBtn) copyBtn.addEventListener('click', copyOutput);

        // 关闭Key弹窗
        if (keyModal) {
            keyModal.addEventListener('click', function (e) {
                if (e.target === keyModal) {
                    keyModal.classList.remove('open');
                    document.body.style.overflow = '';
                }
            });
        }

        // 回车提交
        if (caseInput) {
            caseInput.addEventListener('keydown', function (e) {
                if (e.key === 'Enter' && e.ctrlKey) {
                    handleAnalyze();
                }
            });
        }
    }

    // ============================================================
    //  保存API Key
    // ============================================================
    function saveApiKey() {
        var newKey = keyInput ? keyInput.value.trim() : '';
        if (newKey) {
            API_KEY = newKey;
            try {
                localStorage.setItem('siliconflow_api_key', newKey);
                localStorage.setItem('ai_key_confirmed', '1');
            } catch (e) {}
        }
        if (keyModal) {
            keyModal.classList.remove('open');
            document.body.style.overflow = '';
        }
    }

    // ============================================================
    //  开始分析
    // ============================================================
    function handleAnalyze() {
        if (isGenerating) return;

        var userInput = caseInput ? caseInput.value.trim() : '';
        if (!userInput) {
            showError('请先描述你遇到的法律问题');
            return;
        }
        if (userInput.length < 10) {
            showError('请至少输入10个字描述你的情况，越详细AI分析越准确');
            return;
        }

        // 显示输出区
        if (outputArea) {
            outputArea.style.display = 'block';
            outputArea.innerHTML =
                '<div class="ai-typing-indicator">' +
                    '<span class="ai-typing-dot"></span>' +
                    '<span class="ai-typing-dot"></span>' +
                    '<span class="ai-typing-dot"></span>' +
                    '<span class="ai-typing-label">AI正在分析你的案件...</span>' +
                '</div>';
        }

        if (analyzeBtn) {
            analyzeBtn.disabled = true;
            analyzeBtn.textContent = '⏳ 分析中...';
        }
        if (copyBtn) copyBtn.style.display = 'none';
        if (outputFooter) outputFooter.style.display = 'none';

        isGenerating = true;

        // 使用 AbortController 支持取消
        abortController = new AbortController();

        callSiliconFlowStream(
            [
                { role: 'system', content: SYSTEM_PROMPT },
                { role: 'user', content: userInput }
            ],
            function (chunk) {
                // 收到第一个chunk时清除typing indicator
                if (outputArea && outputArea.querySelector('.ai-typing-indicator')) {
                    outputArea.innerHTML = '<div class="ai-output-content" id="ai-output-content"></div>';
                }
                var contentDiv = document.getElementById('ai-output-content');
                if (contentDiv) {
                    contentDiv.textContent += chunk;
                    // 自动滚动到底部
                    contentDiv.scrollTop = contentDiv.scrollHeight;
                }
            },
            function (error) {
                // 完成/出错
                isGenerating = false;
                abortController = null;
                if (analyzeBtn) {
                    analyzeBtn.disabled = false;
                    analyzeBtn.textContent = '🚀 开始分析';
                }

                if (error) {
                    // 错误：追加错误信息到已有输出，或单独显示
                    var existingContent = document.getElementById('ai-output-content');
                    if (existingContent) {
                        existingContent.innerHTML += '\n\n---\n<span style="color:#c97a6a;">⚠️ ' + escapeHTML(error) + '</span>';
                        if (copyBtn) copyBtn.style.display = 'inline-block';
                    } else {
                        outputArea.innerHTML = '<div class="ai-output-content"><p style="color:#c97a6a;">⚠️ ' + escapeHTML(error) + '</p></div>';
                    }
                    if (outputFooter) outputFooter.style.display = 'flex';
                } else {
                    // 流式完成，渲染结构化输出
                    finalizeOutput();
                }
            },
            abortController.signal
        );
    }

    // ============================================================
    //  流式API调用（SSE解析）
    // ============================================================
    function callSiliconFlowStream(messages, onChunk, onDone, signal) {
        var xhr = new XMLHttpRequest();
        xhr.open('POST', API_URL, true);
        xhr.setRequestHeader('Content-Type', 'application/json');
        xhr.setRequestHeader('Authorization', 'Bearer ' + API_KEY);
        xhr.setRequestHeader('Accept', 'text/event-stream');
        xhr.timeout = 120000;

        var lastIndex = 0;
        var buffer = '';
        var streamedSomething = false;  // 追踪是否已有流式输出

        xhr.onprogress = function () {
            parseStreamChunk(xhr.responseText.substring(lastIndex));
            lastIndex = xhr.responseText.length;
        };

        xhr.onload = function () {
            // 兜底：如果 onprogress 没触发（某些浏览器），从完整响应解析
            var remaining = xhr.responseText.substring(lastIndex);
            if (remaining) parseStreamChunk(remaining);

            // 处理剩余buffer
            if (buffer.trim()) {
                var remainingLines = buffer.split('\n');
                for (var i = 0; i < remainingLines.length; i++) {
                    parseSSELine(remainingLines[i]);
                }
            }

            if (xhr.status === 200) {
                if (!streamedSomething) {
                    // 非流式响应兜底：尝试解析为普通JSON
                    try {
                        var data = JSON.parse(xhr.responseText);
                        var text = data.choices && data.choices[0] && data.choices[0].message
                            ? data.choices[0].message.content
                            : '';
                        if (text) {
                            onChunk(text);
                            streamedSomething = true;
                        }
                    } catch (e) {}
                }
                onDone(null);
            } else {
                var errMsg = '请求失败 (HTTP ' + xhr.status + ')';
                try {
                    var errData = JSON.parse(xhr.responseText);
                    if (errData.error && errData.error.message) errMsg = errData.error.message;
                } catch (e) {}
                onDone(errMsg);
            }
        };

        function parseStreamChunk(newData) {
            if (!newData) return;
            buffer += newData;
            var lines = buffer.split('\n');
            buffer = lines.pop() || '';
            for (var i = 0; i < lines.length; i++) {
                parseSSELine(lines[i]);
            }
        }

        function parseSSELine(line) {
            var trimmed = line.trim();
            if (!trimmed || !trimmed.startsWith('data: ')) return;

            var dataStr = trimmed.substring(6);
            if (dataStr === '[DONE]') return;

            try {
                var data = JSON.parse(dataStr);
                var delta = data.choices && data.choices[0] && data.choices[0].delta;
                if (delta && delta.content) {
                    onChunk(delta.content);
                    streamedSomething = true;
                }
            } catch (e) {
                // 跳过解析失败的行
            }
        }

        xhr.onerror = function () {
            if (signal && signal.aborted) {
                onDone('已取消');
            } else {
                onDone('网络连接失败，请检查网络后重试');
            }
        };

        xhr.ontimeout = function () {
            onDone('请求超时（120秒），你的案件可能比较复杂，尝试分段描述或缩短输入');
        };

        if (signal) {
            signal.addEventListener('abort', function () {
                xhr.abort();
            });
        }

        xhr.send(JSON.stringify({
            model: 'deepseek-ai/DeepSeek-V3',
            messages: messages,
            temperature: 0.7,
            max_tokens: 4096,
            stream: true
        }));
    }

    // ============================================================
    //  流式完成后——渲染为结构化HTML
    // ============================================================
    function finalizeOutput() {
        var contentDiv = document.getElementById('ai-output-content');
        var rawText = contentDiv ? (contentDiv.textContent || '') : '';

        // 空响应降级
        if (!contentDiv || rawText.trim().length < 10) {
            outputArea.innerHTML = '<div class="ai-output-content"><p style="color:var(--text-secondary);text-align:center;padding:40px;">AI 未返回有效内容，请尝试更详细地描述你的问题后重试。</p></div>';
            if (outputFooter) outputFooter.style.display = 'flex';
            return;
        }

        // 将Markdown转换为结构化HTML
        var html = markdownToHTML(rawText);

        outputArea.innerHTML = '<div class="ai-output-content">' + html + '</div>';

        // 显示底部操作栏
        if (outputFooter) outputFooter.style.display = 'flex';
        if (copyBtn && rawText.trim().length > 20) {
            copyBtn.style.display = 'inline-block';
        }
    }

    // ============================================================
    //  简易Markdown→HTML（处理AI输出的章节结构）
    // ============================================================
    function markdownToHTML(text) {
        var html = '';
        var lines = text.split('\n');
        var inList = false;
        var inNumberedList = false;

        for (var i = 0; i < lines.length; i++) {
            var line = lines[i];

            // ## 标题
            if (/^##\s+/.test(line)) {
                if (inList) { html += '</ul>'; inList = false; }
                if (inNumberedList) { html += '</ol>'; inNumberedList = false; }
                var title = line.replace(/^##\s+/, '');
                html += '<div class="ai-step-title">' + escapeHTML(title) + '</div>';
                continue;
            }

            // **粗体**
            line = line.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');

            // 编号列表 1. 2. 3.
            if (/^\d+[\.\、\)]\s+/.test(line)) {
                if (!inNumberedList) {
                    if (inList) { html += '</ul>'; inList = false; }
                    html += '<ol class="ai-numbered-list">';
                    inNumberedList = true;
                }
                var item = line.replace(/^\d+[\.\、\)]\s+/, '');
                html += '<li>' + item + '</li>';
                continue;
            }

            // 短横列表 -
            if (/^-\s+/.test(line)) {
                if (inNumberedList) { html += '</ol>'; inNumberedList = false; }
                if (!inList) {
                    html += '<ul class="ai-bullet-list">';
                    inList = true;
                }
                var bulletItem = line.replace(/^-\s+/, '');
                html += '<li>' + bulletItem + '</li>';
                continue;
            }

            // 普通段落
            if (inNumberedList) { html += '</ol>'; inNumberedList = false; }
            if (inList) { html += '</ul>'; inList = false; }

            if (line.trim() === '') {
                html += '<br>';
            } else {
                html += '<p>' + line + '</p>';
            }
        }

        if (inNumberedList) html += '</ol>';
        if (inList) html += '</ul>';

        return html;
    }

    // ============================================================
    //  复制输出全文
    // ============================================================
    function copyOutput() {
        var contentDiv = outputArea ? outputArea.querySelector('.ai-output-content') : null;
        if (!contentDiv) return;

        var text = contentDiv.textContent || '';
        navigator.clipboard.writeText(text).then(function () {
            if (copyBtn) {
                copyBtn.textContent = '✅ 已复制全文';
                copyBtn.classList.add('copied');
                setTimeout(function () {
                    copyBtn.textContent = '📋 复制全文';
                    copyBtn.classList.remove('copied');
                }, 2000);
            }
        }).catch(function () {
            // 降级
            var range = document.createRange();
            range.selectNodeContents(contentDiv);
            var sel = window.getSelection();
            sel.removeAllRanges();
            sel.addRange(range);
            if (copyBtn) {
                copyBtn.textContent = '⚠️ 请手动 Ctrl+C';
                setTimeout(function () { copyBtn.textContent = '📋 复制全文'; }, 2000);
            }
        });
    }

    // ============================================================
    //  显示错误
    // ============================================================
    function showError(msg) {
        if (outputArea) {
            outputArea.style.display = 'block';
            outputArea.innerHTML =
                '<div class="error-hint"><p>⚠️ ' + escapeHTML(msg) + '</p></div>';
        }
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
    //  启动
    // ============================================================
    document.addEventListener('DOMContentLoaded', init);

})();
