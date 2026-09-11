// ==================== 全局状态 ====================
let currentTab = "all";
let crawlerResults = [];
let pollTimer = null;

// ==================== 初始化 ====================
document.addEventListener("DOMContentLoaded", () => {
    loadConfig();
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

        // 填充数据库弹窗
        document.getElementById("dbEnabled").checked = config.mysql_enabled;
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

// ==================== 运行爬虫 ====================
async function runCrawler() {
    const account = document.getElementById("account").value.trim();
    const password = document.getElementById("password").value.trim();
    const keyword = document.getElementById("keyword").value.trim();
    const timeRange = document.getElementById("timeRange").value;
    const emailSendMode = document.getElementById("emailSendMode").value;

    if (!account || !password || !keyword) {
        showToast("账号、密码和关键词为必填项", "error");
        return;
    }

    const runBtn = document.getElementById("runBtn");
    runBtn.disabled = true;
    runBtn.innerHTML = '<span class="spinner"></span> 运行中...';

    // 显示日志区
    document.getElementById("logSection").style.display = "";
    document.getElementById("logConsole").innerHTML = "";
    setLogStatus("running", "运行中...");

    // 隐藏旧数据
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

    // 过滤数据
    let data;
    if (tab === "all") {
        data = crawlerResults;
    } else if (tab === "new") {
        data = crawlerResults.filter(d => d.is_new === true);
    } else {
        data = crawlerResults.filter(d => d.is_new === false);
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
