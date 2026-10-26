#!/usr/bin/env python3
"""Write the Hermes manual."""

from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPO = "https://github.com/lamng3/hermes"
SRC = REPO + "/blob/master/src/hermes"

NAV = [
    ("index.html", "Overview"),
    ("ask.html", "Try: ask a question"),
    ("plan.html", "Try: plan a query"),
    ("pipeline.html", "Pipeline"),
    ("planner.html", "Planner"),
    ("pricing.html", "Pricing and budgets"),
    ("graphs.html", "Graphs"),
    ("evaluation.html", "Evaluation"),
    ("baselines.html", "Baselines"),
    ("reference.html", "Python and CLI"),
]

FOOTER = f'Hermes Manual. <a href="{REPO}">Code</a> · <a href="{REPO}/tree/master/results">Results</a>.'

HEAD = """<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=TikTok+Sans:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
<link rel="icon" href="favicon.svg" type="image/svg+xml">
<link rel="stylesheet" href="style.css">"""

HEADER = """<header class="site">
  <a class="logo" href="index.html"><span class="logo-mark">H</span><span>Hermes</span></a>
  <nav class="site">
    <a href="ask.html">Ask</a>
    <a href="plan.html">Plan</a>
    <a href="pipeline.html">Pipeline</a>
    <label class="nav-button" for="nav-toggle">Menu</label>
    <a href="https://github.com/lamng3/hermes" class="pill">GitHub ↗</a>
  </nav>
</header>"""

PIPELINE = """<ol class="stages">
<li><b>Refine</b><span>the ontology slice the question needs</span></li>
<li><b>Examples</b><span>synthetic pairs from the graph</span></li>
<li><b>Generate</b><span>one model call writes SPARQL</span></li>
<li><b>Repair</b><span>prefixes, terms, types, probes</span></li>
<li><b>Plan</b><span>relational algebra, rewritten</span></li>
<li><b>Price</b><span>checked against the budget</span></li>
<li><b>Execute</b><span>the plan runs on the graph</span></li>
</ol>"""


def nav_html(current):
    links = ['<a class="brand-desk" href="index.html">Hermes Manual</a>']
    for href, label in NAV:
        current_attr = ' aria-current="page"' if href == current else ""
        links.append(f'<a href="{href}"{current_attr}>{label}</a>')
    return "".join(links)


def page(filename, title, description, kicker, lede, body):
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
{HEAD}
<title>{title} — Hermes Manual</title>
<meta name="description" content="{description}">
</head>
<body>
<a class="skip" href="#content">Skip to content</a>
{HEADER}
<input id="nav-toggle" class="nav-toggle" type="checkbox">
<div class="layout">
<nav class="nav">
{nav_html(filename)}
</nav>
<main id="content">
<p class="kicker">{kicker}</p>
<h1>{title}</h1>
<p class="lede">{lede}</p>
{body}
</main>
</div>
<footer class="site">{FOOTER}</footer>
</body>
</html>
"""
    (ROOT / filename).write_text(html, encoding="utf-8")


def results_html():
    """The pipeline's results, when docs_data.py has collected them."""
    import json

    path = ROOT / "results-data.json"
    if not path.exists():
        return f'<p>The pipeline\'s runs are in <a href="{REPO}/tree/master/results">results/</a>.</p>'
    data = json.loads(path.read_text(encoding="utf-8"))
    head = "".join(f'<th scope="col">{c}</th>' for c in data["columns"])
    rows = "".join("<tr>" + "".join(f"<td>{c}</td>" for c in row) + "</tr>" for row in data["rows"])
    return f'<table><thead><tr>{head}</tr></thead><tbody>{rows}</tbody></table><p>{data["note"]}</p>'


