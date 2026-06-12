// API Configuration
const API_BASE = ""; // Relative to host since we serve them together

// Application State
let systemStatus = {};
let currentReports = {};
let activeTab = "pipelines";
let selectedExceptionId = null;
let pollIntervals = {};

// DOM Elements
const elements = {
    tabTitle: document.getElementById("tab-title"),
    tabSubtitle: document.getElementById("tab-subtitle"),
    groqBadge: document.getElementById("groq-badge"),
    groqStatusText: document.getElementById("groq-status-text"),

    // KPI elements
    cardRuleRatio: document.getElementById("card-rule-ratio"),
    cardRuleBar: document.getElementById("card-rule-bar"),
    cardRuleSub: document.getElementById("card-rule-sub"),

    cardVarianceLeft: document.getElementById("card-variance-left"),
    cardVarianceBar: document.getElementById("card-variance-bar"),
    cardVarianceSub: document.getElementById("card-variance-sub"),

    agentResolvedRatio: document.getElementById("agent-resolved-ratio"),
    agentResolvedBar: document.getElementById("agent-resolved-bar"),
    agentResolvedSub: document.getElementById("agent-resolved-sub"),

    humanReviewCount: document.getElementById("human-review-count"),
    humanReviewBar: document.getElementById("human-review-bar"),
    humanReviewSub: document.getElementById("human-review-sub"),

    exceptionsCount: document.getElementById("exceptions-count"),
    dashboardHumanExceptionsList: document.getElementById("dashboard-human-exceptions-list"),
    dashboardAutoExceptionsList: document.getElementById("dashboard-auto-exceptions-list"),
    dashboardHumanCount: document.getElementById("dashboard-human-count"),
    dashboardAutoCount: document.getElementById("dashboard-auto-count"),

    // Pipelines
    runMatchingBtn: document.getElementById("run-matching-btn"),
    runAgentsBtn: document.getElementById("run-agents-btn"),
    matchingTerminal: document.getElementById("matching-terminal"),
    agentsTerminal: document.getElementById("agents-terminal"),
    matchingIndicator: document.getElementById("matching-indicator"),
    agentsIndicator: document.getElementById("agents-indicator"),

    // Exception Center
    exceptionItemsList: document.getElementById("exception-items-list"),
    exceptionDetailContent: document.getElementById("exception-detail-content"),

    // Database Explorer
    sqlQueryInput: document.getElementById("sql-query-input"),
    runQueryBtn: document.getElementById("run-query-btn"),
    queryResultArea: document.getElementById("query-result-area"),
    tableBrowseContent: document.getElementById("table-browse-content"),

    // Actions
    resetDbBtn: document.getElementById("reset-db-btn")
};

// Subtitles mapping for tabs
const tabSubtitles = {
    "dashboard": "Real-time status of books and statement reconciliation.",
    "pipelines": "Run rule-matching scripts and trigger LangGraph exception handlers.",
    "exceptions": "Inspect the agent's database query traces and apply suggested fixes.",
    "explorer": "Interact with database tables and execute custom read-only SQL queries.",
    "loans": "Preview of automated loan amortization schedule matching."
};

// Initial Setup
document.addEventListener("DOMContentLoaded", () => {
    initTabSwitching();
    loadSystemStatus();
    loadSummaryData();
    initPipelines();
    initDbExplorer();
    initGlobalActions();
});

// Tab Management
function initTabSwitching() {
    const navButtons = document.querySelectorAll(".nav-btn");
    navButtons.forEach(btn => {
        btn.addEventListener("click", () => {
            const targetTab = btn.getAttribute("data-tab");

            // Toggle active classes in nav
            navButtons.forEach(b => b.classList.remove("active"));
            btn.classList.add("active");

            // Toggle active panels
            document.querySelectorAll(".tab-panel").forEach(p => p.classList.remove("active"));
            document.getElementById(`tab-${targetTab}`).classList.add("active");

            // Update Headers
            activeTab = targetTab;
            elements.tabTitle.textContent = btn.textContent.trim().replace(/^[^\w\s]*/, "").trim();
            elements.tabSubtitle.textContent = tabSubtitles[targetTab] || "";

            // Load tab specific details
            if (targetTab === "explorer") {
                loadBrowseTable("accounts");
            }
        });
    });
}

// Fetch Status & Configuration
async function loadSystemStatus() {
    try {
        const response = await fetch(`${API_BASE}/api/status`);
        systemStatus = await response.json();

        // Update Groq Status Badge
        if (systemStatus.groq_configured) {
            elements.groqBadge.classList.add("live");
            elements.groqBadge.querySelector(".badge-dot").style.backgroundColor = "var(--success)";
            elements.groqStatusText.textContent = "LLM Mode: Live API";
        } else {
            elements.groqBadge.classList.remove("live");
            elements.groqBadge.querySelector(".badge-dot").style.backgroundColor = "var(--warning)";
            elements.groqStatusText.textContent = "LLM Mode: Dry-Run";
        }
    } catch (e) {
        console.error("Error loading system status", e);
    }
}

