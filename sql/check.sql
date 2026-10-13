-- 1. holdout mean S by run
SELECT run_id, ROUND(AVG(s), 4) AS mean_s, ROUND(MAX(s) - MIN(s), 4) AS spread, COUNT(*) AS samples
FROM runs WHERE split = 'holdout' GROUP BY run_id ORDER BY MIN(ts);

-- 2. cost by route
SELECT route, COUNT(*) AS responses, ROUND(SUM(dollars), 6) AS total_dollars, ROUND(AVG(dollars), 8) AS avg_dollars
FROM responses GROUP BY route ORDER BY total_dollars DESC;

-- 3. leaked-chunk count (must be 0)
SELECT COUNT(*) AS leaked_chunks FROM responses WHERE leaked = 1;
