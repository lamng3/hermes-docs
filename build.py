#!/usr/bin/env python3
"""Write the Hermes docs site."""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent

NAV = [
    ("index.html", "Overview"),
    ("algebra.html", "Algebra"),
    ("verifier.html", "Verifier"),
    ("systems.html", "Systems"),
    ("stores.html", "Graph stores"),
    ("benchmarks.html", "Benchmarks"),
    ("evaluation.html", "Evaluation"),
    ("experiments.html", "Experiments"),
    ("generate.html", "Training-free"),
    ("vocabulary.html", "Vocabulary"),
    ("stages.html", "Stages"),
    ("validate.html", "Validation"),
    ("models.html", "Models"),
]

REPO = "https://github.com/lamng3/hermes"
SRC = REPO + "/blob/master/src/hermes"

FOOTER = (
    "Hermes: Verified Query Planning over the SPARQL Algebra with Language Agents. "
    f'<a href="{REPO}/blob/master/paper/hermes.pdf">Paper</a> · '
    f'<a href="{REPO}">Code</a>.'
)


def nav_html(current):
    links = ['<a class="brand-desk" href="index.html">Hermes</a>']
    for href, label in NAV:
        current_attr = ' aria-current="page"' if href == current else ""
        links.append(f'<a href="{href}"{current_attr}>{label}</a>')
    return "".join(links)


HEADER = """<header class="site">
  <a class="logo" href="index.html"><span class="logo-mark">H</span><span>Hermes</span></a>
  <nav class="site">
    <a href="algebra.html">Algebra</a>
    <a href="verifier.html">Verifier</a>
    <a href="benchmarks.html">Benchmarks</a>
    <label class="nav-button" for="nav-toggle">Menu</label>
    <a href="https://github.com/lamng3/hermes" class="pill">GitHub ↗</a>
  </nav>
</header>"""

HEAD = """<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=TikTok+Sans:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
<link rel="icon" href="favicon.svg" type="image/svg+xml">
<link rel="stylesheet" href="style.css">"""

HOME = """<section class="hero">
  <div>
    <h1>Verified query planning over the SPARQL algebra</h1>
    <p class="lede">LEDE</p>
    <pre class="install"><span class="prompt">$ </span>git clone https://github.com/lamng3/hermes.git &amp;&amp; cd hermes
<span class="prompt">$ </span>pip install -e ".[dev]"
<span class="prompt">$ </span>hermes generate --graph corporate --system prover --question "..."</pre>
    <div class="actions">
      <a class="btn solid" href="algebra.html">The algebra</a>
      <a class="btn" href="verifier.html">Verifier</a>
      <a class="btn" href="benchmarks.html">Benchmarks</a>
    </div>
  </div>
  <div class="demo-card" id="demo">
    <div class="head"><h3>Four systems, one question</h3><span class="tag">recorded <b>benchmark runs</b></span></div>
    <label class="pick">Question <select id="question" aria-label="Question"></select></label>
    <div class="tabs" id="tabs" role="tablist"></div>
    <pre class="sparql" id="sparql"></pre>
    <div class="verdict-row" id="scores"></div>
    <hr class="rule">
    <div class="head"><h3>Leaderboard</h3><span class="tag">set F-nDCG, <b>ck26</b></span></div>
    <div class="bars" id="board"></div>
    <p class="note">Qwen3-14B on 100 questions of the Text2SPARQL 2026 corporate benchmark; answers are scored by the benchmark's official scorer. Several official systems score higher than every Hermes run, and the leaderboard shows them. The page computes nothing: it shows <code>SOURCE</code>.</p>
  </div>
</section>
<section class="block"><div class="prose-home">BODY</div></section>
<script src="demo.js"></script>"""


def home_page(title, description, lede, body):
    import json

    body = re.sub(r'<nav class="toc">.*?</nav>', "", body, flags=re.S)
    source = json.loads((ROOT / "demo-data.json").read_text())["source"]
    hero = HOME.replace("LEDE", lede).replace("SOURCE", source).replace("BODY", body)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
{HEAD}
<title>Hermes — verified query planning over the SPARQL algebra</title>
<meta name="description" content="{description}">
</head>
<body>
<a class="skip" href="#content">Skip to content</a>
<input id="nav-toggle" class="nav-toggle" type="checkbox">
{HEADER}
<main class="wrap" id="content" style="max-width:1280px">
{hero}
</main>
<footer class="site">{FOOTER}</footer>
</body>
</html>
"""


def page(filename, title, description, kicker, lede, body):
    if filename == "index.html":
        (ROOT / filename).write_text(home_page(title, description, lede, body), encoding="utf-8")
        return
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} - Hermes</title>
<meta name="description" content="{description}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=TikTok+Sans:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
<link rel="icon" href="favicon.svg" type="image/svg+xml">
<link rel="stylesheet" href="style.css">
</head>
<body>
<a class="skip" href="#content">Skip to content</a>
<header class="site">
  <a class="logo" href="index.html"><span class="logo-mark">H</span><span>Hermes</span></a>
  <nav class="site">
    <a href="algebra.html">Algebra</a>
    <a href="verifier.html">Verifier</a>
    <a href="benchmarks.html">Benchmarks</a>
    <label class="nav-button" for="nav-toggle">Menu</label>
    <a href="https://github.com/lamng3/hermes" class="pill">GitHub ↗</a>
  </nav>
</header>
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


def main():
    page(
        "index.html",
        "Overview",
        "Hermes: verified query planning over the SPARQL algebra with language agents. Paper, code, benchmarks, and experiments.",
        "Hermes",
        "Hermes answers a question over a knowledge graph by planning a SPARQL query one algebra operator at a time. A verifier types every step against the RDF schema before it runs, and execution on the graph tells the planner what each step did.",
        f"""
