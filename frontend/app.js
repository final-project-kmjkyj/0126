// app.js
// - 디자인 개선(HTML/CSS 쪽)
// - LLM 생성 중 로딩/경과시간 표시
// - 불필요한 자동 호출 제거 (버튼 클릭 때만 추천/확정)
// - final_report_md / final_report_text 우선 표시

window.state = {
  domain_l1: null,
  route_l2: null,
  route_l3: null,
  route_l4: null,
};

let routeLabels = {}; // route_labels_ko.json 로딩해서 채움

// (선택) 레이스 방지: 가장 마지막 요청만 화면 반영
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
// 한글 라벨 로드
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
  // 최신 요청만 반영
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

function setButtonsDisabled(disabled) {
  ["btnInit", "btnReset", "btnRecommend", "toggleJson"].forEach((id) => {
    const el = $(id);
    if (el) el.disabled = disabled;
  });
  // 옵션 버튼도 같이
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
    // title 단계: {case_code,title}
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
// case detail (LLM 포함)
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

    // JSON
    $("finalJson").innerText = JSON.stringify(data, null, 2);

    // LLM report
    const reportEl = $("finalReport");

    if (data.final_report_md) {
      reportEl.style.display = "block";
      reportEl.innerHTML = renderMarkdownLite(data.final_report_md);
    } else if (data.final_report_text) {
      reportEl.style.display = "block";
      reportEl.innerHTML = `<div class="md"><p>${escapeHtml(data.final_report_text).replace(/\n/g, "<br/>")}</p></div>`;
    } else {
      reportEl.style.display = "block";
      reportEl.innerHTML = `<div class="emptyBox">LLM 리포트가 비어있어요. (백엔드에서 final_report_md 또는 final_report_text 내려주는지 확인)</div>`;
    }

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
// - 헤딩(#/##/###), 굵게(**), 코드(``), 리스트(-), 링크(http)
function renderMarkdownLite(md) {
  const esc = (s) => String(s)
    .replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;");

  let html = esc(md);

  // inline
  html = html
    .replace(/`([^`]+)`/g, "<code>$1</code>")
    .replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>");

  // headings
  html = html
    .replace(/^### (.*)$/gm, "<h3>$1</h3>")
    .replace(/^## (.*)$/gm, "<h2>$1</h2>")
    .replace(/^# (.*)$/gm, "<h1>$1</h1>");

  // unordered list
  html = html
    .replace(/^\- (.*)$/gm, "<li>$1</li>")
    .replace(/(<li>.*<\/li>\n?)+/g, (m) => `<ul>${m}</ul>`);

  // link
  html = html.replace(/(https?:\/\/[^\s)]+)\b/g, `<a href="$1" target="_blank" rel="noreferrer">$1</a>`);

  // line breaks
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
