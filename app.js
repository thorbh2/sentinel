import { makeReader, write, connectWallet, activeAccount, balanceOf, short, toGen, GEN, fmtErr }
  from "./shared/genlayer-lite.js";
import { icon, setIcons } from "./shared/icons.js";

const CONTRACT = "0xFDF377cB5Fb982B4D3f908FB8D3D9dA7aD529032";
const { read } = makeReader(CONTRACT);

const ASSERTED = 0, DISPUTED = 1, RULED = 2;
const V_TRUE = 1, V_FALSE = 2;
let account = null, claims = [], selected = null;
const $ = (id) => document.getElementById(id);
const esc = (s) => (s || "").replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));

$("contractFoot").innerHTML = `NODE ${short(CONTRACT)}`;
setIcons();

function toast(msg, kind = "", title = "sys") {
  const el = document.createElement("div"); el.className = "toast " + kind;
  el.innerHTML = `<span class="tt">${title}</span>`; el.appendChild(document.createTextNode(msg));
  $("log").appendChild(el); setTimeout(() => el.remove(), kind === "err" ? 16000 : 5200);
}

async function refreshWallet() {
  account = await activeAccount();
  const slot = $("walletslot");
  if (account) { let bal = 0n; try { bal = await balanceOf(account); } catch (_) {} slot.innerHTML = `<span class="mono" style="font-size:11px;color:var(--txt2)">${short(account)} · ${toGen(bal)} GEN</span>`; }
  else { slot.innerHTML = `<button class="btn sm" id="connectBtn">Connect<span class="ic">${icon("arrowRight")}</span></button>`; $("connectBtn").onclick = doConnect; }
}
async function doConnect() { try { account = await connectWallet(); toast("Operator linked on studionet.", "ok", "link"); await refreshWallet(); } catch (e) { toast(fmtErr(e), "err", "link"); } }
async function ensureWallet() { if (!account) account = await connectWallet(); await refreshWallet(); }

function vinfo(c) {
  const st = Number(c.status), v = Number(c.verdict);
  if (st === RULED) { if (v === V_TRUE) return ["v-true", "VERIFIED TRUE"]; if (v === V_FALSE) return ["v-false", "DEBUNKED"]; return ["v-unclear", "UNCLEAR"]; }
  return st === DISPUTED ? ["v-disp", "DISPUTED"] : ["v-assert", "ASSERTED"];
}

async function load() {
  try {
    const count = Number(await read("get_claim_count"));
    const out = [];
    for (let i = 0; i < count; i++) out.push({ id: i, ...(await read("get_claim", [i])) });
    claims = out; renderFeed(); $("feedMeta").textContent = count + " rec";
    const open = out.filter((c) => Number(c.status) !== RULED).length;
    const bonded = out.reduce((a, c) => { const disp = c.challenger && !/^0x0+$/.test(c.challenger); return a + BigInt(c.bond) * (disp ? 2n : 1n); }, 0n);
    $("stTotal").textContent = count; $("stOpen").textContent = open; $("stBonded").textContent = toGen(bonded.toString());
    if (selected != null) renderInspect(selected);
  } catch (e) { $("feed").innerHTML = `<div class="empty">REGISTRY OFFLINE<br>${fmtErr(e)}</div>`; }
}

function renderFeed() {
  const f = $("feed");
  if (!claims.length) { f.innerHTML = `<div class="empty">NO CASES ON RECORD.<br>OPEN THE FIRST ONE.</div>`; return; }
  f.innerHTML = "";
  [...claims].reverse().forEach((c) => {
    const [cls, label] = vinfo(c);
    const row = document.createElement("div"); row.className = "tnode" + (selected === c.id ? " sel" : "");
    row.innerHTML = `<div class="id">CASE-${String(c.id).padStart(3, "0")}</div>
      <div class="stmt">${esc(c.statement)}</div>
      <div class="meta"><span class="vtag ${cls}">${label}</span><span class="bondtag">${toGen(c.bond)} GEN</span></div>`;
    row.onclick = () => { selected = c.id; renderFeed(); renderInspect(c.id); };
    f.appendChild(row);
  });
}