<nav class="toc"><strong>On this page</strong><ol><li><a href="#idea">The idea</a></li><li><a href="#pieces">The pieces</a></li><li><a href="#quick-start">Quick start</a></li><li><a href="#install">Install</a></li></ol></nav>
<p>This site documents the code of the paper <a href="{REPO}/blob/master/paper/hermes.pdf"><em>Hermes: Verified Query Planning over the SPARQL Algebra with Language Agents</em></a> (Lam Nguyen, Case Western Reserve University). The repository is its official implementation.</p>
<h2 id="idea">The idea</h2>
<p>Language models usually write a whole SPARQL query, then repair it after it fails. A query optimizer works differently: it applies one algebraic operator at a time and estimates its effect before keeping it. Hermes takes the optimizer's view of query generation:</p>
<ol>
<li><strong>A typed SPARQL algebra.</strong> A query plan is a term of the algebra. The RDF schema gives every variable a type, and rules decide without running the plan whether it is valid. See <a href="verifier.html">Verifier</a>.</li>
<li><strong>Verified query planning.</strong> Actions are algebra operators. After each one the planner sees the number of solutions, how it changed, a sample of rows, and any error. A plan is accepted only when it is valid and meets a goal stated from the question. See <a href="algebra.html">Algebra</a>.</li>
<li><strong>One interface for methods.</strong> One-shot generation, constraint-guided search (UniQGen), and the planners are swappable systems on the same graphs and the same scorer. See <a href="systems.html">Systems</a>.</li>
<li><strong>A reproducible evaluation.</strong> Six benchmarks in one format, and a scorer that reproduces every published Text2SPARQL 2026 score. See <a href="benchmarks.html">Benchmarks</a> and <a href="evaluation.html">Evaluation</a>.</li>
</ol>
<h2 id="pieces">The pieces</h2>
<div class="cards">
<a class="card" href="algebra.html"><strong>Algebra</strong><span>Plans, actions, the explorer, and the feedback after every step.</span></a>
<a class="card" href="verifier.html"><strong>Verifier</strong><span>Typing, well-formedness, goals, and the <code>prover</code> system.</span></a>
<a class="card" href="systems.html"><strong>Systems</strong><span>The registry and the four shipped systems.</span></a>
<a class="card" href="stores.html"><strong>Graph stores</strong><span>Oxigraph, rdflib, and SPARQL endpoints behind one <code>query</code> call.</span></a>
<a class="card" href="benchmarks.html"><strong>Benchmarks</strong><span>Text2SPARQL and QALD in one normalized format, with caveats.</span></a>
<a class="card" href="evaluation.html"><strong>Evaluation</strong><span>Official, strict, and reproducible-subset metrics.</span></a>
<a class="card" href="experiments.html"><strong>Experiments</strong><span>Configs, runs, the leaderboard, and the challenge API.</span></a>
<a class="card" href="models.html"><strong>Models</strong><span>Ollama or an OpenAI-compatible API, with retries and a replay cache.</span></a>
</div>
<h2 id="quick-start">Quick start</h2>
<pre><code>hermes data fetch ck26                      # download and normalize a benchmark
hermes run configs/ck26/algebra-agent.yaml  # predict, execute, score
hermes report                               # leaderboard with official peer scores</code></pre>
<p>One question at a time:</p>
<pre><code>hermes generate --graph corporate --system prover \\
  --question "Who is Heinrich Hoch's manager?"</code></pre>
<pre><code>from hermes import KnowledgeGraph, ask

kg = KnowledgeGraph.from_files("onto.ttl", "data.ttl")
result = ask("Which cities hosted the Winter Olympics?", kg, system="prover")
print(result["sparql"])</code></pre>
<h2 id="install">Install</h2>
<pre><code>git clone {REPO}.git
cd hermes
pip install -e ".[dev]"
pytest</code></pre>
<p>The install name is <code>hermes-sparql</code> and the import name is <code>hermes</code>. Python 3.11 or newer. Dependencies are <code>rdflib</code>, <code>pyoxigraph</code>, <code>httpx</code>, and <code>pyyaml</code>. The tests need no model and no network.</p>
""",
    )
    page(
        "algebra.html",
        "Algebra",
        "SPARQL algebra operators as actions, and the explorer that observes each action's effect on the graph.",
        "hermes.algebra",
        "A query is an immutable plan built one operator at a time. The explorer applies an action, runs the plan, and reports what changed.",
        f"""
