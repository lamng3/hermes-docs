#!/usr/bin/env python3
"""Export Hermes's recorded benchmark runs for the manual's live demo.

    python3 demo_data.py [../hermes/results/ck26]

Reads each run's metrics.json and predictions.jsonl. Keeps the leaderboard (set F-nDCG per run), and, for a fixed-seed
sample of English questions, what each Qwen3-14B system wrote and how it scored. The page shows these and computes nothing.
"""

import json
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
RESULTS = Path(sys.argv[1] if len(sys.argv) > 1 else ROOT.parent / "hermes/results/ck26")
SYSTEMS = ["algebra-agent", "prover", "uniqgen", "training-free"]
MODEL = "qwen3-14b"


def latest(run):
    """The newest finished run in a result folder (one with metrics), or None."""
    done = sorted(p for p in (RESULTS / run).iterdir() if (p / "metrics.json").exists() and (p / "run.json").exists())
    return done[-1] if done else None


def predictions(run):
    return {json.loads(line)["id"]: json.loads(line) for line in (latest(run) / "predictions.jsonl").read_text().splitlines()}


def body(sparql):
    """The query without its PREFIX lines, which are the same on every item."""
    return "\n".join(line for line in sparql.splitlines() if not line.startswith("PREFIX")).strip()


def main():
    board = []
    for run in sorted(p.name for p in RESULTS.iterdir() if p.is_dir()):
        path = latest(run)
        if path is None:
            continue
        metrics = json.loads((path / "metrics.json").read_text())["official"]["average"]
        meta = json.loads((path / "run.json").read_text())
        board.append({"run": run, "system": meta["system"], "model": meta["model"], "f": round(metrics["set_F_ndcg"], 3)})
    # The benchmark's official systems, from the generated leaderboard: several score above every Hermes run.
    section = (RESULTS.parent / "LEADERBOARD.md").read_text().split(f"## {RESULTS.name}")[1].split("\n## ")[0]
    for line in section.splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) > 3 and cells[0].endswith("(official)"):
            board.append({"run": cells[0].replace(" (official)", ""), "system": "official", "model": "", "f": float(cells[3])})
    board.sort(key=lambda r: -r["f"])
    runs = {s: predictions(f"{s}@{MODEL}") for s in SYSTEMS}
    ids = [i for i in runs["algebra-agent"] if i.endswith("-en") and all(i in runs[s] for s in SYSTEMS)]
    rng = random.Random(3)
    wins = [i for i in ids if any(runs[s][i]["scores"]["set_F"] == 1 for s in SYSTEMS)]
    losses = [i for i in ids if not any(runs[s][i]["scores"]["set_F"] > 0 for s in SYSTEMS)]
    picks = rng.sample(wins, min(6, len(wins))) + rng.sample(losses, min(2, len(losses)))
    questions = []
    for i in picks:
        questions.append(
            {
                "id": i,
                "question": runs["algebra-agent"][i]["question"],
                "systems": {
                    s: {
                        "sparql": body(runs[s][i]["sparql"]) or "(no query)",
                        "error": runs[s][i].get("error", ""),
                        "f": round(runs[s][i]["scores"]["set_F"], 2),
                        "precision": round(runs[s][i]["scores"]["set_P"], 2),
                        "recall": round(runs[s][i]["scores"]["set_recall"], 2),
                        "llm_calls": runs[s][i]["cost"]["llm_calls"],
                        "seconds": round(runs[s][i]["seconds"], 1),
                    }
                    for s in SYSTEMS
                },
            }
        )
    out = {"source": f"hermes/results/{RESULTS.name}", "model": MODEL, "systems": SYSTEMS, "board": board, "questions": questions}
    (ROOT / "demo-data.json").write_text(json.dumps(out))
    print(f"{len(board)} runs, {len(questions)} questions")


if __name__ == "__main__":
    main()
