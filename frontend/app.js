// app.js
// - LLM 리포트 + 가감요소(adjustment_text) 표시
// - "현저한 과실/중대한 과실" 자세히보기 버튼(Neo4j Modifier API)
// - 모달 UI
// - 레이스 방지(activeReqId) 유지

window.state = {
  domain_l1: null,
  route_l2: null,
  route_l3: null,
  route_l4: null,
};

let routeLabels = {}; // route_labels_ko.json 로딩해서 채움
let activeReqId = 0;

function $(id) { return document.getElementById(id); }

function API_BASE() {
  return $("apiBase").value.trim().replace(/\/$/, "");
}

function escapeHtml(str) {
  return String(str)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function renderState() {
  const s = window.state;
  const pill = (v) => (v == null ? "<span class='pill null'>null</span>" : `<span class='pill'>${escapeHtml(v)}</span>`);
  $("stateView").innerHTML =
    `STATE · domain=${pill(s.domain_l1)} · l2=${pill(s.route_l2)} · l3=${pill(s.route_l3)} · l4=${pill(s.route_l4)}`;
}

// ============================
// 라벨 로드
// ============================
async function loadLabels() {
  try {
    const res = await fetch("./route_labels_ko.json", { cache: "no-store" });
    routeLabels = await res.json();
    console.log("[labels] loaded", routeLabels);
  } catch (e) {
    console.warn("[labels] not loaded. (optional)", e);
    routeLabels = {};
  }
}

function labelOf(code) {
  if (!code) return code;
  if (typeof routeLabels?.domain_l1?.[code] === "string") return routeLabels.domain_l1[code];
  if (typeof routeLabels?.route_l2?.[code] === "string") return routeLabels.route_l2[code];
  if (typeof routeLabels?.route_l3?.[code] === "string") return routeLabels.route_l3[code];
  if (typeof routeLabels?.route_l4?.[code] === "string") return routeLabels.route_l4[code];
  if (typeof routeLabels?.[code] === "string") return routeLabels[code];
  return code;
}

// ============================
// API 호출
// ============================
async function postJSON(path, payload) {
  const reqId = ++activeReqId;
  const res = await fetch(`${API_BASE()}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  if (!res.ok) {
    const t = await res.text();
    throw new Error(`API ${path} failed (${res.status}): ${t}`);
  }

  const data = await res.json();
  if (reqId !== activeReqId) return { __stale: true, data };
  return { __stale: false, data };
}

async function getJSON(path) {
  const reqId = ++activeReqId;
  const res = await fetch(`${API_BASE()}${path}`);
  if (!res.ok) {
    const t = await res.text();
    throw new Error(`API ${path} failed (${res.status}): ${t}`);
  }
  const data = await res.json();
  if (reqId !== activeReqId) return { __stale: true, data };
  return { __stale: false, data };
}

function setStatus(msg, type = "info") {
  const el = $("statusBar");
  el.className = `status ${type}`;
  el.innerText = msg;
}

function showHelpCard(show) {
  $("helpCard").style.display = show ? "block" : "none";
}

function clearFinal() {
  $("finalTitle").innerText = "아직 없음";
  $("finalReport").style.display = "none";
  $("finalReport").innerHTML = "";
  $("finalJson").innerText = "{}";
  $("finalJson").style.display = "none";
  $("toggleJson").innerText = "원본 JSON 보기";
  hideFinalLoading();
}

function clearHelpArea() {
  $("helpQuestions").innerHTML = "";
  $("recommendResult").innerHTML = "";
  $("userNote").value = "";
}

// ============================
// 로딩(LLM) 표시
// ============================
let loadingTimer = null;
let loadingStart = 0;

function showFinalLoading() {
  const box = $("finalLoading");
  if (!box) return;
  box.style.display = "flex";
  loadingStart = Date.now();
  $("finalLoadingTime").innerText = "0s";
  if (loadingTimer) clearInterval(loadingTimer);
  loadingTimer = setInterval(() => {
    const s = Math.floor((Date.now() - loadingStart) / 1000);
    $("finalLoadingTime").innerText = `${s}s`;
  }, 250);
}

function hideFinalLoading() {
  const box = $("finalLoading");
  if (!box) return;
  box.style.display = "none";
  if (loadingTimer) clearInterval(loadingTimer);
  loadingTimer = null;
}

// ============================
// (NEW) 가감요소 렌더 + 자세히보기 버튼
// ============================
function renderAdjustmentText(text) {
  if (!text || !String(text).trim()) {
    return "<div class='emptyBox'>가감요소 정보 없음</div>";
  }

  const lines = String(text)
    .split("\n")
    .map(s => s.trim())
    .filter(Boolean);

  return `
    <div class="adjBox">
      ${lines.map(line => {
        const safe = escapeHtml(line);

        const hasNotice = line.includes("현저한 과실");
        const hasMajor = line.includes("중대한 과실");

        const btnNotice = hasNotice
          ? ` <button class="btn ghost mini" data-mod="NOTICEABLE_FAULT">자세히보기</button>`
          : "";
        const btnMajor = hasMajor
          ? ` <button class="btn ghost mini" data-mod="MAJOR_FAULT">자세히보기</button>`
          : "";

        return `<div class="adjRow">${safe}${btnNotice}${btnMajor}</div>`;
      }).join("")}
    </div>
  `;
}

// "자세히보기" 이벤트는 innerHTML 이후에 바인딩해야 함
function bindModifierButtons(rootEl) {
  rootEl.querySelectorAll("button[data-mod]").forEach((btn) => {
    btn.onclick = async () => {
      const code = btn.getAttribute("data-mod");
      await openModifier(code);
    };
  });
}

// ============================
// (NEW) 모달
// ============================
function ensureModalStyles() {
  // index.html 안 바꿔도 되게, 모달 최소 CSS를 JS에서 주입
  if (document.getElementById("__modal_style")) return;
  const style = document.createElement("style");
  style.id = "__modal_style";
  style.innerHTML = `
    #modal{ display:none; position:fixed; inset:0; z-index:9999; }
    #modal .modalBg{ position:absolute; inset:0; background:rgba(0,0,0,.45); }
    #modal .modalCard{
      position:relative;
      max-width: 720px;
      margin: 8vh auto;
      background: #fff;
      border-radius: 16px;
      border: 1px solid rgba(0,0,0,.08);
      box-shadow: 0 16px 50px rgba(0,0,0,.22);
      padding: 16px;
    }
    #modal .modalTop{ display:flex; justify-content:space-between; align-items:center; gap:10px; }
    #modal .modalTop .title{ font-weight: 900; }
    #modal .modalBody{ margin-top: 12px; line-height: 1.65; }
    #modal .closeBtn{ padding:8px 12px; border-radius:10px; border:1px solid #e5e7eb; background:#fff; cursor:pointer; font-weight:800; }
    #modal h3{ margin: 0 0 8px; }
    #modal h4{ margin: 12px 0 6px; }
    #modal ul{ margin: 6px 0 10px 18px; }
    .btn.mini{ padding: 6px 10px; border-radius: 10px; font-size: 12px; font-weight: 900; }
    .adjBox{ margin-top: 10px; display:flex; flex-direction:column; gap:8px; }
    .adjRow{
      padding: 10px 12px;
      border: 1px solid #e6e8ef;
      border-radius: 12px;
      background: #fff;
      display:flex;
      gap: 10px;
      align-items:center;
      justify-content: space-between;
      flex-wrap: wrap;
    }
    .adjRow button{ white-space: nowrap; }
  `;
  document.head.appendChild(style);
}

function showModal(title, innerHtml) {
  ensureModalStyles();

  let modal = document.getElementById("modal");
  if (!modal) {
    modal = document.createElement("div");
    modal.id = "modal";
    modal.innerHTML = `
      <div class="modalBg"></div>
      <div class="modalCard" role="dialog" aria-modal="true">
        <div class="modalTop">
          <div class="title" id="modalTitle"></div>
          <button class="closeBtn" id="modalCloseBtn">닫기</button>
        </div>
        <div class="modalBody" id="modalBody"></div>
      </div>
    `;
    document.body.appendChild(modal);

    modal.querySelector(".modalBg").onclick = closeModal;
    modal.querySelector("#modalCloseBtn").onclick = closeModal;
    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape") closeModal();
    });
  }

  document.getElementById("modalTitle").innerText = title || "상세";
  document.getElementById("modalBody").innerHTML = innerHtml;
  modal.style.display = "block";
}

function closeModal() {
  const modal = document.getElementById("modal");
  if (modal) modal.style.display = "none";
}

// ============================
// (NEW) Modifier 상세 조회
// ============================
async function openModifier(code) {
  try {
    const { __stale, data } = await getJSON(`/modifiers/${encodeURIComponent(code)}`);
    if (__stale) return;

    const rules = (data.apply_rules || []).map(r => `<li>${escapeHtml(r)}</li>`).join("");
    const ex = (data.examples || []).map(e => `<li>${escapeHtml(e)}</li>`).join("");

    const html = `
      <div>
        <div class="pill score" style="display:inline-block;margin-bottom:8px;">${escapeHtml(data.kind || "MODIFIER")}</div>
        <h3 style="margin:0 0 8px;">${escapeHtml(data.name || "-")} <span class="mono">(${escapeHtml(data.range || "-")})</span></h3>
        <h4>적용 원칙</h4>
        <ul>${rules || "<li>(없음)</li>"}</ul>
        <h4>적용 예시</h4>
        <ul>${ex || "<li>(없음)</li>"}</ul>
      </div>
    `;

    showModal(data.name || code, html);
  } catch (e) {
    console.error(e);
    alert("가감요소 설명을 불러오지 못했습니다. (백엔드 /modifiers/{code} 확인)");
  }
}

// ============================
// 버튼 비활성화
// ============================
function setButtonsDisabled(disabled) {
  ["btnInit", "btnReset", "btnRecommend", "toggleJson"].forEach((id) => {
    const el = $(id);
    if (el) el.disabled = disabled;
  });
  document.querySelectorAll("button.btn").forEach((b) => {
    b.disabled = disabled;
  });
}

// ============================
// UI helpers
// ============================
function renderStepHeader(next_level, candidate_count) {
  $("stepTitle").innerHTML = `
    <div class="stepHead">
      <div>
        <div class="stepLabel">선택 단계</div>
        <div class="stepTitle">next_level: <span class="mono">${escapeHtml(next_level || "-")}</span></div>
      </div>
      <div class="badge">candidates: <b>${candidate_count ?? "-"}</b></div>
    </div>
  `;
}

function createOptionRow({ leftTitle, leftSub, rightText = "선택", onClick, primary = false }) {
  const row = document.createElement("div");
  row.className = "optRow";

  const left = document.createElement("div");
  left.className = "optLeft";

  const t = document.createElement("div");
  t.className = "optTitle";
  t.innerText = leftTitle;

  const sub = document.createElement("div");
  sub.className = "optSub";
  sub.innerText = leftSub || "";

  left.appendChild(t);
  if (leftSub) left.appendChild(sub);

  const btn = document.createElement("button");
  btn.className = primary ? "btn primary" : "btn";
  btn.innerText = rightText;
  btn.onclick = onClick;

  row.appendChild(left);
  row.appendChild(btn);
  return row;
}

// ============================
// 트리 next
// ============================
async function treeNext() {
  renderState();
  showHelpCard(false);
  clearHelpArea();

  setStatus("트리 옵션을 불러오는 중…", "info");

  const payload = { ...window.state };
  const { __stale, data } = await postJSON("/tree/next", payload);
  if (__stale) return;

  console.log("[/tree/next]", data);

  const next_level = data.next_level;
  const options = data.options || [];
  renderStepHeader(next_level, data.candidate_count);

  const optEl = $("options");
  optEl.innerHTML = "";

  const showHelp = ["route_l2", "route_l3", "route_l4"].includes(next_level);
  if (showHelp) {
    const helpRow = document.createElement("div");
    helpRow.className = "helpBar";
    helpRow.innerHTML = `
      <div>
        <div class="helpTitle">막혔나요?</div>
        <div class="helpSub">질문을 보고 상황을 입력하면, Neo4j 벡터검색으로 Top3를 추천해줘요.</div>
      </div>
    `;

    const helpBtn = document.createElement("button");
    helpBtn.className = "btn primary";
    helpBtn.innerText = "모르겠어요 (HELP)";
    helpBtn.onclick = () => openHelp();

    helpRow.appendChild(helpBtn);
    optEl.appendChild(helpRow);
  }

  options.forEach((opt) => {
    if (typeof opt === "object" && opt.case_code && opt.title) {
      const row = createOptionRow({
        leftTitle: opt.title,
        leftSub: `case_code: ${opt.case_code}`,
        rightText: "확정",
        primary: true,
        onClick: async () => loadCaseDetail(opt.case_code),
      });
      optEl.appendChild(row);
      return;
    }

    const code = opt;
    const label = labelOf(code);
    const row = createOptionRow({
      leftTitle: label,
      leftSub: `code: ${code}`,
      rightText: "선택",
      onClick: async () => {
        if (next_level === "route_l2") window.state.route_l2 = code;
        else if (next_level === "route_l3") window.state.route_l3 = code;
        else if (next_level === "route_l4") window.state.route_l4 = code;
        await treeNext();
      },
    });
    optEl.appendChild(row);
  });

  setStatus("선택지를 불러왔어요.", "ok");
}

// ============================
// HELP
// ============================
async function openHelp() {
  showHelpCard(true);
  clearHelpArea();

  $("helpQuestions").innerHTML = `<div class="skeleton">질문을 불러오는 중…</div>`;
  setStatus("도움 질문을 불러오는 중…", "info");

  const payload = { ...window.state };
  const { __stale, data } = await postJSON("/help/questions", payload);
  if (__stale) return;

  console.log("[/help/questions]", data);

  const qs = data.questions || [];
  const list = qs
    .map((q, i) => `<li><span class="qNo">${i + 1}</span><span class="qText">${escapeHtml(q)}</span></li>`)
    .join("");

  $("helpQuestions").innerHTML = `<ul class="qList">${list}</ul>`;
  setStatus("도움 질문을 확인하고 사고 상황을 입력해보세요.", "ok");
}

async function recommend() {
  const user_note = $("userNote").value.trim();
  if (!user_note) {
    alert("사고 상황을 입력해줘");
    return;
  }

  setStatus("Neo4j 추천을 요청하는 중…", "info");

  const payload = { ...window.state, user_note };
  const { __stale, data } = await postJSON("/help/recommend", payload);
  if (__stale) return;

  console.log("[/help/recommend]", data);

  const topk = data.topk || [];
  const el = $("recommendResult");

  if (topk.length === 0) {
    el.innerHTML = `<div class="emptyBox">추천 결과가 없습니다.</div>`;
    setStatus("추천 결과 없음", "warn");
    return;
  }

  el.innerHTML = `
    <div class="recGrid">
      ${topk
        .map((r) => {
          const score = r.score != null ? Number(r.score).toFixed(4) : null;
          return `
          <div class="recCard">
            <div class="recTitle">${escapeHtml(r.title || "-")}</div>
            <div class="recMeta">
              <span class="mono">${escapeHtml(r.case_code || "-")}</span>
              ${score ? `<span class="pill score">score ${score}</span>` : ""}
            </div>
            ${r.url ? `<a class="recLink" href="${r.url}" target="_blank" rel="noreferrer">원문 URL 열기 ↗</a>` : `<div class="recLink muted">URL 없음</div>`}
            <button class="btn primary full" data-code="${escapeHtml(r.case_code)}">이걸로 확정</button>
          </div>
        `;
        })
        .join("")}
    </div>
  `;

  el.querySelectorAll("button[data-code]").forEach((btn) => {
    btn.onclick = async () => {
      const code = btn.getAttribute("data-code");
      await loadCaseDetail(code);
    };
  });

  setStatus("추천 결과를 확인하고 확정해보세요.", "ok");
}

// ============================
// case detail (LLM 포함) + (NEW) 가감요소 표시
// ============================
async function loadCaseDetail(case_code) {
  setButtonsDisabled(true);
  showFinalLoading();
  setStatus("최종 결과 + LLM 요약을 불러오는 중… (느릴 수 있음)", "info");

  try {
    const { __stale, data } = await getJSON(`/cases/${encodeURIComponent(case_code)}`);
    if (__stale) return;

    console.log("[/cases/{case_code}]", data);

    $("finalTitle").innerText = `✅ ${data.title} (${data.case_code})`;
    $("finalJson").innerText = JSON.stringify(data, null, 2);

    const reportEl = $("finalReport");
    reportEl.style.display = "block";

    // 1) LLM 리포트
    if (data.final_report_md) {
      reportEl.innerHTML = renderMarkdownLite(data.final_report_md);
    } else if (data.final_report_text) {
      reportEl.innerHTML = `<div class="md"><p>${escapeHtml(data.final_report_text).replace(/\n/g, "<br/>")}</p></div>`;
    } else {
      reportEl.innerHTML = `<div class="emptyBox">LLM 리포트가 비어있어요. (final_report_md 또는 final_report_text 확인)</div>`;
    }

    // 2) (NEW) 가감요소 섹션
    reportEl.innerHTML += `
      <hr/>
      <h3>과실 최종 확정 전, 이런 수정요소를 확인하세요</h3>
      <div class="muted">상황에 따라 과실이 달라질 수 있습니다.</div>
      ${renderAdjustmentText(data.adjustment_text)}
    `;
    bindModifierButtons(reportEl);

    setStatus("최종 결과를 표시했어요.", "ok");
  } catch (e) {
    console.error(e);
    setStatus(`오류: ${String(e.message || e)}`, "warn");
    $("finalReport").style.display = "block";
    $("finalReport").innerHTML = `<div class="emptyBox">최종 결과 로딩 실패: ${escapeHtml(String(e.message || e))}</div>`;
  } finally {
    hideFinalLoading();
    setButtonsDisabled(false);
  }
}

// 아주 라이트한 마크다운 렌더 (외부 라이브러리 없이)
function renderMarkdownLite(md) {
  const esc = (s) => String(s)
    .replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;");

  let html = esc(md);

  html = html
    .replace(/`([^`]+)`/g, "<code>$1</code>")
    .replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>");

  html = html
    .replace(/^### (.*)$/gm, "<h3>$1</h3>")
    .replace(/^## (.*)$/gm, "<h2>$1</h2>")
    .replace(/^# (.*)$/gm, "<h1>$1</h1>");

  html = html
    .replace(/^\- (.*)$/gm, "<li>$1</li>")
    .replace(/(<li>.*<\/li>\n?)+/g, (m) => `<ul>${m}</ul>`);

  html = html.replace(/(https?:\/\/[^\s)]+)\b/g, `<a href="$1" target="_blank" rel="noreferrer">$1</a>`);
  html = html.replace(/\n/g, "<br/>");

  return `<div class="md">${html}</div>`;
}

// ============================
// init / reset
// ============================
function resetState() {
  window.state = { domain_l1: null, route_l2: null, route_l3: null, route_l4: null };
  clearFinal();
  showHelpCard(false);
  clearHelpArea();
  renderState();
}

async function init() {
  try { await loadLabels(); } catch (_) {}

  const optEl = $("options");
  optEl.innerHTML = "";

  $("stepTitle").innerHTML = `
    <div class="stepHead">
      <div>
        <div class="stepLabel">시작</div>
        <div class="stepTitle">domain_l1 선택</div>
      </div>
      <div class="badge">3 options</div>
    </div>
  `;

  ["CAR_CAR", "CAR_PED", "CAR_BIK"].forEach((d) => {
    const row = createOptionRow({
      leftTitle: labelOf(d),
      leftSub: `code: ${d}`,
      rightText: "시작",
      primary: true,
      onClick: async () => {
        window.state.domain_l1 = d;
        await treeNext();
      },
    });
    optEl.appendChild(row);
  });

  renderState();
  setStatus("API_BASE 확인 후 시작을 눌러보세요.", "info");
}

// ============================
// 이벤트 바인딩
// ============================
$("btnInit").onclick = () => init();
$("btnReset").onclick = () => { resetState(); init(); };
$("btnRecommend").onclick = () => recommend();

$("toggleJson").onclick = () => {
  const pre = $("finalJson");
  const hidden = pre.style.display === "none";
  pre.style.display = hidden ? "block" : "none";
  $("toggleJson").innerText = hidden ? "원본 JSON 숨기기" : "원본 JSON 보기";
};

// init
resetState();
init();