<nav class="toc"><strong>On this page</strong><ol><li><a href="#actions">Actions</a></li><li><a href="#explorer">The explorer</a></li><li><a href="#observations">Observations</a></li><li><a href="#policies">Policies</a></li></ol></nav>
<h2 id="actions">Actions</h2>
<p>Each action is a frozen dataclass with an <code>apply(plan)</code> method, written as one JSON object. <code>parse_action</code> turns the JSON into a typed command. Source: <a href="{SRC}/algebra.py">algebra.py</a>.</p>
<table>
<tr><th>Action</th><th>SPARQL algebra</th><th>Example</th></tr>
<tr><td><code>triple</code></td><td>BGP, join</td><td><code>{{"op": "triple", "pattern": "?c ex:hosted ?g"}}</code></td></tr>
<tr><td><code>filter</code></td><td>Filter</td><td><code>{{"op": "filter", "expr": "?year &gt; 1900"}}</code></td></tr>
<tr><td><code>optional</code></td><td>LeftJoin</td><td><code>{{"op": "optional", "patterns": ["?c ex:country ?k"]}}</code></td></tr>
<tr><td><code>union</code></td><td>Union</td><td><code>{{"op": "union", "branches": [[...], [...]]}}</code></td></tr>
<tr><td><code>minus</code></td><td>Minus</td><td><code>{{"op": "minus", "patterns": [...]}}</code></td></tr>
<tr><td><code>bind</code></td><td>Extend</td><td><code>{{"op": "bind", "expr": "YEAR(?date)", "var": "?y"}}</code></td></tr>
<tr><td><code>group</code>, <code>aggregate</code></td><td>Group, Aggregation</td><td><code>{{"op": "aggregate", "expr": "COUNT(?g)", "alias": "?n"}}</code></td></tr>
<tr><td><code>having</code></td><td>Filter on groups</td><td><code>{{"op": "having", "expr": "?n &gt; 2"}}</code></td></tr>
<tr><td><code>order</code></td><td>OrderBy</td><td><code>{{"op": "order", "expr": "DESC(?n)"}}</code></td></tr>
<tr><td><code>project</code>, <code>distinct</code></td><td>Project, Distinct</td><td><code>{{"op": "project", "vars": ["?c"]}}</code></td></tr>
<tr><td><code>limit</code>, <code>offset</code></td><td>Slice</td><td><code>{{"op": "limit", "n": 1}}</code></td></tr>
<tr><td><code>ask</code></td><td>ASK form</td><td><code>{{"op": "ask"}}</code></td></tr>
<tr><td><code>remove</code></td><td>retract a triple or filter</td><td><code>{{"op": "remove", "text": "?c ex:country ?k"}}</code></td></tr>
</table>
<p>Two actions read the graph and leave the plan alone: <code>lookup</code> finds entities whose label contains a text, and <code>inspect</code> lists the predicates around an entity, or used by the instances of a class, with counts and an example value. Control actions are <code>goal</code> (see <a href="verifier.html">Verifier</a>), <code>undo</code>, and <code>finish</code>.</p>
<p><code>render(plan, header)</code> is the builder from a plan to SPARQL. It is deterministic.</p>
<h2 id="explorer">The explorer</h2>
<pre><code>from hermes.algebra import Explorer, parse_action

explorer = Explorer(kg)
explorer.run(parse_action({{"op": "triple", "pattern": "?city ex:hosted ?g"}}))
explorer.preview(parse_action({{"op": "triple", "pattern": "?g ex:season \\"Winter\\""}}))
print(explorer.sparql)</code></pre>
<p><code>run</code> commits a plan-changing action only if the new plan parses, passes the verifier when one is installed, and runs. <code>preview</code> returns the same observation without committing. <code>undo</code> restores the previous plan. <code>Explorer(kg, sample_size=5, kernel=None)</code>; pass a kernel to type-check every step.</p>
<h2 id="observations">Observations</h2>
<p>After each step the explorer runs two queries: the number of solutions, as a <code>COUNT</code> over the plan used as a subquery, and a sample of rows under <code>LIMIT</code>. An <code>ASK</code> plan reports its Boolean. <code>Observation.summary()</code> is the line the planner reads:</p>
<pre><code>{{"op": "triple", "pattern": "?city ex:hosted ?g"}}       -&gt; 19 solutions
{{"op": "triple", "pattern": "?city ex:country ex:USA"}}  -&gt; 19 -&gt; 8 solutions
{{"op": "triple", "pattern": "?g ex:season \\"Winter\\""}}  -&gt; 8 -&gt; 4 solutions
{{"op": "distinct"}}                                       -&gt; 4 -&gt; 3 solutions</code></pre>
<p>A rejected step reads <code>rejected: ...</code> with the parser, verifier, or store message. Executions are memoized by the store cache.</p>
<h2 id="policies">Policies</h2>
<p>Any policy can choose the actions. The <code>algebra-agent</code> system is an LLM policy: each turn it sees the action catalogue, the vocabulary, linked entities, every earlier action and observation, and the current query, and replies with one action. It stops on <code>finish</code> or after <code>max_steps</code> (15), refuses an action identical to the previous one, and returns the last committed plan that runs. Source: <a href="{SRC}/systems/algebra_agent.py">algebra_agent.py</a>. UniQGen's Chase and Backchase is, in these terms, a beam search over <code>remove</code> and <code>triple</code>.</p>
""",
    )
    page(
        "verifier.html",
        "Verifier",
        "The Hermes verifier: typing plans against the RDF schema, well-formedness, goals, and the prover system.",
        "hermes.kernel",
        "The verifier checks a plan against the schema and a stated goal before anything runs. Ill-typed steps never reach the graph store.",
        f"""
<nav class="toc"><strong>On this page</strong><ol><li><a href="#typing">Typing</a></li><li><a href="#errors">Errors</a></li><li><a href="#goals">Goals</a></li><li><a href="#prover">The prover system</a></li></ol></nav>
<h2 id="typing">Typing</h2>
<p><code>Schema.from_kg(kg)</code> reads classes, properties, <code>rdfs:domain</code>, <code>rdfs:range</code>, and the closure of <code>rdfs:subClassOf</code>. <code>Kernel.check(plan, goal)</code> builds a typing context for the plan's variables:</p>
<ul>
<li><code>?x a C</code> gives <code>?x : C</code>.</li>
<li><code>?x p ?y</code> gives <code>?x</code> the domain of <code>p</code> and <code>?y</code> its range.</li>
<li>Classes are compared up to subclass.</li>
</ul>
<p>Two unrelated classes on one variable are a warning, not an error: RDF is open world and the schema need not declare disjointness. Source: <a href="{SRC}/kernel.py">kernel.py</a>.</p>
<h2 id="errors">Errors</h2>
<table>
<tr><th>Error</th><th>Example message</th></tr>
<tr><td>Unknown term in a namespace the schema describes</td><td><code>unknown property ex:hosts (did you mean ex:hosted?)</code></td></tr>
<tr><td>Literal where an entity is required</td><td><code>type mismatch: ex:hosted expects an entity of ex:OlympicGames, got the literal "Winter"</code></td></tr>
<tr><td>Literal used as an entity, or the reverse</td><td><code>type mismatch: ?s is a literal but ...</code></td></tr>
<tr><td>Unbound variable</td><td><code>unbound variable ?y in FILTER</code></td></tr>
<tr><td>BIND onto a bound variable</td><td><code>BIND target ?g is already bound</code></td></tr>
<tr><td>Ungrouped projection</td><td><code>?g is neither grouped nor aggregated</code></td></tr>
</table>
<p>Variables that occur only inside <code>MINUS</code> are not bound, as in SPARQL. The check runs in one pass over the plan; nothing is executed.</p>
<h2 id="goals">Goals</h2>
<p>A goal states what the question asks for before the query exists:</p>
<pre><code>{{"op": "goal", "answer": ["?c"], "kind": "entity", "type": "ex:City", "many": true}}</code></pre>
<p><code>kind</code> is <code>entity</code>, <code>literal</code>, <code>number</code>, or <code>boolean</code>; <code>type</code> is optional; <code>many</code> is false when one answer is expected. The verifier lists the open goals the plan does not yet meet: the answer variable is not bound or not projected, other variables are projected, a number is not an aggregate or a numeric value, an entity is a literal, the type is not established, a yes-or-no question is not an <code>ASK</code>, or, after execution, there is more than one solution when one was asked for.</p>
<p>The goal is written by the planner from the question, so it can be wrong. The verifier guarantees that a plan has the shape its goal asks for, not that the goal is the question.</p>
<h2 id="prover">The prover system</h2>
<p><code>prover</code> is the algebra agent with the verifier installed. The planner states the goal first. Each turn the prompt shows the plan state: the typing context and the open goals. <code>finish</code> is refused while an error or an open goal remains. The result adds <code>kernel_rejections</code> and <code>goal</code>. Source: <a href="{SRC}/systems/prover.py">prover.py</a>.</p>
<pre><code>context:
  ?c : ex:City
  ?g : ex:OlympicGames
