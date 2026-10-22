// The Hermes playground: ask a question over the corporate knowledge graph, in the browser.
// The query comes from a recorded Hermes system, or from a model you run yourself; it is run by Oxigraph (WebAssembly)
// on the real graph (about 26.6k triples), and can be replayed one pattern at a time like the planner's explorer.
// Prompt building and query extraction are ports of hermes.systems.training_free and hermes.validate.
var HP = (function () {
  // ---- ports of the Python ----
  var FENCE = /```(?:sparql)?\s*([\s\S]*?)```/i;
  var QUERY = /((?:PREFIX\s+\S+\s*<[^>]+>\s*)*(?:SELECT|ASK|CONSTRUCT|DESCRIBE)\b[\s\S]+)/i;
  var MODIFIER = /^(GROUP\s+BY|ORDER\s+BY|HAVING|LIMIT|OFFSET)\b/i;
  function extractSparql(content) {
    var fenced = FENCE.exec(content || ""), text = fenced ? fenced[1] : content || "", match = QUERY.exec(text);
    return (match ? match[1] : text).trim();
  }
  function liftModifiers(sparql) {
    var m = /\bWHERE\b/i.exec(sparql);
    if (!m) return sparql;
    var start = sparql.indexOf("{", m.index + m[0].length);
    if (start < 0) return sparql;
    var depth = 0, end = null;
    for (var i = start; i < sparql.length; i++) {
      if (sparql[i] === "{") depth++;
      else if (sparql[i] === "}") { depth--; if (depth === 0) { end = i; break; } }
    }
    if (end === null) return sparql;
    var kept = [], moved = [], inner = 0;
    sparql.slice(start + 1, end).split(/\r\n|\r|\n/).forEach(function (line) {
      if (inner === 0 && MODIFIER.test(line.trim())) moved.push(line.trim()); else kept.push(line);
      inner += (line.split("{").length - 1) - (line.split("}").length - 1);
    });
    if (!moved.length) return sparql;
    var body = kept.join("\n").replace(/\s+$/, "");
    return sparql.slice(0, start + 1) + "\n" + body + "\n}\n" + moved.join("\n") + sparql.slice(end + 1);
  }
  function prepareDraft(content) {
    var sparql = extractSparql(content);
    if (!sparql) throw new Error("The model did not return a SPARQL query.");
    return liftModifiers(sparql);
  }
  function buildPrompt(question, vocab) {
    var classes = vocab.classes.map(function (c) { return "- " + c; }).join("\n") || "- (none found)";
    var properties = vocab.properties.map(function (p) { return "- " + p; }).join("\n") || "- (none found)";
    var prefixes = vocab.prefixes.map(function (p) { return "PREFIX " + p[0] + ": <" + p[1] + ">"; }).join("\n");
    return [
      "Write one SPARQL query for this competency question. Use only the prefixes and terms below. Match the question to the labels in quotes. " +
        "Put triple patterns inside WHERE { }. Put ORDER BY and LIMIT after that block. Do not put SELECT inside FILTER. Do not copy the shape example terms. Return only the query.",
      "Shape:\nPREFIX ex: <http://example.org/>\nSELECT ?item ?value\nWHERE {\n  ?item a ex:Record ;\n        ex:relatedItem ?other ;\n        ex:amount ?value .\n}\nORDER BY DESC(?value)",
      "Prefixes:\n" + (prefixes || "(none)"), "Classes:\n" + classes, "Properties:\n" + properties, "Question: " + question.trim(),
    ].join("\n\n");
  }
  function repairPrompt(sparql, error) {
    return "Fix this SPARQL query and return only the corrected query.\nDo not put SELECT inside FILTER. Put GROUP BY, ORDER BY, and LIMIT after WHERE { }. " +
      "When grouping, select the aggregate, as in (MAX(?value) AS ?maxValue).\n\nError: " + error + "\nQuery:\n" + sparql;
  }

  // ---- the explorer: the WHERE group's top-level statements, added one at a time ----
  function whereBody(sparql) {
    var m = /\bWHERE\b/i.exec(sparql) || /\{/.exec(sparql);
    if (!m) return null;
    var start = sparql.indexOf("{", m.index), depth = 0;
    for (var i = start; i < sparql.length; i++) {
      if (sparql[i] === "{") depth++;
      else if (sparql[i] === "}") { depth--; if (depth === 0) return { head: sparql.slice(0, start), body: sparql.slice(start + 1, i), tail: sparql.slice(i + 1) }; }
    }
    return null;
  }
  function statements(body) {
    var out = [], cur = "", depth = 0, i = 0, inStr = null;
    while (i < body.length) {
      var c = body[i];
      if (inStr) { cur += c; if (c === "\\") { cur += body[++i] || ""; } else if (c === inStr) inStr = null; i++; continue; }
      if (c === '"' || c === "'") { inStr = c; cur += c; i++; continue; }
      if (c === "<" && /[^\s=<]/.test(body[i + 1] || " ") && body.indexOf(">", i) > 0 && !/\s/.test(body.slice(i, body.indexOf(">", i)))) { var e = body.indexOf(">", i); cur += body.slice(i, e + 1); i = e + 1; continue; }
      if ("({[".indexOf(c) >= 0) depth++;
      if (")}]".indexOf(c) >= 0) depth--;
      var rest = body.slice(i);
      if (depth === 0 && /^(FILTER|OPTIONAL|BIND|VALUES|MINUS)\b/i.test(rest) && cur.trim() && !/^\s*$/.test(cur)) { out.push(cur.trim()); cur = ""; }
      if (c === "." && depth === 0 && /\s|$/.test(body[i + 1] || " ") && !/\d$/.test(cur)) { out.push((cur + ".").trim()); cur = ""; i++; continue; }
      cur += c; i++;
    }
    if (cur.trim()) out.push(cur.trim());
    return out.filter(Boolean);
  }
  return { extractSparql: extractSparql, liftModifiers: liftModifiers, prepareDraft: prepareDraft, buildPrompt: buildPrompt, repairPrompt: repairPrompt, whereBody: whereBody, statements: statements };
})();

(async function () {
  var root = document.getElementById("hplay");
  if (!root) return;
  var h = PG.h, data, demo, handle;
  var STATUS = h("span", { class: "pg-status" });
  var question = h("input", { type: "text", id: "hp-question", class: "grow", list: "hp-questions", placeholder: "Ask a question about the company, for example: Who is Heinrich Hoch's manager?", "aria-label": "Question" });
  var datalist = h("datalist", { id: "hp-questions" });
  var editor = h("textarea", { id: "hp-sparql", spellcheck: "false", "aria-label": "SPARQL query", placeholder: "The query appears here. You can edit it before running it." });
  var promptBox = h("pre", { class: "pg-pre", id: "hp-prompt" });
  var result = h("div", { id: "hp-result", "aria-live": "polite" });
  var steps = h("div", { id: "hp-steps" });
  var where = h("p", { class: "pg-line", id: "hp-where" });
  var SYS = { "algebra-agent": "Algebra agent", prover: "Prover", uniqgen: "UniQGen", "training-free": "Training-free" };

  // The PREFIX lines the recorded queries were written with (the display data keeps only their bodies).
  function header() { return data.queryPrefixes.map(function (p) { return "PREFIX " + p[0] + ": <" + p[1] + ">"; }).join("\n") + "\n"; }
  function withPrefixes(body) { return /^\s*PREFIX/i.test(body) ? body : header() + body; }
  function setQuery(q, from) { editor.value = q; where.textContent = from || ""; steps.replaceChildren(); result.replaceChildren(); }
  function currentPrompt() { var q = question.value.trim() || "(your question)"; promptBox.textContent = HP.buildPrompt(q, data.vocabulary); return q; }

  async function run() {
    steps.replaceChildren(); result.replaceChildren();
    try { PG.show(result, PG.run(handle.store, editor.value, { "http://ld.company.org/prod-vocab/": "pv:", "http://ld.company.org/prod-instances/": "prodi:" })); }
    catch (e) { result.append(h("div", { class: "pg-error", role: "alert", text: String(e.message || e) })); }
  }
  function recorded(system) {
    var q = demo.questions.filter(function (x) { return x.question === question.value.trim(); })[0];
    if (!q) { result.replaceChildren(h("p", { class: "pg-note", text: "Recorded queries exist for the eight sample questions in the list. Pick one, or ask your own model." })); return; }
    var r = q.systems[system];
    setQuery(withPrefixes(r.sparql), "Recorded query of the " + SYS[system].toLowerCase() + " (Qwen3-14B): set F " + r.f + ", " + r.llm_calls + " model calls" + (r.error ? ", error: " + r.error : "") + ".");
    currentPrompt();
  }
  async function askModel() {
    var q = currentPrompt();
    if (!q || q === "(your question)") { result.replaceChildren(h("p", { class: "pg-note", text: "Type a question first." })); return; }
    where.textContent = "Asking " + PG.llmConfig().model + " at " + PG.llmConfig().base + "…"; result.replaceChildren();
    try {
      var raw = await PG.chat([{ role: "user", content: HP.buildPrompt(q, data.vocabulary) }]);
      var sparql = HP.prepareDraft(raw), err = parseError(sparql), note = "Model output, extracted like Hermes's training-free system.";
      if (err) { // the one repair the training-free system makes
        where.textContent = "The first draft did not parse (" + err + "). Asking once to repair it…";
        raw = await PG.chat([{ role: "user", content: HP.repairPrompt(sparql, err) }]); sparql = HP.prepareDraft(raw); err = parseError(sparql); note = "Repaired once, as the training-free system does.";
      }
      setQuery(sparql, note + (err ? " It still does not parse: " + err : ""));
      if (!err) await run();
    } catch (e) { where.textContent = ""; result.replaceChildren(h("div", { class: "pg-error", role: "alert", text: String(e.message || e) + (/Failed to fetch|NetworkError/.test(String(e)) ? "\nThe browser could not reach the endpoint. Is it running, and does it allow this page's origin (CORS)? See the note under Your model." : "") })); }
  }
  function parseError(sparql) { try { handle.store.query(sparql); return null; } catch (e) { return String(e.message || e).split("\n")[0]; } }

  async function explore() {
    steps.replaceChildren(); var parts = HP.whereBody(editor.value);
    if (!parts) { steps.append(h("p", { class: "pg-note", text: "Write a SELECT query with a WHERE { } group to explore it." })); return; }
    var items = HP.statements(parts.body), prefix = (/^[\s\S]*?(?=SELECT|ASK|CONSTRUCT|DESCRIBE)/i.exec(parts.head) || [""])[0], rows = [], prev = null, acc = [];
    for (var i = 0; i < items.length; i++) {
      acc.push(items[i]);
      var group = "{\n  " + acc.join("\n  ") + "\n}", row = { text: items[i] };
      try { var n = PG.run(handle.store, prefix + "SELECT (COUNT(*) AS ?n) WHERE " + group); row.count = +n.rows[0][0].text.replace(/^"|".*$/g, "").replace(/"/g, ""); }
      catch (e) { row.error = String(e.message || e).split("\n")[0]; }
      rows.push(row); if (row.count != null) prev = row.count;
    }
    var last = null;
    var table = h("table", { class: "pg-table" }, h("thead", {}, h("tr", {}, ["Step", "Added to the plan", "Solutions", "Change"].map(function (t) { return h("th", { scope: "col", text: t }); }))),
      h("tbody", {}, rows.map(function (r, i) {
        var change = r.count == null ? "" : last == null ? "" : r.count - last;
        var tr = h("tr", {}, h("td", { text: i + 1 }), h("td", { text: r.text }), h("td", { class: r.error ? "pg-blank" : "", text: r.error ? "error" : r.count.toLocaleString() }),
          h("td", { text: r.error ? r.error : change === "" ? "" : (change > 0 ? "+" : "") + change }));
        if (r.count != null) last = r.count; return tr;
      })));
    steps.append(h("h4", { text: "Replayed one pattern at a time" }), h("div", { class: "pg-scroll" }, table),
      h("p", { class: "pg-note", text: "After each step the planner sees how many solutions remain and how that changed; a step that sends the count to zero is a sign of a wrong pattern. Modifiers such as ORDER BY and LIMIT are not replayed." }));
  }

  // ---- layout ----
  root.className = "pg";
  var systemButtons = Object.keys(SYS).map(function (s) { return h("button", { type: "button", class: "btn", onclick: function () { recorded(s); } }, SYS[s]); });
  var vocabBox = h("div", {});
  root.replaceChildren(
    h("div", { class: "pg-panel" }, h("h3", { text: "1. Ask" }), h("p", { class: "pg-sub", text: "Pick a sample question or write your own. Then get a query from a recorded system, or from a model you run." }),
      h("div", { class: "pg-row" }, question, datalist),
      h("div", { class: "pg-row" }, h("span", { class: "pg-status", text: "Recorded query from:" }), systemButtons),
      h("div", { class: "pg-row" }, h("button", { type: "button", class: "btn solid", id: "hp-ask", onclick: askModel }, "Ask my model"), h("span", { class: "pg-status", id: "hp-model", text: "" })),
      where),
    h("div", { class: "pg-panel" }, h("h3", { text: "2. The query" }), editor,
      h("div", { class: "pg-row" }, h("button", { type: "button", class: "btn solid", id: "hp-run", onclick: run }, "Run on the graph"), h("button", { type: "button", class: "btn", id: "hp-explore", onclick: explore }, "Replay step by step"), STATUS),
      result, steps),
    h("details", { class: "pg-panel" }, h("summary", { text: "The prompt a model gets" }), h("p", { class: "pg-sub", text: "The exact prompt of the training-free system for the question above: the vocabulary of the graph, one shape example, and the question." }), promptBox),
    h("details", { class: "pg-panel", id: "hp-model-panel" }, h("summary", { text: "Your model" }), h("div", { id: "hp-llm" })),
    h("details", { class: "pg-panel" }, h("summary", { text: "The graph's vocabulary" }), vocabBox));

  STATUS.textContent = "loading the engine and the graph…";
  var [vocabData, demoData] = await Promise.all([fetch("playground-data.json").then(function (r) { return r.json(); }), fetch("demo-data.json").then(function (r) { return r.json(); })]);
  data = vocabData; demo = demoData;
  data.questions.forEach(function (q) { datalist.append(h("option", { value: q })); });
  question.value = data.questions[0]; question.addEventListener("input", currentPrompt);
  var seed = await Promise.all(["data/prod-vocab.ttl", "data/prod-inst.ttl"].map(function (u) { return fetch(u).then(function (r) { return r.text(); }); }));
  handle = await PG.openStore("hermes:corporate", seed.map(function (t) { return { text: t, format: "text/turtle" }; }));
  STATUS.textContent = handle.store.size.toLocaleString() + " triples" + (handle.restored ? ", restored from this browser" : ", loaded");
  vocabBox.append(h("p", { class: "pg-sub", text: "Classes" }), h("pre", { class: "pg-pre", text: data.vocabulary.classes.join("\n") }), h("p", { class: "pg-sub", text: "Properties" }), h("pre", { class: "pg-pre", text: data.vocabulary.properties.join("\n") }));
  PG.llmPanel(document.getElementById("hp-llm"), { onChange: function () { document.getElementById("hp-model").textContent = PG.llmConfig().model; } });
  document.getElementById("hp-model").textContent = PG.llmConfig().model;
  currentPrompt(); recorded("prover"); await run();
})();
