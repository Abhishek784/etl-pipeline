-- Gold layer DDL. Every table declares a PRIMARY KEY

CREATE TABLE IF NOT EXISTS dim_company (
    company_key            VARCHAR PRIMARY KEY,
    company_name           VARCHAR NOT NULL,
    industry_raw           VARCHAR,
    industry_std           VARCHAR,
    founded_year           INTEGER,
    headquarters           VARCHAR,
    employee_count         INTEGER,
    company_size_category  VARCHAR,
    is_public              BOOLEAN,
    stock_ticker           VARCHAR
);

CREATE TABLE IF NOT EXISTS dim_article (
    article_sk             VARCHAR PRIMARY KEY,
    article_id             VARCHAR NOT NULL UNIQUE,
    company_key            VARCHAR,          -- nullable: 25 unmatched articles
    title                  VARCHAR,
    summary                VARCHAR,
    url                    VARCHAR,
    author                 VARCHAR,          -- 204 nulls; not a quality failure
    word_count             INTEGER,
    published_date         DATE,
    published_year         INTEGER,
    published_quarter      INTEGER,
    published_month        INTEGER,
    category_raw           VARCHAR,
    category_std           VARCHAR,
    date_status            VARCHAR,
    company_match_method   VARCHAR,
    company_match_score    DOUBLE
);

CREATE TABLE IF NOT EXISTS fact_arr_observation (
    arr_observation_id     VARCHAR PRIMARY KEY,
    article_id             VARCHAR NOT NULL,
    company_key            VARCHAR NOT NULL,
    observed_date          DATE    NOT NULL,
    arr_usd                BIGINT  NOT NULL CHECK (arr_usd > 0),
    source_currency        VARCHAR NOT NULL,
    source_value_raw       VARCHAR NOT NULL,
    parse_method           VARCHAR NOT NULL,
    fx_rate_applied        DOUBLE  NOT NULL,
    company_age_at_obs     INTEGER,
    date_status            VARCHAR NOT NULL,
    source_value_hash      VARCHAR NOT NULL,  -- detects upstream restatement
    batch_id               VARCHAR NOT NULL,
    updated_at             TIMESTAMP DEFAULT current_timestamp
);

CREATE TABLE IF NOT EXISTS quarantine_record (
    quarantine_id          VARCHAR PRIMARY KEY,
    source_file            VARCHAR NOT NULL,
    source_row_num         INTEGER NOT NULL,
    article_id             VARCHAR,
    failure_stage          VARCHAR NOT NULL,
    failure_reason         VARCHAR,
    raw_value              VARCHAR,
    best_candidate         VARCHAR,
    match_score            DOUBLE,
    batch_id               VARCHAR NOT NULL
);

CREATE TABLE IF NOT EXISTS pipeline_run_log (
    batch_id               VARCHAR PRIMARY KEY,
    started_at             TIMESTAMP,
    finished_at            TIMESTAMP,
    table_name             VARCHAR,
    rows_written           INTEGER
);

-- NOT NULL on the fact table is enforceable precisely because gold already
-- routed every failure to quarantine_record. A constraint violation here means
-- a bug in the selection logic, not bad source data.