open goals:
  goals accomplished</code></pre>
""",
    )
    page(
        "systems.html",
        "Systems",
        "The Hermes system registry and the four shipped systems.",
        "hermes.systems",
        "A system turns a question into SPARQL over a knowledge graph. Systems register by name, so experiments swap them without code changes.",
        f"""
<nav class="toc"><strong>On this page</strong><ol><li><a href="#contract">Contract</a></li><li><a href="#shipped">Shipped systems</a></li><li><a href="#register">Register a system</a></li><li><a href="#plugins">Plugins</a></li></ol></nav>
<h2 id="contract">Contract</h2>
<pre><code>def system(question, kg, context):
    return {{"sparql": "..."}}</code></pre>
<p><code>kg</code> is a <a href="stores.html"><code>KnowledgeGraph</code></a>. <code>context</code> is a <code>Context</code> or <code>None</code>: free text, example question and query pairs, and, for ablations only, reference answers. The result has at least <code>sparql</code>; systems may add traces and counters. <code>hermes.ask(question, kg_or_path, context, system=..., **params)</code> runs one. Source: <a href="{SRC}/systems/__init__.py">systems/__init__.py</a>.</p>
<h2 id="shipped">Shipped systems</h2>
<table>
<tr><th>Name</th><th>Method</th><th>Parameters</th></tr>
<tr><td><code>training-free</code></td><td>One prompted draft, fixed stages, one repair. <a href="generate.html">Details</a>.</td><td><code>llm</code></td></tr>
<tr><td><code>uniqgen</code></td><td>UniQGen (Wang et al., <a href="https://arxiv.org/abs/2605.00845">arXiv:2605.00845</a>): a constraint table, then Chase and Backchase against reference answers.</td><td><code>beam_width</code> 5, <code>max_depth</code> 5, <code>threshold</code> 1.0, <code>alpha</code> 0.5, <code>hops</code> 2, <code>oracle</code> (LLM, <code>"gold"</code>, or a callable), <code>llm</code></td></tr>
<tr><td><code>algebra-agent</code></td><td>An LLM plans over the <a href="algebra.html">algebra</a> with execution feedback.</td><td><code>max_steps</code> 15, <code>sample_size</code> 5, <code>max_entities</code> 10, <code>llm</code></td></tr>
<tr><td><code>prover</code></td><td>The algebra agent with the <a href="verifier.html">verifier</a> and goals.</td><td>as <code>algebra-agent</code></td></tr>
</table>
<p>The UniQGen reimplementation differs from the paper in two documented ways: queries are rendered from constraints deterministically, and candidates are scored by comparing answer sets with the reference answers. That keeps it at two model calls per question. Aggregates, <code>ORDER BY</code>, and <code>LIMIT</code> are not handled.</p>
<h2 id="register">Register a system</h2>
<pre><code>import hermes

@hermes.systems.register("my-system")
class MySystem:
    def __init__(self, llm=None, depth=3):   # config params arrive here
        self.llm = llm

    def __call__(self, question, kg, context):
        return {{"sparql": "SELECT * WHERE {{ ?s ?p ?o }} LIMIT 1"}}</code></pre>
<p>A class receives its parameters from <code>systems.create(name, **params)</code>, which is how experiment configs pass them; a function takes none. A name can be registered once. <code>hermes.systems.available()</code> lists the names, and <code>hermes systems</code> prints them.</p>
<h2 id="plugins">Plugins</h2>
<p>Another package can add a system without touching Hermes by declaring an entry point in the <code>hermes.systems</code> group that points at the system.</p>
""",
    )
    page(
        "stores.html",
        "Graph stores",
        "Knowledge graphs, graph stores, and entity linking in Hermes.",
        "hermes.store, hermes.knowledge, hermes.linking",
        "Systems and the scorer only call query(sparql), which returns SPARQL 1.1 JSON results. The same system runs on local files or a remote endpoint.",
        f"""
<nav class="toc"><strong>On this page</strong><ol><li><a href="#kg">KnowledgeGraph</a></li><li><a href="#stores">Stores</a></li><li><a href="#linking">Entity linking</a></li></ol></nav>
<h2 id="kg">KnowledgeGraph</h2>
<pre><code>from hermes import KnowledgeGraph

