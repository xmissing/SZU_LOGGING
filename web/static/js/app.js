// ==================== 全局状态 ====================
let currentTab = "all";
let dateFilter = "all"; // all | today | week | month
let crawlerResults = [];
let mysqlEnabled = false;
let pollTimer = null;
let schedulerPollTimer = null;

// ==================== 初始化 ====================
document.addEventListener("DOMContentLoaded", () => {
    loadConfig();
    loadSchedulerConfig();
    bindTableEvents();
    bindEmailInputListeners();
});

// 表格行点击事件委托（处理详情查看）
function bindTableEvents() {
    const tbody = document.getElementById("tableBody");
    tbody.addEventListener("click", (e) => {
        const link = e.target.closest(".detail-link");
        if (!link) return;
        const tr = link.closest("tr");
        if (!tr) return;
        const id = tr.getAttribute("data-id");
        if (id) showDetail(id);
    });
}

// ==================== API 封装 ====================
async function api(url, options = {}) {
    const resp = await fetch(url, {
        headers: { "Content-Type": "application/json" },
        ...options,
    });
    const data = await resp.json();
    if (!resp.ok) {
        throw new Error(data.error || "请求失败");
    }
    return data;
}

// ==================== 配置加载 ====================
async function loadConfig() {
    try {
        const config = await api("/api/config");

        // 填充搜索表单
        document.getElementById("account").value = config.account || "";
        document.getElementById("keyword").value = config.keyword || "";

        // 填充时间范围下拉
        const timeSelect = document.getElementById("timeRange");
        timeSelect.innerHTML = "";
        (config.time_ranges || []).forEach(r => {
            const opt = document.createElement("option");
            opt.value = r.value;
            opt.textContent = r.label;
            if (r.value === config.time_range) opt.selected = true;
            timeSelect.appendChild(opt);
        });

        // 填充邮件模式下拉
        const modeSelect = document.getElementById("emailSendMode");
        modeSelect.innerHTML = "";
        const modes = config.email_send_modes || {};
        Object.entries(modes).forEach(([key, label]) => {
            const opt = document.createElement("option");
            opt.value = key;
            opt.textContent = label;
            if (key === config.email_send_mode) opt.selected = true;
            modeSelect.appendChild(opt);
        });

        // 记录数据库状态，后续用于优先查询数据库
        mysqlEnabled = Boolean(config.mysql_enabled);

        // 填充数据库弹窗
        document.getElementById("dbEnabled").checked = mysqlEnabled;
        document.getElementById("dbHost").value = config.mysql_host || "localhost";
        document.getElementById("dbPort").value = config.mysql_port || 3306;
        document.getElementById("dbUser").value = config.mysql_user || "root";
        document.getElementById("dbPassword").value = config.mysql_password || "";
        document.getElementById("dbName").value = config.mysql_database || "szu_board";

        // 填充邮箱弹窗
        document.getElementById("emailEnabled").checked = config.email_enabled;
        document.getElementById("senderEmail").value = config.sender_email || "";
        document.getElementById("senderPassword").value = config.sender_password || "";
        document.getElementById("receiverEmail").value = config.receiver_email || "";

        // 根据邮箱启用状态控制下拉
        updateEmailModeSelect();
    } catch (e) {
        showToast("加载配置失败：" + e.message, "error");
    }
}

function updateEmailModeSelect() {
    const enabled = document.getElementById("emailEnabled").checked;
    const senderEmail = document.getElementById("senderEmail").value.trim();
    const senderPassword = document.getElementById("senderPassword").value.trim();
    const receiverEmail = document.getElementById("receiverEmail").value.trim();
    const modeSelect = document.getElementById("emailSendMode");

    const hasEmailConfig = enabled && senderEmail && senderPassword && receiverEmail;

    if (!hasEmailConfig) {
        modeSelect.disabled = true;
        modeSelect.innerHTML = "";
        const opt = document.createElement("option");
        opt.value = "none";
        opt.textContent = "请先在邮箱配置中填写邮箱信息";
        modeSelect.appendChild(opt);
    } else {
        modeSelect.disabled = false;
        // 重新填充选项
        const currentVal = modeSelect.value;
        modeSelect.innerHTML = "";
        const modes = { "none": "不发送", "new_only": "仅发送新数据", "all": "发送全部数据" };
        Object.entries(modes).forEach(([key, label]) => {
            const opt = document.createElement("option");
            opt.value = key;
            opt.textContent = label;
            if (key === currentVal) opt.selected = true;
            modeSelect.appendChild(opt);
        });
    }
}

