// The two demos of the Hermes manual, running Hermes itself in the browser.
// Hermes's Python package (the wheel the benchmarks run) is installed under Pyodide; queries run on Oxigraph compiled to
// WebAssembly, the engine Hermes uses for local graphs. "Ask" runs the whole pipeline: a model reply is recorded,
// comes from a model you run, or is pasted; the page asks Python for the next prompt and runs again with the reply.
// "Plan" needs no model: a SPARQL query is translated, rewritten, and both plans run. docs-data.json (docs_data.py)
// holds the samples and what the native Python run gave for each.
(function () {
  const PYODIDE = "https://cdn.jsdelivr.net/pyodide/v0.27.7/full/";
  const { h } = PG;
  const DRIVER = `
import json
from hermes import planner
from hermes.graph.browser import knowledge_graph
from hermes.llm import NeedReply, ReplayLLM
from hermes.pipeline import Hermes
from hermes.pipeline.catalog import catalog_for
from hermes.pipeline.events import Recorder
from hermes.pipeline.fewshot import Example, FewShotStore
from hermes.pricing.budget import Budget
_graphs = {}

def open_graph(key, data, schema, texts, examples):
    kg = knowledge_graph(data, schema, list(texts), key)
    store = FewShotStore(Example(**e) for e in json.loads(examples))
    _graphs[key] = (kg, store)
    catalog = catalog_for(kg)
    return json.dumps({"classes": len(catalog.classes()), "properties": len(catalog.properties()),
                       "examples": len(store)})

def _value(term, names):
    return "-" if term is None else planner.expression(term, names)

def _tree(optimized, query, trace=None):
    est = optimized.estimator
    def note(node):
        got = trace.rows.get(id(node)) if trace is not None else None
        return f"   est {est(node).rows:,.1f}" + (f" · got {got:,}" if got is not None else "")
    return planner.tree(query.root, query.namespaces, note)

def ask(key, question, replies, budget):
    kg, store = _graphs[key]
    b = json.loads(budget)
    recorder = Recorder()
    hermes = Hermes(kg, llm=ReplayLLM(json.loads(replies)), fewshots=store,
                    budget=Budget(llm_calls=b["calls"], rows=b.get("rows")),
                    executor=b.get("executor", "plan"), observers=[recorder])
    try:
        answer = hermes.ask(question)
    except NeedReply as need:
        return json.dumps({"need": need.prompt, "system": need.system})
    out = {"sparql": answer.sparql, "error": answer.error, "repairs": answer.repairs,
           "problems": answer.problems, "seconds": answer.seconds,
           "spend": answer.spend.to_dict(), "examples": [e.question for e in answer.examples],
           "events": [{"stage": e.stage, "kind": e.kind, "data": e.data} for e in recorder.events]}
    if answer.slice is not None:
        out["slice"] = answer.slice.render(hermes.catalog, hermes.names)
    if answer.plan is not None:
        names = answer.plan.query.namespaces
        out["written"] = _tree(answer.plan, answer.plan.written)
        out["optimized"] = _tree(answer.plan, answer.plan.query)
        out["rewrites"] = [r.text for r in answer.plan.rewrites]
        out["variables"] = [str(v) for v in answer.variables]
        out["rows"] = [[_value(row.get(v), names) for v in answer.variables] for row in answer.rows[:200]]
        out["count"] = len(answer.rows)
        out["boolean"] = answer.boolean
    return json.dumps(out, default=str)

def plan(key, sparql):
    kg, _ = _graphs[key]
    optimized = planner.plan(sparql, kg)
    run = planner.PlanExecutor(kg)
    before, after = run(optimized.written), run(optimized.query)
    engine = planner.EngineExecutor(kg)(optimized.written)
    names = optimized.query.namespaces
    def metrics(query, result):
        t = result.trace
        return {"cost": round(optimized.estimator(query.root).cost), "queries": t.queries,
                "fetched": t.fetched, "intermediate": t.intermediate, "ms": round(t.seconds * 1000, 1)}
    return json.dumps({
        "written": _tree(optimized, optimized.written, before.trace),
        "optimized": _tree(optimized, optimized.query, after.trace),
        "formula": planner.formula(optimized.query.root, names),
        "rewrites": [{"rule": r.rule, "text": r.text} for r in optimized.rewrites],
        "before": metrics(optimized.written, before), "after": metrics(optimized.query, after),
        "same": planner.same_answers(after, engine) and planner.same_answers(before, engine),
        "variables": [str(v) for v in after.variables], "boolean": after.boolean,
        "rows": [[_value(row.get(v), names) for v in after.variables] for row in after.rows[:200]],
        "count": len(after.rows)})
`;

  let data, py, driver, ready;
  const state = { graph: null, graphs: {} };
  const FORMATS = { ttl: "text/turtle", nt: "application/n-triples", nq: "application/n-quads", trig: "application/trig", rdf: "application/rdf+xml", owl: "application/rdf+xml", xml: "application/rdf+xml" };

  function status(text) { document.querySelectorAll(".hd-status").forEach((s) => (s.textContent = text)); }

  async function python() {
    if (driver) return driver;
    status("Loading Python in your browser (Pyodide, about 10 MB, kept by your browser after the first visit)…");
    if (!window.loadPyodide) await new Promise((ok, fail) => { const s = h("script", { src: PYODIDE + "pyodide.js" }); s.onload = ok; s.onerror = () => fail(new Error("Could not load Pyodide.")); document.head.append(s); });
    py = await loadPyodide({ indexURL: PYODIDE });
    await py.loadPackage(["micropip", "httpx", "pyyaml", "pyparsing"]);
    status("Installing Hermes (commit " + data.commit + ")…");
    const urls = data.wheels.map((w) => new URL(w, location.href).href);
    await py.runPythonAsync(`import micropip\nawait micropip.install(${JSON.stringify(urls)}, deps=False)`);
    py.runPython(DRIVER);
    driver = { open: py.globals.get("open_graph"), ask: py.globals.get("ask"), plan: py.globals.get("plan") };
    return driver;
  }

  async function openGraph(key, files) {
    const ox = await PG.load();
    let ontology, instances, examples = [];
    if (key === "yours") { ontology = files.ontology; instances = files.data; }
    else {
      const spec = data.graphs[key], get = async (p) => ({ text: await (await fetch(p)).text(), format: "text/turtle", name: p.split("/").pop() });
      ontology = await Promise.all(spec.ontology.map(get)); instances = await Promise.all(spec.data.map(get));
      examples = spec.examples ? await (await fetch(spec.examples)).text().then((t) => t.split("\n").filter(Boolean).map(JSON.parse)) : [];
    }
    status("Loading the graph into Oxigraph…");
    const store = new ox.Store(), schema = ontology.length ? new ox.Store() : null;
    for (const f of [...ontology, ...instances]) store.load(f.text, { format: f.format });
    for (const f of ontology) schema.load(f.text, { format: f.format });
    const d = await python();
    status("Reading the ontology and the graph's statistics…");
    const info = JSON.parse(d.open(key, store, schema, py.toPy([...ontology, ...instances].map((f) => f.text)), JSON.stringify(examples)));
    state.graphs[key] = { store, info, files: [...ontology, ...instances].map((f) => f.name) };
    state.graph = key;
    status("");
    return state.graphs[key];
  }
  async function readFile(file) { return { text: await file.text(), format: FORMATS[(file.name.split(".").pop() || "").toLowerCase()] || "text/turtle", name: file.name }; }

  // ---- shared pieces of the forms ----
  function graphPicker(onReady) {
    const select = h("select", { class: "hd-graph", "aria-label": "Knowledge graph" },
      [...Object.entries(data.graphs).map(([k, g]) => [k, g.label]), ["yours", "Your own ontology and data…"]].map(([v, t]) => h("option", { value: v, text: t })));
    const info = h("span", { class: "pg-status" });
    const onto = h("input", { type: "file", multiple: true, accept: ".ttl,.nt,.rdf,.owl,.xml,.nq,.trig", "aria-label": "Ontology files" });
    const inst = h("input", { type: "file", multiple: true, accept: ".ttl,.nt,.rdf,.owl,.xml,.nq,.trig", "aria-label": "Data files" });
    const files = h("div", { class: "pg-row", hidden: true }, h("label", { class: "pg-field" }, "Ontology files", onto), h("label", { class: "pg-field" }, "Data files", inst),
      h("button", { type: "button", class: "btn", onclick: async () => {
        const read = async (input) => Promise.all([...input.files].map(readFile));
        const chosen = { ontology: await read(onto), data: await read(inst) };
        if (!chosen.ontology.length && !chosen.data.length) return status("Choose at least one RDF file.");
        try { show(await openGraph("yours", chosen)); } catch (e) { status("Could not read the files: " + (e.message || e)); }
      } }, "Load these files"));
    const show = (g) => { info.textContent = `${g.store.size.toLocaleString()} triples · ${g.info.classes} classes · ${g.info.properties} properties · ${g.files.join(", ")}`; onReady(); };
    select.addEventListener("change", async () => {
      files.hidden = select.value !== "yours"; info.textContent = "";
      if (select.value === "yours") return;
      show(state.graphs[select.value] || await openGraph(select.value));
      state.graph = select.value;
    });
    return { el: h("div", {}, h("div", { class: "pg-row" }, h("label", {}, "Graph "), select, info), files), select,
      start: async () => show(await openGraph(select.value)) };
  }
  const table = (variables, rows) => h("div", { class: "pg-scroll" }, h("table", { class: "pg-table" },
    h("thead", {}, h("tr", {}, variables.map((v) => h("th", { scope: "col", text: "?" + v })))),
    h("tbody", {}, rows.map((r) => h("tr", {}, r.map((c) => h("td", { text: c })))))));
  const card = (title, ...kids) => h("section", { class: "pg-panel hd-card" }, h("h3", { text: title }), ...kids.flat().filter(Boolean));
  const pre = (text, cls = "") => h("pre", { class: "pg-pre " + cls, text });
  const list = (items) => items.length ? h("ul", { class: "hd-list" }, items.map((t) => h("li", { text: t }))) : h("p", { class: "pg-note", text: "none" });

  // ---- Ask ----
  function askDemo(root) {
    const picker = graphPicker(() => refreshSamples());
    const question = h("input", { type: "text", class: "grow", "aria-label": "Question", placeholder: "Ask a question about this graph" });
    const samples = h("select", { "aria-label": "Sample questions" });
    const mode = h("select", { "aria-label": "Where the model's replies come from" },
      [["recorded", "Recorded replies (Llama 3.1 8B), no model needed"], ["mine", "My model (Ollama, in-browser, or an endpoint)"], ["paste", "I paste the replies"]].map(([v, t]) => h("option", { value: v, text: t })));
    const llm = h("details", { class: "pg-panel", hidden: true }, h("summary", { text: "Your model" }), h("div", {}));
    mode.addEventListener("change", () => { llm.hidden = mode.value !== "mine"; if (!llm.hidden && !llm.querySelector("select")) PG.llmPanel(llm.lastChild); });
    const calls = h("input", { type: "number", min: 1, max: 6, value: 3, "aria-label": "Model calls", class: "hd-num" });
    const rows = h("input", { type: "number", min: 1, placeholder: "no cap", "aria-label": "Row cap", class: "hd-num" });
    const executor = h("select", { "aria-label": "Executor" }, h("option", { value: "plan", text: "Hermes's plan" }), h("option", { value: "engine", text: "the engine (Oxigraph)" }));
    const go = h("button", { type: "button", class: "btn solid", disabled: true }, "Ask");
    const out = h("div", { class: "hd-out" });
    function refreshSamples() {
      const list = data.samples.filter((s) => s.graph === state.graph);
      samples.replaceChildren(h("option", { value: "", text: list.length ? "Sample questions…" : "No samples for this graph" }), ...list.map((s, i) => h("option", { value: String(i), text: s.question })));
      samples.onchange = () => { if (samples.value !== "") question.value = list[+samples.value].question; };
      if (list.length && !question.value) question.value = list[0].question;
      go.disabled = false;
    }
    go.addEventListener("click", async () => {
      const q = question.value.trim(); if (!q) return status("Write a question first.");
      const sample = data.samples.find((s) => s.graph === state.graph && s.question === q);
      if (mode.value === "recorded" && !sample) return status("No recorded replies for this question: choose a sample, or use your model.");
      go.disabled = true; out.replaceChildren();
      const replies = [];
      const budget = JSON.stringify({ calls: +calls.value || 3, rows: rows.value ? +rows.value : null, executor: executor.value });
      try {
        for (let round = 0; round < 8; round++) {
          status(round ? `Running the pipeline again with reply ${round}…` : "Running the pipeline…");
          const result = JSON.parse(driver.ask(state.graph, q, JSON.stringify(replies), budget));
          if (!result.need) { render(result, sample); break; }
          status(mode.value === "mine" ? "Asking " + PG.llmName() + "…" : "Waiting for a reply…");
          replies.push(await reply(result, replies.length, sample));
        }
        status("");
      } catch (e) { status("Stopped: " + (e.message || e)); }
      go.disabled = false;
    });
    async function reply(need, index, sample) {
      if (mode.value === "recorded") { if (sample && index < sample.replies.length) return sample.replies[index]; mode.value = "paste"; }
      if (mode.value === "mine") return PG.chat([{ role: "system", content: need.system }, { role: "user", content: need.need }], { temperature: 0, maxTokens: 800 });
      return new Promise((resolve) => {
        const box = h("textarea", { "aria-label": "The model's reply", placeholder: "Paste the model's reply here" });
        const panel = card("Reply " + (index + 1) + ": paste what the model answers",
          h("details", {}, h("summary", { text: "The prompt" }), pre(need.need)),
          h("div", { class: "pg-row" }, h("button", { type: "button", class: "btn", onclick: () => navigator.clipboard && navigator.clipboard.writeText(need.need) }, "Copy the prompt")),
          box, h("div", { class: "pg-row" }, h("button", { type: "button", class: "btn solid", onclick: () => { panel.remove(); resolve(box.value); } }, "Use this reply")));
        out.prepend(panel);
      });
    }
    function render(r, sample) {
      const ended = (stage) => (r.events.find((e) => e.stage === stage && e.kind === "end") || {}).data || {};
      const gen = ended("generate");
      const s = r.spend.total, est = r.spend.estimated;
      out.replaceChildren(
        r.error ? h("div", { class: "pg-error", text: "No answer: " + r.error }) : null,
        card("1 · Ontology slice", h("p", { class: "pg-note", text: "The classes, properties, values and entities the question needs, chosen from the ontology catalog." }), r.slice ? pre(r.slice) : null),
        card("2 · Examples", h("p", { class: "pg-note", text: "Synthetic question and query pairs over this graph, closest to the question." }), list(r.examples)),
        card("3 · Generate", gen.prompt ? h("details", {}, h("summary", { text: `The prompt (${gen.prompt.length.toLocaleString()} characters)` }), pre(gen.prompt)) : null, gen.sparql ? pre(gen.sparql) : null),
        card("4 · Repair", list(r.repairs), r.problems.length ? h("div", { class: "pg-error", text: "Still wrong: " + r.problems.join("; ") }) : null, r.sparql ? pre(r.sparql) : null),
        r.written ? card("5 · Plan", h("div", { class: "pg-cols" }, h("div", {}, h("h4", { text: "As written" }), pre(r.written, "hd-tree")), h("div", {}, h("h4", { text: "Optimized" }), pre(r.optimized, "hd-tree"))), h("h4", { text: "Rewrites" }), list(r.rewrites)) : null,
        card("6 · Price and spend", h("table", { class: "pg-table" }, h("thead", {}, h("tr", {}, ["", "estimated", "spent"].map((t) => h("th", { scope: "col", text: t })))),
          h("tbody", {}, [["model calls", "llm_calls"], ["tokens in", "input_tokens"], ["tokens out", "output_tokens"], ["graph queries", "queries"], ["graph rows", "rows"]].map(([label, k]) => h("tr", {}, h("td", { text: label }), h("td", { text: Math.round(est[k]).toLocaleString() }), h("td", { text: Math.round(s[k]).toLocaleString() })))))),
        r.variables ? card("7 · Answer", r.boolean != null ? h("p", { text: "Answer: " + r.boolean }) : [h("p", { class: "pg-line", text: `${r.count} rows` }), table(r.variables, r.rows)],
          sample ? h("p", { class: "pg-line" }, h("span", { class: "pg-tag " + (sample.expected.sparql === r.sparql ? "ok" : "bad"), text: sample.expected.sparql === r.sparql ? "same as the native run" : "differs from the native run" })) : null) : null);
    }
    root.replaceChildren(h("div", { class: "pg-panel" }, picker.el, h("div", { class: "pg-row" }, question, samples),
      h("div", { class: "pg-row" }, h("label", {}, "Replies "), mode), llm,
      h("div", { class: "pg-row" }, h("label", {}, "Model calls "), calls, h("label", {}, "Graph rows at most "), rows, h("label", {}, "Run with "), executor),
      h("div", { class: "pg-row" }, go, h("span", { class: "pg-status hd-status" }))), out);
    picker.start().catch((e) => status("Could not start: " + (e.message || e)));
  }

  // ---- Plan ----
  function planDemo(root) {
    const picker = graphPicker(() => refreshSamples());
    const text = h("textarea", { class: "hd-sparql", "aria-label": "SPARQL query", spellcheck: "false" });
    const samples = h("select", { "aria-label": "Sample queries" });
    const go = h("button", { type: "button", class: "btn solid", disabled: true }, "Plan and run");
    const out = h("div", { class: "hd-out" });
    function refreshSamples() {
      const list = data.queries.filter((q) => q.graph === state.graph);
      samples.replaceChildren(h("option", { value: "", text: list.length ? "Sample queries…" : "No samples for this graph" }), ...list.map((q, i) => h("option", { value: String(i), text: q.title })));
      samples.onchange = () => { if (samples.value !== "") text.value = list[+samples.value].sparql; };
      if (list.length && !text.value) text.value = list[0].sparql;
      go.disabled = false;
    }
    go.addEventListener("click", () => {
      try {
        const r = JSON.parse(driver.plan(state.graph, text.value));
        const row = (label, k) => h("tr", {}, h("td", { text: label }), h("td", { text: r.before[k].toLocaleString() }), h("td", { text: r.after[k].toLocaleString() }));
        out.replaceChildren(
          card("As written", pre(r.written, "hd-tree")),
          card("Rewrites", list(r.rewrites.map((w) => w.rule + ": " + w.text))),
          card("Optimized", pre(r.optimized, "hd-tree"), h("details", {}, h("summary", { text: "As one formula" }), pre(r.formula))),
          card("What each plan did", h("table", { class: "pg-table" }, h("thead", {}, h("tr", {}, ["", "as written", "optimized"].map((t) => h("th", { scope: "col", text: t })))),
            h("tbody", {}, row("estimated C_out", "cost"), row("store queries", "queries"), row("rows fetched", "fetched"), row("intermediate rows", "intermediate"), row("milliseconds", "ms"))),
            h("p", { class: "pg-line" }, h("span", { class: "pg-tag " + (r.same ? "ok" : "bad"), text: r.same ? "same answers as the engine" : "answers differ from the engine" }))),
          card("Answer", r.boolean != null ? h("p", { text: "Answer: " + r.boolean }) : [h("p", { class: "pg-line", text: `${r.count} rows` }), table(r.variables, r.rows)]));
        status("");
      } catch (e) { out.replaceChildren(h("div", { class: "pg-error", text: String(e.message || e).split("\n").slice(-3).join("\n") })); }
    });
    root.replaceChildren(h("div", { class: "pg-panel" }, picker.el, h("div", { class: "pg-row" }, samples), text,
      h("div", { class: "pg-row" }, go, h("span", { class: "pg-status hd-status" }))), out);
    picker.start().catch((e) => status("Could not start: " + (e.message || e)));
  }

  async function boot() {
    const ask = document.getElementById("hd-ask"), plan = document.getElementById("hd-plan");
    if (!ask && !plan) return;
    data = await (await fetch("docs-data.json")).json();
    if (ask) askDemo(ask);
    if (plan) planDemo(plan);
  }
  boot().catch((e) => { const root = document.getElementById("hd-ask") || document.getElementById("hd-plan"); if (root) root.replaceChildren(h("div", { class: "pg-error", text: "The demo could not start: " + (e.message || e) })); });
})();