kg = KnowledgeGraph.from_files("prod-vocab.ttl", "prod-inst.ttl")          # Oxigraph
kg = KnowledgeGraph.from_files("onto.ttl", engine="rdflib")
kg = KnowledgeGraph.from_endpoint("https://dbpedia.org/sparql",
                                  prefixes=[("dbo", "http://dbpedia.org/ontology/")])</code></pre>
<p>A knowledge graph pairs a store with the <a href="vocabulary.html">vocabulary</a> used to prompt for it. <code>schema</code> names smaller files to read the vocabulary from. Loading is lazy, so nothing is parsed until the first query. <code>kg.executions</code> counts real executions. Source: <a href="{SRC}/knowledge.py">knowledge.py</a>.</p>
<h2 id="stores">Stores</h2>
<table>
<tr><th>Store</th><th>Backend</th></tr>
<tr><td><code>OxigraphStore</code></td><td>Local RDF files in Oxigraph. The default: it loads the 26.6k-triple corporate graph in a fraction of a second.</td></tr>
<tr><td><code>LocalStore</code></td><td>Local RDF files in rdflib, in pure Python.</td></tr>
<tr><td><code>EndpointStore</code></td><td>A SPARQL endpoint over HTTP POST, with retries on server errors, a 60-second timeout, and a User-Agent header.</td></tr>
<tr><td><code>CachedStore</code></td><td>Wraps any store, memoizes results, and counts executions.</td></tr>
</table>
<p>A failed query raises <code>QueryError</code>; <code>try_query</code> returns empty results instead. Turtle, N-Triples, N-Quads, RDF/XML, and TriG are read by extension. Source: <a href="{SRC}/store.py">store.py</a>.</p>
<h2 id="linking">Entity linking</h2>
<p><code>LabelIndex</code> reads <code>rdfs:label</code>, <code>skos:prefLabel</code>, <code>skos:altLabel</code>, and the local names of typed subjects once, and matches in memory, falling back to partial-word matches. <code>ExactLabel</code> sends capitalized n-grams of the question to the store as label literals in one <code>VALUES</code> query, for large endpoints such as DBpedia. <code>linker_for(kg)</code> picks the first for local stores and the second for endpoints. Source: <a href="{SRC}/linking.py">linking.py</a>.</p>
""",
    )
    page(
        "benchmarks.html",
        "Benchmarks",
        "Six NL-to-SPARQL benchmarks in one normalized format, with their sources, licenses, and caveats.",
        "hermes.benchmarks",
        "Every benchmark, whatever its source format, is stored the same way, so every system is scored the same way.",
        f"""
<nav class="toc"><strong>On this page</strong><ol><li><a href="#suite">The suite</a></li><li><a href="#format">Format</a></li><li><a href="#commands">Commands</a></li><li><a href="#caveats">Caveats</a></li></ol></nav>
<h2 id="suite">The suite</h2>
<table>
<tr><th>Name</th><th>Questions</th><th>Items</th><th>Graph</th><th>License</th></tr>
<tr><td><code>ck26</code></td><td>50</td><td>100 (en, de)</td><td>Text2SPARQL corporate graph, local</td><td>CC BY-SA 4.0</td></tr>
<tr><td><code>db26</code></td><td>50</td><td>100 (en, es)</td><td>DBpedia, organizers' endpoint</td><td>CC BY-SA 4.0</td></tr>
<tr><td><code>ck25</code></td><td>50</td><td>50 (en)</td><td>corporate graph, local</td><td>CC BY-SA 4.0</td></tr>
<tr><td><code>db25</code></td><td>100</td><td>200 (en, es)</td><td>DBpedia, organizers' endpoint</td><td>CC BY-SA 4.0</td></tr>
<tr><td><code>qald10</code></td><td>394</td><td>1,564</td><td>Wikidata, live</td><td>MIT</td></tr>
<tr><td><code>qald9plus</code></td><td>150</td><td>450</td><td>DBpedia, live</td><td>CC BY 4.0</td></tr>
</table>
<h2 id="format">Format</h2>
<pre><code>data/graphs.yaml                       local files or an endpoint per graph
data/benchmarks/&lt;name&gt;/benchmark.yaml   graph, languages, license, source URLs and SHA-256
data/benchmarks/&lt;name&gt;/questions.jsonl  one row per question and language
data/benchmarks/&lt;name&gt;/gold.json        gold answer sets</code></pre>
<pre><code>{{"id": "ck26:7-en", "qid": "7", "lang": "en", "question": "...", "sparql": "...",
 "features": ["SELECT", "ORDER"], "order_matters": false}}</code></pre>
<p>Ids follow the official scorer. Gold answers use its layout: every value of every variable, flattened into one set. Sources are pinned to commits. Adapters convert Text2SPARQL YAML and QALD JSON; a new benchmark is an adapter and an entry in <code>sources.py</code>. Source: <a href="{SRC}/benchmarks">benchmarks/</a>.</p>
<h2 id="commands">Commands</h2>
<pre><code>hermes data list                 # known and downloaded benchmarks
hermes data fetch ck26 db26      # download, normalize, fetch local graphs
hermes data verify ck26          # run every gold query and compare with gold</code></pre>
<h2 id="caveats">Caveats</h2>
<div class="callout next"><span class="label">Read first</span><p>These facts change how any number on these benchmarks should be read.</p></div>
<ol>
<li><strong>CK26 is CK25 paraphrased.</strong> 49 of the 50 CK26 gold queries appear verbatim in CK25, on the same graph. Neither is a development set for the other. Runs count overlapping few-shot examples as <code>contaminated_examples</code>.</li>
<li><strong>The CK gold answers depend on the engine.</strong> They were computed on Tentris. On Oxigraph, 43 of 50 CK26 gold queries reproduce; the rest differ in tie-breaking under <code>LIMIT</code>, number formatting, or the non-standard <code>xsd:int()</code>. All 50 DB26 gold queries reproduce on the organizers' endpoint.</li>
<li><strong>QALD answers drift.</strong> QALD-9-plus targets DBpedia 2016-10 and QALD-10 was answered on Wikidata in 2022; the live endpoints have changed.</li>
</ol>
""",
    )
    page(
        "evaluation.html",
        "Evaluation",
        "Official Text2SPARQL metrics reproduced exactly, a strict variant, and a reproducible subset.",
        "hermes.evaluation",
        "The scorer reproduces all 5,024 published Text2SPARQL 2026 scores, so Hermes numbers sit on the leaderboard's scale.",
        f"""