// ==================== 弹窗控制 ====================
function openModal(id) {
    document.getElementById(id).classList.add("show");
}

function closeModal(id) {
    document.getElementById(id).classList.remove("show");
}

function closeModalOnOverlay(event, id) {
    if (event.target === event.currentTarget) {
        closeModal(id);
    }
}

function openDbModal() {
    openModal("dbModal");
}

function openEmailModal() {
    openModal("emailModal");
    updateEmailModeSelect();
}

function openSchedulerModal() {
    openModal("schedulerModal");
    loadSchedulerConfig();
}

function updateSchedulerEmailModeSelect() {
    const modeSelect = document.getElementById("schedulerEmailMode");
    const enabled = document.getElementById("emailEnabled").checked;
    const senderEmail = document.getElementById("senderEmail").value.trim();
    const senderPassword = document.getElementById("senderPassword").value.trim();
    const receiverEmail = document.getElementById("receiverEmail").value.trim();

    const hasEmailConfig = enabled && senderEmail && senderPassword && receiverEmail;

    if (!hasEmailConfig) {
        modeSelect.disabled = true;
        modeSelect.innerHTML = "";
        const opt = document.createElement("option");
        opt.value = "none";
        opt.textContent = "请先在邮箱配置中填写邮箱信息";
        modeSelect.appendChild(opt);
    } else {
        modeSelect.disabled = false;
        const currentVal = modeSelect.value;
        modeSelect.innerHTML = "";
        const modes = { "none": "不发送", "new_only": "仅发送新数据", "all": "发送全部数据" };
        Object.entries(modes).forEach(([key, label]) => {
            const opt = document.createElement("option");
            opt.value = key;
            opt.textContent = label;
            if (key === currentVal) opt.selected = true;
            modeSelect.appendChild(opt);
        });
    }
}

async function refreshSchedulerStatus() {
    try {
        const data = await api("/api/scheduler");
        updateSchedulerDisplay(data);
    } catch (e) {
        console.error("刷新定时任务状态失败:", e);
    }
}

// 邮箱配置输入变化时实时更新邮件模式下拉
function bindEmailInputListeners() {
    ["emailEnabled", "senderEmail", "senderPassword", "receiverEmail"].forEach(id => {
        const el = document.getElementById(id);
        if (el) {
            el.addEventListener("input", updateEmailModeSelect);
            el.addEventListener("change", updateEmailModeSelect);
        }
    });
}

// ==================== 保存配置 ====================
async function saveDbConfig() {
    const data = {
        mysql_enabled: document.getElementById("dbEnabled").checked,
        mysql_host: document.getElementById("dbHost").value.trim(),
        mysql_port: parseInt(document.getElementById("dbPort").value) || 3306,
        mysql_user: document.getElementById("dbUser").value.trim(),
        mysql_password: document.getElementById("dbPassword").value.trim(),
        mysql_database: document.getElementById("dbName").value.trim(),
    };
    try {
        await api("/api/config", {
            method: "POST",
            body: JSON.stringify(data),
        });
        mysqlEnabled = data.mysql_enabled;
        showToast("数据库配置已保存", "success");
        closeModal("dbModal");
    } catch (e) {
        showToast("保存失败：" + e.message, "error");
    }
}

async function testDbConnection() {
    const data = {
        host: document.getElementById("dbHost").value.trim() || "localhost",
        port: parseInt(document.getElementById("dbPort").value) || 3306,
        user: document.getElementById("dbUser").value.trim() || "root",
        password: document.getElementById("dbPassword").value.trim(),
        database: document.getElementById("dbName").value.trim() || "szu_board",
    };
    const btn = document.getElementById("testDbBtn");
    const oldText = btn.textContent;
    btn.disabled = true;
    btn.textContent = "测试中...";
    try {
        const resp = await api("/api/database/test", {
            method: "POST",
            body: JSON.stringify(data),
        });
        if (resp.ok) {
            showToast("✅ 数据库连接成功", "success");
        } else {
            showToast("❌ 连接失败：" + resp.error, "error");
        }
    } catch (e) {
        showToast("❌ 连接失败：" + e.message, "error");
    } finally {
        btn.disabled = false;
        btn.textContent = oldText;
    }
}