function renderInspect(id) {
  const c = claims.find((x) => x.id === id); if (!c) return;
  const st = Number(c.status), v = Number(c.verdict);
  const disputed = c.challenger && !/^0x0+$/.test(c.challenger);
  let verdictHtml = "";
  if (st === RULED) {
    const vb = v === V_TRUE ? "vb-true" : v === V_FALSE ? "vb-false" : "vb-unclear";
    const big = v === V_TRUE ? "TRUE" : v === V_FALSE ? "FALSE" : "UNCLEAR";
    verdictHtml = `<div class="verdictbox ${vb}"><div class="big disp">${big}</div><div class="why">${c.rationale ? esc(c.rationale) : "Adjudicated by validator consensus over the live evidence."}</div></div>`;
  }
  let actions = "";
  if (st === ASSERTED) actions = `<button class="btn amber" id="challengeBtn">Challenge · bond ${toGen(c.bond)} GEN against</button><button class="btn" id="adjBtn">Adjudicate from evidence <span class="ic">${icon("arrowRight")}</span></button>`;
  else if (st === DISPUTED) actions = `<button class="btn" id="adjBtn">Adjudicate from evidence <span class="ic">${icon("arrowRight")}</span></button>`;
  $("inspect").innerHTML = `<div class="casefile">
    <div class="cf-id">CASE FILE · CASE-${String(id).padStart(3, "0")}</div>
    <div class="cf-stmt disp">${esc(c.statement)}</div>
    <div class="cf-rule">CLAIM UNDER VERIFICATION · contract reads the cited source and validators must agree</div>
    ${verdictHtml}
    <div class="bondface">
      <div class="side t"><div class="lab">Asserts True</div><div class="amt disp">${toGen(c.bond)}</div><div class="who">${short(c.asserter)}</div></div>
      <div class="side f"><div class="lab">Asserts False</div><div class="amt disp">${disputed ? toGen(c.bond) : "-"}</div><div class="who">${disputed ? short(c.challenger) : "open seat"}</div></div>
    </div>
    <div class="specs">
      <div class="spec"><div class="l">Evidence source</div><div class="v"><a href="${esc(c.evidence_url)}" target="_blank" rel="noopener">${esc(c.evidence_url)}</a></div></div>
      <div class="spec"><div class="l">Pot at stake</div><div class="v">${toGen((BigInt(c.bond) * (disputed ? 2n : 1n)).toString())} GEN</div></div>
    </div>
    ${st !== RULED ? `<div class="actions">${actions}</div>` : `<div class="mono" style="color:var(--dim);font-size:12px">CASE CLOSED · ${c.paid ? "settlement disbursed" : "settled"}</div>`}
  </div>`;
  if (st === ASSERTED) $("challengeBtn").onclick = () => doChallenge(id, c.bond);
  if (st === ASSERTED || st === DISPUTED) $("adjBtn").onclick = () => doAdjudicate(id);
}

function openDrawer() { $("scrim").classList.add("on"); $("drawer").classList.add("on"); }
function closeDrawer() { $("scrim").classList.remove("on"); $("drawer").classList.remove("on"); }
function openFile() {
  $("drawerTitle").textContent = "File a claim";
  $("drawerBody").innerHTML = `
    <p style="color:var(--txt2);font-size:14.5px">Assert a claim, link the evidence the contract will read, and post your bond that it's true.</p>
    <label>Claim statement</label><input id="statement" maxlength="180" placeholder="X acquired Y for $2.4B in 2025" />
    <label>Evidence URL (contract reads this)</label><input id="url" placeholder="https://example.com/press-release" />
    <label>Bond (GEN)</label><input id="bond" type="number" min="0" step="0.1" value="1" />
    <button class="btn block" id="submitClaim" style="margin-top:18px">Post claim <span class="ic">${icon("arrowRight")}</span></button>`;
  $("submitClaim").onclick = doSubmit; openDrawer();
}

async function doSubmit() {
  const statement = $("statement").value.trim(), url = $("url").value.trim(), bond = parseFloat($("bond").value);
  if (!statement) return toast("Enter the claim statement.", "err", "file");
  if (!url) return toast("Evidence URL is required.", "err", "file");
  if (!(bond > 0)) return toast("Bond must be above zero.", "err", "file");
  const btn = $("submitClaim"); btn.disabled = true; btn.innerHTML = '<span class="spinner"></span> posting';
  try { await ensureWallet(); await write(CONTRACT, "assert_claim", [statement, url], GEN(bond)); toast("Claim filed on-chain.", "ok", "filed"); closeDrawer(); await load(); }
  catch (e) { toast(fmtErr(e), "err", "failed"); btn.disabled = false; btn.textContent = "Post claim"; }
}
async function doChallenge(id, bondWei) {
  const btn = $("challengeBtn"); btn.disabled = true; btn.innerHTML = '<span class="spinner"></span> bonding';
  try { await ensureWallet(); await write(CONTRACT, "challenge", [id], BigInt(bondWei)); toast("Counter-bond posted. Claim disputed.", "ok", "on-chain"); await load(); }
  catch (e) { toast(fmtErr(e), "err", "failed"); if (btn) { btn.disabled = false; btn.textContent = "Challenge"; } }
}
async function doAdjudicate(id) {
  if (!confirm("Adjudicate now? The contract reads the evidence page and validators must agree on the verdict. Calls a real LLM.")) return;
  const btn = $("adjBtn"); btn.disabled = true; btn.innerHTML = '<span class="spinner"></span> reading evidence';
  try { await ensureWallet(); toast("Validators are reading the evidence and converging…", "", "adjudicate"); await write(CONTRACT, "adjudicate", [id]); toast("Verdict recorded on-chain. Pot settled.", "ok", "ruled"); await load(); }
  catch (e) { toast(fmtErr(e), "err", "failed"); if (btn) { btn.disabled = false; btn.textContent = "Adjudicate from evidence"; } }
}

if (window.gsap) {
  gsap.registerPlugin(ScrollTrigger);
}

$("connectBtn").onclick = doConnect;
$("refreshBtn").onclick = load;
$("newClaimBtn").onclick = openFile;
$("closeDrawer").onclick = closeDrawer;
$("scrim").onclick = closeDrawer;
if (window.ethereum) window.ethereum.on?.("accountsChanged", refreshWallet);

refreshWallet();
load();