<nav class="toc"><strong>On this page</strong><ol><li><a href="#metrics">Metrics</a></li><li><a href="#parity">Parity</a></li><li><a href="#quirks">Official quirks and the strict variant</a></li><li><a href="#subset">Reproducible subset</a></li></ol></nav>
<h2 id="metrics">Metrics</h2>
<p>The official scorer flattens every value of every variable into one set and scores it with trec_eval: set precision, set recall, and set F1 per question, nDCG where order matters, and the ranking metric <code>set_F_ndcg</code>, which uses nDCG on those questions and F1 elsewhere. <code>score(result, gold, order_matters, strict)</code> scores one question; <code>aggregate(per_item, languages, strict)</code> gives overall and per-language averages. Source: <a href="{SRC}/evaluation.py">evaluation.py</a>.</p>
<h2 id="parity">Parity</h2>
<p><code>experiments/check_scorer.py</code> downloads every team's predictions and official scores for CK26 and DB26 from the pinned challenge repository, rescores them, and compares all 5,024 per-question and average numbers. None differ.</p>
<h2 id="quirks">Official quirks and the strict variant</h2>
<table>
<tr><th>Official behavior</th><th>Strict</th></tr>
<tr><td>An ASK answer is a document named <code>true</code>. A gold <code>true</code> scores 1.0 whatever the answer; a gold <code>false</code> scores 0.0 for everyone.</td><td>Booleans score by exact match.</td></tr>
<tr><td>nDCG ignores the returned order, since every value has the same score.</td><td>nDCG uses the returned order.</td></tr>
<tr><td><code>set_F_ndcg</code> counts the scope's mean nDCG as one extra item.</td><td>A plain mean.</td></tr>
</table>
<p>Runs report both, side by side.</p>
<h2 id="subset">Reproducible subset</h2>
<p>Each run also reruns every gold query on its own store and flags <code>gold_reproduces</code>. The <code>reproducible</code> averages restrict the official metrics to those items, which separates a method's errors from differences between graph engines.</p>
""",
    )
    page(
        "experiments.html",
        "Experiments",
        "Experiment configs, run outputs, provenance, the leaderboard, and the Text2SPARQL API.",
        "hermes.experiments, hermes.serve",
        "An experiment is a YAML config. A run predicts, executes, and scores every item, and keeps everything needed to reproduce or audit it.",
        f"""
<nav class="toc"><strong>On this page</strong><ol><li><a href="#config">Config</a></li><li><a href="#run">A run</a></li><li><a href="#report">Leaderboard</a></li><li><a href="#serve">Challenge API</a></li><li><a href="#rules">Rules for comparable numbers</a></li></ol></nav>
<h2 id="config">Config</h2>
<pre><code>benchmark: ck26
system: uniqgen
params:            # constructor arguments of the system
  beam_width: 5
llm:
  provider: ollama # or openai
  model: llama3.1
  cache: .cache/llm
languages: [en]    # optional
limit: 20          # optional
examples:          # optional few-shot pool from another benchmark
  benchmark: db25
  limit: 10
leak_gold: true    # ablations only: gold answers in context.answers</code></pre>
<p>Configs live in <code>configs/&lt;benchmark&gt;/</code>. <code>bash experiments/run_all.sh</code> reruns them all.</p>
<h2 id="run">A run</h2>
<pre><code>hermes run configs/ck26/prover.yaml [--limit N] [--resume RUN_ID]</code></pre>
<p>For each item, the system predicts a query, the query runs on the benchmark's store, and the answers are scored. Errors are recorded, not raised. A run writes <code>results/&lt;benchmark&gt;/&lt;config&gt;/&lt;run id&gt;/</code>:</p>
<table>
<tr><th>File</th><th>Contents</th></tr>
<tr><td><code>config.yaml</code></td><td>the config as run</td></tr>
<tr><td><code>predictions.jsonl</code></td><td>per item: SPARQL, error, seconds, official and strict scores, <code>gold_reproduces</code>, and system traces</td></tr>
<tr><td><code>metrics.json</code></td><td><code>official</code>, <code>strict</code>, and <code>reproducible</code> averages, error count, latency p50 and p95</td></tr>
<tr><td><code>run.json</code></td><td>model, model calls and cache hits, graph executions, contaminated examples, the commit the run started from and whether <code>src/</code> had local changes</td></tr>
</table>
<p>Observers receive start, item, and end events; <code>Progress</code> prints one line per item. Source: <a href="{SRC}/experiments.py">experiments.py</a>.</p>
<h2 id="report">Leaderboard</h2>
<pre><code>hermes report [--benchmark ck26] [--write]</code></pre>
<p>Prints the latest run of each config next to the official Text2SPARQL 2026 entries from <code>results/peers/</code>; <code>--write</code> saves <code>results/LEADERBOARD.md</code>.</p>
<h2 id="serve">Challenge API</h2>
<pre><code>hermes serve --config configs/ck26/prover.yaml --port 8000</code></pre>
<p><code>GET /?question=...&amp;dataset=&lt;dataset id&gt;</code> returns <code>{{"dataset", "question", "query"}}</code>, the contract the official text2sparql-client calls, so any system can be submitted or scored with the organizers' tools. An unknown dataset is 404, a missing question 422. Source: <a href="{SRC}/serve.py">serve.py</a>.</p>
<h2 id="rules">Rules for comparable numbers</h2>
<ul>
<li>Set the official metrics on all items next to published entries, with strict and reproducible figures beside them.</li>
<li>Never tune on the test benchmark; CK25 and CK26 share 49 of 50 queries.</li>
<li>Keep benchmark content out of prompts and examples. A run with <code>leak_gold</code> or contaminated examples is an upper bound, not a result.</li>
<li>Name the model. A local 8B model is a lower bound for a method, not its ceiling.</li>
</ul>
""",
    )
    page(
        "generate.html",
        "Training-free",
        "The training-free system: one prompted draft from the vocabulary, fixed stages, and one repair.",
        "hermes.systems.training_free",
        "The training-free system writes one SPARQL query from the schema vocabulary in a single model call, plus one repair call if the draft does not parse.",
        f"""