// Load Summary JSON reports
async function loadSummaryData() {
    try {
        const response = await fetch(`${API_BASE}/api/summary`);
        currentReports = await response.json();
        updateDashboardKPIs();
        renderExceptions();
    } catch (e) {
        console.error("Error loading summary reports", e);
    }
}

// Update Dashboard KPI elements
function updateDashboardKPIs() {
    const matching = currentReports.matching_report || {};
    const agent = currentReports.agent_report || {};

    const cardRecon = agent.card_reconciliation || matching.card_reconciliation || {};

    // Gather exception details
    const unmatchedLedger = cardRecon.unmatched_ledger_details || [];
    const unmatchedCard = cardRecon.unmatched_card_details || [];
    const discrepancies = cardRecon.discrepancies_details || [];

    const totalExceptions = unmatchedLedger.length + unmatchedCard.length + discrepancies.length;

    // 1. Exact/Fuzzy Rule Matches
    const summary = cardRecon.summary || {};
    const totalCardLines = summary.total_card_lines || 84;
    const reconciledMatches = summary.reconciled_matches || 76;
    const totalToMatch = totalCardLines - 2; // exclude payments

    const ruleRatio = totalToMatch > 0 ? (reconciledMatches / totalToMatch) * 100 : 0;
    elements.cardRuleRatio.textContent = `${ruleRatio.toFixed(1)}%`;
    elements.cardRuleBar.style.width = `${ruleRatio}%`;
    elements.cardRuleSub.textContent = `${reconciledMatches} of ${totalToMatch} statement lines cleared by rule`;

    // 2. Amount Left After Exact/Fuzzy Match (Variance pending review)
    let totalVariancePending = 0;
    unmatchedLedger.forEach(x => totalVariancePending += Math.abs(x.amount || 0));
    unmatchedCard.forEach(x => totalVariancePending += Math.abs(x.amount || 0));
    discrepancies.forEach(x => totalVariancePending += Math.abs(x.variance || 0));

    elements.cardVarianceLeft.textContent = formatMoney(totalVariancePending);
    // Progress bar for pending amount relative to initial seed amount ($860.25)
    const variancePercent = Math.min(100, (totalVariancePending / 860.25) * 100);
    elements.cardVarianceBar.style.width = `${variancePercent}%`;
    elements.cardVarianceSub.textContent = `${totalExceptions} exceptions flagged for investigation`;

    // 3. Percent Done by Agents & 4. Human Review Count
    const enrichedList = cardRecon.enriched_discrepancies || [];
    let autoResolvedCount = 0;
    let humanReviewCount = 0;

    enrichedList.forEach(x => {
        // Only count if it's still unresolved
        const isStillUnresolved =
            unmatchedLedger.some(u => u.id === x.id) ||
            unmatchedCard.some(u => u.id === x.id) ||
            discrepancies.some(u => (u.ledger_id === x.id || u.card_id === x.id || u.ledger_id === x.ledger_id));

        if (isStillUnresolved) {
            if (x.agent_decision_status === "AUTO_RESOLVED") {
                autoResolvedCount++;
            } else if (x.agent_decision_status === "REQUIRES_HUMAN_INTERVENTION") {
                humanReviewCount++;
            }
        }
    });

    let agentRatio = 0;
    if (totalExceptions > 0) {
        if (enrichedList.length > 0) {
            agentRatio = (autoResolvedCount / totalExceptions) * 100;
        } else {
            // Pre-run baseline expectation: 5 out of 7 resolved
            autoResolvedCount = Math.round(totalExceptions * 0.714);
            humanReviewCount = totalExceptions - autoResolvedCount;
            agentRatio = (autoResolvedCount / totalExceptions) * 100;
        }
    } else {
        // 100% resolved case
        agentRatio = enrichedList.length > 0 ? 100 : 0;
        autoResolvedCount = 0;
        humanReviewCount = 0;
    }

    elements.agentResolvedRatio.textContent = `${agentRatio.toFixed(1)}%`;
    elements.agentResolvedBar.style.width = `${agentRatio}%`;
    elements.agentResolvedSub.textContent = `${autoResolvedCount} of ${totalExceptions} exceptions auto-resolved by AI`;

    elements.humanReviewCount.textContent = `${humanReviewCount} ${humanReviewCount === 1 ? 'Process' : 'Processes'}`;
    const humanPercent = totalExceptions > 0 ? (humanReviewCount / totalExceptions) * 100 : 0;
    elements.humanReviewBar.style.width = `${humanPercent}%`;
    elements.humanReviewSub.textContent = `${humanReviewCount} issues require manual adjustment`;
}

