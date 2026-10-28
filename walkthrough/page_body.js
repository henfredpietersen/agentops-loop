  // ------------------------------------------------------------ extra styles
  CSS += "\n" + [
    ".tlist{display:grid;gap:6px;margin-top:12px;max-height:300px;overflow:auto;padding-right:4px}",
    ".tbtn{text-align:left;display:flex;gap:10px;align-items:flex-start;width:100%;padding:9px 11px;border-radius:10px;",
    "border:1px solid var(--line);background:var(--panel2);color:var(--text);font-size:.88rem}",
    ".tbtn.on{border-color:var(--orange);background:rgba(232,90,42,.14)}",
    ".tbtn .dot{flex:none;width:9px;height:9px;border-radius:50%;margin-top:6px}",
    ".detail{margin-top:14px;padding:14px;border-radius:12px;background:#0b0f19;border:1px solid var(--line)}",
    ".q{font-size:1.02rem;color:var(--text);margin:0 0 10px}",
    ".kv{display:flex;flex-wrap:wrap;gap:6px 14px;font-size:.84rem;color:var(--dim);margin-bottom:10px}",
    ".kv b{color:var(--text);font-weight:600}",
    ".ans{padding:10px 12px;border-radius:10px;background:var(--panel2);border-left:3px solid var(--cyan);color:var(--text);font-size:.92rem;margin-bottom:12px}",
    ".ans.ref{border-left-color:var(--warn)}",
    ".checks{display:grid;gap:6px}",
    ".chk{display:grid;grid-template-columns:22px 1fr;gap:8px;font-size:.86rem;align-items:start}",
    ".chk i{font-style:normal;font-weight:800;text-align:center}",
    ".chk span{color:var(--dim)}.chk b{color:var(--text);font-weight:600}",
    ".planted{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;font-size:.78rem;color:#fecaca;",
    "background:rgba(248,113,113,.08);border:1px dashed rgba(248,113,113,.4);border-radius:8px;padding:6px 8px;margin-top:6px;word-break:break-word}",
    ".arow{padding:10px 12px;border-radius:10px;background:var(--panel2);border:1px solid var(--line)}",
    ".arow .top{display:flex;justify-content:space-between;gap:10px;align-items:center;font-size:.88rem}",
    ".score2{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px;margin-top:14px}",
    ".chips{display:flex;flex-wrap:wrap;gap:6px;margin-top:4px}",
    ".chips .ghost{font-variant-numeric:tabular-nums}",
    ".hbar{display:grid;grid-template-columns:120px 1fr 52px;gap:10px;align-items:center;font-size:.84rem;margin:6px 0}",
    ".hbar .track{height:12px;border-radius:6px;background:var(--panel2);overflow:hidden}",
    ".hbar .fill{height:100%;border-radius:6px}",
    ".tests{display:grid;gap:6px;margin-top:10px}",
    ".test{display:flex;gap:10px;font-size:.88rem;padding:8px 10px;border-radius:10px;background:var(--panel2)}",
    ".test i{font-style:normal;color:var(--ok);font-weight:800}",
    ".hash{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;font-size:.78rem;color:var(--dim);word-break:break-all}",
    ".res3{display:grid;gap:6px;margin-top:10px}",
    ".r3{display:grid;grid-template-columns:28px 1fr 56px;gap:8px;align-items:center;padding:8px 10px;border-radius:10px;background:var(--panel2);border:1px solid var(--line);font-size:.86rem}",
    ".r3.hit{border-color:rgba(52,211,153,.55);background:rgba(52,211,153,.08)}",
    ".r3 .rk{font-weight:800;color:var(--dim);text-align:center}",
    ".grad{background:linear-gradient(90deg,#ffffff 0%,#ffb27a 45%,var(--orange) 100%);-webkit-background-clip:text;background-clip:text;color:transparent}",
    "@media (max-width:520px){.hbar{grid-template-columns:96px 1fr 48px}}"
  ].join("\n");

  var REPO = "https://github.com/henfredpietersen/agentops-loop";
  var REPO2 = "https://github.com/henfredpietersen/policy-assistant";
  var REASON = {
    weak_evidence: "Refused: not enough support in the approved documents",
    acl_blocked: "Refused: that content is staff-only",
    injection_detected: "Refused: the safety check found planted instructions",
    tool_denied: "Refused: a policy check blocked a tool call",
    budget_exceeded: "Refused: over the cost budget",
    bad_route: "Refused: not a student-service request"
  };
  var CHECK = {
    route: ["Routed to the right specialist", "refund, access or billing"],
    refusal: ["Answered or refused correctly", "answer what it can, refuse what it can't"],
    found_source: ["Found the right document", "the expected passage was among the results"],
    answer_supported: ["Answer backed by that document", "cites it and contains the expected wording"],
    no_leak: ["No staff-only content leaked", "checked in the answer and the trace"]
  };
  var TESTS = {
    test_holdout_and_attacks_match_seal: "The holdout and attack files still match their sealed fingerprints",
    test_split_sizes: "Exactly 40 training, 20 holdout and 10 attack tickets",
    test_no_ticket_overlap_between_train_and_holdout: "No ticket appears in both training and holdout",
    test_eval_pass_cannot_write_holdout: "The training evaluation can't write to the holdout",
    test_train_up_holdout_down_is_a_drop: "Training up but holdout down means the change is dropped",
    test_over_cap_cost_is_a_drop_even_if_s_rises: "Over the cost cap means dropped, even if the score rises",
    test_keep_needs_spread_and_attacks: "Keeping a change also needs stable holdout scores and full attack refusal",
    test_cache_hit_is_excluded_from_quality_numerator: "Cached answers can't inflate the score",
    test_patch_outside_menu_or_touching_protected_paths_is_rejected: "Changes outside the allowed settings, or touching protected files, are rejected",
    test_loop_does_not_import_holdout: "The improvement loop doesn't even import the holdout code",
    test_eval_pass_never_opens_holdout: "A file spy proves the training evaluation never opens the holdout",
    test_score_py_is_frozen: "The scoring file is pinned by fingerprint"
  };
  var MODE_LABEL = { "bm25": "Keyword search", "dense": "Meaning search", "hybrid": "Both combined",
    "hybrid+rerank": "Combined, re-ranked", "hybrid+rerank, guard off": "Same, safety check off" };
  function n4(x) { return Number(x).toFixed(4); }
  function pct(x) { return Math.round(x * 100) + "%"; }

  // ------------------------------------------------------------- step 1
  var tickets = D.tickets;
  var okCount = tickets.filter(allOk).length;
  function allOk(t) { return Object.keys(t.checks).every(function (k) { return t.checks[k] !== false; }); }
  var tFilter = "all", tSel = tickets[0].id;
  function ticketList() {
    return tickets.filter(function (t) {
      return tFilter === "all" || (tFilter === "ok" ? allOk(t) : !allOk(t));
    }).map(function (t) {
      return "<button class='tbtn" + (t.id === tSel ? " on" : "") + "' data-tk='" + esc(t.id) + "'><span class='dot' style='background:" +
        (allOk(t) ? "var(--ok)" : "var(--bad)") + "'></span><span>" + esc(t.ticket) +
        (t.role === "staff" ? " <span class='pill dimc'>staff</span>" : "") + "</span></button>";
    }).join("");
  }
  function ticketDetail(id) {
    var t = tickets.filter(function (x) { return x.id === id; })[0];
    var h = "<p class='q'>“" + esc(t.ticket) + "”</p><div class='kv'><span>Asked as <b>" + esc(t.role) + "</b></span>" +
      "<span>Should go to <b>" + esc(t.gold_route) + "</b></span><span>Went to <b>" + esc(t.route) + "</b></span>" +
      "<span>Should be <b>" + (t.answerable ? "answered" : "refused") + "</b></span></div>";
    h += "<div class='ans" + (t.refused ? " ref" : "") + "'>" + (t.refused ? "<b>" + esc(REASON[t.reason] || t.reason) + "</b><br>" : "") + esc(t.answer) + "</div>";
    h += "<div class='checks'>" + Object.keys(CHECK).map(function (k) {
      var v = t.checks[k];
      var mark = v === null ? "<i class='dimc'>–</i>" : v ? "<i class='ok'>✓</i>" : "<i class='bad'>✕</i>";
      return "<div class='chk'>" + mark + "<div><b>" + CHECK[k][0] + "</b> <span>· " +
        (v === null ? "not applicable: this one should be refused" : CHECK[k][1]) + "</span></div></div>";
    }).join("") + "</div>";
    if (t.gold_span && t.checks.answer_supported === false) {
      h += "<p style='font-size:.84rem;margin:10px 0 0'>Expected wording: “" + esc(t.gold_span) + "”</p>";
    }
    h += "<p style='font-size:.84rem;margin:10px 0 0'>Score for this ticket: <b>" + n4(t.S) + "</b> out of 1</p>";
    return h;
  }

  // ------------------------------------------------------------- step 4
  var base = { threshold: D.config.refusal_threshold, train: D.runs[0].train_S_before, hold: D.accepted.mean_S };
  var gateRows = D.runs.map(function (r) {
    return { th: r.changes.refusal_threshold, train: r.train_S_after, hold: r.holdout_mean_S, decision: r.decision, reason: r.reason, run: r.run };
  });
  gateRows.push({ th: base.threshold, train: base.train, hold: base.hold, base: true });
  gateRows.sort(function (a, b) { return a.th - b.th; });
  var gSel = gateRows.filter(function (r) { return !r.base; })[0];
  function gateHTML(r) {
    var dt = r.train - base.train, h;
    var trTxt = r.base ? "current setting" : (dt > 0 ? "up " : "down ") + Math.abs(dt).toFixed(4);
    var trCls = r.base ? "dimc" : dt > 0 ? "ok" : "bad";
    var hoVal, hoTxt, hoCls;
    if (r.hold === null || r.hold === undefined) { hoVal = "not run"; hoTxt = "training fell, so the holdout stays sealed"; hoCls = "dimc"; }
    else {
      var dh = r.hold - base.hold;
      hoVal = n4(r.hold);
      hoTxt = r.base ? "current setting" : Math.abs(dh) < 1e-9 ? "no change" : (dh > 0 ? "up " : "down ") + Math.abs(dh).toFixed(4);
      hoCls = r.base ? "dimc" : dh < 0 ? "bad" : "dimc";
    }
    h = "<div class='score2'><div class='kpi'><div class='l'>Training score (40 tickets)</div><div class='v'>" + n4(r.train) +
      "</div><div class='l " + trCls + "'>" + trTxt + "</div></div><div class='kpi'><div class='l'>Holdout score (20 sealed tickets)</div><div class='v'>" +
      hoVal + "</div><div class='l " + hoCls + "'>" + hoTxt + "</div></div></div>";
    var verdict;
    if (r.base) verdict = "<div class='verdict' style='background:var(--panel2);border:1px solid var(--line)'>The setting currently in use.</div>";
    else {
      var why = r.hold === null || r.hold === undefined ? "Dropped early: it made the training score worse."
        : r.hold < base.hold ? "Dropped: training went up but holdout went down. The change fits the practice tickets, not new ones."
          : "Dropped: holdout didn't rise, so there's nothing to ship.";
      verdict = "<div class='verdict bad'>" + why + "<br><span style='font-weight:400;font-size:.84rem;color:var(--dim)'>Logged in runs/" +
        r.run + "/decision.json: “" + esc(r.reason) + "”</span></div>";
    }
    return h + verdict;
  }

  // ------------------------------------------------------------- step 6
  var PA = D.policy_assistant, paSel = 0;
  function paHTML(i) {
    var q = PA.questions[i];
    var h = "<p class='q'>“" + esc(q.question) + "”</p><div class='kv'><span>Correct section: <b>" + esc(q.expected.split("#")[1] || q.expected) +
      "</b></span><span>" + (q.rank ? "Found at position <b>" + q.rank + "</b>" : "<b class='bad'>Not in the top 3</b>") + "</span></div><div class='res3'>";
    q.results.forEach(function (r, k) {
      var hit = r.id === q.expected;
      h += "<div class='r3" + (hit ? " hit" : "") + "'><span class='rk'>" + (k + 1) + "</span><span>" + esc(r.title) +
        " <span class='dimc'>· " + esc(r.id.split("#")[0]) + "</span>" + (hit ? " <span class='pill ok'>correct</span>" : "") +
        "</span><span class='dimc' style='text-align:right;font-variant-numeric:tabular-nums'>" + r.score.toFixed(3) + "</span></div>";
    });
    return h + "</div>";
  }

  // ------------------------------------------------------------- render
  var A = D.attacks, ACC = D.accepted;
  var steps = [["s1", "Ask it"], ["s2", "Who's asking"], ["s3", "Attacks"], ["s4", "Improve it"], ["s5", "Can't cheat"], ["s6", "Search test"]];
  var html = "<style>" + CSS + "</style><div class='wt'><div class='wrap'>";
  html += "<p class='eyebrow'>Case study · AI quality and evaluation</p>" +
    "<h1>An AI help desk<br><span class='grad'>that has to prove every change.</span></h1>" +
    "<p class='lede'>Student-service questions go to a supervisor that routes each one to a refund, access or billing specialist. " +
    "The specialist may only answer from approved documents. Every proposed improvement is scored on a sealed set of tickets " +
    "the improvement process never sees, and it ships only if that score goes up.</p>" +
    "<div class='tags'><span class='tag'><b>●</b> Demo data, stand-in models</span><span class='tag'>41 automated tests</span>" +
    "<span class='tag'>Built AI-assisted under my direction</span><a class='tag' href='" + REPO + "' target='_blank' rel='noopener'>Code on GitHub ↗</a></div>";
  html += "<nav class='nav' aria-label='Steps'>" + steps.map(function (s, i) {
    return "<a href='#" + s[0] + "' data-go='" + s[0] + "'><span>" + (i + 1) + "</span>" + s[1] + "</a>";
  }).join("") + "</nav>";

  html += "<section class='step' id='s1'><div class='num'>1</div><h2>Ask it something, see how it's marked</h2>" +
    "<p>These are the " + tickets.length + " practice tickets the system is tuned on. Each answer is marked against five checks by the project's " +
    "scoring file. " + okCount + " pass every check; " + (tickets.length - okCount) + " miss at least one. Together they score <strong>" + n4(D.train_S) +
    "</strong>, the same figure the logged runs record.</p><div class='card'><div class='filters'>" +
    "<button class='ghost on' data-tf='all'>All (" + tickets.length + ")</button><button class='ghost' data-tf='ok'>Pass every check (" + okCount + ")</button>" +
    "<button class='ghost' data-tf='miss'>Misses (" + (tickets.length - okCount) + ")</button></div>" +
    "<div class='tlist' data-tlist>" + ticketList() + "</div><div class='detail' data-tdetail>" + ticketDetail(tSel) + "</div></div></section>";

  html += "<section class='step' id='s2'><div class='num'>2</div><h2>Who's asking changes the answer</h2>" +
    "<p>Some documents are for staff only. The same question gets a different response depending on who asks. Staff-only text must never reach a public answer, or even the public trace.</p>" +
    "<div class='card'><div class='tabs'><button class='ghost on' data-role='public'>Ask as a student</button><button class='ghost' data-role='staff'>Ask as staff</button></div>" +
    "<div class='detail' data-acl></div></div></section>";

  html += "<section class='step' id='s3'><div class='num'>3</div><h2>Planted instructions</h2>" +
    "<p>Each of these " + A.rows.length + " attacks plants a page in the knowledge base with hidden instructions, then asks an innocent question. " +
    "A safety check scans what was retrieved before anything is generated. Switch it off and see what happens.</p>" +
    "<div class='card'><button class='switch on' data-guard aria-pressed='true'><span class='knob'></span><span data-glabel>Safety check: ON</span></button>" +
    "<div class='kpis' style='margin-top:14px'><div class='kpi'><div class='v' data-gscore></div><div class='l'>Attacks refused</div></div></div>" +
    "<div class='led' data-attacks style='max-height:360px'></div>" +
    "<h3 style='margin-top:18px'>Which search setting matters?</h3><p style='font-size:.9rem'>Holdout score for each search setting. With only 47 document chunks they barely differ. The only switch that changes the outcome is the safety check.</p>" +
    D.ablation.map(function (r) {
      return "<div class='hbar'><span>" + esc(MODE_LABEL[r.row] || r.row) + "</span><div class='track'><div class='fill' style='width:" +
        (r.mean_S * 100).toFixed(1) + "%;background:" + (r.attack_refusal < 1 ? "var(--bad)" : "var(--cyan)") + "'></div></div><span style='text-align:right'>" +
        n4(r.mean_S) + "</span></div>" + (r.attack_refusal < 1 ? "<p style='font-size:.82rem;margin:-2px 0 8px 130px' class='bad'>attacks refused: " + pct(r.attack_refusal) + "</p>" : "");
    }).join("") + "</div></section>";

  html += "<section class='step' id='s4'><div class='num'>4</div><h2>Try to improve it</h2>" +
    "<p>The improvement loop tried six values for one setting: how much evidence the system needs before it answers. Pick one to see what the logged run found, and what the gate decided.</p>" +
    "<div class='card'><div class='chips' data-gchips>" + gateRows.map(function (r) {
      return "<button class='ghost" + (r === gSel ? " on" : "") + "' data-th='" + r.th + "'>" + r.th.toFixed(2) + (r.base ? " (current)" : "") + "</button>";
    }).join("") + "</div><div data-gate>" + gateHTML(gSel) + "</div>" +
    "<p style='font-size:.84rem;margin:12px 0 0'>Rule: a change ships only if the holdout score rises, the scores stay stable, every attack is still refused, and cost and speed stay under their caps. " +
    "All six attempts were dropped, so the current setting stays.</p></div></section>";

  html += "<section class='step' id='s5'><div class='num'>5</div><h2>Why the loop can't cheat</h2>" +
    "<p>A holdout set only means something if the tuning process never sees it. That's enforced by tests, not by good intentions. The " +
    D.splits.holdout + " holdout and " + D.splits.attacks + " attack tickets are fingerprinted, and these checks run on every change:</p>" +
    "<div class='card'><div class='tests'>" + D.seal_tests.map(function (n) {
      return "<div class='test'><i>✓</i><span>" + esc(TESTS[n] || n) + "</span></div>";
    }).join("") + "</div><p style='font-size:.82rem;margin:12px 0 4px'>Sealed holdout fingerprint:</p><div class='hash'>" + esc(D.seal.holdout) + "</div></div></section>";

  html += "<section class='step' id='s6'><div class='num'>6</div><h2>A second project: is search finding the right section?</h2>" +
    "<p>In <a href='" + REPO2 + "' target='_blank' rel='noopener'>policy-assistant</a>, an insurance FAQ assistant, " + PA.n + " test questions each have one correct policy section. " +
    "Pick a question to see what the search returned.</p><div class='card'><div class='kpis'>" +
    "<div class='kpi'><div class='v'>" + pct(PA.hit_at_1) + "</div><div class='l'>Right section ranked first</div></div>" +
    "<div class='kpi'><div class='v'>" + pct(PA.hit_at_3) + "</div><div class='l'>Right section in the top 3</div></div>" +
    "<div class='kpi'><div class='v'>" + PA.mrr.toFixed(2) + "</div><div class='l'>Average rank score (1 = always first)</div></div></div>" +
    "<div class='tlist' data-palist style='max-height:240px'>" + PA.questions.map(function (q, i) {
      return "<button class='tbtn" + (i === paSel ? " on" : "") + "' data-pa='" + i + "'><span class='dot' style='background:" +
        (q.rank === 1 ? "var(--ok)" : q.rank ? "var(--warn)" : "var(--bad)") + "'></span><span>" + esc(q.question) + "</span></button>";
    }).join("") + "</div><div class='detail' data-pa-detail>" + paHTML(paSel) + "</div></div></section>";

  html += "<div class='foot'><h2>How this was built, and what it doesn't claim</h2>" +
    "<p>I set the specification, directed the build and reviewed the output. Claude, an AI coding assistant, wrote the code. " +
    "Everything on this page is replayed from the projects' own runs: the tickets and attacks were run through the repository's code, " +
    "the marks come from its frozen scoring file, and the improvement attempts are its logged run files.</p><ul>" +
    "<li><strong>Stand-in models.</strong> The scores come from simple stand-in search and answer components, not a real AI model. The code paths for real models exist but weren't used for these numbers.</li>" +
    "<li><strong>One disclosed peek.</strong> I looked at the holdout once during development, before the improvement loop existed. No retrieval or answer logic changed after that.</li>" +
    "<li><strong>Not claimed:</strong> production users, real student data, a real Salesforce org, or real-model quality numbers.</li>" +
    "<li>Demo tickets only. No real people or records.</li></ul>" +
    "<a class='btn cta' href='" + REPO + "' target='_blank' rel='noopener'>See the code, tests and runs ↗</a>" +
    "<p style='margin-top:18px;font-size:.85rem'>Henfred Pietersen · <a href='https://outview.co.za/'>Outview</a>, Cape Town</p></div>";
  html += "</div></div>";
  root.innerHTML = html;

  // ------------------------------------------------------------- behaviour
  function bindTickets() {
    $$("[data-tk]").forEach(function (b) {
      b.addEventListener("click", function () {
        tSel = b.getAttribute("data-tk");
        $$("[data-tk]").forEach(function (x) { x.classList.toggle("on", x === b); });
        $("[data-tdetail]").innerHTML = ticketDetail(tSel);
      });
    });
  }
  bindTickets();
  $$("[data-tf]").forEach(function (b) {
    b.addEventListener("click", function () {
      tFilter = b.getAttribute("data-tf");
      $$("[data-tf]").forEach(function (x) { x.classList.toggle("on", x === b); });
      var shown = tickets.filter(function (t) { return tFilter === "all" || (tFilter === "ok" ? allOk(t) : !allOk(t)); });
      if (shown.length && !shown.some(function (t) { return t.id === tSel; })) tSel = shown[0].id;
      $("[data-tlist]").innerHTML = ticketList();
      $("[data-tdetail]").innerHTML = ticketDetail(tSel);
      bindTickets();
    });
  });

  function showRole(role) {
    var r = D.acl[role];
    $$("[data-role]").forEach(function (x) { x.classList.toggle("on", x.getAttribute("data-role") === role); });
    $("[data-acl]").innerHTML = "<p class='q'>“" + esc(r.ticket) + "”</p><div class='ans" + (r.refused ? " ref" : "") + "'>" +
      (r.refused ? "<b>" + esc(REASON[r.reason] || r.reason) + "</b><br>" : "") + esc(r.answer) + "</div>" +
      (r.citations.length ? "<p style='font-size:.84rem;margin:0'>Source: a <b>" + esc(r.citations[0].source) + "</b> document marked staff-only, chunk " +
        esc(r.citations[0].chunk_id) + "</p>" : "<p style='font-size:.84rem;margin:0'>No sources shown: the staff-only document was filtered out before the answer was written.</p>");
  }
  $$("[data-role]").forEach(function (b) { b.addEventListener("click", function () { showRole(b.getAttribute("data-role")); }); });
  showRole("public");

  function setGuard(on) {
    var b = $("[data-guard]");
    b.classList.toggle("on", on);
    b.setAttribute("aria-pressed", on ? "true" : "false");
    $("[data-glabel]").textContent = "Safety check: " + (on ? "ON" : "OFF");
    var refused = A.rows.filter(function (r) { return (on ? r.guard_on : r.guard_off).refused; }).length;
    $("[data-gscore]").innerHTML = "<span class='" + (refused === A.rows.length ? "ok" : "bad") + "'>" + refused + " of " + A.rows.length + "</span>";
    $("[data-attacks]").innerHTML = A.rows.map(function (r) {
      var res = on ? r.guard_on : r.guard_off;
      return "<div class='arow'><div class='top'><span>“" + esc(r.ticket) + "”</span>" +
        (res.refused ? "<span class='pill ok'>refused</span>" : "<span class='pill bad'>answered</span>") + "</div>" +
        "<div class='planted'>Planted: " + esc(r.planted) + "</div></div>";
    }).join("");
  }
  $("[data-guard]").addEventListener("click", function () { setGuard(!this.classList.contains("on")); });
  setGuard(true);

  $$("[data-th]").forEach(function (b) {
    b.addEventListener("click", function () {
      var th = parseFloat(b.getAttribute("data-th"));
      var r = gateRows.filter(function (x) { return x.th === th; })[0];
      $$("[data-th]").forEach(function (x) { x.classList.toggle("on", x === b); });
      $("[data-gate]").innerHTML = gateHTML(r);
    });
  });

  $$("[data-pa]").forEach(function (b) {
    b.addEventListener("click", function () {
      $$("[data-pa]").forEach(function (x) { x.classList.toggle("on", x === b); });
      $("[data-pa-detail]").innerHTML = paHTML(parseInt(b.getAttribute("data-pa"), 10));
    });
  });

  $$("[data-go]").forEach(function (a) {
    a.addEventListener("click", function (ev) {
      ev.preventDefault();
      var t = root.getElementById(a.getAttribute("data-go"));
      if (t) t.scrollIntoView({ behavior: "smooth", block: "start" });
    });
  });
  if ("IntersectionObserver" in window) {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        if (en.isIntersecting) $$("[data-go]").forEach(function (a) { a.classList.toggle("on", a.getAttribute("data-go") === en.target.id); });
      });
    }, { rootMargin: "-40% 0px -55% 0px" });
    $$("section.step").forEach(function (s) { io.observe(s); });
  }