<nav class="toc"><strong>On this page</strong><ol><li><a href="#command">Command</a></li><li><a href="#python">From Python</a></li><li><a href="#prompt">Prompt</a></li><li><a href="#errors">Errors</a></li></ol></nav>
<h2 id="command">Command</h2>
<pre><code>hermes generate \\
  --ontology GeoOutage.ttl \\
  --question "Which counties have the highest number of outages?" \\
  --context notes.txt \\
  --examples pairs.jsonl</code></pre>
<table>
<tr><th>Flag</th><th>Meaning</th></tr>
<tr><td><code>--ontology</code>, <code>--graph</code>, or <code>--endpoint</code></td><td>One is required: an RDF file, a graph name from <code>data/graphs.yaml</code>, or a SPARQL endpoint URL.</td></tr>
<tr><td><code>--question</code></td><td>Required.</td></tr>
<tr><td><code>--context</code></td><td>A text file of extra context.</td></tr>
<tr><td><code>--examples</code></td><td>JSONL, one object per line with <code>nl</code> and <code>sparql</code> (<code>nl_text</code> and <code>sparql_query</code> are accepted).</td></tr>
<tr><td><code>--system</code></td><td>Any registered system; the default is <code>training-free</code>.</td></tr>
</table>
<p>Source: <a href="{SRC}/cli.py">cli.py</a>.</p>
<h2 id="python">From Python</h2>
<pre><code>from hermes import Context, Example, TrainingFree

system = TrainingFree()          # or TrainingFree(llm=...)
result = system(
    "Which counties have the highest number of outages?",
    "GeoOutage.ttl",
    Context(text="Counties are administrative regions.",
            examples=[Example(nl="List outage records.",
                              sparql="SELECT ?rec WHERE {{ ?rec a geooutageonto:OutageRecord }}")]),
)
print(result["sparql"])</code></pre>
<p>The result has <code>sparql</code>, <code>model</code>, and <code>provider</code>. Source: <a href="{SRC}/systems/training_free.py">training_free.py</a>.</p>
<h2 id="prompt">Prompt</h2>
<p><code>build_prompt</code> joins these sections with a blank line:</p>
<ol>
<li>Instructions: one query, only the prefixes and terms below, match labels in quotes, triples inside <code>WHERE</code>, <code>ORDER BY</code> and <code>LIMIT</code> after it, no <code>SELECT</code> inside <code>FILTER</code>, do not copy the shape example, return only the query.</li>
<li>A shape example with <code>ex:</code> terms that are not from the ontology.</li>
<li>Prefixes, classes, and properties from the <a href="vocabulary.html">vocabulary</a>.</li>
<li>Context text and example pairs, when given.</li>
<li>The question, last.</li>
</ol>
<h2 id="errors">Errors</h2>
<p>A reply without a query raises <code>ValueError</code>. A query that still fails to parse after one repair raises <code>ValueError</code> with the parser message. Model failures are <code>LookupError</code>; see <a href="models.html">Models</a>.</p>
""",
    )
    page(
        "vocabulary.html",
        "Vocabulary",
        "How Hermes reads classes, properties, and prefixes for prompting, through any graph store.",
        "hermes.ontology",
        "The vocabulary is a compact list of prefixes, classes, and properties. It is queried through a store, so it works the same for a file and an endpoint.",
        f"""
<nav class="toc"><strong>On this page</strong><ol><li><a href="#result">Result</a></li><li><a href="#terms">Classes and properties</a></li><li><a href="#prefixes">Prefixes</a></li></ol></nav>
<h2 id="result">Result</h2>
<pre><code>kg.vocabulary
{{
  "classes": ['ex:City "City"'],
  "properties": ['ex:inCountry "in country"'],
  "prefixes": [("ex", "http://example.org/demo#")],
}}</code></pre>
<p><code>vocabulary(store, declared, limit)</code> runs two queries on the store; <code>load_vocabulary(path)</code> does the same for one file. Source: <a href="{SRC}/ontology.py">ontology.py</a>.</p>
<h2 id="terms">Classes and properties</h2>
<p>Classes are IRIs typed <code>owl:Class</code> or <code>rdfs:Class</code>. Properties are IRIs typed <code>owl:ObjectProperty</code>, <code>owl:DatatypeProperty</code>, or <code>rdf:Property</code>. An <code>rdfs:label</code> is appended in quotes. Each list stops at <code>vocabulary_limit</code> terms (60 by default). A limit of 0 skips the queries, which is how large graphs such as DBpedia and Wikidata are declared in <code>data/graphs.yaml</code>.</p>
<h2 id="prefixes">Prefixes</h2>
<p>For files, declared prefixes come from the <code>@prefix</code> lines in the file text; for endpoints, from the graph's entry in <code>data/graphs.yaml</code>. RDF, RDFS, OWL, XSD, and XML namespaces are skipped, and at most 12 prefixes are kept. A namespace without a declaration gets a prefix from its last path segment, with a numeric suffix on collision.</p>
""",
    )
    page(
        "stages.html",
        "Stages",
        "The stages the training-free system runs between the draft query and parse checking.",
        "hermes.stages",
        "apply_stages walks a fixed tuple. Each function takes the draft and returns a query. Replacing a function is how a later technique enters the training-free pipeline.",
        f"""