async function saveEmailConfig() {
    const data = {
        email_enabled: document.getElementById("emailEnabled").checked,
        sender_email: document.getElementById("senderEmail").value.trim(),
        sender_password: document.getElementById("senderPassword").value.trim(),
        receiver_email: document.getElementById("receiverEmail").value.trim(),
    };
    try {
        await api("/api/config", {
            method: "POST",
            body: JSON.stringify(data),
        });
        updateEmailModeSelect();
        showToast("邮箱配置已保存", "success");
        closeModal("emailModal");
    } catch (e) {
        showToast("保存失败：" + e.message, "error");
    }
}

// ==================== 数据库优先查询 ====================
async function loadDatabaseResults(keyword, timeRange) {
    if (!mysqlEnabled) return false;

    const params = new URLSearchParams();
    if (keyword) params.set("keyword", keyword);
    if (timeRange) params.set("time_range", timeRange);

    const result = await api(`/api/data/search?${params.toString()}`);
    const rows = (result.data || []).map(item => ({
        ...item,
        is_new: false,
    }));

    if (rows.length > 0) {
        crawlerResults = rows;
        renderData();
        appendLog(`数据库优先查询完成，找到 ${rows.length} 条已存公告`);
        return true;
    }

    appendLog("数据库优先查询完成，暂无匹配的已存公告，将继续访问官网抓取");
    return false;
}

function appendLog(message) {
    const consoleEl = document.getElementById("logConsole");
    if (!consoleEl) return;
    const div = document.createElement("div");
    div.innerHTML = `<span class="log-time">[${new Date().toLocaleTimeString("zh-CN", { hour12: false })}]</span> <span class="log-msg">${escapeHtml(message)}</span>`;
    consoleEl.appendChild(div);
    consoleEl.scrollTop = consoleEl.scrollHeight;
}

// ==================== 运行爬虫 ====================
async function runCrawler() {
    const account = document.getElementById("account").value.trim();
    const password = document.getElementById("password").value.trim();
    const keyword = document.getElementById("keyword").value.trim();
    const timeRange = document.getElementById("timeRange").value;
    const emailSendMode = document.getElementById("emailSendMode").value;

    if (!account || !password) {
        showToast("账号和密码为必填项", "error");
        return;
    }

    const runBtn = document.getElementById("runBtn");
    runBtn.disabled = true;
    runBtn.innerHTML = '<span class="spinner"></span> 运行中...';

    // 显示日志区
    document.getElementById("logSection").style.display = "";
    document.getElementById("logConsole").innerHTML = "";
    setLogStatus("running", "运行中...");

    // 数据库启用时先查本地，命中后不重复访问官网；未命中才启动爬虫
    if (mysqlEnabled) {
        try {
            const found = await loadDatabaseResults(keyword, timeRange);
            if (found) {
                runBtn.disabled = false;
                runBtn.innerHTML = "🚀 运行爬虫";
                setLogStatus("success", "数据库查询完成");
                showToast(`数据库查询完成，共 ${crawlerResults.length} 条公告`, "success");
                return;
            }
        } catch (e) {
            appendLog(`数据库查询失败，将继续抓取：${e.message}`);
        }
    }

    // 隐藏旧数据，准备接收官网抓取结果
    document.getElementById("dataSection").style.display = "none";

    try {
        await api("/api/crawler/run", {
            method: "POST",
            body: JSON.stringify({
                account, password, keyword, time_range: timeRange,
                email_send_mode: emailSendMode,
            }),
        });
        showToast("爬虫已启动", "info");
        startPolling();
    } catch (e) {
        showToast(e.message, "error");
        runBtn.disabled = false;
        runBtn.innerHTML = "🚀 运行爬虫";
        setLogStatus("error", "启动失败");
    }
}

// ==================== 轮询状态 ====================
function startPolling() {
    if (pollTimer) clearInterval(pollTimer);
    pollTimer = setInterval(checkStatus, 1000);
}