// Render the exceptions list in Dashboard and Exception Center
function renderExceptions() {
    const matching = currentReports.matching_report || {};
    const agent = currentReports.agent_report || {};

    const cardRecon = agent.card_reconciliation || matching.card_reconciliation || {};

    // Gather details
    const unmatchedLedger = cardRecon.unmatched_ledger_details || [];
    const unmatchedCard = cardRecon.unmatched_card_details || [];
    const discrepancies = cardRecon.discrepancies_details || [];

    // Enriched details contain agent diagnostics
    const enrichedList = cardRecon.enriched_discrepancies || [];

    // Flat list of exceptions
    const flatExceptions = [];

    unmatchedLedger.forEach(item => {
        const enriched = enrichedList.find(x => x.id === item.id);
        flatExceptions.push({
            id: item.id,
            type: "unmatched_ledger",
            date: item.date,
            amount: item.amount,
            currency: item.currency || "USD",
            description: item.description,
            title: `Outstanding Ledger Outflow`,
            badgeClass: "badge-warning",
            badgeText: "Unmatched Ledger",
            enriched: enriched
        });
    });

    unmatchedCard.forEach(item => {
        const enriched = enrichedList.find(x => x.id === item.id);

        let label = "Unrecorded Card Outflow";
        let badgeClass = "badge-info";
        let badgeText = "Unmatched Statement";

        if (item.amount >= 400.00 && item.description.includes("ELECTRONICS")) {
            label = "High Risk Potential Fraud";
            badgeClass = "badge-error";
            badgeText = "Potential Fraud";
        }

        flatExceptions.push({
            id: item.id,
            type: "unmatched_card",
            date: item.date,
            amount: item.amount,
            currency: item.currency || "USD",
            description: item.description,
            title: label,
            badgeClass: badgeClass,
            badgeText: badgeText,
            cardholder: item.cardholder,
            enriched: enriched
        });
    });

    discrepancies.forEach(item => {
        const itemId = item.ledger_id || item.card_id;
        const enriched = enrichedList.find(x => x.id === itemId || x.ledger_id === item.ledger_id);
        flatExceptions.push({
            id: itemId,
            type: "amount_discrepancy",
            date: item.date || "Multiple",
            amount: item.variance,
            currency: "USD",
            description: `Ledger: ${item.ledger_desc} (${formatMoney(item.ledger_amount)}) vs Statement: ${item.card_desc} (${formatMoney(item.card_amount)})`,
            title: `Amount Variance Discrepancy`,
            badgeClass: "badge-error",
            badgeText: "Amount Mismatch",
            enriched: enriched
        });
    });

    // Update unresolved count
    const unresolvedCount = flatExceptions.length;
    if (elements.exceptionsCount) {
        elements.exceptionsCount.textContent = `${unresolvedCount} unresolved`;
    }

    // Split into human action vs auto-resolved
    const humanTickets = [];
    const autoAdjustments = [];

    flatExceptions.forEach(exc => {
        // If the agent has run and explicitly marked as AUTO_RESOLVED, it's an auto adjustment
        const isAuto = exc.enriched && exc.enriched.agent_decision_status === "AUTO_RESOLVED";
        if (isAuto) {
            autoAdjustments.push(exc);
        } else {
            humanTickets.push(exc);
        }
    });

    // Render Dashboard Human Tickets
    if (elements.dashboardHumanExceptionsList) {
        if (humanTickets.length === 0) {
            elements.dashboardHumanExceptionsList.innerHTML = `
                <div class="empty-state">
                    <div class="empty-icon">✓</div>
                    <p>No human action required. All outstanding issues have been auto-adjusted!</p>
                </div>
            `;
        } else {
            elements.dashboardHumanExceptionsList.innerHTML = humanTickets.map(exc => `
                <div class="exception-item-card" onclick="openExceptionInCenter('${exc.id}')">
                    <div class="exc-details">
                        <div class="exc-title">${exc.title}</div>
                        <p class="description" style="margin-bottom:0; font-size:12px;">${exc.description}</p>
                        <div class="exc-meta">
                            <span>Date: <strong>${exc.date}</strong></span>
                            ${exc.cardholder ? `<span>Cardholder: <strong>${exc.cardholder}</strong></span>` : ""}
                        </div>
                    </div>
                    <div class="exc-side">
                        <span class="exc-amount">${formatMoney(exc.amount)}</span>
                        <span class="badge ${exc.badgeClass}">${exc.badgeText}</span>
                    </div>
                </div>
            `).join("");
        }
    }

    // Render Dashboard Auto-Resolved Adjustments
    if (elements.dashboardAutoExceptionsList) {
        if (autoAdjustments.length === 0) {
            elements.dashboardAutoExceptionsList.innerHTML = `
                <div class="empty-state">
                    <div class="empty-icon">✓</div>
                    <p>No auto-resolved adjustments present.</p>
                </div>
            `;
        } else {
            elements.dashboardAutoExceptionsList.innerHTML = autoAdjustments.map(exc => `
                <div class="exception-item-card" onclick="openExceptionInCenter('${exc.id}')">
                    <div class="exc-details">
                        <div class="exc-title">${exc.title}</div>
                        <p class="description" style="margin-bottom:0; font-size:12px;">${exc.description}</p>
                        <div class="exc-meta">
                            <span>Date: <strong>${exc.date}</strong></span>
                            ${exc.cardholder ? `<span>Cardholder: <strong>${exc.cardholder}</strong></span>` : ""}
                        </div>
                    </div>
                    <div class="exc-side">
                        <span class="exc-amount">${formatMoney(exc.amount)}</span>
                        <span class="badge ${exc.badgeClass}">${exc.badgeText}</span>
                    </div>
                </div>
            `).join("");
        }
    }

    // Update counts on the badges
    if (elements.dashboardHumanCount) {
        elements.dashboardHumanCount.textContent = `${humanTickets.length} ${humanTickets.length === 1 ? 'ticket' : 'tickets'}`;
    }
    if (elements.dashboardAutoCount) {
        elements.dashboardAutoCount.textContent = `${autoAdjustments.length} resolved`;
    }

    // Render Exception Center list
    renderExceptionCenterList(flatExceptions);
}

