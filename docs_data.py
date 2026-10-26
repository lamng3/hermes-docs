#!/usr/bin/env python3
"""Export what the demos need from the sibling Hermes checkout.

    ../hermes/.venv/bin/python docs_data.py

Builds the Hermes wheel the pages install under Pyodide, copies the synthetic
few-shot examples of the corporate graph, runs every sample question through
the pipeline natively with the model replies replayed from Hermes's LLM cache
(Llama 3.1 8B), and records the replies and the query each run reached; the
page replays the same replies and shows whether it reaches the same query.
Writes docs-data.json.
"""

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
HERMES = ROOT.parent / "hermes"
sys.path.insert(0, str(HERMES / "src"))
os.environ.setdefault("HERMES_DATA", str(HERMES / "data"))  # the benchmarks, for the gold queries

from hermes import Budget, Hermes, KnowledgeGraph  # noqa: E402
from hermes import llm as llms  # noqa: E402
from hermes.pipeline.fewshot import FewShotStore  # noqa: E402

GRAPHS = {
    "corporate": {"label": "Corporate knowledge graph (Text2SPARQL)",
                  "ontology": ["data/prod-vocab.ttl"], "data": ["data/prod-inst.ttl"],
                  "examples": "data/fewshot-corporate.jsonl"},
    "olympics": {"label": "Olympic host cities (toy)", "ontology": [], "data": ["data/olympics.ttl"]},
}
QUESTIONS = [
    ("corporate", "Which department does Ms. Brant belong to?"),
    ("corporate", "Who is Heinrich Hoch's manager?"),
    ("corporate", "Which products can be used with the U990 LCD Inductor?"),
    ("corporate", "Who are our suppliers in Toulouse?"),
    ("corporate", "Which employees are members of the Marketing department?"),
    ("olympics", "Which cities hosted the Winter Olympics?"),
]
QUERIES = [
    ("corporate", "Marketing staff with an S in their name",
     """PREFIX pv: <http://ld.company.org/prod-vocab/>
SELECT ?name ?email WHERE {
  ?p pv:email ?email .
  ?p pv:name ?name .
  ?p pv:memberOf ?d .
  ?d pv:name "Marketing" .
  FILTER(CONTAINS(?name, "S"))
}"""),
    ("corporate", "Is there a service for a BOM with parts from Russia? (CK26 question 28)", None),
    ("corporate", "The network expert in the marketing department (CK26 question 10)", None),
    ("corporate", "Suppliers of the most expensive hardware, priced in euros (CK26 question 29)", None),
    ("olympics", "Winter host cities in Norway after 1950",
     """PREFIX ex: <http://example.org/olympics#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
SELECT ?city ?year WHERE {
  ?g ex:year ?year .
  ?city ex:hosted ?g .
  ?city ex:country ?k .
  ?k rdfs:label "Norway" .
  ?g ex:season "Winter" .
  FILTER(?year > 1950)
} ORDER BY ?year"""),
]
GOLD = {"28": "ck26:28-en", "10": "ck26:10-en", "29": "ck26:29-en"}


def graph(name):
    spec = GRAPHS[name]
    ontology = [ROOT / p for p in spec["ontology"]]
    return KnowledgeGraph.from_files(*ontology, *(ROOT / p for p in spec["data"]),
                                     schema=ontology, name=name)


def gold_queries():
    from hermes import benchmarks

    items = {i.id: i for i in benchmarks.load("ck26").select()}
    found = []
    for name, title, sparql in QUERIES:
        if sparql is None:
            number = title.rsplit("question ", 1)[1].rstrip(")")
            sparql = items[GOLD[number]].sparql.strip()
        found.append({"graph": name, "title": title, "sparql": sparql})
    return found


def main():
    shutil.copy(HERMES / "data/fewshot/corporate.jsonl", ROOT / GRAPHS["corporate"]["examples"])
    llm = llms.create(provider="ollama", model="llama3.1", cache=str(HERMES / ".cache/llm"))
    kgs = {name: graph(name) for name in GRAPHS}
    samples = []
    for name, question in QUESTIONS:
        examples = FewShotStore.load(ROOT / GRAPHS[name]["examples"]) if "examples" in GRAPHS[name] \
            else FewShotStore()
        replies = []

        class Recording(llms.LLM):
            provider, model = llm.provider, llm.model

            def complete(self, prompt, system=llms.SYSTEM):
                replies.append(llm.complete(prompt, system))
                return replies[-1]

        answer = Hermes(kgs[name], llm=Recording(), budget=Budget(llm_calls=3),
                        fewshots=examples).ask(question)
        samples.append({"graph": name, "question": question, "replies": replies,
                        "expected": {"sparql": answer.sparql, "rows": len(answer.rows),
                                     "error": answer.error}})
        print(f"{question}: {len(replies)} replies, {len(answer.rows)} rows {answer.error}")
    if llm.calls != llm.hits:
        print(f"note: {llm.calls - llm.hits} of {llm.calls} replies were new (not cached)")

    wheels = ROOT / "py"
    for old in wheels.glob("hermes_sparql-*.whl"):
        old.unlink()
    subprocess.run(["uv", "build", "--wheel", "-o", str(wheels), str(HERMES)], check=True,
                   capture_output=True)
    (wheels / ".gitignore").unlink(missing_ok=True)  # uv writes one that ignores the wheels
    commit = subprocess.run(["git", "-C", str(HERMES), "rev-parse", "--short", "HEAD"],
                            capture_output=True, text=True).stdout.strip()
    data = {
        "graphs": GRAPHS,
        "samples": samples,
        "queries": gold_queries(),
        "wheels": ["py/" + sorted(wheels.glob("hermes_sparql-*.whl"))[-1].name,
                   "py/" + sorted(wheels.glob("rdflib-*.whl"))[-1].name],
        "commit": commit,
    }
    (ROOT / "docs-data.json").write_text(json.dumps(data, ensure_ascii=False))
    print(f"{len(samples)} samples, {len(data['queries'])} queries, Hermes {commit}")


if __name__ == "__main__":
    main()
