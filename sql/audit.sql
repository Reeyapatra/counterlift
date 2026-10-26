-- Run against runs/<run-id>/audit.sqlite using SQLite.
SELECT split, treatment, COUNT(*) AS users,
       SUM(conversion) AS conversions, AVG(conversion) AS conversion_rate
FROM assignments GROUP BY split, treatment ORDER BY split, treatment;

-- No source record may appear in more than one split.
SELECT _source_row, COUNT(DISTINCT split) AS splits
FROM assignments GROUP BY _source_row HAVING COUNT(DISTINCT split) > 1;

SELECT model, budget_fraction, selected_fraction,
       incremental_per_user, lower, upper, net_value_per_user
FROM policy_evaluation ORDER BY budget_fraction, model;