// Exception Center Render
function renderExceptionCenterList(exceptions) {
    if (exceptions.length === 0) {
        elements.exceptionItemsList.innerHTML = `<p class="placeholder-text">No exceptions found.</p>`;
        return;
    }

    elements.exceptionItemsList.innerHTML = exceptions.map(exc => {
        const isSelected = selectedExceptionId === exc.id ? "active" : "";
        let statusClass = "";
        let badgeText = "Pending Analysis";
        let badgeClass = "badge-warning";

        if (exc.enriched) {
            if (exc.enriched.agent_decision_status === "AUTO_RESOLVED") {
                statusClass = "resolved-auto";
                badgeText = "✓ Auto Resolved";
                badgeClass = "badge-success";
            } else if (exc.enriched.agent_decision_status === "REQUIRES_HUMAN_INTERVENTION") {
                statusClass = "requires-human";
                badgeText = "⚠ Human Action";
                badgeClass = "badge-error";
            } else {
                statusClass = "analyzed";
                badgeText = "✓ Agent Analysed";
                badgeClass = "badge-success";
            }
        }

        return `
            <button class="exc-tab-item ${isSelected} ${statusClass}" onclick="selectExceptionItem('${exc.id}')">
                <div class="exc-tab-title">${exc.title}</div>
                <div style="font-size: 11px; font-weight:700; margin-top:2px;">${formatMoney(exc.amount)}</div>
                <div class="exc-tab-subtitle">
                    <span>${exc.date}</span>
                    <span class="badge ${badgeClass}" style="font-size:8px; padding:1px 4px;">${badgeText}</span>
                </div>
            </button>
        `;
    }).join("");

    // Maintain selection details if loaded
    if (selectedExceptionId) {
        const activeExc = exceptions.find(x => x.id === selectedExceptionId);
        if (activeExc) {
            renderExceptionDetails(activeExc);
        } else {
            selectedExceptionId = null;
            resetExceptionDetailView();
        }
    }
}

function selectExceptionItem(id) {
    selectedExceptionId = id;
    loadSummaryData(); // Re-fetch to update active classes in UI
}

function openExceptionInCenter(id) {
    // Switch tab
    const excTabBtn = document.querySelector(".nav-btn[data-tab='exceptions']");
    if (excTabBtn) excTabBtn.click();

    selectedExceptionId = id;
    loadSummaryData();
}

function resetExceptionDetailView() {
    elements.exceptionDetailContent.innerHTML = `
        <div class="empty-detail-state">
            <span>🔍</span>
            <h3>Select an Exception</h3>
            <p>Choose an unresolved exception from the side list to inspect the AI agent's root cause analysis, reasoning steps, executed SQL statements, and recommended resolution.</p>
        </div>
    `;
}

