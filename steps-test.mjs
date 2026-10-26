// Does Hermes under Pyodide, on Oxigraph-WASM, reach the same query as the native Python run for every sample?
//   mkdir t && cd t && npm i pyodide@0.27.7 oxigraph@0.5.12 && cp <docs>/steps-test.mjs . && node steps-test.mjs <docs>
import { loadPyodide } from "pyodide";
import * as ox from "oxigraph";
import fs from "fs";
const DOCS = process.argv[2];
const data = JSON.parse(fs.readFileSync(DOCS + "/steps-data.json", "utf8"));
const t0 = Date.now();
const py = await loadPyodide();
await py.loadPackage(["micropip", "httpx", "pyyaml", "pyparsing"]);
for (const w of data.wheels) { const name = w.split("/").pop(); py.FS.writeFile("/tmp/" + name, fs.readFileSync(DOCS + "/" + w)); }
await py.runPythonAsync(`
import micropip
await micropip.install(["emfs:/tmp/${data.wheels[0].split("/").pop()}", "emfs:/tmp/${data.wheels[1].split("/").pop()}"], deps=False)
`);
console.log("python ready", (Date.now() - t0) / 1000, "s");
py.runPython(`
import json
from hermes.browser import knowledge_graph
from hermes.systems.budgeted import Budgeted
planner = Budgeted(llm_calls=3, executions=8)
graphs = {}
def run(name, data_store, schema_store, texts, question, replies):
    if name not in graphs:
        graphs[name] = knowledge_graph(data_store, schema_store, list(texts), name)
    session = planner.start(question, graphs[name], explain=True)
    replies = list(replies)
    while (text := session.next_prompt()) is not None and replies:
        session.take(replies.pop(0))
    result = session.result()
    return json.dumps({"sparql": result["sparql"], "confidence": result["confidence"], "abstain": result["abstain"], "phases": [e["phase"] for e in session.events], "events": len(session.events)})
`);
const stores = {};
for (const [name, spec] of Object.entries(data.graphs)) {
  const d = new ox.Store(), s = spec.ontology.length ? new ox.Store() : null, texts = [];
  for (const f of [...spec.ontology, ...spec.data]) { const t = fs.readFileSync(DOCS + "/" + f, "utf8"); texts.push(t); d.load(t, { format: "text/turtle" }); }
  for (const f of spec.ontology) s.load(fs.readFileSync(DOCS + "/" + f, "utf8"), { format: "text/turtle" });
  stores[name] = { d, s, texts };
}
let same = 0;
for (const sample of data.samples) {
  const t = Date.now(), st = stores[sample.graph];
  const got = JSON.parse(py.globals.get("run")(sample.graph, st.d, st.s, py.toPy(st.texts), sample.question, py.toPy(sample.replies)));
  const ok = got.sparql === sample.expected.sparql && got.abstain === sample.expected.abstain && JSON.stringify(got.phases) === JSON.stringify(sample.expected.phases);
  same += ok;
  console.log(ok ? "SAME" : "DIFF", sample.item, (Date.now() - t) / 1000 + "s", "conf", got.confidence, "vs", sample.expected.confidence, "events", got.events);
  if (!ok) console.log(got.sparql, "\n---\n", sample.expected.sparql, got.phases, sample.expected.phases);
}
console.log(same + "/" + data.samples.length + " match the native Python run");
