-- Same three checks in BigQuery dialect over the parquet export (data/parquet/*.parquet).
-- Upload the two files to a bucket you own, set the dataset and bucket names, then run.
-- Nothing here is executed by this repo and no GCP project is required to use the service.

CREATE OR REPLACE EXTERNAL TABLE `agentops.runs`
OPTIONS (format = 'PARQUET', uris = ['gs://YOUR_BUCKET/agentops/runs.parquet']);

CREATE OR REPLACE EXTERNAL TABLE `agentops.responses`
OPTIONS (format = 'PARQUET', uris = ['gs://YOUR_BUCKET/agentops/responses.parquet']);

-- 1. holdout mean S by run
SELECT run_id, ROUND(AVG(s), 4) AS mean_s, ROUND(MAX(s) - MIN(s), 4) AS spread, COUNT(*) AS samples
FROM `agentops.runs` WHERE split = 'holdout' GROUP BY run_id ORDER BY MIN(ts);

-- 2. cost by route
SELECT route, COUNT(*) AS responses, ROUND(SUM(dollars), 6) AS total_dollars, ROUND(AVG(dollars), 8) AS avg_dollars
FROM `agentops.responses` GROUP BY route ORDER BY total_dollars DESC;

-- 3. leaked-chunk count (must be 0)
SELECT COUNT(*) AS leaked_chunks FROM `agentops.responses` WHERE leaked = 1;