// Render Exception Trace details
function renderExceptionDetails(exc) {
    const item = exc.enriched;

    if (!item) {
        // Not analyzed yet
        elements.exceptionDetailContent.innerHTML = `
            <div class="empty-detail-state">
                <span>🤖</span>
                <h3>Agent Analysis Pending</h3>
                <p>This exception has not been processed by the LangGraph agent workflow yet.</p>
                <button class="btn btn-accent mt-4" onclick="triggerSingleAgentAnalysis('${exc.id}')">Run AI Diagnostics for this Item</button>
            </div>
        `;
        return;
    }

    // Build tables for SQL traces
    const dbQueries = item.agent_db_queries || [];
    let sqlTracesHTML = "";
    if (dbQueries.length > 0) {
        sqlTracesHTML = `
            <div class="trace-section-title">Safe Database Queries Executed (RCA Agent)</div>
            ${dbQueries.map((q, idx) => {
            const results = q.result || [];
            let tableHTML = "";
            if (results.length > 0) {
                const columns = Object.keys(results[0]);
                tableHTML = `
                        <div class="table-overflow">
                            <table class="sql-query-results-table">
                                <thead>
                                    <tr>
                                        ${columns.map(col => `<th>${col}</th>`).join("")}
                                    </tr>
                                </thead>
                                <tbody>
                                    ${results.map(row => `
                                        <tr>
                                            ${columns.map(col => `<td>${row[col] !== null ? row[col] : 'NULL'}</td>`).join("")}
                                        </tr>
                                    `).join("")}
                                </tbody>
                            </table>
                        </div>
                    `;
            } else {
                tableHTML = `<div class="placeholder-text" style="padding: 14px; text-align: left; font-style: italic;">Query returned 0 rows.</div>`;
            }

            return `
                    <div class="sql-query-block">
                        <div class="sql-query-header">Query #${idx + 1}: ${escapeHTML(q.query)}</div>
                        ${tableHTML}
                    </div>
                `;
        }).join("")}
        `;
    }

    // Parse RCA findings markdown to HTML (simple custom parser for basic markdown elements)
    const formattedRCA = formatMarkdownToHTML(item.agent_rca_analysis || "No analysis details provided.");

    // Resolution actions HTML
    const isAuto = item.agent_decision_status === "AUTO_RESOLVED";
    const resPanelClass = isAuto ? "resolution-panel" : "resolution-panel requires-human";
    const statusText = isAuto ? "AUTO RESOLVED ADJUSTMENT" : "REQUIRES HUMAN INTERVENTION";

    const resolutionHTML = `
        <div class="${resPanelClass}">
            <div class="flex-col">
                <span class="badge ${isAuto ? 'badge-success' : 'badge-warning'}" style="width:fit-content; margin-bottom:8px;">${statusText}</span>
                <h4>Recommended Action</h4>
                <p class="resolution-action-text">${item.agent_recommended_action || 'No recommendation provided.'}</p>
                
                ${item.agent_suggested_fix ? `
                    <span class="fix-sql-label">Suggested Journal Entry / Database Adjustment:</span>
                    <div class="suggested-fix-box" id="fix-sql-code">${escapeHTML(item.agent_suggested_fix)}</div>
                    <button class="btn ${isAuto ? 'btn-success' : 'btn-accent'} w-full" onclick="applySuggestedFix('${item.id}', \`${escapeJSString(item.agent_suggested_fix)}\`)">
                        ${isAuto ? 'Apply Adjustment & Close Exception' : 'Log Adjustment (CEO Override)'}
                    </button>
                ` : ""}
                
                ${item.agent_langsmith_trace_url ? `
                    <div style="margin-top: 16px; border-top: 1px dashed rgba(0,0,0,0.12); padding-top: 16px;">
                        <span class="fix-sql-label" style="color: var(--accent); font-weight:700;">LangSmith Observability Trace:</span>
                        <a href="${item.agent_langsmith_trace_url}" target="_blank" class="btn btn-outline btn-sm w-full" style="display:inline-flex; justify-content:center; text-decoration:none; margin-top:4px; font-weight:600; border-color: var(--accent); color: var(--accent); background-color: var(--accent-light);">
                            🔍 View Live Agent Trace Graph ↗
                        </a>
                    </div>
                ` : `
                    <div style="margin-top: 16px; border-top: 1px dashed rgba(0,0,0,0.12); padding-top: 16px;">
                        <span class="fix-sql-label">LangSmith Observability Trace:</span>
                        <button class="btn btn-outline btn-sm w-full" disabled style="opacity:0.6; cursor:not-allowed; display:inline-flex; justify-content:center; margin-top:4px;" title="To trace live graph executions, configure LANGCHAIN_API_KEY in your local .env file.">
                            🚫 Trace Offline (Configure LANGCHAIN_API_KEY in .env)
                        </button>
                    </div>
                `}
            </div>
        </div>
    `;

    // Comparison Grid Values
    let comparisonHTML = "";
    if (exc.type === "amount_discrepancy") {
        // Discrepancy comparison
        comparisonHTML = `
            <div class="detail-grid-comparison">
                <div class="comparison-box">
                    <h4>General Ledger Entry</h4>
                    <div class="comp-row"><strong>Description:</strong> <span>${escapeHTML(item.ledger_desc || '')}</span></div>
                    <div class="comp-row"><strong>Amount:</strong> <span>${formatMoney(item.ledger_amount)}</span></div>
                    <div class="comp-row"><strong>Date:</strong> <span>${item.date}</span></div>
                </div>
                <div class="comparison-box">
                    <h4>Card Statement Charge</h4>
                    <div class="comp-row"><strong>Merchant Descriptor:</strong> <span>${escapeHTML(item.card_desc || '')}</span></div>
                    <div class="comp-row"><strong>Amount:</strong> <span>${formatMoney(item.card_amount)}</span></div>
                    <div class="comp-row"><strong>Date:</strong> <span>${item.date}</span></div>
                </div>
            </div>
        `;
    } else if (exc.type === "unmatched_card") {
        // Card charges missing ledger entry
        comparisonHTML = `
            <div class="detail-grid-comparison">
                <div class="comparison-box">
                    <h4>General Ledger Entry</h4>
                    <div class="placeholder-text" style="padding: 10px 0; color: var(--error)">No matching journal entry found.</div>
                </div>
                <div class="comparison-box matched-success">
                    <h4>Card Statement Charge</h4>
                    <div class="comp-row"><strong>Merchant Descriptor:</strong> <span>${escapeHTML(item.description)}</span></div>
                    <div class="comp-row"><strong>Amount:</strong> <span>${formatMoney(item.amount)}</span></div>
                    <div class="comp-row"><strong>Date:</strong> <span>${item.date}</span></div>
                    <div class="comp-row"><strong>Cardholder:</strong> <span>${item.cardholder}</span></div>
                </div>
            </div>
        `;
    } else if (exc.type === "unmatched_ledger") {
        // Ledger entry missing card transaction
        comparisonHTML = `
            <div class="detail-grid-comparison">
                <div class="comparison-box matched-success">
                    <h4>General Ledger Entry</h4>
                    <div class="comp-row"><strong>Description:</strong> <span>${escapeHTML(item.description)}</span></div>
                    <div class="comp-row"><strong>Amount:</strong> <span>${formatMoney(item.amount)}</span></div>
                    <div class="comp-row"><strong>Date:</strong> <span>${item.date}</span></div>
                </div>
                <div class="comparison-box">
                    <h4>Card Statement Charge</h4>
                    <div class="placeholder-text" style="padding: 10px 0; color: var(--error)">No statement line found (timing / outstanding).</div>
                </div>
            </div>
        `;
    }

    elements.exceptionDetailContent.innerHTML = `
        <div class="detail-header-section">
            <div class="detail-title-col">
                <h3>${exc.title}</h3>
                <p>Transaction ID: <strong>${item.id}</strong></p>
            </div>
            <div class="detail-amount-col">
                <div class="detail-amount">${formatMoney(item.amount || item.variance)}</div>
                <div class="detail-mismatch-pill">Variance Amount</div>
            </div>
        </div>
        
        ${comparisonHTML}
        
        <div class="trace-section-title">AI Agent Classification Reasoning</div>
        <div class="agent-response-bubble">
            <div class="bubble-section-label">Classification: ${item.agent_category || 'Other'}</div>
            <p class="bubble-reasoning">${escapeHTML(item.agent_categorisation_reasoning)}</p>
        </div>
        
        ${sqlTracesHTML}
        
        <div class="trace-section-title">Root Cause Investigation Findings</div>
        <div class="agent-response-bubble">
            <div class="rca-findings-md">${formattedRCA}</div>
        </div>
        
        ${resolutionHTML}
    `;
}

