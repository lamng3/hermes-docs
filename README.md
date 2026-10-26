# Hermes docs

Docs for [Hermes](https://github.com/lamng3/hermes): the SPARQL algebra as actions, the verifier, the systems, graph stores, benchmarks, evaluation, experiments, and the model clients.

`python3 build.py` rewrites the HTML. GitHub Pages serves the files at the repository root.

## Shared structure

`normalize.py` (shared by the manuals) runs at the end of the build. It gives every content page a search box, an "On this page" list, previous and next links, and one title format, and writes `search-index.json`. It is called by `build.py`.

## Step through

`steps.html` runs Hermes's budgeted planner in the browser: the Hermes and rdflib wheels in `py/` are installed under Pyodide, and queries run on Oxigraph (WebAssembly). `../hermes/.venv/bin/python steps_data.py` rebuilds the Hermes wheel from the sibling checkout, replays the sample questions natively with the recorded model replies, and writes `steps-data.json`. `steps-test.mjs` replays the same samples under Pyodide in Node and checks that each reaches the native run's query, confidence, and phases.
