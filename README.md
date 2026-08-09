# Tech-News ARR Pipeline
 
A local Python pipeline that turns messy technology-news articles into a
queryable warehouse model of **company ARR observations over time**, plus a
filtered AI export and a semantic search index.
 
---

## Quickstart
 
```bash
python -m venv .venv && source .venv/bin/activate
pip install -e .
pip install -r requirements.txt
 
make run     # builds every table and writes outputs/*.csv
make test    # 25 tests, ~5s
```

Input files are expected at `data/input/tech_news.csv` and
`data/input/company_metadata.json`; paths are configurable in
`config/settings.yaml`.

## What it produces
 
| File | Rows | Grain |
|---|---|---|
| `dim_company.csv` | 21 | one resolved company |
| `dim_article.csv` | 750 | one source article |
| `fact_arr_observation.csv` | 538 | one valid (article, ARR) pair |
| `quarantine_record.csv` | 217 | one rejected value |
| `ai_articles_enriched.csv` | 118 | AI articles, 2022–24, ARR > $50M |
| `article_embedding.csv` | 750 | article × model |
| `article_similarity.csv` | 2,250 | article × neighbour rank |

**Bronze** lands the source verbatim — every column a string, nothing coerced,
nothing rejected. It is append-only and immutable, so gold can be rebuilt from
it if the cleaning logic later turns out to be wrong.
 
**Silver** has exactly the same row count as bronze. Values are typed and
parsed, but **rows that fail parsing survive here**, carrying a status flag.
This is the layer where "what did we fail on, and why" is answerable in SQL.
 
**Gold** is the dimensional model, built purely by selection from silver.


## The AI export filter
 
`(article category is AI/ML **OR** company industry is AI/ML)` AND published
2022–2024 AND `arr_usd > $50M`.
 
**The `OR` is load-bearing.** Of the 118 exported rows, 62 qualify on article
category alone, 41 on company industry alone, and only 15 on both. Implementing
either condition without the other loses roughly a third of the result.
 
The metadata industry values are counter-intuitive — Anthropic is tagged
`FinTech`, Tesla `Cloud Computing`, and only NVIDIA, SpaceX and Scale AI carry
`AI/ML`. The pipeline does **not** "correct" these toward what the company
names suggest; the metadata file is the stated source of truth for industry.
 
---


## The warehouse
 
`make run` loads all five gold tables into `data/warehouse/arr.duckdb`.
 
The schema declares primary keys, foreign-key-shaped constraints, and
`CHECK (arr_usd > 0)` on the fact table. Those `NOT NULL`s are only enforceable
*because* gold already routed every failure to `quarantine_record` — a
constraint violation here would mean a bug in the selection logic, not bad
source data.
 
Two reporting views are created:
 
- **`vw_company_arr_latest`** — the most recent observation per company.
  Tie-break: latest `observed_date`, then the **median** across observations
  sharing that date. It exposes `observation_count_on_date`, so a contested
  figure is reported rather than hidden. `DENSE_RANK` is used rather than
  `ROW_NUMBER` precisely so tied rows both survive the filter.
- **`vw_company_arr_quarterly`** — one row per company-quarter with an
  `observation_count`, so a single-article quarter is distinguishable from a
  well-evidenced one.
Both are views, never materialised columns. "Latest ARR" is an interpretation,
not a fact; different consumers may want different tie-break rules, and the
underlying observations must stay intact for all of them.
 
```bash
make query   
```
 
---
 
## How to verify it works
 
```bash
make test
```
 
Two suites carry the weight:
 
- **`test_pipeline_counts.py`** pins every count in this README. A parser change
  that silently shifts what qualifies fails here first.
- **`test_idempotency.py`** runs the pipeline twice and asserts identical keys
  and content. This is the architecture's central claim as a pass/fail.
- **`test_warehouse.py`** proves the DuckDB write is a merge and not an append,
  and that a restated source value updates in place rather than inserting.
The rest are unit tests over the cleaning functions, which take plain strings
and return plain values — no DataFrame fixtures.
 
---
 
## Known limitations
 
- `dim_company` is SCD Type 1. `employee_count` and `company_size_category`
  reflect the metadata snapshot, not the company's state at article time. The
  metadata has no effective date, so Type 2 is not implementable from this input.
- FX rates are fixed rather than date-aware (see above).
- One ARR observation per article maximum. An article quoting two figures for
  the same company would need a grain change to `(article_id, sequence)`.
- A restated source value overwrites in place rather than versioning.
  `source_value_hash` detects the change; making restatement history queryable
  would need `valid_from`/`valid_to` on the fact table.
- **Semantic search is not implemented.** The bonus section (embeddings,
  cosine similarity, hybrid search) was deliberately traded for a complete and
  tested core pipeline: the dimensional model, the parsers, and the merge
  semantics. The design is specified in `ARCHITECTURE.md` §3.5 — embeddings
  keyed by `(article_id, model_name)` so a model upgrade is an insert rather
  than a destructive overwrite, and similarity stored as a normalised long
  table rather than a repeating group.
