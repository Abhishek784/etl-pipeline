# Data Architecture
 
Tech-news ARR observation pipeline.


## 1. Purpose and framing
 
The pipeline ingests synthetic technology-news articles and produces two artefacts:
 
1. A queryable warehouse model of **company ARR observations over time**.
2. A **semantic search index** over article text, plus a per-article nearest-neighbour set.
The single most important framing decision is this: the source `revenue`
column is **not** a company attribute. Each value is a *claim made by one
article on one date*. The model therefore treats ARR as an **event**, not a
property. Every downstream consumer sees the observation, its date, and the
article it came from — never a bare "Snowflake ARR = $2.31B" divorced from
provenance.
 
This single decision drives the grain, the key strategy, and the refusal to
materialise a `current_arr` column anywhere.



## 2. Layer overview
 
```
  raw files                bronze                 silver                  gold
┌──────────────┐      ┌──────────────┐      ┌──────────────┐      ┌────────────────────┐
│ tech_news    │      │ bronze_      │      │ silver_      │      │ dim_company        │
│   .csv       │─────▶│  articles    │─────▶│  articles    │─────▶│ dim_article        │
│ company_     │      │ bronze_      │      │ silver_      │      │ fact_arr_          │
│  metadata    │─────▶│  companies   │─────▶│  companies   │─────▶│   observation      │
│   .json      │      │              │      │ silver_      │      │ quarantine_record  │
└──────────────┘      │ append-only  │      │  aliases     │      │                    │
                      │ all strings  │      │ typed + flags│      │  (all in DuckDB)   │
                      └──────────────┘      └──────────────┘      └────────────────────┘
                                                                            │
                                                                            ▼
                                                                  ai_articles_enriched.csv
```


## 6.5 Implementation status
 
Everything is covered by tests
 
| Component | Status |
|---|---|
| bronze / silver / gold layers | built, tested |
| four cleaning modules | built, unit-tested against real fixtures |
| deterministic keys + idempotency | built, proven at both DataFrame and storage layer |
| CSV exports (5 files) | built |
| DuckDB schema, merge loader, views | built, tested |
| semantic search (§3.5) | **designed, not built** |
 



## 7. Beyond a local batch
 
### Ingestion and orchestration
Land raw files in object storage partitioned by ingest date
(`s3://…/raw/tech_news/dt=2026-07-31/`). Bronze becomes an append-only Delta or
Iceberg table. Orchestrate with Airflow or Dagster: one task group per layer,
a sensor on new-batch arrival, per-task retries. The transform code is unchanged
— only the read/write endpoints differ.
 
### Incrementality
Bronze appends by `batch_id`. Silver processes only the new batch. Gold
`MERGE`s on the deterministic keys from §4. Because keys derive from source
content and not from run order, **replaying any historical batch converges to
the same state**, which is what makes backfills safe.
 
### Backfills
Two modes:
 
- *Reprocess* — re-run silver and gold from a bronze slice for one `batch_id`
  range. Used when cleaning logic changes.
- *Full rebuild* — truncate gold, replay all of bronze. Bronze is immutable and
  complete, so the source files are never needed again.
Neither mode can duplicate rows, which is the whole return on the deterministic
key strategy.
 
### Schema evolution
Bronze stores the raw payload plus a `schema_version`, so a new upstream column
lands harmlessly and is available retroactively once silver is taught to read
it. Delta/Iceberg schema evolution handles additive changes. A **contract test**
runs pre-flight and fails the batch loudly if a required source column
disappears or changes type — silent nulls are worse than a failed run.
 
### Data quality
Great Expectations or dbt tests at layer boundaries:
 
- referential integrity — every `fact.company_key` resolves in `dim_company`
- `arr_usd > 0`, non-null `observed_date`, no duplicate PKs
- **distributional checks** — parse-failure rate, fuzzy-match rate, and
  observation count per batch alert when they deviate from trailing norms.
  A sudden spike in `not_disclosed` usually means an upstream format change,
  not a change in the world.
### FX rates
The fixed multipliers are the exercise's biggest simplification. In production,
a `dim_fx_rate` table keyed by `(currency, rate_date)` lets each observation
convert at the rate **as of its published date** — necessary for a time series
spanning years, since a 2022 EUR figure and a 2024 EUR figure converted at one
rate are not comparable. `fx_rate_applied` is already on the fact row, so this
is a lookup change, not a model change.
 
### Embeddings at scale
Batch encode on GPU; persist to a purpose-built vector store (pgvector, Qdrant,
LanceDB) once brute-force cosine over the full corpus stops being viable —
around 10⁵–10⁶ articles. Version by `model_name` so a model upgrade is a
backfill of a new keyed set, not a destructive overwrite. Only articles whose
`title || summary` hash changed need re-embedding.
 
### Scale path
750 rows is comfortably pandas. The transforms are all row-wise and free of
cross-row dependencies, so the port to PySpark is mechanical: the parsers become
UDFs or native column expressions, and the MERGE becomes a Delta merge. The
model itself is unchanged — that portability is a reason to keep cleaning logic
in pure functions with no framework types in their signatures.
 
---
 


## 8. Known limitations
 
- `dim_company` is SCD Type 1; `employee_count` and `company_size_category`
  reflect the metadata snapshot, not the state at article time.
- Fixed FX rates ignore the observation date.
- One ARR observation per article maximum; an article quoting two figures for
  the same company would need a grain change to `(article_id, sequence)`.
- Restated source values overwrite in place rather than versioning. Adding
  `valid_from` / `valid_to` to the fact table would make restatement history
  queryable, at the cost of complicating every downstream query.
- Semantic search is not implemented (§3.5, §6.5). Were it built,
  `article_similarity` would be recomputed in full each run; incremental
  nearest-neighbour maintenance would be a later optimisation.
- The 66 `ambiguous_resolved` dates rest on a documented majority assumption.
  They are flagged rather than excluded, so the exposure is one `WHERE` clause
  away, but they are not *known* correct.
- `ai_articles_enriched` is exported as CSV only and not loaded into DuckDB; it
  is a derived mart fully reproducible from the fact table and both dimensions.
 




