async function checkStatus() {
    try {
        const status = await api("/api/crawler/status");

        // 渲染日志
        const consoleEl = document.getElementById("logConsole");
        const existingCount = consoleEl.children.length;
        const logs = status.logs || [];

        for (let i = existingCount; i < logs.length; i++) {
            const log = logs[i];
            const div = document.createElement("div");
            const msgClass = log.message.includes("失败") || log.message.includes("出错") || log.message.includes("❌") ? "error" :
                             log.message.includes("完成") || log.message.includes("新增") || log.message.includes("✅") ? "success" : "";
            div.innerHTML = `<span class="log-time">[${log.time}]</span> <span class="log-msg ${msgClass}">${escapeHtml(log.message)}</span>`;
            consoleEl.appendChild(div);
        }
        consoleEl.scrollTop = consoleEl.scrollHeight;

        if (!status.running) {
            clearInterval(pollTimer);
            pollTimer = null;

            const runBtn = document.getElementById("runBtn");
            runBtn.disabled = false;
            runBtn.innerHTML = "🚀 运行爬虫";

            if (status.error) {
                setLogStatus("error", "运行出错");
                showToast("运行出错：" + status.error, "error");
            } else if (status.results) {
                setLogStatus("success", "完成");
                crawlerResults = status.results;
                renderData();
                showToast(`抓取完成！共 ${status.results.length} 条公告`, "success");
            }
        }
    } catch (e) {
        console.error("状态查询失败:", e);
    }
}

function setLogStatus(cls, text) {
    const el = document.getElementById("logStatus");
    el.className = "log-status " + cls;
    el.textContent = text;
}

// ==================== 数据渲染 ====================
function renderData() {
    const all = crawlerResults;
    const hasDb = all.some(d => d.is_new !== null && d.is_new !== undefined);
    const newData = all.filter(d => d.is_new === true);
    const oldData = all.filter(d => d.is_new === false);

    // 更新徽章
    document.getElementById("badgeAll").textContent = all.length;
    document.getElementById("badgeNew").textContent = newData.length;
    document.getElementById("badgeOld").textContent = oldData.length;

    // 更新摘要
    const summary = document.getElementById("dataSummary");
    if (hasDb) {
        summary.innerHTML = `共 <strong>${all.length}</strong> 条 · 🆕 新增 <strong style="color:var(--success)">${newData.length}</strong> 条 · 📦 已存 <strong style="color:var(--primary)">${oldData.length}</strong> 条`;
    } else {
        summary.innerHTML = `共 <strong>${all.length}</strong> 条公告`;
    }

    // 显示数据区
    document.getElementById("dataSection").style.display = "";

    // 数据库未启用时隐藏新旧 Tab，只显示全部
    const newTab = document.querySelector('.tab[data-tab="new"]');
    const oldTab = document.querySelector('.tab[data-tab="old"]');
    if (hasDb) {
        newTab.style.display = "";
        oldTab.style.display = "";
    } else {
        newTab.style.display = "none";
        oldTab.style.display = "none";
    }

    // 数据库未启用时强制切到全部
    if (!hasDb) currentTab = "all";

    // 渲染当前 Tab
    switchTab(currentTab);
}

