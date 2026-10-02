#!/usr/bin/env python3
"""Write the nl2sparql notes site."""

from pathlib import Path

ROOT = Path(__file__).resolve().parent

NAV = [
    ("index.html", "Overview"),
    ("generate.html", "Generate"),
    ("vocabulary.html", "Vocabulary"),
    ("stages.html", "Stages"),
    ("validate.html", "Validation"),
    ("models.html", "Models"),
]

FOOTER = (
    "nl2sparql. Training-free natural language to SPARQL. "
    'Code: <a href="https://github.com/lamng3/nl2sparql">github.com/lamng3/nl2sparql</a>.'
)


def nav_html(current):
    links = ['<a class="brand-desk" href="index.html">nl2sparql</a>']
    for href, label in NAV:
        current_attr = ' aria-current="page"' if href == current else ""
        links.append(f'<a href="{href}"{current_attr}>{label}</a>')
    return "".join(links)


def page(filename, title, description, kicker, lede, body):
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} - nl2sparql</title>
<meta name="description" content="{description}">
<link rel="stylesheet" href="style.css">
</head>
<body>
<a class="skip" href="#content">Skip to content</a>
<header class="top">
  <a class="brand" href="index.html">nl2sparql</a>
  <label class="nav-button" for="nav-toggle">Menu</label>
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
        "Training-free natural language to SPARQL: a question and a Turtle ontology in, one query out.",
        "nl2sparql",
        "A question, a Turtle ontology, and optional context go in. One SPARQL query comes out. The model is a generator. Nothing here is trained on query pairs.",
        """
<nav class="toc"><strong>On this page</strong><ol><li><a href="#the-pieces">The pieces</a></li><li><a href="#one-call">One call</a></li><li><a href="#install">Install</a></li></ol></nav>
<p>The public entry is <code>generate</code>. It loads a compact vocabulary, asks a model for a draft, walks a fixed list of stages, and checks that the result parses. The stages are the place later techniques plug in. Today each of them returns the draft unchanged.</p>
<h2 id="the-pieces">The pieces</h2>
<div class="cards">
<a class="card" href="generate.html"><strong>Generate</strong><span>The command, <code>generate</code>, and the prompt that lists prefixes, classes, and properties.</span></a>
<a class="card" href="vocabulary.html"><strong>Vocabulary</strong><span>Classes, properties, and prefixes read from a Turtle file, capped for the prompt.</span></a>
<a class="card" href="stages.html"><strong>Stages</strong><span>Guardrails, query guided, context guided, and chase and backchase. Hooks only, for now.</span></a>
<a class="card" href="validate.html"><strong>Validation</strong><span>Extract the query, lift modifiers out of <code>WHERE</code>, parse, and repair once.</span></a>
<a class="card" href="models.html"><strong>Models</strong><span>A local Ollama model by default, or an OpenAI-compatible API.</span></a>
</div>
<h2 id="one-call">One call</h2>
<ol>
<li><code>load_vocabulary</code> reads the Turtle file.</li>
<li><code>build_prompt</code> lists prefixes, classes, properties, context, and examples.</li>
<li><code>complete</code> asks the model for one query.</li>
<li><code>prepare_draft</code> extracts the query and lifts solution modifiers.</li>
<li><code>apply_stages</code> walks guardrails, query guided, context guided, then chase and backchase.</li>
<li><code>parse_error</code> checks the query. On failure, one repair call runs, then the same stages and the same check.</li>
</ol>
<p>The return value is a dict with <code>sparql</code>, <code>model</code>, and <code>provider</code>.</p>
<h2 id="install">Install</h2>
<pre><code>git clone https://github.com/lamng3/nl2sparql.git
cd nl2sparql
pip install -e .</code></pre>
<p>Python 3.11 or newer. Dependencies are <code>rdflib</code> and <code>httpx</code>. Tests use the <code>dev</code> extra: <code>pip install -e ".[dev]"</code>, then <code>pytest</code>.</p>
""",
    )
    page(
        "generate.html",
        "Generate",
        "The nl2sparql generate command, the Python function, and the prompt it builds.",
        "nl2sparql.generate",
        "generate writes one SPARQL query for a question and an ontology. The command prints that result as JSON.",
        """
<nav class="toc"><strong>On this page</strong><ol><li><a href="#command">Command</a></li><li><a href="#python">From Python</a></li><li><a href="#prompt">Prompt</a></li><li><a href="#errors">Errors</a></li></ol></nav>
<h2 id="command">Command</h2>
<pre><code>nl2sparql generate \\
  --ontology GeoOutage.ttl \\
  --question "Which counties have the highest number of outages?" \\
  --context notes.txt \\
  --examples pairs.jsonl</code></pre>
<table>
<tr><th>Flag</th><th>Required</th><th>Meaning</th></tr>
<tr><td><code>--ontology</code></td><td>yes</td><td>Turtle file.</td></tr>
<tr><td><code>--question</code></td><td>yes</td><td>The competency question.</td></tr>
<tr><td><code>--context</code></td><td>no</td><td>A text file. The whole file is extra context.</td></tr>
<tr><td><code>--examples</code></td><td>no</td><td>JSONL. Each line is one object with <code>nl</code> and <code>sparql</code>. <code>nl_text</code> and <code>sparql_query</code> are accepted aliases.</td></tr>
</table>
<p>Blank lines in the JSONL file are skipped. Source: <a href="https://github.com/lamng3/nl2sparql/blob/master/src/nl2sparql/cli.py">cli.py</a>.</p>
<h2 id="python">From Python</h2>
<pre><code>from nl2sparql import Context, Example, generate

result = generate(
    "Which counties have the highest number of outages?",
    "GeoOutage.ttl",
    context=Context(
        text="Counties are administrative regions.",
        examples=[
            Example(
                nl="List outage records.",
                sparql="SELECT ?rec WHERE { ?rec a geooutageonto:OutageRecord }",
            )
        ],
    ),
)
print(result["sparql"])</code></pre>
<p><code>context</code> is optional. Pass <code>None</code> or a <code>Context</code>. Anything else raises <code>TypeError</code>. A blank question raises <code>ValueError</code>.</p>
<p><code>Context.text</code> defaults to an empty string. <code>Context.examples</code> defaults to an empty list. <code>Example</code> has two strings, <code>nl</code> and <code>sparql</code>.</p>
<h2 id="prompt">Prompt</h2>
<p><code>build_prompt</code> joins these sections with a blank line:</p>
<ol>
<li>Instructions: one query, only the prefixes and terms below, match labels in quotes, triples inside <code>WHERE</code>, <code>ORDER BY</code> and <code>LIMIT</code> after that block, no <code>SELECT</code> inside <code>FILTER</code>, do not copy the shape example terms, return only the query.</li>
<li>A shape example that shows the clause order, using <code>ex:</code> terms that are not from the ontology.</li>
<li>Declared prefixes as <code>PREFIX name: &lt;namespace&gt;</code>.</li>
<li>Classes, one per line.</li>
<li>Properties, one per line.</li>
<li>Context text, when it is non-empty.</li>
<li>Example question and query pairs, when any example has text.</li>
<li>The question, always last.</li>
</ol>
<p>Empty class or property lists render as <code>(none found)</code>. No prefixes renders as <code>(none)</code>.</p>
<h2 id="errors">Errors</h2>
<p>If the model text has no query, <code>prepare_draft</code> raises <code>ValueError</code>. If the query still fails to parse after one repair call, <code>generate</code> raises <code>ValueError</code> with the parser message. Model failures are <code>LookupError</code>, described on the <a href="models.html">Models</a> page.</p>
""",
    )
    page(
        "vocabulary.html",
        "Vocabulary",
        "How nl2sparql turns a Turtle ontology into prefixes, classes, and properties for the prompt.",
        "nl2sparql.ontology",
        "load_vocabulary reads a Turtle file and returns a small dict the prompt can list. It does not send the whole ontology.",
        """
<nav class="toc"><strong>On this page</strong><ol><li><a href="#result">Result</a></li><li><a href="#terms">Classes and properties</a></li><li><a href="#prefixes">Prefixes</a></li></ol></nav>
<h2 id="result">Result</h2>
<pre><code>{
  "path": "city.ttl",
  "classes": ['ex:City "City"'],
  "properties": ['ex:inCountry "in country"'],
  "prefixes": [("ex", "http://example.org/demo#")],
}</code></pre>
<p>The parser is RDFLib with <code>format="turtle"</code>. Other serializations are not accepted. Source: <a href="https://github.com/lamng3/nl2sparql/blob/master/src/nl2sparql/ontology.py">ontology.py</a>.</p>
<h2 id="terms">Classes and properties</h2>
<p>Classes are IRIs typed <code>owl:Class</code> or <code>rdfs:Class</code>. Properties are IRIs typed <code>owl:ObjectProperty</code>, <code>owl:DatatypeProperty</code>, or <code>rdf:Property</code>. Blank nodes are dropped. Each term is kept once.</p>
<p>An <code>rdfs:label</code> is appended in quotes when one exists. The list stops at 60 classes and 60 properties. Later terms are omitted, so a large ontology is only partly visible to the model until this cap moves.</p>
<p>A term is written as <code>prefix:local</code> when its namespace has a prefix, otherwise as a full IRI in angle brackets.</p>
<h2 id="prefixes">Prefixes</h2>
<p>Declared prefixes come from <code>prefix name: &lt;namespace&gt;</code> and <code>@prefix</code> lines in the file text, not from the graph. RDF, RDFS, OWL, XSD, and XML namespaces are skipped. At most 12 prefixes are kept.</p>
<p>A namespace that appears on a kept term and has no declaration gets a prefix from its last path segment, lowercased, cut to 16 characters, and made to start with a letter. Collisions gain a numeric suffix (<code>outage2</code>). Derivation also stops at 12 prefixes total.</p>
""",
    )
    page(
        "stages.html",
        "Stages",
        "The four research stages between the draft SPARQL query and parse checking.",
        "nl2sparql.stages",
        "apply_stages walks a fixed tuple. Each function takes the draft and returns a query. Replacing a function is how a later technique enters the pipeline.",
        """
<nav class="toc"><strong>On this page</strong><ol><li><a href="#contract">Contract</a></li><li><a href="#guardrails">Guardrails</a></li><li><a href="#query-guided">Query guided</a></li><li><a href="#context-guided">Context guided</a></li><li><a href="#chase">Chase and backchase</a></li></ol></nav>
<div class="callout next"><span class="label">Later</span><p>All four functions return the draft unchanged. The order and the call signature are the stable part. The bodies are the work still to do.</p></div>
<h2 id="contract">Contract</h2>
<pre><code>def stage(sparql, *, ontology, context):
    return sparql

STAGES = (guardrails, query_guided, context_guided, chase_backchase)</code></pre>
<p><code>sparql</code> is the draft string after <a href="validate.html">extraction and modifier lifting</a>. <code>ontology</code> is the vocabulary dict from <code>load_vocabulary</code>, not the file path. <code>context</code> is the <code>Context</code> passed to <code>generate</code>.</p>
<p><code>generate</code> calls <code>apply_stages</code> on the first draft, and again on the repair draft if the first query does not parse. A replacement should return a string. It should not assume it is the last step: validation still runs after the tuple.</p>
<p>Source: <a href="https://github.com/lamng3/nl2sparql/blob/master/src/nl2sparql/stages.py">stages.py</a>.</p>
<h2 id="guardrails">Guardrails <span class="tag">later</span></h2>
<p>Reject or rewrite a query that leaves the ontology vocabulary. The intended check is the prefixes, classes, and properties already loaded for the prompt. The function does not inspect them yet.</p>
<h2 id="query-guided">Query guided <span class="tag">later</span></h2>
<p>Steer a draft using a target query shape or a previous SPARQL query. The prompt already shows one fixed shape. This stage is where a caller-supplied shape, or an earlier query, would revise the draft after generation.</p>
<h2 id="context-guided">Context guided <span class="tag">later</span></h2>
<p>Retrieve and place example questions, beyond stuffing them into the prompt. Examples today are only the JSONL rows the caller passed, copied verbatim into the prompt. This stage is where retrieval over a larger pool would choose and place them.</p>
<h2 id="chase">Chase and backchase <span class="tag">later</span></h2>
<p>Reformulate the query with ontology constraints, then minimize it. The function documents that intent and does not implement the algorithm. Constraints would come from the same Turtle file the vocabulary was loaded from. Minimization would drop triples the constraints make redundant.</p>
""",
    )
    page(
        "validate.html",
        "Validation",
        "How a model reply becomes one SPARQL string, and how a parse error is repaired once.",
        "nl2sparql.validate",
        "prepare_draft extracts a query and moves solution modifiers out of WHERE. parse_error checks it with RDFLib. One repair call is allowed.",
        """
<nav class="toc"><strong>On this page</strong><ol><li><a href="#extract">Extract</a></li><li><a href="#lift">Lift modifiers</a></li><li><a href="#parse">Parse and repair</a></li></ol></nav>
<h2 id="extract">Extract</h2>
<p><code>extract_sparql</code> prefers the first fenced block, including a <code>sparql</code> fence. Without a fence, it uses the whole reply. It then keeps the first span that starts at <code>SELECT</code>, <code>ASK</code>, <code>CONSTRUCT</code>, or <code>DESCRIBE</code>, including any <code>PREFIX</code> lines immediately before it. If that span is missing, the whole text is returned. An empty result raises <code>ValueError</code> from <code>prepare_draft</code>.</p>
<h2 id="lift">Lift modifiers</h2>
<p>Models often write <code>ORDER BY</code>, <code>LIMIT</code>, <code>GROUP BY</code>, <code>HAVING</code>, or <code>OFFSET</code> inside the outer <code>WHERE</code> block. <code>lift_modifiers</code> moves those lines to after the block when they sit at brace depth zero inside it.</p>
<pre><code>SELECT ?city WHERE {
  ?s a ex:City .
  ORDER BY ?city
  LIMIT 5
}</code></pre>
<p>becomes a query with the triple inside <code>WHERE</code> and <code>ORDER BY ?city</code> then <code>LIMIT 5</code> after the closing brace. The same modifiers inside a nested <code>SELECT</code> stay where they are, because that depth is not zero. A query with no <code>WHERE</code>, or with unbalanced braces, is returned unchanged.</p>
<h2 id="parse">Parse and repair</h2>
<p><code>parse_error</code> calls <code>rdflib.plugins.sparql.prepareQuery</code>. It returns <code>None</code> when the query parses, and the exception text otherwise.</p>
<p>On an error, <code>generate</code> sends <code>repair_prompt</code>: the parser message, the bad query, and instructions to return only the corrected query, keep <code>SELECT</code> out of <code>FILTER</code>, put <code>GROUP BY</code>, <code>ORDER BY</code>, and <code>LIMIT</code> after <code>WHERE</code>, and write aggregates as <code>(MAX(?value) AS ?maxValue)</code>. The repair reply goes through <code>prepare_draft</code> and <code>apply_stages</code> again. A second parse error raises <code>ValueError</code>. There is no third call.</p>
<p>Source: <a href="https://github.com/lamng3/nl2sparql/blob/master/src/nl2sparql/validate.py">validate.py</a>.</p>
""",
    )
    page(
        "models.html",
        "Models",
        "The Ollama client and the OpenAI-compatible client used by nl2sparql.",
        "nl2sparql.llm",
        "complete returns the reply text, the model name, and the provider. The default provider is a local Ollama server.",
        """
<nav class="toc"><strong>On this page</strong><ol><li><a href="#choice">Which provider</a></li><li><a href="#ollama">Ollama</a></li><li><a href="#openai">OpenAI-compatible</a></li></ol></nav>
<h2 id="choice">Which provider</h2>
<p><code>ONTOCHECK_LLM_PROVIDER=openai</code> selects the HTTP client below. Any other value, including an empty one, selects Ollama. Temperature is 0 for both. The system message asks for one SPARQL query and nothing else.</p>
<p>Source: <a href="https://github.com/lamng3/nl2sparql/blob/master/src/nl2sparql/llm.py">llm.py</a>.</p>
<h2 id="ollama">Ollama</h2>
<table>
<tr><th>Variable</th><th>Default</th></tr>
<tr><td><code>ONTOCHECK_OLLAMA_BASE_URL</code></td><td><code>http://127.0.0.1:11434</code></td></tr>
<tr><td><code>ONTOCHECK_OLLAMA_MODEL</code></td><td>chosen from installed models</td></tr>
</table>
<p>With no model set, the client reads <code>/api/tags</code> and picks the first installed name that matches this order: <code>llama3.1</code>, <code>llama3</code>, <code>mistral</code>, <code>phi3</code>, <code>qwen2.5</code>, <code>qwen</code>. A name matches exactly or with a tag, as in <code>llama3.1:latest</code>. If none match, the first installed model is used. If none are installed, the error tells you to run <code>ollama pull llama3.1</code>.</p>
<p>The chat call uses <code>/api/chat</code>, <code>stream</code> false, and <code>keep_alive</code> of 10 minutes. The timeout is 180 seconds. A connection failure says to start <code>ollama serve</code>. A timeout suggests a smaller <code>ONTOCHECK_OLLAMA_MODEL</code>. A 404 says to <code>ollama pull</code> that model.</p>
<h2 id="openai">OpenAI-compatible</h2>
<table>
<tr><th>Variable</th><th>Default</th></tr>
<tr><td><code>ONTOCHECK_LLM_API_KEY</code></td><td>required</td></tr>
<tr><td><code>ONTOCHECK_LLM_BASE_URL</code></td><td><code>https://api.together.xyz/v1</code></td></tr>
<tr><td><code>ONTOCHECK_LLM_MODEL</code></td><td><code>meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo</code></td></tr>
</table>
<p>The client posts to <code>/chat/completions</code> with a bearer token. The timeout is 40 seconds. A missing API key raises <code>LookupError</code> and points back at Ollama.</p>
""",
    )


if __name__ == "__main__":
    main()
