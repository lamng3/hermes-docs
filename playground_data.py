#!/usr/bin/env python3
"""Export what the Hermes playground needs from the real code.

    ../hermes/.venv/bin/python playground_data.py

The corporate graph's vocabulary, built by hermes.ontology.vocabulary, the prompt hermes.systems.training_free builds for
each sample question, and fixtures that pin the page's JavaScript ports of prompt building and query extraction to the
Python they copy (the page's tests compare them).
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
HERMES = ROOT.parent / "hermes"
sys.path.insert(0, str(HERMES / "src"))

from hermes.ontology import declared_prefixes, load_vocabulary  # noqa: E402
from hermes.systems.training_free import build_prompt  # noqa: E402
from hermes.validate import prepare_draft, repair_prompt  # noqa: E402

VOCAB = HERMES / "data/graphs/corporate/prod-vocab.ttl"
RAW_OUTPUTS = [
    "```sparql\nPREFIX pv: <http://ld.company.org/prod-vocab/>\nSELECT ?x WHERE {\n  ?x a pv:Product .\n  LIMIT 5\n}\n```",
    "Here is the query:\nSELECT ?a WHERE { ?a ?b ?c } ORDER BY ?a",
    "```\nSELECT ?a WHERE {\n  ?a ?b ?c .\n  ORDER BY ?a\n  LIMIT 3\n}\n```\nHope that helps.",
]


def query_prefixes():
    """The PREFIX lines every recorded query was written with (the same set for each item of a run)."""
    run = sorted(p for p in (HERMES / "results/ck26/prover@qwen3-14b").iterdir() if (p / "predictions.jsonl").exists())[-1]
    first = json.loads((run / "predictions.jsonl").read_text().splitlines()[0])
    return [line.split(None, 2)[1:] and [line.split()[1].rstrip(":"), line.split("<", 1)[1].rstrip(">")] for line in first["sparql"].splitlines() if line.startswith("PREFIX")]


def main():
    vocab = load_vocabulary(VOCAB, limit=60)
    demo = json.loads((ROOT / "demo-data.json").read_text())
    questions = [q["question"] for q in demo["questions"]]
    prompts = {q: build_prompt(q, vocab) for q in questions}
    data = {
        "vocabulary": vocab,
        "queryPrefixes": query_prefixes(),
        "questions": questions,
        "prompts": prompts,
        "fixtures": {
            "extract": [{"input": raw, "output": prepare_draft(raw)} for raw in RAW_OUTPUTS],
            "repair": {"sparql": "SELECT ?a WHERE { ?a ?b }", "error": "Expected {", "output": repair_prompt("SELECT ?a WHERE { ?a ?b }", "Expected {")},
        },
    }
    (ROOT / "playground-data.json").write_text(json.dumps(data))
    print(f"{len(vocab['classes'])} classes, {len(vocab['properties'])} properties, {len(prompts)} prompts")


if __name__ == "__main__":
    main()
