# Golden Datasets

Curated, versioned datasets for eval. Keep these small but representative.

- `search_golden.jsonl` - 30 queries: skills+location+exp combos
- `ranking_golden.jsonl` - 15 JDs with human ideal ranking
- `parser_golden.jsonl` - 20 resume excerpts with expected JSON
- `chat_golden.jsonl` - 20 chat turns with expected tools

Run `python -m app.eval.datasets.build_golden --sample 50` to bootstrap from your Qdrant.
Then hand-correct.

Format is JSONL, one JSON per line.
