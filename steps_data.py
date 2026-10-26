#!/usr/bin/env python3
"""Export what the step-by-step page needs from the real code.

    ../hermes/.venv/bin/python steps_data.py

For each sample question, the budgeted planner runs here, natively, with the
model replies replayed from Hermes's LLM cache (Llama 3.1 8B, the replies of
the committed CK26 run), and records the replies and what the session
concluded. The page replays the same replies through the same Python under
Pyodide and checks that it reaches the same query. The Hermes and rdflib
wheels the page installs are written to py/.
"""

import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
HERMES = ROOT.parent / "hermes"
sys.path.insert(0, str(HERMES / "src"))

from hermes import KnowledgeGraph  # noqa: E402
from hermes import llm as llms  # noqa: E402
from hermes.systems.budgeted import SYSTEM, Budgeted  # noqa: E402

GRAPHS = {
    "corporate": {"label": "Corporate KG (Text2SPARQL)", "ontology": ["data/prod-vocab.ttl"],
                  "data": ["data/prod-inst.ttl"]},
    "olympics": {"label": "Olympic host cities (toy)", "ontology": [], "data": ["data/olympics.ttl"]},
}
SAMPLES = [
    ("corporate", "ck26:1-en", "Which department does Ms. Brant belong to?"),
    ("corporate", "ck26:7-en", "Who heads the Data Services department?"),
    ("corporate", "ck26:22-en", "Which products can be used with the U990 LCD Inductor?"),
    ("corporate", "ck26:5-de", "Wer kennt sich mit Transistoren aus?"),
    ("corporate", "ck26:3-en", "Who is Heinrich Hoch's manager?"),
    ("corporate", "ck26:16-en", "Are there any suppliers we have in Toulouse?"),
]
WINTER = {
    "goal": {"answer": ["?c"], "kind": "entity", "type": "[city]", "many": True},
    "actions": [{"op": "triple", "pattern": "?c [hosted] ?g"},
                {"op": "triple", "pattern": "?g [season] [Winter]"},
                {"op": "project", "vars": ["?c"]}, {"op": "distinct"}],
}


def graph(name):
    """As data/graphs.yaml loads a benchmark graph: ontology and data queried together,
    the vocabulary read from the ontology alone. The page loads its stores the same way."""
    spec = GRAPHS[name]
    ontology = [ROOT / p for p in spec["ontology"]]
    data = [ROOT / p for p in spec["data"]]
    return KnowledgeGraph.from_files(*ontology, *data, schema=ontology or (), name=name)


def record(planner, kg, question, reply_for):
    session = planner.start(question, kg, explain=True)
    replies = []
    while (text := session.next_prompt()) is not None:
        replies.append(reply_for(text))
        session.take(replies[-1])
    result = session.result()
    return replies, {"sparql": result["sparql"], "confidence": result["confidence"],
                     "abstain": result["abstain"],
                     "phases": [event["phase"] for event in session.events]}


def main():
    llm = llms.create(provider="ollama", model="llama3.1", cache=str(HERMES / ".cache/llm"))
    planner = Budgeted(llm_calls=3, executions=8)
    graphs, samples = {}, []
    for name in GRAPHS:
        graphs[name] = graph(name)
    for name, item, question in SAMPLES:
        replies, expected = record(planner, graphs[name], question,
                                   lambda text: llm.complete(text, SYSTEM))
        samples.append({"graph": name, "item": item, "question": question, "replies": replies,
                        "expected": expected})
        print(item, len(replies), "replies,", "abstains" if expected["abstain"] else "answers")
    replies, expected = record(planner, graphs["olympics"], "Which cities hosted the Winter Olympics?",
                               lambda text: json.dumps(WINTER))
    samples.append({"graph": "olympics", "item": "toy", "question":
                    "Which cities hosted the Winter Olympics?", "replies": replies,
                    "expected": expected})
    calls, hits = llm.calls, llm.hits
    if calls != hits:
        print(f"warning: {calls - hits} of {calls} replies were new, not from the cached run")

    wheels = ROOT / "py"
    wheels.mkdir(exist_ok=True)
    for old in wheels.glob("hermes_sparql-*.whl"):
        old.unlink()
    subprocess.run(["uv", "build", "--wheel", "-o", str(wheels), str(HERMES)], check=True,
                   capture_output=True)
    (wheels / ".gitignore").unlink(missing_ok=True)  # uv writes one that ignores the wheels
    wheel = sorted(wheels.glob("hermes_sparql-*.whl"))[-1].name
    commit = subprocess.run(["git", "-C", str(HERMES), "rev-parse", "--short", "HEAD"],
                            capture_output=True, text=True).stdout.strip()
    data = {
        "graphs": GRAPHS,
        "samples": samples,
        "system": SYSTEM,
        "budget": {"llm_calls": planner.llm_calls, "executions": planner.executions,
                   "accept": planner.accept, "abstain": planner.abstain},
        "wheels": [f"py/{wheel}", "py/" + sorted(wheels.glob("rdflib-*.whl"))[-1].name],
        "model": "llama3.1 (8B) on Ollama",
        "commit": commit,
    }
    (ROOT / "steps-data.json").write_text(json.dumps(data, ensure_ascii=False))
    print(f"{len(samples)} samples, Hermes {commit}, wheel {wheel}")


if __name__ == "__main__":
    main()