def main():
    page(
        "index.html",
        "Hermes",
        "Hermes: ontology-based natural-language querying over knowledge graphs, with a statistics-aware query planner, query pricing, and cost budgets.",
        "Ontology-based natural-language querying over knowledge graphs",
        "Ask a question in English; Hermes writes SPARQL from the slice of the ontology the question needs, repairs it, plans it as relational algebra with the graph's statistics, and runs it, pricing every model call and graph query before it spends it.",
        f"""
<div class="actions"><a class="btn solid" href="ask.html">Ask a question</a> <a class="btn" href="plan.html">Plan a query</a> <a class="btn" href="{REPO}">GitHub</a></div>
<h2 id="how-it-works">How it works</h2>
<p>The ontology is the schema and the knowledge graph is the data. A question goes through seven stages:</p>
{PIPELINE}
<p>One model call writes the query; everything after it is checked before it costs anything, and the model is asked again only when a check fails and the budget allows. See <a href="pipeline.html">Pipeline</a>.</p>
<h2 id="quick-start">Quick start</h2>
<pre><code>git clone {REPO}.git &amp;&amp; cd hermes
pip install -e ".[dev]"
hermes data fetch ck26                          # the Text2SPARQL corporate graph and benchmark
hermes ask --graph corporate "Which department does Ms. Brant belong to?"</code></pre>
<pre><code>from hermes import Budget, Hermes, KnowledgeGraph

kg = KnowledgeGraph.from_files("ontology.ttl", "data.ttl", schema=["ontology.ttl"])
answer = Hermes(kg, budget=Budget(llm_calls=3)).ask("Which cities hosted the Winter Olympics?")
print(answer.sparql, answer.rows, answer.spend.total)</code></pre>
<p>The model is a local one through Ollama by default, or any OpenAI-compatible API; see <a href="reference.html">Python and CLI</a>.</p>
<h2 id="what-is-measured">What is measured</h2>
<p>On the gold queries of the Text2SPARQL 2026 benchmarks, every plan that ran returned the engine's answers, and the optimizer cut the work; <a href="planner.html#study">Planner</a> has the details. The pipeline's accuracy and cost are on <a href="evaluation.html#results">Evaluation</a>.</p>
<table>
<thead><tr><th scope="col"></th><th scope="col">CK26 (local)</th><th scope="col">DB26 (DBpedia endpoint)</th></tr></thead>
<tbody>
<tr><td>gold queries whose plans ran and gave the engine's answers</td><td>48 of 48</td><td>41 of 41</td></tr>
<tr><td>intermediate rows, as written → optimized</td><td>1,302,989 → 106,719</td><td>1,097,107 → 1,060,291</td></tr>
<tr><td>plan seconds, as written → optimized</td><td>4.67 → 1.35</td><td>68.4 → 29.7</td></tr>
</tbody></table>
""",
    )
    page(
        "ask.html",
        "Try: ask a question",
        "Run Hermes's whole pipeline in your browser: the ontology slice, the examples, the generated SPARQL, its repairs, the plan, the price and the answer.",
        "Demo",
        "Pick a graph and a question; Hermes runs in your browser and shows every stage. The sample questions replay recorded replies of Llama 3.1 8B; for your own questions, use a model you run or paste its replies.",
        """
<aside class="callout"><span class="label">What runs where</span><p>Hermes's own Python package runs in your browser under <strong>Pyodide</strong>, the same wheel the benchmarks run, and its queries run on <strong>Oxigraph</strong> compiled to WebAssembly, the engine Hermes uses for local graphs. No server of ours is involved. Only the model is not here: Ollama on your computer is detected under <em>My model</em>, a small model can run in the page on WebGPU, or you can paste replies. Your files stay in the page.</p></aside>
<div id="hd-ask" aria-label="Ask a question">Loading…</div>
<script src="pg.js"></script>
<script src="app.js"></script>
<h2 id="reading-it">Reading it</h2>
<ul>
<li><b>Ontology slice</b>: what the model is shown of the ontology. Classes and properties are chosen by the question's words, then completed with what the chosen classes use; values and entities are those the question names.</li>
<li><b>Repair</b>: each change, with its reason. Problems that remain are sent back to the model while the budget allows.</li>
<li><b>Plan</b>: the query as relational algebra, as written and as rewritten, with the estimated rows of every operator.</li>
<li><b>Price and spend</b>: what the run was expected to cost before each step, and what it cost. A step that would go over the budget is not taken.</li>
</ul>
""",
    )
    page(
        "plan.html",
        "Try: plan a query",
        "Paste a SPARQL query: see it as relational algebra, the rewrites the optimizer makes with the graph's statistics, and what each plan fetches.",
        "Demo",
        "No model needed. Paste a SPARQL query or pick a sample; Hermes translates it into relational algebra, rewrites it with the graph's statistics, runs both plans, and checks their answers against the engine.",
        """
<div id="hd-plan" aria-label="Plan a query">Loading…</div>
<script src="pg.js"></script>
<script src="app.js"></script>
<h2 id="reading-it">Reading it</h2>
<p>Each line of a plan is one operator: <code>scan</code> a triple pattern, <code>⋈</code> a join, <code>σ</code> a filter, <code>π</code> a projection, <code>⟕</code> OPTIONAL, <code>γ</code> grouping. <em>est</em> is the planner's estimate of the rows, <em>got</em> what the run produced. The plan executor treats the graph as a black box that answers single-pattern queries, so the join order decides how much is fetched; see <a href="planner.html">Planner</a>.</p>
""",
    )
    page(
        "pipeline.html",
        "Pipeline",
        "The stages of Hermes: ontology catalog and refiner, synthetic few-shot examples, prompt, generation, query refiner.",
        "hermes.pipeline",
        "A question goes through seven stages; each reports to observers as it starts and ends, and each prices what it is about to spend.",
        f"""
{PIPELINE}
<h2 id="catalog">The ontology catalog</h2>
<p>Everything the model may need to know about the graph. From the ontology: classes and properties with labels, comments, declared domains and ranges. From the data: how often each term is used, which properties the instances of each class use, which classes a property's objects belong to, whether a property holds literals or entities, the values of properties with few distinct values (currencies, countries), and the members of classes with at most 100 instances (departments, product categories). Built once per graph; 0.1 s for the corporate graph. Source: <a href="{SRC}/pipeline/catalog.py">catalog.py</a>.</p>
<h2 id="refiner">The ontology refiner</h2>
<p>Hermes keeps the classes, properties and values that rank highest for the question, adds the properties the chosen classes' instances use and the classes at both ends of the chosen properties, and links the entities the question names: exact labels, members of small classes the question names, and capitalized mentions ("Ms. Brant" finds "Karen Brant"). Ranking is pluggable: BM25 by default, or embeddings from any OpenAI-compatible or Ollama endpoint (<a href="{SRC}/retrieval.py">retrieval.py</a>).</p>
<pre><code>Properties (subject → object):
- pv:memberOf "member of": Agent, Employee, Manager → Department
Values that occur in the graph:
- pv:addressCountry "France"
Entities named in the question:
- prodi:prod-cat-Compensator "Compensator" (Product Category)</code></pre>
<h2 id="examples">Few-shot examples</h2>
<p>Built from the graph, never from benchmark questions (<a href="{SRC}/pipeline/synthetic.py">synthetic.py</a>): template queries over the catalog (an entity's attribute, a relation either way, instances with a listed value, a count, a superlative, two hops), filled with sampled entities and kept when they return 1 to 50 rows. The model writes the question each query answers from its terms' labels, and the pair is kept only if the pipeline, without examples, answers that question with the same answers (F1 ≥ 0.7). <code>hermes fewshot build --graph corporate</code> writes <code>data/fewshot/corporate.jsonl</code>; the two closest examples go in each prompt.</p>
<h2 id="generate">Generate</h2>
<p>One call. The prompt is built by a builder (<a href="{SRC}/pipeline/prompt.py">prompt.py</a>) from instructions, prefixes, the ontology slice, the examples and the question.</p>
<h2 id="repair">The query refiner</h2>
<p>Cheapest first, each change recorded (<a href="{SRC}/pipeline/repair.py">repair.py</a>):</p>
<ol>
<li>declare prefixes the query uses but forgot; move ORDER BY and LIMIT out of WHERE;</li>
<li>replace an unknown property or class by the closest known name;</li>
<li>replace an entity IRI the graph does not mention by the entity whose label matches it;</li>
<li>check types: a class used as a property, a literal where a property holds entities, an entity where it holds literals;</li>
<li>probe: one ASK query per pattern about a named entity, so <code>empl-Heinrich.Hoch a pv:Manager</code> is caught before the query runs empty;</li>
<li>send what is still wrong back to the model, at most twice, while the budget allows. An answer with no rows is sent back once more.</li>
</ol>
<h2 id="observers">Observers</h2>
<pre><code>from hermes.pipeline.events import Recorder, Printer
answer = Hermes(kg, observers=[Printer()]).ask(question)   # one line per stage</code></pre>
""",
    )
    page(
        "planner.html",
        "Planner",
        "SPARQL as relational algebra: translation, System R estimates, rewrite rules, the plan executor, and the study on gold queries.",
        "hermes.planner",
        "A query becomes a relational-algebra plan, the optimizer rewrites it with the graph's statistics, and the plan executor runs it against a graph that answers only single-pattern queries.",
        f"""
<h2 id="algebra">Relational algebra</h2>
<p>A triple pattern is a relation over its variables, a basic graph pattern the natural join of its patterns, and every other SPARQL operator a relational one: σ FILTER, π SELECT, ⟕ OPTIONAL, ∪ UNION, − MINUS, ε BIND, δ DISTINCT, τ ORDER BY, λ LIMIT and OFFSET, γ GROUP BY. <code>translate</code> keeps the patterns in the written order, so every reordering is the optimizer's and can be measured. Source: <a href="{SRC}/planner/algebra.py">algebra.py</a>.</p>
<pre><code>hermes plan --graph corporate --query 'SELECT ?name ?email WHERE {{ ?p pv:email ?email . ?p pv:name ?name .
  ?p pv:memberOf ?d . ?d pv:name "Marketing" . FILTER(CONTAINS(?name, "S")) }}'

Optimized
π ?name ?email                                   est 10.2 · got 2
└─ ⋈
   ├─ ⋈
   │  ├─ ⋈
   │  │  ├─ scan (?d pv:name "Marketing")          est 1.2 · got 1
   │  │  └─ scan (?p pv:memberOf ?d)               est 53.0 · got 10
   │  └─ σ CONTAINS(?name, "S")
   │     └─ scan (?p pv:name ?name)                got 10
   └─ scan (?p pv:email ?email)                    est 53.0 · got 2
                      as written   optimized
rows fetched                 160          23
intermediate rows            280          41</code></pre>
<h2 id="estimates">Estimates</h2>
<p>System R (Selinger et al., SIGMOD 1979), from the graph's statistics: per predicate its triples, distinct subjects and objects; per class its instances; property paths from their predicates. A scan joined after operands that bind its variables is priced as an index access, about (distinct bindings) × (rows per binding), because that is how the executor runs it. The cost of a plan is C_out, the summed sizes of its scans and joins. Source: <a href="{SRC}/planner/estimate.py">estimate.py</a>.</p>
<h2 id="rules">Rewrite rules</h2>
<p>Each rule is a command that rewrites the plan and logs what it did (<a href="{SRC}/planner/rules.py">rules.py</a>); the optimizer applies them in order, and a list of rules can be passed instead.</p>
<ul>
<li><b>push selections</b>: each σ moves to the lowest operator that binds all of its variables in every solution.</li>
<li><b>order joins</b>: each join group is reordered by dynamic programming over left-deep orders without cartesian products, minimizing C_out; each selection goes right after the operand that binds its last variable.</li>
<li><b>prune scans</b>: a scan fetches only the variables used above it.</li>
</ul>
<h2 id="executor">Executors</h2>
<p>The plan executor runs scans as single-pattern queries and joins as hash joins, or bind joins that send the left side's bindings with the scan (up to 500, 100 per query); every other operator is evaluated by rdflib's SPARQL engine over its children's rows, with EXISTS and property paths reading the graph through the same single-pattern queries. The engine executor sends the query text to the store and is the reference. Source: <a href="{SRC}/planner/executor.py">executor.py</a>.</p>
<h2 id="study">Study on gold queries</h2>
<p><code>experiments/planner_study.py</code> plans every distinct gold query of a benchmark as written and optimized, runs both, and compares their answers with the engine's. Report: <a href="{REPO}/blob/master/results/planner/README.md">results/planner</a>.</p>
<table>
<thead><tr><th scope="col"></th><th scope="col">CK26</th><th scope="col">DB26</th></tr></thead>
<tbody>
<tr><td>same answers as the engine</td><td>46</td><td>41</td></tr>
<tr><td>same up to rows tied under ORDER BY with LIMIT</td><td>1</td><td>0</td></tr>
<tr><td>the engine is wrong, the plan right (Oxigraph 0.5.11 reads <code>a / b * c</code> as <code>a / (b * c)</code>)</td><td>1</td><td>0</td></tr>
<tr><td>the engine cannot run the gold query</td><td>2</td><td>0</td></tr>
<tr><td>a scan over 200,000 rows, or the endpoint failed</td><td>0</td><td>9</td></tr>
<tr><td><b>plans that ran and gave other answers</b></td><td><b>0</b></td><td><b>0</b></td></tr>
<tr><td>intermediate rows, as written → optimized</td><td>1,302,989 → 106,719</td><td>1,097,107 → 1,060,291</td></tr>
<tr><td>rows fetched, as written → optimized</td><td>56,460 → 48,429</td><td>622,861 → 588,535</td></tr>
<tr><td>plan seconds, as written → optimized</td><td>4.67 → 1.35</td><td>68.4 → 29.7</td></tr>
<tr><td>q-error of the row estimate, median / 90th percentile</td><td>1.10 / 5.17</td><td>1.41 / 10.79</td></tr>
</tbody></table>
<p>Most gold queries have one or two patterns and nothing to reorder; the savings come from the others, such as CK26 question 28 (intermediate rows 419,035 → 3,353) and DB26 question 41 (rows fetched 32,896 → 27).</p>
""",
    )
    page(
        "pricing.html",
        "Pricing and budgets",
        "How Hermes prices model calls and graph queries before it spends them, and how a budget caps a run.",
        "hermes.pricing",
        "Every model call and every plan is priced before it runs; a budget caps calls, tokens, dollars, graph queries and rows, and a run reports what each stage was expected to cost and what it cost.",
        f"""
<h2 id="prices">Prices</h2>
<p>A <code>Price</code> counts model calls, input and output tokens, dollars when the model has a list price, graph queries and rows fetched. A model call is priced from its prompt (four characters a token) with 400 output tokens; a plan from the planner's estimates of the queries and rows its executor will fetch. Source: <a href="{SRC}/pricing/budget.py">budget.py</a>, list prices in <a href="{SRC}/pricing/prices.py">prices.py</a>.</p>
<h2 id="budgets">Budgets</h2>
<pre><code>from hermes import Budget, Hermes
answer = Hermes(kg, budget=Budget(llm_calls=3, tokens=20_000, rows=50_000)).ask(question)
answer.spend.to_dict()     # per stage: estimated and actual
answer.error               # "over budget at execute: rows would reach 61,204, over the cap of 50,000"</code></pre>
<p>A step that would break the budget is not taken: a repair the budget cannot afford is skipped and the problems are reported; a plan over the row cap is not run. <code>BudgetedLLM</code> decorates any model client with the same check.</p>
<h2 id="graph-pricing">Pricing graph queries</h2>
<p>The graph side of a price comes from the planner (see <a href="planner.html#estimates">estimates</a>): a plan's rows fetched are estimated scan by scan, with bind joins priced as index accesses, before anything is sent. On the corporate graph the median q-error of the result's row estimate is 1.10; on DBpedia, where statistics come from the endpoint one predicate at a time, 1.41.</p>
""",
    )
    page(
        "graphs.html",
        "Graphs",
        "Knowledge graphs in Hermes: local RDF files in Oxigraph or rdflib, SPARQL endpoints, and the browser.",
        "hermes.graph",
        "A KnowledgeGraph is a store to query, a schema to read the ontology from, and preferred prefixes. Stores answer SPARQL 1.1 JSON, so files and endpoints are interchangeable.",
        f"""
<pre><code>from hermes import KnowledgeGraph
kg = KnowledgeGraph.from_files("ontology.ttl", "data.ttl", schema=["ontology.ttl"])
kg = KnowledgeGraph.from_endpoint("https://dbpedia.org/sparql")
from hermes import benchmarks; kg = benchmarks.graph("corporate")   # data/graphs.yaml</code></pre>
<ul>
<li><b>Oxigraph</b> (default for files), <b>rdflib</b>, <b>endpoint</b> and <b>browser</b> (the page's Oxigraph under Pyodide) stores; a caching decorator memoizes results and counts executions. Source: <a href="{SRC}/graph/stores.py">stores.py</a>.</li>
<li>Statistics are read once for local graphs and one predicate at a time from endpoints (<a href="{SRC}/pricing/statistics.py">statistics.py</a>).</li>
<li>Entity linking matches labels exactly, or by their words (<a href="{SRC}/graph/linking.py">linking.py</a>).</li>
</ul>
""",
    )
    page(
        "evaluation.html",
        "Evaluation",
        "Benchmarks, the official Text2SPARQL scorer, experiment runs, and the results of Hermes and its baselines.",
        "hermes.experiments",
        "Six benchmarks in one format, a scorer that reproduces every published Text2SPARQL 2026 score, and runs that record their config, commit, answers and cost.",
        f"""
<h2 id="benchmarks">Benchmarks</h2>
<p>Text2SPARQL 2026 corporate (CK26) and DBpedia (DB26), their 2025 editions, QALD-9-plus and QALD-10, fetched with <code>hermes data fetch</code>. CK26 is CK25 paraphrased, so CK25 is not a development set for CK26.</p>
<h2 id="runs">Runs</h2>
<pre><code>hermes run configs/ck26/hermes.yaml
hermes sweep configs/sweeps/hermes.yaml   # Hermes, its ablations, and baselines
hermes report</code></pre>
<p>Each run writes its config, commit, every prediction with its cost, and metrics under <code>results/</code>. Scores: the official set F1 and F1-nDCG, a strict variant, and the subset whose gold answers reproduce on the local engine.</p>
<h2 id="results">Results</h2>
{results_html()}
""",
    )
    page(
        "baselines.html",
        "Baselines",
        "The systems Hermes is compared with: training-free, UniQGen, the algebra agent, the prover, and the budgeted planner.",
        "hermes.baselines",
        "Earlier systems, behind the same system interface and run on the same graphs and scorer.",
        f"""
<table>
<thead><tr><th scope="col">system</th><th scope="col">what it does</th><th scope="col">model calls</th></tr></thead>
<tbody>
<tr><td><code>training-free</code></td><td>one prompted draft from the vocabulary, one parse repair</td><td>1-2</td></tr>
<tr><td><code>uniqgen</code></td><td>UniQGen (Wang et al., arXiv 2605.00845): a constraint table refined with Chase and Backchase</td><td>2</td></tr>
<tr><td><code>algebra-agent</code></td><td>the model applies one algebra operator per step and sees its effect</td><td>up to 15</td></tr>
<tr><td><code>prover</code></td><td>the algebra agent with a verifier and a stated goal</td><td>up to 15</td></tr>
<tr><td><code>budgeted</code></td><td>bracketed phrases bound to the ontology, candidates checked, priced and run within a budget</td><td>up to 3</td></tr>
</tbody></table>
<p>Their earlier runs are archived in <a href="{REPO}/tree/master/results/archive">results/archive</a>.</p>
""",
    )
    page(
        "reference.html",
        "Python and CLI",
        "The Python API and command line of Hermes, and how to choose the model.",
        "Reference",
        "Ask, plan, build few-shot examples, run benchmarks, and serve the Text2SPARQL challenge API.",
        f"""
<h2 id="cli">Command line</h2>
<pre><code>hermes ask --graph corporate "Who is Heinrich Hoch's manager?" --calls 3 --rows 50000
hermes ask --files data.ttl --ontology onto.ttl "..."
hermes plan --graph corporate --file query.rq
hermes fewshot build --graph corporate --count 30
hermes data fetch ck26 db26
hermes run configs/ck26/hermes.yaml
hermes sweep configs/sweeps/hermes.yaml
hermes report
hermes serve --config configs/ck26/hermes.yaml     # the Text2SPARQL challenge API</code></pre>
<h2 id="python">Python</h2>
<pre><code>from hermes import Budget, Hermes, KnowledgeGraph
from hermes import planner

answer = Hermes(kg, budget=Budget(llm_calls=3)).ask(question)
optimized = planner.plan(sparql, kg)
result = planner.PlanExecutor(kg)(optimized.query)</code></pre>
<h2 id="models">Models</h2>
<p>Ollama by default (<code>HERMES_OLLAMA_MODEL</code>), or <code>HERMES_LLM_PROVIDER</code> = <code>openai</code>, <code>anthropic</code>, <code>together</code>, <code>huggingface</code>, <code>vllm</code> or <code>modal</code> with the provider's key. Completions can be cached on disk so runs replay (<a href="{SRC}/llm.py">llm.py</a>).</p>
""",
    )
    import normalize

    normalize.run(ROOT)


if __name__ == "__main__":
    main()
