// Step through: compile a question into SPARQL with Hermes's budgeted planner, one phase at a time.
// Hermes itself runs here: its Python package, installed under Pyodide, drives a planning session whose every phase
// (parse, repair, bind, check, price, run, answer) is recorded and drawn below. Queries run on Oxigraph (WebAssembly),
// the engine Hermes uses for local graphs. The model is a recorded reply of Llama 3.1 8B, a model you run, or a reply
// you paste. steps-data.json (from steps_data.py) holds the samples and the native Python's result for each.
(function () {
  const root = document.getElementById("hsteps");
  if (!root) return;
  const { h } = PG;
  const PYODIDE = "https://cdn.jsdelivr.net/pyodide/v0.27.7/full/";
  const PHASES = [["parse", "Parse"], ["repair", "Repair"], ["bind", "Bind"], ["check", "Check"], ["price", "Price"], ["run", "Run"], ["answer", "Answer"]];
  const KIND = { property: "property", class: "class", entity: "entity", value: "value" };
  const FORMATS = { ttl: "text/turtle", nt: "application/n-triples", nq: "application/n-quads", trig: "application/trig", rdf: "application/rdf+xml", owl: "application/rdf+xml", xml: "application/rdf+xml" };
  const DRIVER = `
import json
from hermes.browser import knowledge_graph
from hermes.systems.budgeted import Budgeted, SYSTEM
_graphs = {}

def open_graph(key, data, schema, texts):
    kg = _graphs[key] = knowledge_graph(data, schema, list(texts), key)
    v = kg.vocabulary
    return json.dumps({"classes": len(v["classes"]), "properties": len(v["properties"])})

def start(key, question, budget):
    b = json.loads(budget)
    planner = Budgeted(llm_calls=b["llm_calls"], executions=b["executions"], accept=b["accept"])
    return planner.start(question, _graphs[key], explain=True)

def events(session, since):
    return json.dumps(session.events[since:], default=str)
`;

  let data, py, driver, state = { graph: null, stores: {}, steps: [], at: 0, playing: null, busy: false };
  const el = (id) => document.getElementById(id);
  // For reading only: drop the PREFIX lines and write IRIs with their prefixes (the query that runs is unchanged).
  const short = (sparql) => {
    const map = prefixMap(sparql || ""), body = (sparql || "").split("\n").filter((l) => !/^PREFIX\s/i.test(l)).join("\n");
    return body.replace(/<([^<>\s]+)>/g, (whole, iri) => { for (const [ns, p] of Object.entries(map)) if (iri.startsWith(ns) && iri.length > ns.length) return p + decodeURIComponent(iri.slice(ns.length)); return whole; });
  };
  const fmt = (n, d = 2) => (n == null ? "–" : Number(n).toLocaleString(undefined, { maximumFractionDigits: d }));

  // ---- loading: data, the graph engine, Python and Hermes ----
  async function boot() {
    root.replaceChildren(h("p", { class: "pg-status", id: "hs-boot", text: "Loading the samples…" }));
    data = await (await fetch("steps-data.json")).json();
    render();
    await loadGraph("corporate");
  }
  async function python() {
    if (driver) return driver;
    status("Loading Python in your browser (Pyodide, about 10 MB, kept by your browser after the first visit)…");
    if (!window.loadPyodide) await new Promise((ok, fail) => { const s = h("script", { src: PYODIDE + "pyodide.js" }); s.onload = ok; s.onerror = () => fail(new Error("Could not load Pyodide from " + PYODIDE)); document.head.append(s); });
    py = await loadPyodide({ indexURL: PYODIDE });
    await py.loadPackage(["micropip", "httpx", "pyyaml", "pyparsing"]);
    status("Installing Hermes (commit " + data.commit + ") and rdflib…");
    const urls = data.wheels.map((w) => new URL(w, location.href).href);
    await py.runPythonAsync(`import micropip\nawait micropip.install(${JSON.stringify(urls)}, deps=False)`);
    py.runPython(DRIVER);
    driver = { open: py.globals.get("open_graph"), start: py.globals.get("start"), events: py.globals.get("events"), system: data.system };
    return driver;
  }
  async function readFile(file) { return { text: await file.text(), format: FORMATS[(file.name.split(".").pop() || "").toLowerCase()] || "text/turtle", name: file.name }; }
  async function loadGraph(key, files) {
    state.graph = key;
    const ox = await PG.load();
    let ontology, instances;
    if (key === "yours") { ontology = files.ontology; instances = files.data; }
    else {
      const spec = data.graphs[key], get = async (p) => ({ text: await (await fetch(p)).text(), format: "text/turtle", name: p.split("/").pop() });
      ontology = await Promise.all(spec.ontology.map(get)); instances = await Promise.all(spec.data.map(get));
    }
    status("Loading the graph into Oxigraph…");
    const store = new ox.Store(), schema = ontology.length ? new ox.Store() : null;
    try {
      for (const f of [...ontology, ...instances]) store.load(f.text, { format: f.format });
      for (const f of ontology) schema.load(f.text, { format: f.format });
    } catch (e) { status("Could not read " + "the files: " + (e.message || e)); return; }
    const d = await python();
    status("Reading the graph's schema and statistics…");
    const info = JSON.parse(d.open(key, store, schema, py.toPy([...ontology, ...instances].map((f) => f.text))));
    state.stores[key] = { store, info, files: [...ontology, ...instances].map((f) => f.name) };
    status("");
    render();
  }
  function status(text) { const s = el("hs-status") || el("hs-boot"); if (s) s.textContent = text; }

  // ---- the setup panel ----
  function samplesFor(key) { return data.samples.filter((s) => s.graph === key); }
  function render() {
    const key = state.graph || "corporate", loaded = state.stores[key];
    const graphSel = h("select", { id: "hs-graph", "aria-label": "Knowledge graph" },
      [...Object.entries(data.graphs).map(([k, g]) => [k, g.label]), ["yours", "Your own ontology and data…"]].map(([v, t]) => h("option", { value: v, text: t, selected: v === key })));
    const files = h("div", { class: "pg-row", id: "hs-files", hidden: key !== "yours" },
      h("label", { class: "pg-field", for: "hs-onto" }, "Ontology (schema) files", h("input", { id: "hs-onto", type: "file", multiple: true, accept: ".ttl,.nt,.rdf,.owl,.xml,.nq,.trig" })),
      h("label", { class: "pg-field", for: "hs-data" }, "Data (instance) files", h("input", { id: "hs-data", type: "file", multiple: true, accept: ".ttl,.nt,.rdf,.owl,.xml,.nq,.trig" })),
      h("button", { type: "button", class: "btn", id: "hs-load", onclick: async () => {
        const read = async (id) => Promise.all([...el(id).files].map(readFile));
        const files = { ontology: await read("hs-onto"), data: await read("hs-data") };
        if (!files.data.length && !files.ontology.length) return status("Choose at least one RDF file.");
        await loadGraph("yours", files);
      } }, "Load these files"));
    graphSel.addEventListener("change", async () => { state.graph = graphSel.value; render(); if (graphSel.value !== "yours" && !state.stores[graphSel.value]) await loadGraph(graphSel.value); });
    const info = loaded ? `${loaded.store.size.toLocaleString()} triples · ${loaded.info.classes} classes · ${loaded.info.properties} properties in the vocabulary · ${loaded.files.join(", ")}` : "";

    const samples = samplesFor(key);
    const question = h("input", { type: "text", id: "hs-question", class: "grow", "aria-label": "Question", value: (state.question && state.question.graph === key) ? state.question.text : (samples[0] ? samples[0].question : ""), placeholder: "Ask a question about this graph" });
    const pick = h("select", { id: "hs-sample", "aria-label": "Sample questions" }, h("option", { value: "", text: samples.length ? "Sample questions…" : "No samples for this graph" }),
      samples.map((s, i) => h("option", { value: String(i), text: s.question + (s.expected.abstain ? "  (abstains)" : "") })));
    pick.addEventListener("change", () => { if (pick.value !== "") { question.value = samples[+pick.value].question; syncModel(); } });
    question.addEventListener("input", () => syncModel());

    const model = h("select", { id: "hs-model", "aria-label": "Where the model's replies come from" },
      [["recorded", "Recorded replies (Llama 3.1 8B), no model needed"], ["mine", "My model (Ollama, in-browser, or an endpoint)"], ["paste", "I paste the replies myself"]].map(([v, t]) => h("option", { value: v, text: t })));
    const llm = h("details", { id: "hs-llm", class: "pg-panel", hidden: true }, h("summary", { text: "Your model" }), h("div", { id: "hs-llm-panel" }));
    model.addEventListener("change", () => { llm.hidden = model.value !== "mine"; if (!llm.hidden && !el("llm-backend")) PG.llmPanel(el("hs-llm-panel")); syncModel(); });

    const range = (id, label, min, max, step, value) => h("label", { class: "pg-field", for: id }, h("span", { id: id + "-label", text: label + ": " + value }),
      h("input", { id, type: "range", min, max, step, value, oninput: (e) => { el(id + "-label").textContent = label + ": " + e.target.value; syncModel(); } }));
    const b = data.budget;
    const budget = h("div", { class: "hs-budget" }, range("hs-calls", "Model calls", 1, 5, 1, b.llm_calls), range("hs-runs", "Query runs", 1, 16, 1, b.executions), range("hs-accept", "Accept at confidence", 0.5, 0.95, 0.05, b.accept));
    const go = h("button", { type: "button", class: "btn solid", id: "hs-go", onclick: compile, disabled: !loaded || state.busy }, "Compile the question");

    root.replaceChildren(
      h("div", { class: "pg-panel hs-setup" },
        h("div", { class: "pg-row" }, h("label", { for: "hs-graph" }, "Graph "), graphSel, h("span", { class: "pg-status", id: "hs-info", text: info })),
        files,
        h("div", { class: "pg-row" }, question, pick),
        h("div", { class: "pg-row" }, h("label", { for: "hs-model" }, "Replies "), model, h("span", { class: "pg-status", id: "hs-model-note" })),
        llm, budget,
        h("div", { class: "pg-row" }, go, h("span", { class: "pg-status", id: "hs-status" }))),
      h("div", { id: "hs-run" }));
    syncModel();
    if (state.steps.length) drawRun();
  }
  function budgetNow() { return { llm_calls: +el("hs-calls").value, executions: +el("hs-runs").value, accept: +el("hs-accept").value }; }
  function recordedSample() { const q = (el("hs-question").value || "").trim(); return samplesFor(state.graph).find((s) => s.question === q); }
  function isDefaultBudget() { const b = budgetNow(), d = data.budget; return b.llm_calls === d.llm_calls && b.executions === d.executions && Math.abs(b.accept - d.accept) < 1e-9; }
  function syncModel() {
    const note = el("hs-model-note"), m = el("hs-model").value, s = recordedSample();
    if (m !== "recorded") { note.textContent = m === "paste" ? "The page shows each prompt; paste the model's reply." : "Replies come from " + PG.llmName() + "."; return; }
    note.textContent = s ? "Replies recorded for this sample." + (isDefaultBudget() ? "" : " With a different budget the planner may ask for a reply that was not recorded; the page then asks you to paste it.") : "No recorded reply for this question: choose a sample, or use your model.";
  }

  // ---- running a session ----
  async function reply(prompt, index, sample, mode) {
    if (mode === "recorded" && sample && index < sample.replies.length) return sample.replies[index];
    if (mode === "mine") return PG.chat([{ role: "system", content: driver.system }, { role: "user", content: prompt }], { temperature: 0, maxTokens: 800 });
    return pasted(prompt, index);
  }
  function pasted(prompt, index) {
    return new Promise((resolve) => {
      const box = h("textarea", { id: "hs-paste", "aria-label": "The model's reply", placeholder: "Paste the model's reply (a JSON object) here" });
      const panel = h("div", { class: "pg-panel", id: "hs-ask" },
        h("h3", { text: "Reply " + (index + 1) + ": paste what the model answers to this prompt" }),
        h("details", {}, h("summary", { text: "The prompt (" + prompt.length.toLocaleString() + " characters)" }), h("pre", { class: "pg-pre", text: prompt })),
        h("div", { class: "pg-row" }, h("button", { type: "button", class: "btn", onclick: () => navigator.clipboard && navigator.clipboard.writeText(driver.system + "\n\n" + prompt) }, "Copy the prompt")),
        box, h("div", { class: "pg-row" }, h("button", { type: "button", class: "btn solid", onclick: () => { panel.remove(); resolve(box.value); } }, "Use this reply")));
      el("hs-run").prepend(panel);
    });
  }
  async function compile() {
    const question = (el("hs-question").value || "").trim(), mode = el("hs-model").value, sample = recordedSample();
    if (!question) return status("Write a question first.");
    if (mode === "recorded" && !sample) return status("There is no recorded reply for this question. Choose a sample question, or use your model.");
    state.question = { graph: state.graph, text: question };
    state.busy = true; el("hs-go").disabled = true; stop();
    state.steps = []; state.at = 0; state.sample = mode === "recorded" && isDefaultBudget() ? sample : null; state.result = null; state.prefixes = null;
    let session;
    try {
      session = driver.start(state.graph, question, JSON.stringify(budgetNow()));
      let seen = 0, index = 0, prompt;
      while ((prompt = session.next_prompt()) != null) {
        status(mode === "mine" ? "Asking " + PG.llmName() + " (reply " + (index + 1) + ")…" : "Reading reply " + (index + 1) + "…");
        const text = await reply(prompt, index, sample, mode);
        session.take(text); index++;
        seen = addSteps(JSON.parse(driver.events(session, seen)), seen);
        drawRun(true);
        await new Promise((r) => setTimeout(r, 0));
      }
      session.result();
      addSteps(JSON.parse(driver.events(session, seen)), seen);
      status("");
    } catch (e) { status("Stopped: " + (e.message || e)); }
    finally { if (session) session.destroy(); state.busy = false; el("hs-go").disabled = false; state.at = 0; drawRun(); }
  }
  // Each recorded event is one step, except that a check is shown twice: the verdicts, then the prices.
  function addSteps(events, seen) {
    for (const e of events) {
      if (e.phase === "check") { state.steps.push({ ...e, view: "check" }); if (e.candidates.some((c) => c.ok && !c.duplicate)) state.steps.push({ ...e, view: "price" }); }
      else state.steps.push({ ...e, view: e.phase });
    }
    return seen + events.length;
  }

  // ---- the stepper ----
  function stop() { if (state.playing) { clearInterval(state.playing); state.playing = null; } }
  function go(i) { state.at = Math.max(0, Math.min(state.steps.length - 1, i)); drawRun(); }
  document.addEventListener("keydown", (e) => {
    if (!state.steps.length || /input|textarea|select/i.test(document.activeElement.tagName)) return;
    if (e.key === "ArrowRight") { stop(); go(state.at + 1); } else if (e.key === "ArrowLeft") { stop(); go(state.at - 1); }
  });
  function drawRun(follow) {
    const run = el("hs-run");
    if (!run || !state.steps.length) return;
    if (follow && state.busy) state.at = state.steps.length - 1;
    const step = state.steps[state.at], last = state.steps[state.steps.length - 1];
    const reached = new Set(state.steps.slice(0, state.at + 1).map((s) => s.view === "pause" ? "run" : s.view));
    const pipe = h("ol", { class: "hs-pipe", "aria-label": "Phases" }, PHASES.map(([k, label]) => h("li", { class: (step.view === k || (step.view === "pause" && k === "run") ? "now" : reached.has(k) ? "done" : "") }, label)));
    const spent = step.spent || (state.steps.slice(0, state.at + 1).reverse().find((s) => s.spent) || {}).spent || { llm_calls: 0, executions: 0 };
    const b = budgetNow();
    const meter = h("p", { class: "hs-meter" }, meterBar("Model calls", spent.llm_calls, b.llm_calls), meterBar("Query runs", spent.executions, b.executions));
    const controls = h("div", { class: "pg-row hs-controls" },
      h("button", { type: "button", class: "btn", onclick: () => { stop(); go(0); }, disabled: state.at === 0 }, "⏮"),
      h("button", { type: "button", class: "btn", onclick: () => { stop(); go(state.at - 1); }, disabled: state.at === 0 }, "◀ Back"),
      h("button", { type: "button", class: "btn solid", onclick: () => { stop(); go(state.at + 1); }, disabled: state.at >= state.steps.length - 1 }, "Next ▶"),
      h("button", { type: "button", class: "btn", onclick: () => { if (state.playing) return stop(), drawRun(); state.playing = setInterval(() => { if (state.at >= state.steps.length - 1) { stop(); drawRun(); } else go(state.at + 1); }, 1600); drawRun(); } }, state.playing ? "⏸ Pause" : "⏵ Play"),
      h("button", { type: "button", class: "btn", onclick: () => { stop(); go(state.steps.length - 1); }, disabled: state.at >= state.steps.length - 1 }, "⏭"),
      h("span", { class: "pg-status" }, `Step ${state.at + 1} of ${state.steps.length}${state.busy ? " so far" : ""} · ← → keys`));
    run.replaceChildren(h("div", { class: "pg-panel hs-stage" }, pipe, meter, controls, view(step)));
  }
  function meterBar(label, used, total) {
    const cells = Array.from({ length: total }, (_, i) => h("span", { class: i < used ? "on" : "" }));
    return h("span", { class: "hs-cells", title: `${used} of ${total}` }, label + " ", ...cells, ` ${used}/${total}`);
  }

  // ---- one view per phase ----
  function slotKinds(reading) {
    const bind = state.steps.find((s) => s.view === "bind" && s.reading === reading), kinds = {};
    if (bind) for (const s of bind.slots) kinds[s.phrase] = s.kind;
    return kinds;
  }
  function withSlots(text, kinds) {
    const parts = [], re = /\[([^\[\]]+)\]/g; let last = 0, m;
    while ((m = re.exec(text))) {
      parts.push(text.slice(last, m.index));
      const kind = kinds[m[1].trim()] || (m[1].startsWith("=") ? "value" : "");
      parts.push(h("span", { class: "hs-slot " + (KIND[kind] || ""), title: kind ? "binds to a " + kind : "" }, "[" + m[1] + "]"));
      last = re.lastIndex;
    }
    parts.push(text.slice(last));
    return parts;
  }
  function actionLine(a, kinds) {
    const op = a.op, args = Object.entries(a).filter(([k]) => k !== "op");
    if (op === "triple") return h("div", { class: "hs-line" }, h("span", { class: "hs-op", text: "triple" }), " ", ...withSlots(a.pattern || "", kinds));
    return h("div", { class: "hs-line" }, h("span", { class: "hs-op", text: op }), " ", ...withSlots(args.map(([k, v]) => k + " " + JSON.stringify(v)).join(", "), kinds));
  }
  function goalLine(goal, kinds) {
    if (!goal) return null;
    const parts = ["find ", h("b", { text: (goal.answer || []).join(", ") || "?" }), " : " + (goal.kind || "entity")];
    if (goal.type) parts.push(" of type ", ...withSlots(goal.type, kinds));
    parts.push(goal.many === false ? ", one answer" : ", any number of answers");
    return h("p", { class: "hs-goal" }, "Goal: ", ...parts);
  }
  const say = (title, ...lines) => [h("h3", { class: "hs-title", text: title }), ...lines.filter(Boolean).map((l) => typeof l === "string" ? h("p", { class: "hs-say", text: l }) : l)];

  function view(s) {
    const box = h("div", { class: "hs-view" });
    const add = (...kids) => box.append(...kids.flat().filter(Boolean));
    if (s.view === "parse") {
      const n = s.reading + 1;
      add(say(`Parse · reading ${n}`, n === 1 ? "The model reads the question once, into a goal and a plan of SPARQL algebra operators. Words it is not sure how the graph names stay in [brackets]; it never has to know an IRI." : "No candidate was good enough, so the planner asks again. The prompt now shows what the earlier readings ran and returned, and asks for a different reading."));
      if (s.error) add(h("div", { class: "pg-error", text: "The reply is not a usable reading: " + s.error }));
      else { const kinds = slotKinds(s.reading); add(goalLine(s.parsed.goal, kinds), h("div", { class: "hs-plan" }, s.parsed.actions.map((a) => actionLine(a, kinds)))); }
      add(h("details", {}, h("summary", { text: "The model's reply" }), h("pre", { class: "pg-pre", text: s.reply })),
        h("details", {}, h("summary", { text: "The prompt (" + s.prompt.length.toLocaleString() + " characters: instructions, vocabulary, linked entities, the question)" }), h("pre", { class: "pg-pre hs-prompt", text: s.prompt })));
    } else if (s.view === "repair") {
      add(say("Repair", s.changes.length ? "Before binding, Hermes fixes what models commonly get wrong." : "Nothing to repair: the reading uses only brackets, known terms, and variables."));
      if (s.changes.length) add(h("table", { class: "pg-table hs-table" }, h("thead", {}, h("tr", {}, ["Before", "After", "Why"].map((t) => h("th", { scope: "col", text: t })))),
        h("tbody", {}, s.changes.map((c) => h("tr", {}, h("td", { text: typeof c.before === "string" ? c.before : JSON.stringify(c.before) }), h("td", {}, ...withSlots(typeof c.after === "string" ? c.after : JSON.stringify(c.after), {})), h("td", { class: "hs-why", text: c.why }))))));
    } else if (s.view === "bind") {
      add(say("Bind", "Like a database binder resolving names against its catalog, each phrase gets ranked candidates from the ontology and the graph. Its position decides what it can be: a property in predicate position, a class after a, an entity or a value elsewhere. A property can also be read backwards (^)."));
      add(h("table", { class: "pg-table hs-table" }, h("thead", {}, h("tr", {}, ["Phrase", "Kind", "Candidates, best first"].map((t) => h("th", { scope: "col", text: t })))),
        h("tbody", {}, s.slots.map((slot) => h("tr", {}, h("td", {}, h("span", { class: "hs-slot " + slot.kind, text: "[" + slot.phrase + "]" })), h("td", { text: slot.kind }),
          h("td", { class: "hs-cands" }, slot.candidates.length ? slot.candidates.map((c) => h("span", { class: "hs-cand", title: c.term.startsWith("<") ? c.term : c.label ? "named \"" + c.label + "\"" : "" }, h("code", { text: c.term.startsWith("<") && c.label ? c.label : c.term }), h("span", { class: "hs-score", style: "--w:" + Math.round(c.score * 100) + "%" }), h("small", { text: fmt(c.score) }))) : h("span", { class: "pg-tag bad", text: "nothing matches" })))))));
    } else if (s.view === "check") {
      const ok = s.candidates.filter((c) => c.ok && !c.duplicate), bad = s.candidates.filter((c) => !c.ok);
      add(say("Check", `The best joint assignments of the candidates become plans. The verifier types each one against the ontology (and, where the ontology declares no range, against the kind of values the data holds) before anything runs: ${ok.length} well-typed, ${bad.length} rejected.`));
      const dup = s.candidates.filter((c) => c.duplicate).length;
      const reasons = {};
      for (const c of bad) { const r = (c.errors[0] || "rejected").replace(/<[^>]+>|\b\w+:[\w%.@-]+/g, "…"); reasons[r] = (reasons[r] || 0) + 1; }
      add(h("div", { class: "hs-cards" }, ok.map(candidateCard)),
        bad.length ? h("details", { class: "hs-rejected" }, h("summary", {}, `${bad.length} rejected before running · `,
          Object.entries(reasons).sort((a, b) => b[1] - a[1]).slice(0, 3).map(([r, n]) => `${n} × ${r}`).join(" · ")),
          h("div", { class: "hs-cards" }, bad.map(candidateCard))) : null,
        dup ? h("p", { class: "pg-note", text: `${dup} more ${dup === 1 ? "plan was" : "plans were"} the same as one above and ${dup === 1 ? "is" : "are"} not shown.` }) : null);
    } else if (s.view === "price") {
      const ok = s.candidates.filter((c) => c.ok && !c.duplicate).sort((a, b) => b.p - a.p);
      add(say("Price", "Each well-typed plan is priced before it is sent, with System R estimates from the graph's statistics: the rows it should return and C_out, the summed size of its scans and joins. A logistic estimate p says how likely it is to answer the question. The planner runs the one with the best p net of its price."));
      add(h("div", { class: "pg-scroll" }, h("table", { class: "pg-table hs-table hs-price" }, h("thead", {}, h("tr", {}, ["Plan", "Rows (est.)", "C_out", "p", "Why this p"].map((t) => h("th", { scope: "col", text: t })))),
        h("tbody", {}, ok.map((c) => h("tr", {}, h("td", {}, h("pre", { class: "hs-sparql", text: short(c.sparql) })), h("td", { text: fmt(c.estimate.rows) }), h("td", { text: fmt(c.estimate.cost, 0) }), h("td", {}, pBar(c.p)), h("td", { class: "hs-why", text: why(c.features) })))))));
    } else if (s.view === "run") {
      const q = s.rows != null && s.estimate ? Math.max(Math.max(s.estimate.rows, 1) / Math.max(s.rows, 1), Math.max(s.rows, 1) / Math.max(s.estimate.rows, 1)) : null;
      add(say("Run", s.accepted ? `It ran and returned ${fmt(s.rows, 0)} ${s.rows === 1 ? "row" : "rows"}. The estimate p rose from ${fmt(s.p_before)} to ${fmt(s.p)}, past the threshold of ${fmt(s.accept)}: the planner accepts it and stops.` :
        `It ran and returned ${fmt(s.rows, 0)} ${s.rows === 1 ? "row" : "rows"}${s.rows === 0 ? ", which the goal does not allow" : ""}. p moved from ${fmt(s.p_before)} to ${fmt(s.p)}, below ${fmt(s.accept)}, so the planner tries the next best.`));
      add(h("pre", { class: "pg-pre hs-sparql", text: short(s.sparql) }),
        h("p", { class: "pg-line" }, pBar(s.p_before, s.accept, "before"), " → ", pBar(s.p, s.accept)),
        h("p", { class: "pg-line" }, `Pricing expected ${fmt(s.estimate.rows)} ${s.estimate.rows === 1 ? "row" : "rows"}; it returned ${fmt(s.rows, 0)} (q-error ${fmt(q, 1)}) · ${fmt(s.seconds * 1000, 1)} ms`));
      if (s.error) add(h("div", { class: "pg-error", text: s.error }));
      if (s.sample && s.sample.length) add(sampleTable(s.sample));
    } else if (s.view === "pause") {
      const reading = s.spent.llm_calls - 1, bind = state.steps.find((x) => x.view === "bind" && x.reading === reading);
      const lost = bind ? bind.slots.filter((x) => !x.candidates.length).map((x) => "[" + x.phrase + "]") : [];
      const parsed = state.steps.find((x) => x.view === "parse" && x.reading === reading);
      const reason = parsed && parsed.error ? "the reply was not a usable reading" : lost.length ? lost.join(", ") + (lost.length > 1 ? " match" : " matches") + " no term in the graph, so this reading gives no plan" : s.why;
      add(say("Pause", "The planner stops running candidates: " + reason + ".", s.spent.llm_calls < budgetNow().llm_calls ? "It will parse the question again." : "The model-call budget is spent, so it picks the best candidate it has."));
    } else if (s.view === "answer") {
      add(say("Answer", s.sparql ? (s.abstain ? `The best candidate has confidence ${fmt(s.confidence)}, below ${fmt(s.threshold)}: Hermes abstains rather than claim an answer. The query is shown for inspection.` : `The chosen query, with confidence ${fmt(s.confidence)}.`) : "No reading bound to a well-typed plan, so there is no query: Hermes abstains."));
      if (s.sparql) {
        add(h("pre", { class: "pg-pre hs-sparql", text: short(s.sparql) }),
          h("details", {}, h("summary", { text: "The query exactly as sent, with its PREFIX lines" }), h("pre", { class: "pg-pre", text: s.sparql })));
        const out = h("div", {});
        try { PG.show(out, PG.run(state.stores[state.graph].store, s.sparql, prefixMap(s.sparql))); } catch (e) { out.append(h("div", { class: "pg-error", text: String(e.message || e) })); }
        add(out);
      }
      if (state.sample) {
        const same = state.sample.expected.sparql === s.sparql && state.sample.expected.abstain === s.abstain;
        add(h("p", { class: "pg-line" }, h("span", { class: "pg-tag " + (same ? "ok" : "bad"), text: same ? "same as the native run" : "differs from the native run" }),
          same ? " Hermes in your browser reached the same query, confidence, and decision as the Python run that recorded these replies (commit " + data.commit + ")." : " The browser and the native Python disagree here; please report it."));
      }
    }
    return box;
  }
  function candidateCard(c) {
    const ctx = Object.entries(c.context || {}).filter(([, t]) => t.length).map(([v, t]) => h("span", { class: "pg-tag" }, v + " : " + t.join(", ")));
    return h("div", { class: "hs-card " + (c.ok ? (c.duplicate ? "dup" : "ok") : "bad") },
      h("div", { class: "hs-card-head" }, h("span", { class: "pg-tag " + (c.ok ? "ok" : "bad"), text: c.ok ? (c.duplicate ? "same as an earlier plan" : "well-typed") : "rejected" }),
        c.origin === "label collapse" ? h("span", { class: "pg-tag", text: "label collapsed into its entity" }) : null,
        c.closed_type ? h("span", { class: "pg-tag", text: "type goal closed with ?x a " + c.closed_type }) : null,
        h("small", { class: "pg-status", text: "binding score " + fmt(c.weight, 3) })),
      c.sparql ? h("pre", { class: "hs-sparql", text: short(c.sparql) }) : null,
      ...(c.errors || []).map((e) => h("div", { class: "hs-err", text: e })),
      ...(c.warnings || []).map((w) => h("div", { class: "hs-warn", text: "warning: " + w })),
      ...(c.goals || []).map((g) => h("div", { class: "hs-goalopen", text: "open goal " + g })),
      ctx.length ? h("div", { class: "hs-ctx" }, "typing ", ...ctx) : null);
  }
  function why(f) {
    const out = [];
    out.push(f.binding > -0.05 ? "exact names" : f.binding > -0.5 ? "close names" : "loose names");
    if (f.warnings) out.push(f.warnings + " warning" + (f.warnings > 1 ? "s" : ""));
    if (f.open_goals) out.push(f.open_goals + " open goal" + (f.open_goals > 1 ? "s" : ""));
    if (f.estimated_empty) out.push("expected empty");
    if (f.estimated_excess) out.push("expected too many rows");
    return out.join(", ");
  }
  function pBar(p, accept, label) {
    return h("span", { class: "hs-p", title: (label ? label + ": " : "") + "p = " + fmt(p, 3) }, h("span", { class: "hs-p-bar", style: "--p:" + Math.round(p * 100) + "%" + (accept != null ? ";--a:" + Math.round(accept * 100) + "%" : "") }), h("small", { text: fmt(p) }));
  }
  function sampleTable(rows) {
    const vars = Object.keys(rows[0]);
    return h("div", { class: "pg-scroll" }, h("table", { class: "pg-table" }, h("thead", {}, h("tr", {}, vars.map((v) => h("th", { scope: "col", text: v })))),
      h("tbody", {}, rows.map((r) => h("tr", {}, vars.map((v) => h("td", { text: r[v] || "" })))))));
  }
  function prefixMap(sparql) {
    const map = {}, re = /PREFIX\s+([\w-]*):\s*<([^>]+)>/gi; let m;
    while ((m = re.exec(sparql))) map[m[2]] = m[1] + ":";
    return map;
  }

  boot().catch((e) => { root.replaceChildren(h("div", { class: "pg-error", text: "The page could not start: " + (e.message || e) })); });
})();