function switchTab(tab) {
    currentTab = tab;

    // 更新 Tab 样式
    document.querySelectorAll(".tab").forEach(t => {
        t.classList.remove("tab-active");
    });
    document.querySelector(`.tab[data-tab="${tab}"]`).classList.add("tab-active");

    // 过滤数据（Tab + 日期筛选）
    let data;
    if (tab === "all") {
        data = crawlerResults;
    } else if (tab === "new") {
        data = crawlerResults.filter(d => d.is_new === true);
    } else {
        data = crawlerResults.filter(d => d.is_new === false);
    }

    // 日期筛选
    if (dateFilter !== "all") {
        const now = new Date();
        data = data.filter(d => {
            const t = d.publish_time || "";
            if (!t) return false;
            const pubDate = new Date(t.replace(/\//g, "-"));
            if (isNaN(pubDate)) return false;
            if (dateFilter === "today") {
                return pubDate.toDateString() === now.toDateString();
            } else if (dateFilter === "week") {
                const weekAgo = new Date(now);
                weekAgo.setDate(weekAgo.getDate() - 7);
                return pubDate >= weekAgo;
            } else if (dateFilter === "month") {
                const monthAgo = new Date(now);
                monthAgo.setMonth(monthAgo.getMonth() - 1);
                return pubDate >= monthAgo;
            }
            return true;
        });
    }

    // 渲染表格
    const tbody = document.getElementById("tableBody");
    const empty = document.getElementById("emptyState");

    if (data.length === 0) {
        tbody.innerHTML = "";
        empty.style.display = "";
        const msgs = { all: "暂无数据", new: "暂无新数据", old: "暂无已存数据" };
        empty.querySelector("p").textContent = msgs[tab] + "，请运行爬虫获取公告";
        return;
    }

    empty.style.display = "none";
    tbody.innerHTML = data.map(d => {
        let tag;
        if (d.is_new === true) {
            tag = '<span class="tag tag-new">🆕 新</span>';
        } else if (d.is_new === false) {
            tag = '<span class="tag tag-old">📦 已存</span>';
        } else {
            tag = '';
        }
        const title = escapeHtml(d.title || "");
        const id = escapeHtml(d.announcement_id || "");
        const author = escapeHtml(d.author || "");
        const pubTime = escapeHtml(d.publish_time || "");
        const viewCount = escapeHtml(d.view_count || "");
        const aid = escapeHtml(d.announcement_id || "");
        return `<tr data-id="${id}">
            <td>${tag}</td>
            <td class="col-id">${id}</td>
            <td><a class="action-link detail-link">${title}</a></td>
            <td>${author}</td>
            <td>${pubTime}</td>
            <td>${viewCount}</td>
            <td><a class="action-link detail-link">查看</a></td>
        </tr>`;
    }).join("");
}

// ==================== 详情弹窗 ====================
async function showDetail(announcementId) {
    openModal("detailModal");
    document.getElementById("detailTitle").textContent = "加载中...";
    document.getElementById("detailBody").innerHTML = '<p style="color:var(--text-secondary)">正在加载...</p>';

    try {
        const resp = await api(`/api/data/detail?id=${encodeURIComponent(announcementId)}`);
        const d = resp.data;
        let tag;
        if (d.is_new === true) {
            tag = '<span class="tag tag-new">🆕 新数据</span>';
        } else if (d.is_new === false) {
            tag = '<span class="tag tag-old">📦 已存数据</span>';
        } else {
            tag = '<span class="tag" style="background:var(--bg-secondary);color:var(--text-secondary)">📄 已抓取</span>';
        }

        document.getElementById("detailTitle").textContent = d.title || "无标题";

        document.getElementById("detailBody").innerHTML = `
            <div class="detail-meta">
                <div class="detail-meta-item">
                    <span class="detail-meta-label">状态</span>
                    <span>${tag}</span>
                </div>
                <div class="detail-meta-item">
                    <span class="detail-meta-label">发布人</span>
                    <span class="detail-meta-value">${escapeHtml(d.author || "—")}</span>
                </div>
                <div class="detail-meta-item">
                    <span class="detail-meta-label">发布时间</span>
                    <span class="detail-meta-value">${escapeHtml(d.publish_time || "—")}</span>
                </div>
                <div class="detail-meta-item">
                    <span class="detail-meta-label">浏览量</span>
                    <span class="detail-meta-value">${escapeHtml(d.view_count || "—")}</span>
                </div>
                <div class="detail-meta-item">
                    <span class="detail-meta-label">公告ID</span>
                    <span class="detail-meta-value" style="font-family:var(--font-mono);font-size:13px">${escapeHtml(d.announcement_id || "—")}</span>
                </div>
            </div>
            <div class="detail-content">${escapeHtml(d.content || "暂无内容")}</div>
            ${d.url ? `<div style="margin-top:20px"><a href="${d.url}" target="_blank" class="action-link">🔗 查看原文</a></div>` : ""}
        `;
    } catch (e) {
        document.getElementById("detailTitle").textContent = "加载失败";
        document.getElementById("detailBody").innerHTML = `<p style="color:var(--danger)">${escapeHtml(e.message)}</p>`;
    }
}

// ==================== 定时任务 ====================
async function loadSchedulerConfig() {
    try {
        const data = await api("/api/scheduler");

        // 填充时间
        document.getElementById("schedulerTime").value = data.scheduler_time || "08:00";
        document.getElementById("schedulerKeyword").value = data.scheduler_keyword || "";

        // 填充时间范围下拉
        const timeSelect = document.getElementById("schedulerTimeRange");
        timeSelect.innerHTML = "";
        (data.time_ranges || []).forEach(r => {
            const opt = document.createElement("option");
            opt.value = r.value;
            opt.textContent = r.label;
            if (r.value === data.scheduler_time_range) opt.selected = true;
            timeSelect.appendChild(opt);
        });

        // 填充邮件模式下拉
        const modeSelect = document.getElementById("schedulerEmailMode");
        modeSelect.innerHTML = "";
        const modes = data.email_send_modes || {};
        Object.entries(modes).forEach(([key, label]) => {
            const opt = document.createElement("option");
            opt.value = key;
            opt.textContent = label;
            if (key === data.scheduler_email_mode) opt.selected = true;
            modeSelect.appendChild(opt);
        });

        // 更新开关和状态显示
        document.getElementById("schedulerEnabled").checked = data.enabled;
        updateSchedulerDisplay(data);

        // 启动轮询（如果已启用）
        if (data.enabled) {
            startSchedulerPolling();
        }
    } catch (e) {
        console.error("加载定时任务配置失败:", e);
    }
}

async function saveSchedulerConfig() {
    const data = {
        scheduler_time: document.getElementById("schedulerTime").value,
        scheduler_keyword: document.getElementById("schedulerKeyword").value.trim(),
        scheduler_time_range: document.getElementById("schedulerTimeRange").value,
        scheduler_email_mode: document.getElementById("schedulerEmailMode").value,
    };
    try {
        await api("/api/scheduler", {
            method: "POST",
            body: JSON.stringify(data),
        });
        showToast("定时任务配置已保存", "success");
        closeModal("schedulerModal");
        // 刷新状态
        const status = await api("/api/scheduler");
        updateSchedulerDisplay(status);
    } catch (e) {
        showToast("保存失败：" + e.message, "error");
    }
}

async function toggleScheduler() {
    const enabled = document.getElementById("schedulerEnabled").checked;
    try {
        const resp = await api("/api/scheduler/toggle", {
            method: "POST",
            body: JSON.stringify({ enabled }),
        });
        showToast(resp.message, "success");
        if (enabled) {
            startSchedulerPolling();
        } else {
            stopSchedulerPolling();
        }
        // 刷新状态
        const status = await api("/api/scheduler");
        updateSchedulerDisplay(status);
    } catch (e) {
        showToast("操作失败：" + e.message, "error");
        // 恢复开关状态
        document.getElementById("schedulerEnabled").checked = !enabled;
    }
}

function updateSchedulerDisplay(data) {
    const statusEl = document.getElementById("schedulerStatus");
    if (data.enabled) {
        statusEl.textContent = "已启用";
        statusEl.className = "scheduler-status active";
    } else {
        statusEl.textContent = "未启用";
        statusEl.className = "scheduler-status inactive";
    }

    // 下次运行时间
    const nextRunEl = document.getElementById("schedulerNextRun");
    if (data.next_run_time) {
        nextRunEl.textContent = formatDateTime(data.next_run_time);
        nextRunEl.className = "scheduler-info-value";
    } else {
        nextRunEl.textContent = "—";
        nextRunEl.className = "scheduler-info-value";
    }

    // 最近运行时间
    const lastRunEl = document.getElementById("schedulerLastRun");
    if (data.last_run_time) {
        lastRunEl.textContent = formatDateTime(data.last_run_time);
    } else {
        lastRunEl.textContent = "—";
    }

    // 最近运行结果
    const resultEl = document.getElementById("schedulerLastResult");
    if (data.last_run_result === "success") {
        resultEl.textContent = `成功（${data.last_run_count} 条）`;
        resultEl.className = "scheduler-info-value success";
    } else if (data.last_run_result === "error") {
        resultEl.textContent = "失败";
        resultEl.className = "scheduler-info-value error";
        resultEl.title = data.last_run_error || "";
    } else {
        resultEl.textContent = "—";
        resultEl.className = "scheduler-info-value";
        resultEl.title = "";
    }
}

function startSchedulerPolling() {
    if (schedulerPollTimer) return;
    schedulerPollTimer = setInterval(checkSchedulerStatus, 30000);
}

function stopSchedulerPolling() {
    if (schedulerPollTimer) {
        clearInterval(schedulerPollTimer);
        schedulerPollTimer = null;
    }
}

async function checkSchedulerStatus() {
    try {
        const data = await api("/api/scheduler");
        updateSchedulerDisplay(data);
        // 如果被关闭了就停止轮询
        if (!data.enabled) {
            stopSchedulerPolling();
        }
    } catch (e) {
        console.error("定时任务状态查询失败:", e);
    }
}

function formatDateTime(isoStr) {
    try {
        const d = new Date(isoStr);
        const now = new Date();
        const isToday = d.toDateString() === now.toDateString();
        const tomorrow = new Date(now);
        tomorrow.setDate(tomorrow.getDate() + 1);
        const isTomorrow = d.toDateString() === tomorrow.toDateString();

        const timeStr = d.toLocaleTimeString("zh-CN", { hour: "2-digit", minute: "2-digit" });
        if (isToday) {
            return `今天 ${timeStr}`;
        } else if (isTomorrow) {
            return `明天 ${timeStr}`;
        } else {
            return d.toLocaleString("zh-CN", {
                month: "2-digit", day: "2-digit",
                hour: "2-digit", minute: "2-digit",
            });
        }
    } catch (e) {
        return isoStr;
    }
}

// ==================== 工具函数 ====================
function escapeHtml(text) {
    const div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML;
}

function showToast(message, type = "info") {
    const container = document.getElementById("toastContainer");
    const toast = document.createElement("div");
    toast.className = `toast toast-${type}`;
    const icon = type === "success" ? "✅" : type === "error" ? "❌" : "ℹ️";
    toast.innerHTML = `<span>${icon}</span> <span>${escapeHtml(message)}</span>`;
    container.appendChild(toast);

    setTimeout(() => {
        toast.style.opacity = "0";
        toast.style.transform = "translateX(100%)";
        toast.style.transition = "all 0.3s ease";
        setTimeout(() => toast.remove(), 300);
    }, 3500);
}

// ==================== 日期筛选 ====================
function filterByDate(filter) {
    dateFilter = filter;

    // 更新按钮样式
    const btns = ["filterAllBtn", "filterTodayBtn", "filterWeekBtn", "filterMonthBtn"];
    const filterMap = { all: "filterAllBtn", today: "filterTodayBtn", week: "filterWeekBtn", month: "filterMonthBtn" };
    btns.forEach(id => {
        const btn = document.getElementById(id);
        if (btn) btn.className = "btn btn-sm btn-ghost";
    });
    const activeBtn = document.getElementById(filterMap[filter] || "filterAllBtn");
    if (activeBtn) activeBtn.className = "btn btn-sm btn-filter";

    // 更新筛选信息
    const infoEl = document.getElementById("dateFilterInfo");
    if (infoEl) {
        const labels = { all: "", today: "今日", week: "本周", month: "本月" };
        infoEl.textContent = labels[filter] ? `筛选：${labels[filter]}` : "";
    }

    // 重新渲染
    switchTab(currentTab);
}

// ==================== 打印功能 ====================
function printCurrentList() {
    // 获取当前显示的数据条数
    const rowCount = document.querySelectorAll("#tableBody tr").length;
    if (rowCount === 0) {
        showToast("没有可打印的数据", "error");
        return;
    }

    // 设置打印标题
    const today = new Date();
    const dateStr = `${today.getFullYear()}年${today.getMonth() + 1}月${today.getDate()}日`;
    let title = "深圳大学公告列表";
    if (dateFilter === "today") {
        title = `深圳大学今日公告（${dateStr}）`;
    } else {
        title = `深圳大学公告列表（${dateStr}）`;
    }
    const tabLabels = { all: "全部", new: "新数据", old: "已存数据" };
    title += ` - ${tabLabels[currentTab] || ""}（共 ${rowCount} 条）`;
    document.getElementById("printTitle").textContent = title;

    // 触发打印
    window.print();
}
