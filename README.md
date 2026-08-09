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