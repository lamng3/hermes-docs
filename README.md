# Hermes docs

Docs for [Hermes](https://github.com/lamng3/hermes), the official implementation of *Hermes: Verified Query Planning over the SPARQL Algebra with Language Agents*: the SPARQL algebra as actions, the verifier, the systems, graph stores, benchmarks, evaluation, experiments, and the model clients.

`python3 build.py` rewrites the HTML. GitHub Pages serves the files at the repository root.

## Shared structure

`normalize.py` (shared by the manuals) runs at the end of the build. It gives every content page a search box, an "On this page" list, previous and next links, and one title format, and writes `search-index.json`. It is called by `build.py`.