<nav class="toc"><strong>On this page</strong><ol><li><a href="#contract">Contract</a></li><li><a href="#guardrails">Guardrails</a></li><li><a href="#later">Query guided, context guided, chase and backchase</a></li></ol></nav>
<h2 id="contract">Contract</h2>
<pre><code>def stage(sparql, *, ontology, context):
    return sparql

STAGES = (guardrails, query_guided, context_guided, chase_backchase)</code></pre>
<p><code>ontology</code> is the vocabulary dict, not a path. The stages run on the first draft and again on the repair draft. Source: <a href="{SRC}/stages.py">stages.py</a>.</p>
<h2 id="guardrails">Guardrails</h2>
<p>Declares known prefixes that the draft uses but does not declare, from the vocabulary and the RDF, RDFS, OWL, and XSD namespaces. Prefixes inside IRIs and string literals are ignored. Rejecting terms outside the vocabulary is the job of the <a href="verifier.html">verifier</a>, which the planners use.</p>
<h2 id="later">Query guided, context guided, chase and backchase <span class="tag">later</span></h2>
<p>These return the draft unchanged. Chase and Backchase now lives in the <code>uniqgen</code> system, over constraint tables, rather than as a post-processing stage.</p>
""",
    )
    page(
        "validate.html",
        "Validation",
        "How a model reply becomes one SPARQL string, and how a parse error is repaired once.",
        "hermes.validate",
        "prepare_draft extracts a query and moves solution modifiers out of WHERE. parse_error checks it with rdflib. One repair call is allowed.",
        f"""
<nav class="toc"><strong>On this page</strong><ol><li><a href="#extract">Extract</a></li><li><a href="#lift">Lift modifiers</a></li><li><a href="#parse">Parse and repair</a></li></ol></nav>
<h2 id="extract">Extract</h2>
<p><code>extract_sparql</code> prefers the first fenced block, including a <code>sparql</code> fence, and keeps the first span that starts at <code>SELECT</code>, <code>ASK</code>, <code>CONSTRUCT</code>, or <code>DESCRIBE</code> with any <code>PREFIX</code> lines before it. An empty result raises <code>ValueError</code>.</p>
<h2 id="lift">Lift modifiers</h2>
<p>Models often write <code>ORDER BY</code>, <code>LIMIT</code>, <code>GROUP BY</code>, <code>HAVING</code>, or <code>OFFSET</code> inside the outer <code>WHERE</code> block. <code>lift_modifiers</code> moves those lines after the block when they sit at brace depth zero; modifiers inside a nested <code>SELECT</code> stay put.</p>
<h2 id="parse">Parse and repair</h2>
<p><code>parse_error</code> calls <code>rdflib.plugins.sparql.prepareQuery</code> and returns <code>None</code> or the parser message. On an error, the training-free system sends <code>repair_prompt</code> once, then runs extraction and the stages again. A second error raises <code>ValueError</code>. Source: <a href="{SRC}/validate.py">validate.py</a>.</p>
""",
    )
    page(
        "models.html",
        "Models",
        "LLM clients in Hermes: Ollama, OpenAI-compatible APIs, retries, and a replay cache.",
        "hermes.llm",
        "Systems receive an LLM client, so experiments choose the model. Completions can be cached on disk, so a rerun replays the same outputs.",
        f"""
<nav class="toc"><strong>On this page</strong><ol><li><a href="#clients">Clients</a></li><li><a href="#ollama">Ollama</a></li><li><a href="#openai">OpenAI-compatible</a></li><li><a href="#cache">Cache and retries</a></li></ol></nav>
<h2 id="clients">Clients</h2>
<pre><code>from hermes import llm

client = llm.create(provider="ollama", model="llama3.1", cache=".cache/llm")
text = client.complete(prompt, system="...")</code></pre>
<p>Every client has <code>complete(prompt, system)</code>, <code>model</code>, and <code>provider</code>. <code>llm.create</code> builds one from a config's <code>llm</code> section; <code>llm.from_env()</code> builds the default from environment variables. Temperature is 0. Source: <a href="{SRC}/llm.py">llm.py</a>.</p>
<h2 id="ollama">Ollama</h2>
<table>
<tr><th>Variable</th><th>Default</th></tr>
<tr><td><code>HERMES_OLLAMA_BASE_URL</code></td><td><code>http://127.0.0.1:11434</code></td></tr>
<tr><td><code>HERMES_OLLAMA_MODEL</code></td><td>chosen from installed models: <code>llama3.1</code>, <code>llama3</code>, <code>mistral</code>, <code>phi3</code>, <code>qwen2.5</code>, <code>qwen</code>, then the first installed</td></tr>
</table>
<p>The timeout is 180 seconds. Connection failures, timeouts, and missing models raise <code>LookupError</code> with the command to fix them.</p>
<h2 id="openai">OpenAI-compatible</h2>
<table>
<tr><th>Variable</th><th>Default</th></tr>
<tr><td><code>HERMES_LLM_PROVIDER</code></td><td>set to <code>openai</code> to select this client</td></tr>
<tr><td><code>HERMES_LLM_API_KEY</code></td><td>required</td></tr>
<tr><td><code>HERMES_LLM_BASE_URL</code></td><td><code>https://api.together.xyz/v1</code></td></tr>
<tr><td><code>HERMES_LLM_MODEL</code></td><td><code>meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo</code></td></tr>
</table>
<p>The timeout is 60 seconds.</p>
<h2 id="cache">Cache and retries</h2>
<p><code>CachedLLM</code> stores each completion as a JSON file keyed by a hash of the provider, model, system prompt, and prompt, and counts calls and cache hits for <code>run.json</code>. Both clients retry up to three attempts on read errors and on HTTP 429, 502, 503, and 504, with backoff.</p>
""",
    )


if __name__ == "__main__":
    main()
