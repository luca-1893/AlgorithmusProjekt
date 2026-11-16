SELECT variant,
       COUNT(*) AS runs,
       ROUND(AVG(input_tokens), 1) AS avg_input_tokens,
       ROUND(AVG(duration_ms), 1) AS avg_duration_ms,
       COUNT(*) FILTER (WHERE found_source = true) * 1.0 / NULLIF(COUNT(found_source), 0) AS hit_rate
FROM runs
GROUP BY variant;