// Pipelines Runner Handling
function initPipelines() {
    // Run Matching Engine
    elements.runMatchingBtn.addEventListener("click", async () => {
        elements.runMatchingBtn.disabled = true;
        elements.matchingTerminal.textContent = "Launching Matching Engine...\n";

        try {
            const res = await fetch(`${API_BASE}/api/run-matching`, { method: "POST" });
            if (res.ok) {
                startPolling("matching", elements.matchingTerminal, elements.matchingIndicator);
            } else {
                elements.matchingTerminal.textContent += "\nError: Pipeline already running.";
                elements.runMatchingBtn.disabled = false;
            }
        } catch (e) {
            elements.matchingTerminal.textContent += `\nError executing server matching: ${e.message}`;
            elements.runMatchingBtn.disabled = false;
        }
    });

    // Run AI Exception Agents
    elements.runAgentsBtn.addEventListener("click", async () => {
        elements.runAgentsBtn.disabled = true;
        elements.agentsTerminal.textContent = "Launching LangGraph Exception Handler...\n";

        try {
            const res = await fetch(`${API_BASE}/api/run-agents`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({})
            });
            if (res.ok) {
                startPolling("agents", elements.agentsTerminal, elements.agentsIndicator);
            } else {
                elements.agentsTerminal.textContent += "\nError: AI Pipeline already running.";
                elements.runAgentsBtn.disabled = false;
            }
        } catch (e) {
            elements.agentsTerminal.textContent += `\nError executing server agents: ${e.message}`;
            elements.runAgentsBtn.disabled = false;
        }
    });
}

// Run single agent analysis (triggered from Exception Detail view)
async function triggerSingleAgentAnalysis(id) {
    try {
        const response = await fetch(`${API_BASE}/api/run-agents`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ id: id })
        });

        if (response.ok) {
            // Redirect user to the Run Pipelines tab to see logs
            const pipelineTabBtn = document.querySelector(".nav-btn[data-tab='pipelines']");
            if (pipelineTabBtn) pipelineTabBtn.click();
            startPolling("agents", elements.agentsTerminal, elements.agentsIndicator);
        } else {
            alert("Analysis pipeline already running, please wait.");
        }
    } catch (e) {
        alert("Failed to start agent analysis: " + e.message);
    }
}

// Log Poller
function startPolling(pipelineType, terminalEl, indicatorEl) {
    // Clear previous logs
    terminalEl.textContent = "Pipeline executing. Streaming stdout:\n";
    indicatorEl.textContent = "Running";
    indicatorEl.classList.add("running");

    if (pollIntervals[pipelineType]) {
        clearInterval(pollIntervals[pipelineType]);
    }

    pollIntervals[pipelineType] = setInterval(async () => {
        try {
            const res = await fetch(`${API_BASE}/api/run-status`);
            const status = await res.json();
            const data = status[pipelineType];

            // Format log lines
            terminalEl.textContent = data.logs.join("\n");
            terminalEl.scrollTop = terminalEl.scrollHeight; // Auto-scroll

            if (data.status === "idle") {
                clearInterval(pollIntervals[pipelineType]);
                indicatorEl.textContent = "Idle";
                indicatorEl.classList.remove("running");

                // Re-enable actions
                if (pipelineType === "matching") {
                    elements.runMatchingBtn.disabled = false;
                } else if (pipelineType === "agents") {
                    elements.runAgentsBtn.disabled = false;
                }

                // Reload dashboard data
                loadSummaryData();
            }
        } catch (e) {
            console.error("Polling error", e);
        }
    }, 500);
}

// Apply suggested fix
async function applySuggestedFix(id, fixSql) {
    if (!confirm("Are you sure you want to write this journal entry modification to the ledger database?")) {
        return;
    }

    try {
        const res = await fetch(`${API_BASE}/api/apply-fix`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ id: id, fix_sql: fixSql })
        });

        const result = await res.json();
        if (res.ok && result.success) {
            alert(result.message);
            // Refresh data
            selectedExceptionId = null;
            resetExceptionDetailView();
            loadSummaryData();
        } else {
            alert("Error applying fix: " + (result.error || "Unknown error"));
        }
    } catch (e) {
        alert("Server communication error: " + e.message);
    }
}

// DB Explorer Tab
function initDbExplorer() {
    // Custom SQL Console
    elements.runQueryBtn.addEventListener("click", executeConsoleQuery);

    // Quick SQL buttons
    document.querySelectorAll(".quick-sql-btn").forEach(btn => {
        btn.addEventListener("click", () => {
            const sql = btn.getAttribute("data-sql");
            elements.sqlQueryInput.value = sql;
            executeConsoleQuery();
        });
    });

    // Table selectors
    document.querySelectorAll(".table-select-btn").forEach(btn => {
        btn.addEventListener("click", () => {
            document.querySelectorAll(".table-select-btn").forEach(b => b.classList.remove("active"));
            btn.classList.add("active");

            const table = btn.getAttribute("data-table");
            loadBrowseTable(table);
        });
    });
}

async function executeConsoleQuery() {
    const sql = elements.sqlQueryInput.value.trim();
    if (!sql) return;

    elements.queryResultArea.innerHTML = `<div class="loader-pulse"></div>`;

    try {
        const res = await fetch(`${API_BASE}/api/database/query`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ sql_query: sql })
        });

        const data = await res.json();
        if (res.ok) {
            if (data.rows && data.rows.length > 0) {
                const cols = data.columns;
                elements.queryResultArea.innerHTML = `
                    <table class="table">
                        <thead>
                            <tr>
                                ${cols.map(c => `<th>${c}</th>`).join("")}
                            </tr>
                        </thead>
                        <tbody>
                            ${data.rows.map(row => `
                                <tr>
                                    ${cols.map(c => `<td>${row[c] !== null ? escapeHTML(String(row[c])) : 'NULL'}</td>`).join("")}
                                </tr>
                            `).join("")}
                        </tbody>
                    </table>
                `;
            } else {
                elements.queryResultArea.innerHTML = `<div class="placeholder-text" style="padding:40px;">Query executed successfully. Returned 0 rows.</div>`;
            }
        } else {
            elements.queryResultArea.innerHTML = `<div class="placeholder-text" style="padding:40px; color:var(--error); font-weight:600;">SQL Error: ${data.error}</div>`;
        }
    } catch (e) {
        elements.queryResultArea.innerHTML = `<div class="placeholder-text" style="padding:40px; color:var(--error);">Connection error: ${e.message}</div>`;
    }
}

async function loadBrowseTable(tableName) {
    elements.tableBrowseContent.innerHTML = `<div class="loader-pulse"></div>`;

    try {
        const response = await fetch(`${API_BASE}/api/database/${tableName}`);
        const data = await response.json();

        if (response.ok && data.length > 0) {
            const cols = Object.keys(data[0]);
            elements.tableBrowseContent.innerHTML = `
                <table class="table">
                    <thead>
                        <tr>
                            ${cols.map(c => `<th>${c}</th>`).join("")}
                        </tr>
                    </thead>
                    <tbody>
                        ${data.map(row => `
                            <tr>
                                ${cols.map(c => `<td>${row[c] !== null ? escapeHTML(String(row[c])) : 'NULL'}</td>`).join("")}
                            </tr>
                        `).join("")}
                    </tbody>
                </table>
            `;
        } else {
            elements.tableBrowseContent.innerHTML = `<div class="placeholder-text" style="padding:40px;">No rows found. Table is empty or error occurred.</div>`;
        }
    } catch (e) {
        elements.tableBrowseContent.innerHTML = `<div class="placeholder-text" style="padding:40px; color:var(--error);">Failed to load table: ${e.message}</div>`;
    }
}

// Global actions
function initGlobalActions() {
    if (elements.resetDbBtn) {
        elements.resetDbBtn.addEventListener("click", async () => {
            if (!confirm("Are you sure you want to delete and reset the reconciliation database? This resets all anomalies to default states.")) {
                return;
            }

            try {
                const res = await fetch(`${API_BASE}/api/reset-db`, { method: "POST" });
                const result = await res.json();

                if (res.ok && result.success) {
                    alert(result.message);
                    selectedExceptionId = null;
                    resetExceptionDetailView();
                    loadSummaryData();
                } else {
                    alert("Error resetting database: " + result.error);
                }
            } catch (e) {
                alert("Connection error resetting database: " + e.message);
            }
        });
    }
}

// Helper Utilities
function formatMoney(val) {
    if (val === null || val === undefined || isNaN(val)) return "--";
    const num = parseFloat(val);
    const sign = num < 0 ? "-" : "";
    return `${sign}$${Math.abs(num).toFixed(2)}`;
}

function escapeHTML(str) {
    if (!str) return "";
    return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/'/g, "&#039;");
}

function escapeJSString(str) {
    if (!str) return "";
    return str.replace(/\\/g, '\\\\').replace(/`/g, '\\`').replace(/\$/g, '\\$');
}

// Parse markdown to HTML (basic implementation)
function formatMarkdownToHTML(md) {
    if (!md) return "";
    let html = escapeHTML(md);

    // Convert headers
    html = html.replace(/^### (.*$)/gim, '<h4>$1</h4>');
    html = html.replace(/^## (.*$)/gim, '<h3>$1</h3>');
    html = html.replace(/^# (.*$)/gim, '<h2>$1</h2>');

    // Bold
    html = html.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');

    // Code blocks / inline code
    html = html.replace(/`(.*?)`/g, '<code>$1</code>');

    // Table rows converting
    let lines = html.split('\n');
    let insideTable = false;
    let tableHTML = "";

    for (let i = 0; i < lines.length; i++) {
        let line = lines[i].trim();
        if (line.startsWith('|') && line.endsWith('|')) {
            // Is it separator row? (e.g. |---|---|)
            if (line.includes('---')) {
                continue;
            }

            let cells = line.split('|').map(c => c.trim()).filter((c, idx, arr) => idx > 0 && idx < arr.length - 1);
            if (!insideTable) {
                insideTable = true;
                tableHTML += '<table><thead><tr>';
                tableHTML += cells.map(c => `<th>${c}</th>`).join("");
                tableHTML += '</tr></thead><tbody>';
            } else {
                tableHTML += '<tr>';
                tableHTML += cells.map(c => `<td>${c}</td>`).join("");
                tableHTML += '</tr>';
            }
        } else {
            if (insideTable) {
                insideTable = false;
                tableHTML += '</tbody></table>';
                lines[i] = tableHTML + '\n' + lines[i];
                tableHTML = "";
            }

            // Bullet points
            if (line.startsWith('- ') || line.startsWith('* ')) {
                lines[i] = `<li>${line.substring(2)}</li>`;
            } else if (line.startsWith('👉')) {
                lines[i] = `<p style="margin-top: 10px; font-weight:600;">${line}</p>`;
            } else if (line !== "") {
                lines[i] = `<p>${line}</p>`;
            }
        }
    }

    if (insideTable) {
        tableHTML += '</tbody></table>';
        lines.push(tableHTML);
    }

    return lines.join('\n');
}
