-- SQL Practice Workbook: runnable PostgreSQL solutions.
-- Run against the loaded sql_workbook database, e.g.
--   psql -d sql_workbook -f solutions_postgresql.sql
-- Exercises that create sandbox objects (sb_*) drop them again.

-- SQL-001 · European mid-size and enterprise accounts created in 2024
SELECT org_id,
       org_name,
       segment,
       country_code,
       CAST(created_at AS DATE) AS created_date
FROM organizations
WHERE segment IN ('Mid-Market', 'Enterprise')
  AND country_code IN ('DE', 'GB', 'NL')
  AND created_at >= TIMESTAMP '2024-01-01 00:00:00'
  AND created_at <  TIMESTAMP '2025-01-01 00:00:00'
ORDER BY created_date, org_id;

-- SQL-002 · Distinct acquisition channels including unknowns
SELECT DISTINCT COALESCE(acquisition_channel, 'unknown') AS channel
FROM users
ORDER BY channel;

-- SQL-003 · Marketing consent and three-valued logic
SELECT SUM(CASE WHEN marketing_opt_in = TRUE  THEN 1 ELSE 0 END) AS opted_in,
       SUM(CASE WHEN marketing_opt_in = FALSE THEN 1 ELSE 0 END) AS opted_out,
       SUM(CASE WHEN marketing_opt_in IS NULL THEN 1 ELSE 0 END) AS unknown,
       SUM(CASE WHEN marketing_opt_in <> TRUE THEN 1 ELSE 0 END) AS naive_not_opted_in,
       SUM(CASE WHEN marketing_opt_in IS NULL OR marketing_opt_in = FALSE
                THEN 1 ELSE 0 END)                                AS correct_not_opted_in
FROM users;

-- SQL-004 · Operator precedence in a revenue filter
SELECT SUM(CASE WHEN status = 'completed' OR status = 'refunded'
                     AND sales_channel = 'web'
                     AND order_ts >= TIMESTAMP '2025-01-01 00:00:00'
                     AND order_ts <  TIMESTAMP '2025-04-01 00:00:00'
                THEN 1 ELSE 0 END) AS buggy_count,
       SUM(CASE WHEN status IN ('completed', 'refunded')
                     AND sales_channel = 'web'
                     AND order_ts >= TIMESTAMP '2025-01-01 00:00:00'
                     AND order_ts <  TIMESTAMP '2025-04-01 00:00:00'
                THEN 1 ELSE 0 END) AS correct_count
FROM orders;

-- SQL-005 · BETWEEN and timestamp boundaries
SELECT SUM(CASE WHEN order_ts BETWEEN TIMESTAMP '2025-03-01 00:00:00'
                                  AND TIMESTAMP '2025-03-31 00:00:00' THEN 1 ELSE 0 END) AS naive_between,
       SUM(CASE WHEN order_ts BETWEEN TIMESTAMP '2025-03-01 00:00:00'
                                  AND TIMESTAMP '2025-03-31 23:59:59' THEN 1 ELSE 0 END) AS between_end_of_day,
       SUM(CASE WHEN order_ts >= TIMESTAMP '2025-03-01 00:00:00'
                 AND order_ts <  TIMESTAMP '2025-04-01 00:00:00' THEN 1 ELSE 0 END) AS half_open
FROM orders;

-- SQL-006 · SLA targets with CASE and a custom sort order
SELECT ticket_id,
       priority,
       CASE priority
            WHEN 'urgent' THEN 1
            WHEN 'high'   THEN 4
            WHEN 'medium' THEN 24
            WHEN 'low'    THEN 72
       END AS sla_hours,
       CASE WHEN status IN ('open', 'pending') THEN 'active' ELSE 'done' END AS status_group
FROM support_tickets
WHERE created_at >= TIMESTAMP '2025-06-28 00:00:00'
  AND created_at <  TIMESTAMP '2025-07-01 00:00:00'
ORDER BY CASE priority WHEN 'urgent' THEN 1 WHEN 'high' THEN 2 WHEN 'medium' THEN 3 ELSE 4 END,
         ticket_id;

-- SQL-007 · Effective annual price per plan with COALESCE
SELECT plan_name,
       price_per_seat_month,
       ROUND(price_per_seat_month * (1 - COALESCE(annual_discount_pct, 0) / 100.0), 2)
           AS annual_price_per_seat_month,
       CASE WHEN seat_limit IS NULL THEN 'unlimited'
            ELSE CONCAT(seat_limit, ' seats')
       END AS seat_limit_label
FROM plans
WHERE is_active = TRUE
ORDER BY price_per_seat_month, plan_name;

-- SQL-008 · Line-level revenue and discount percentage
SELECT oi.order_id,
       oi.line_number,
       oi.product_id,
       oi.quantity * oi.unit_price                              AS gross_amount,
       oi.discount_amount,
       oi.quantity * oi.unit_price - oi.discount_amount         AS net_amount,
       ROUND(100.0 * oi.discount_amount
             / NULLIF(oi.quantity * oi.unit_price, 0), 1)       AS discount_pct
FROM order_items oi
JOIN orders o ON o.order_id = oi.order_id
WHERE o.order_ts >= TIMESTAMP '2024-11-29 00:00:00'
  AND o.order_ts <  TIMESTAMP '2024-11-30 00:00:00'
ORDER BY oi.order_id, oi.line_number;

-- SQL-009 · Spot e-mails that are not normalized
SELECT user_id,
       email                                    AS raw_email,
       LOWER(TRIM(email))                       AS normalized_email,
       SUBSTRING(LOWER(TRIM(email)) FROM POSITION('@' IN LOWER(TRIM(email))) + 1) AS email_domain
FROM users
WHERE email <> LOWER(TRIM(email))
ORDER BY user_id;

-- SQL-010 · Daily sign-ups in the last week of data
SELECT CAST(signup_at AS DATE) AS signup_date,
       COUNT(*)                AS signups
FROM users
WHERE signup_at >= TIMESTAMP '2025-07-01 00:00:00' - INTERVAL '7' DAY
  AND signup_at <  TIMESTAMP '2025-07-01 00:00:00'
GROUP BY CAST(signup_at AS DATE)
ORDER BY signup_date;

-- SQL-011 · First-response time in hours for urgent tickets
SELECT ticket_id,
       created_at,
       ROUND(EXTRACT(EPOCH FROM (first_response_at - created_at)) / 3600, 2) AS response_hours,
       CASE WHEN first_response_at IS NULL THEN 'no_response'
            WHEN first_response_at <= created_at + INTERVAL '1' HOUR THEN 'met'
            ELSE 'breached'
       END AS sla_status
FROM support_tickets
WHERE priority = 'urgent'
  AND created_at >= TIMESTAMP '2025-05-01 00:00:00'
  AND created_at <  TIMESTAMP '2025-06-01 00:00:00'
ORDER BY ticket_id;

-- SQL-012 · Paginate the document catalogue deterministically
SELECT document_id,
       doc_key,
       version_number,
       updated_at
FROM documents
ORDER BY updated_at DESC, document_id DESC
LIMIT 10 OFFSET 20;

-- SQL-013 · The NOT IN trap with NULLs
SELECT (SELECT COUNT(*) FROM users u
         WHERE u.user_id NOT IN (SELECT r.referred_by_user_id FROM users r))          AS naive_not_in,
       (SELECT COUNT(*) FROM users u
         WHERE u.user_id NOT IN (SELECT r.referred_by_user_id FROM users r
                                  WHERE r.referred_by_user_id IS NOT NULL))           AS filtered_not_in,
       (SELECT COUNT(*) FROM users u
         WHERE NOT EXISTS (SELECT 1 FROM users r
                            WHERE r.referred_by_user_id = u.user_id))                AS not_exists_count;

-- SQL-014 · Format feature values with CAST and ROUND
SELECT entity_id,
       CAST(as_of_ts AS DATE)                         AS as_of_date,
       CAST(avg_session_minutes AS DECIMAL(10,1))     AS avg_session_minutes,
       CAST(seats_used_pct * 100 AS DECIMAL(10,1))    AS seats_used_pct
FROM entity_features
WHERE entity_id = 10
ORDER BY as_of_date;

-- SQL-015 · Find knowledge-base articles by pattern
SELECT document_id,
       doc_key,
       title
FROM documents
WHERE status = 'published'
  AND doc_key LIKE 'help/billing/%'
  AND (LOWER(title) LIKE '%refund%' OR LOWER(title) LIKE '%payment%')
ORDER BY doc_key;

-- SQL-016 · Order statistics by status
SELECT status,
       COUNT(*)                   AS orders,
       SUM(order_total)           AS total_amount,
       ROUND(AVG(order_total), 2) AS avg_amount,
       MIN(order_ts)              AS first_order_ts,
       MAX(order_ts)              AS last_order_ts
FROM orders
GROUP BY status
ORDER BY orders DESC, status;

-- SQL-017 · COUNT(*) versus COUNT(column) versus COUNT(DISTINCT)
SELECT COUNT(*)                                   AS tickets,
       COUNT(user_id)                             AS tickets_with_user,
       COUNT(DISTINCT user_id)                    AS distinct_users,
       COUNT(csat_score)                          AS tickets_with_csat,
       ROUND(AVG(csat_score), 2)                  AS avg_csat_rated,
       ROUND(AVG(COALESCE(csat_score, 0)), 2)     AS avg_csat_null_as_zero,
       COUNT(*) - COUNT(first_response_at)        AS unanswered
FROM support_tickets;

-- SQL-018 · CSAT satisfaction rate without integer division
SELECT category,
       COUNT(csat_score)                                         AS rated_tickets,
       SUM(CASE WHEN csat_score >= 4 THEN 1 ELSE 0 END)          AS satisfied,
       ROUND(100.0 * SUM(CASE WHEN csat_score >= 4 THEN 1 ELSE 0 END)
             / NULLIF(COUNT(csat_score), 0), 1)                  AS satisfaction_pct
FROM support_tickets
GROUP BY category
HAVING COUNT(csat_score) >= 30
ORDER BY satisfaction_pct DESC, category;

-- SQL-019 · Large organizations by user count
SELECT org_id,
       COUNT(*)                                          AS total_users,
       SUM(CASE WHEN status = 'active' THEN 1 ELSE 0 END) AS active_users
FROM users
GROUP BY org_id
HAVING COUNT(*) > 25
   AND SUM(CASE WHEN status = 'active' THEN 1 ELSE 0 END) >= 20
ORDER BY total_users DESC, org_id;

-- SQL-020 · Monthly revenue and average order value
SELECT CAST(DATE_TRUNC('month', order_ts) AS DATE) AS month_start,
       COUNT(*)                                    AS completed_orders,
       SUM(order_total)                            AS revenue,
       ROUND(AVG(order_total), 2)                  AS avg_order_value
FROM orders
WHERE status = 'completed'
  AND order_ts >= TIMESTAMP '2024-01-01 00:00:00'
  AND order_ts <  TIMESTAMP '2025-07-01 00:00:00'
GROUP BY DATE_TRUNC('month', order_ts)
ORDER BY month_start;

-- SQL-021 · LLM request outcomes pivoted by feature
SELECT feature,
       COUNT(*)                                                     AS requests,
       SUM(CASE WHEN status = 'success'          THEN 1 ELSE 0 END) AS success,
       SUM(CASE WHEN status = 'error'            THEN 1 ELSE 0 END) AS error,
       SUM(CASE WHEN status = 'timeout'          THEN 1 ELSE 0 END) AS timeout,
       SUM(CASE WHEN status = 'rate_limited'     THEN 1 ELSE 0 END) AS rate_limited,
       SUM(CASE WHEN status = 'content_filtered' THEN 1 ELSE 0 END) AS content_filtered,
       ROUND(100.0 * SUM(CASE WHEN status <> 'success' THEN 1 ELSE 0 END) / COUNT(*), 2)
                                                                    AS failure_rate_pct
FROM llm_requests
GROUP BY feature
ORDER BY failure_rate_pct DESC, feature;

-- SQL-022 · Revenue by product category across three tables
SELECT pc.category_name,
       COUNT(DISTINCT oi.order_id)                                AS orders,
       SUM(oi.quantity)                                           AS units,
       SUM(oi.quantity * oi.unit_price - oi.discount_amount)      AS net_revenue
FROM order_items oi
JOIN orders o              ON o.order_id = oi.order_id
JOIN products p            ON p.product_id = oi.product_id
JOIN product_categories pc ON pc.category_id = p.category_id
WHERE o.status = 'completed'
  AND o.order_ts >= TIMESTAMP '2025-01-01 00:00:00'
  AND o.order_ts <  TIMESTAMP '2025-07-01 00:00:00'
GROUP BY pc.category_name
ORDER BY net_revenue DESC, pc.category_name;

-- SQL-023 · First and last order of repeat buyers
SELECT user_id,
       COUNT(*)         AS completed_orders,
       MIN(order_ts)    AS first_order_ts,
       MAX(order_ts)    AS last_order_ts,
       SUM(order_total) AS lifetime_value
FROM orders
WHERE status = 'completed'
GROUP BY user_id
HAVING COUNT(*) >= 5
ORDER BY lifetime_value DESC, user_id;

-- SQL-024 · Refund rate by sales channel
SELECT o.sales_channel,
       COUNT(DISTINCT p.order_id)                                              AS paid_orders,
       COUNT(DISTINCT CASE WHEN p.status = 'refunded' THEN p.order_id END)      AS refunded_orders,
       ROUND(100.0 * COUNT(DISTINCT CASE WHEN p.status = 'refunded' THEN p.order_id END)
             / NULLIF(COUNT(DISTINCT p.order_id), 0), 2)                        AS refund_rate_pct,
       SUM(p.amount)                                                           AS collected_amount,
       COALESCE(SUM(p.refunded_amount), 0)                                     AS refunded_amount,
       ROUND(100.0 * COALESCE(SUM(p.refunded_amount), 0) / NULLIF(SUM(p.amount), 0), 2)
                                                                               AS refunded_amount_pct
FROM payments p
JOIN orders o ON o.order_id = p.order_id
WHERE p.status IN ('succeeded', 'refunded')
GROUP BY o.sales_channel
ORDER BY o.sales_channel;

-- SQL-025 · Daily active users and engagement depth in June 2025
SELECT CAST(event_ts AS DATE)                                   AS event_date,
       COUNT(DISTINCT user_id)                                  AS active_users,
       COUNT(*)                                                 AS events,
       ROUND(1.0 * COUNT(*) / COUNT(DISTINCT user_id), 2)       AS events_per_active_user
FROM events
WHERE event_ts >= TIMESTAMP '2025-06-01 00:00:00'
  AND event_ts <  TIMESTAMP '2025-07-01 00:00:00'
GROUP BY CAST(event_ts AS DATE)
ORDER BY event_date;

-- SQL-026 · Token usage with subtotals (ROLLUP)
SELECT CASE WHEN GROUPING(model_name) = 1 THEN 'ALL' ELSE model_name END AS model_name,
       CASE WHEN GROUPING(feature) = 1    THEN 'ALL' ELSE feature END    AS feature,
       COUNT(*)                                           AS requests,
       SUM(input_tokens + COALESCE(output_tokens, 0))     AS total_tokens
FROM llm_requests
WHERE requested_at >= TIMESTAMP '2025-06-01 00:00:00'
  AND requested_at <  TIMESTAMP '2025-07-01 00:00:00'
GROUP BY ROLLUP (model_name, feature)
ORDER BY GROUPING(llm_requests.model_name), llm_requests.model_name,
         GROUPING(llm_requests.feature), llm_requests.feature;

-- SQL-027 · Average output tokens and the NULL denominator question
SELECT model_name,
       COUNT(*)                                   AS requests,
       COUNT(output_tokens)                       AS requests_with_output,
       ROUND(AVG(output_tokens), 1)               AS avg_output_tokens_answered,
       ROUND(AVG(COALESCE(output_tokens, 0)), 1)  AS avg_output_tokens_all_requests
FROM llm_requests
GROUP BY model_name
ORDER BY model_name;

-- SQL-028 · Average session length: overall versus average of user averages
SELECT device_type,
       SUM(n_sessions)                                 AS sessions,
       COUNT(*)                                        AS users,
       ROUND(SUM(total_minutes) / SUM(n_sessions), 2)  AS avg_minutes_per_session,
       ROUND(AVG(user_avg_minutes), 2)                 AS avg_of_user_avg_minutes
FROM (
    SELECT device_type,
           user_id,
           COUNT(*)                                              AS n_sessions,
           SUM(EXTRACT(EPOCH FROM (ended_at - started_at)) / 60) AS total_minutes,
           AVG(EXTRACT(EPOCH FROM (ended_at - started_at)) / 60) AS user_avg_minutes
    FROM sessions
    WHERE ended_at IS NOT NULL
      AND started_at >= TIMESTAMP '2025-04-01 00:00:00'
      AND started_at <  TIMESTAMP '2025-07-01 00:00:00'
    GROUP BY device_type, user_id
) per_user
GROUP BY device_type
ORDER BY device_type;

-- SQL-029 · Latency summary statistics per model
SELECT model_name,
       COUNT(*)                                                         AS requests,
       ROUND(AVG(latency_ms), 1)                                        AS mean_ms,
       ROUND(CAST(STDDEV_SAMP(latency_ms) AS DECIMAL(14,4)), 1)         AS stddev_ms,
       MIN(latency_ms)                                                  AS min_ms,
       MAX(latency_ms)                                                  AS max_ms,
       ROUND(CAST(STDDEV_SAMP(latency_ms) / AVG(latency_ms) AS DECIMAL(14,6)), 3) AS cv
FROM llm_requests
WHERE status = 'success'
  AND cache_hit = FALSE
  AND requested_at >= TIMESTAMP '2025-04-01 00:00:00'
  AND requested_at <  TIMESTAMP '2025-07-01 00:00:00'
GROUP BY model_name
ORDER BY mean_ms, model_name;

-- SQL-030 · Admins of enterprise customers
SELECT o.org_id,
       o.org_name,
       u.user_id,
       u.full_name,
       u.email
FROM users u
JOIN organizations o ON o.org_id = u.org_id
WHERE o.segment = 'Enterprise'
  AND u.role = 'admin'
  AND u.status = 'active'
ORDER BY o.org_id, u.user_id;

-- SQL-031 · Revenue by segment and the join fan-out trap
SELECT c.segment,
       n.naive_revenue,
       c.correct_revenue,
       ROUND(100.0 * (n.naive_revenue / c.correct_revenue - 1), 1) AS inflation_pct
FROM (
    SELECT og.segment, SUM(o.order_total) AS correct_revenue
    FROM orders o
    JOIN organizations og ON og.org_id = o.org_id
    WHERE o.status = 'completed'
      AND o.order_ts >= TIMESTAMP '2025-01-01 00:00:00'
      AND o.order_ts <  TIMESTAMP '2025-07-01 00:00:00'
    GROUP BY og.segment
) c
JOIN (
    SELECT og.segment, SUM(o.order_total) AS naive_revenue
    FROM orders o
    JOIN organizations og ON og.org_id = o.org_id
    JOIN order_items oi  ON oi.order_id = o.order_id
    WHERE o.status = 'completed'
      AND o.order_ts >= TIMESTAMP '2025-01-01 00:00:00'
      AND o.order_ts <  TIMESTAMP '2025-07-01 00:00:00'
    GROUP BY og.segment
) n ON n.segment = c.segment
ORDER BY c.segment;

-- SQL-032 · Purchase conversion by acquisition channel
SELECT COALESCE(u.acquisition_channel, 'unknown')                       AS channel,
       COUNT(*)                                                          AS users,
       SUM(CASE WHEN o.completed_orders > 0 THEN 1 ELSE 0 END)           AS buyers,
       ROUND(100.0 * SUM(CASE WHEN o.completed_orders > 0 THEN 1 ELSE 0 END) / COUNT(*), 2)
                                                                         AS conversion_pct,
       ROUND(1.0 * COALESCE(SUM(o.completed_orders), 0)
             / NULLIF(SUM(CASE WHEN o.completed_orders > 0 THEN 1 ELSE 0 END), 0), 2)
                                                                         AS completed_orders_per_buyer
FROM users u
LEFT JOIN (
    SELECT user_id, COUNT(*) AS completed_orders
    FROM orders
    WHERE status = 'completed'
    GROUP BY user_id
) o ON o.user_id = u.user_id
WHERE u.signup_at >= TIMESTAMP '2024-01-01 00:00:00'
GROUP BY COALESCE(u.acquisition_channel, 'unknown')
ORDER BY conversion_pct DESC, channel;

-- SQL-033 · Completed orders without a payment record (anti-join)
SELECT o.order_id,
       o.order_ts,
       o.sales_channel,
       o.order_total
FROM orders o
WHERE o.status = 'completed'
  AND NOT EXISTS (SELECT 1
                  FROM payments p
                  WHERE p.order_id = o.order_id)
ORDER BY o.order_id;

-- SQL-034 · LEFT JOIN filter placement (ON versus WHERE)
SELECT o.org_id,
       o.org_name,
       COUNT(t.ticket_id) AS urgent_tickets_h1_2025
FROM organizations o
LEFT JOIN support_tickets t
       ON t.org_id = o.org_id
      AND t.priority = 'urgent'
      AND t.created_at >= TIMESTAMP '2025-01-01 00:00:00'
      AND t.created_at <  TIMESTAMP '2025-07-01 00:00:00'
WHERE o.segment = 'Enterprise'
GROUP BY o.org_id, o.org_name
ORDER BY urgent_tickets_h1_2025 DESC, o.org_id;

-- SQL-035 · AI feature adoption by segment (semi-join)
SELECT o.segment,
       COUNT(*) AS organizations,
       SUM(CASE WHEN EXISTS (SELECT 1
                             FROM llm_requests r
                             WHERE r.org_id = o.org_id
                               AND r.status = 'success'
                               AND r.requested_at >= TIMESTAMP '2025-04-01 00:00:00'
                               AND r.requested_at <  TIMESTAMP '2025-07-01 00:00:00')
                THEN 1 ELSE 0 END) AS adopting_orgs,
       ROUND(100.0 * SUM(CASE WHEN EXISTS (SELECT 1
                                           FROM llm_requests r
                                           WHERE r.org_id = o.org_id
                                             AND r.status = 'success'
                                             AND r.requested_at >= TIMESTAMP '2025-04-01 00:00:00'
                                             AND r.requested_at <  TIMESTAMP '2025-07-01 00:00:00')
                              THEN 1 ELSE 0 END) / COUNT(*), 1) AS adoption_pct
FROM organizations o
WHERE o.is_deleted = FALSE
GROUP BY o.segment
ORDER BY o.segment;

-- SQL-036 · Top referrers and whether referrals stay in the same company
SELECT ref.user_id                                              AS referrer_id,
       ref.full_name                                            AS referrer_name,
       COUNT(*)                                                 AS referrals,
       SUM(CASE WHEN r.org_id = ref.org_id THEN 1 ELSE 0 END)   AS same_org_referrals
FROM users r
JOIN users ref ON ref.user_id = r.referred_by_user_id
GROUP BY ref.user_id, ref.full_name
HAVING COUNT(*) >= 2
ORDER BY referrals DESC, referrer_id;

-- SQL-037 · Most-retrieved knowledge-base documents (many-to-many)
SELECT d.doc_key,
       COUNT(DISTINCT rc.request_id)  AS requests,
       COUNT(*)                       AS chunk_retrievals,
       COUNT(DISTINCT d.document_id)  AS distinct_versions
FROM llm_requests r
JOIN llm_request_chunks rc ON rc.request_id = r.request_id
JOIN document_chunks c     ON c.chunk_id = rc.chunk_id
JOIN documents d           ON d.document_id = c.document_id
WHERE r.feature = 'support_bot'
  AND r.requested_at >= TIMESTAMP '2025-06-01 00:00:00'
  AND r.requested_at <  TIMESTAMP '2025-07-01 00:00:00'
GROUP BY d.doc_key
ORDER BY requests DESC, d.doc_key
LIMIT 10;

-- SQL-038 · Attribute orders to the active subscription (range join)
SELECT matching_subscriptions,
       COUNT(*) AS completed_orders
FROM (
    SELECT o.order_id,
           COUNT(s.subscription_id) AS matching_subscriptions
    FROM orders o
    LEFT JOIN subscriptions s
           ON s.org_id = o.org_id
          AND s.started_at <= o.order_ts
          AND (s.ended_at IS NULL OR o.order_ts < s.ended_at)
    WHERE o.status = 'completed'
    GROUP BY o.order_id
) m
GROUP BY matching_subscriptions
ORDER BY matching_subscriptions;

-- SQL-039 · Complete model-by-feature grid (CROSS JOIN)
SELECT m.model_name,
       f.feature,
       COALESCE(r.requests, 0) AS requests
FROM llm_models m
CROSS JOIN (SELECT 'support_bot' AS feature
            UNION ALL SELECT 'sql_copilot'
            UNION ALL SELECT 'doc_summary') f
LEFT JOIN (SELECT model_name, feature, COUNT(*) AS requests
           FROM llm_requests
           WHERE requested_at >= TIMESTAMP '2025-06-01 00:00:00'
             AND requested_at <  TIMESTAMP '2025-07-01 00:00:00'
           GROUP BY model_name, feature) r
       ON r.model_name = m.model_name
      AND r.feature = f.feature
ORDER BY m.model_name, f.feature;

-- SQL-040 · Compare two retrieval configurations on the composite key
SELECT COUNT(*)                                                                       AS queries,
       SUM(CASE WHEN a.chunk_id = b.chunk_id THEN 1 ELSE 0 END)                       AS same_top1_chunk,
       SUM(CASE WHEN COALESCE(a.is_relevant, FALSE) THEN 1 ELSE 0 END)               AS top1_relevant_cfg2,
       SUM(CASE WHEN COALESCE(b.is_relevant, FALSE) THEN 1 ELSE 0 END)               AS top1_relevant_cfg3,
       SUM(CASE WHEN COALESCE(b.is_relevant, FALSE) AND NOT COALESCE(a.is_relevant, FALSE)
                THEN 1 ELSE 0 END)                                                   AS improved,
       SUM(CASE WHEN COALESCE(a.is_relevant, FALSE) AND NOT COALESCE(b.is_relevant, FALSE)
                THEN 1 ELSE 0 END)                                                   AS regressed
FROM retrieval_evaluations a
JOIN retrieval_evaluations b
  ON b.query_id = a.query_id
 AND b.rank_position = a.rank_position
WHERE a.config_id = 2
  AND b.config_id = 3
  AND a.rank_position = 1;

-- SQL-041 · Reconcile event data with ingestion runs (FULL OUTER JOIN)
SELECT COALESCE(e.activity_date, r.run_date)                 AS activity_date,
       COALESCE(e.events, 0)                                 AS events,
       COALESCE(r.successful_runs, 0)                        AS successful_runs,
       CASE WHEN COALESCE(r.successful_runs, 0) = 0 THEN 'no successful run'
            ELSE 'run without events' END                    AS issue
FROM (SELECT CAST(event_ts AS DATE) AS activity_date, COUNT(*) AS events
      FROM events
      WHERE event_ts >= TIMESTAMP '2025-04-01 00:00:00'
        AND event_ts <  TIMESTAMP '2025-07-01 00:00:00'
      GROUP BY CAST(event_ts AS DATE)) e
FULL OUTER JOIN
     (SELECT run_date,
             SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) AS successful_runs
      FROM pipeline_runs
      WHERE pipeline_name = 'events_ingest'
        AND run_date >= DATE '2025-04-01'
        AND run_date <  DATE '2025-07-01'
      GROUP BY run_date) r
  ON r.run_date = e.activity_date
WHERE COALESCE(e.events, 0) = 0
   OR COALESCE(r.successful_runs, 0) = 0
ORDER BY activity_date;

-- SQL-042 · Open subscriptions per plan with RIGHT JOIN
SELECT p.plan_name,
       COUNT(s.subscription_id)   AS open_subscriptions,
       COALESCE(SUM(s.mrr), 0)    AS open_mrr
FROM subscriptions s
RIGHT JOIN plans p
        ON p.plan_id = s.plan_id
       AND s.ended_at IS NULL
GROUP BY p.plan_id, p.plan_name, p.tier_rank
ORDER BY p.tier_rank, p.plan_name;

-- SQL-043 · Two one-to-many children: lines and payment attempts per order
SELECT o.order_id,
       li.line_count,
       li.line_net_amount,
       pa.payment_attempts,
       pa.failed_attempts,
       nv.naive_line_net_amount
FROM orders o
JOIN (SELECT order_id,
             COUNT(*)                                          AS line_count,
             SUM(quantity * unit_price - discount_amount)      AS line_net_amount
      FROM order_items
      GROUP BY order_id) li ON li.order_id = o.order_id
JOIN (SELECT order_id,
             COUNT(*)                                          AS payment_attempts,
             SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) AS failed_attempts
      FROM payments
      GROUP BY order_id) pa ON pa.order_id = o.order_id
JOIN (SELECT o2.order_id,
             SUM(oi.quantity * oi.unit_price - oi.discount_amount) AS naive_line_net_amount
      FROM orders o2
      JOIN order_items oi ON oi.order_id = o2.order_id
      JOIN payments p     ON p.order_id = o2.order_id
      GROUP BY o2.order_id) nv ON nv.order_id = o.order_id
WHERE o.status = 'completed'
  AND o.order_ts >= TIMESTAMP '2025-05-01 00:00:00'
  AND o.order_ts <  TIMESTAMP '2025-06-01 00:00:00'
  AND pa.payment_attempts >= 2
ORDER BY o.order_id;

-- SQL-044 · Pair duplicate user accounts (self join on a normalized key)
SELECT a.user_id                                  AS original_user_id,
       b.user_id                                  AS duplicate_user_id,
       LOWER(TRIM(a.email))                       AS normalized_email,
       CASE WHEN a.org_id = b.org_id THEN 1 ELSE 0 END AS same_org,
       a.signup_at                                AS original_signup_at,
       b.signup_at                                AS duplicate_signup_at
FROM users a
JOIN users b
  ON LOWER(TRIM(b.email)) = LOWER(TRIM(a.email))
 AND a.user_id < b.user_id
ORDER BY original_user_id, duplicate_user_id;

-- SQL-045 · Experiment overlap matrix (composite keys)
SELECT a.variant  AS ai_assist_variant,
       b.variant  AS onboarding_variant,
       COUNT(*)   AS users
FROM experiment_assignments a
JOIN experiments ea ON ea.experiment_id = a.experiment_id
JOIN experiment_assignments b ON b.user_id = a.user_id
JOIN experiments eb ON eb.experiment_id = b.experiment_id
WHERE ea.experiment_name = 'ai_assist_default_on'
  AND eb.experiment_name = 'onboarding_checklist'
GROUP BY a.variant, b.variant
ORDER BY ai_assist_variant, onboarding_variant;

-- SQL-046 · Products priced above the catalogue average
SELECT product_name,
       list_price,
       ROUND((SELECT AVG(list_price) FROM products WHERE is_active = TRUE), 2) AS avg_list_price,
       ROUND(list_price - (SELECT AVG(list_price) FROM products WHERE is_active = TRUE), 2) AS above_avg_by
FROM products
WHERE is_active = TRUE
  AND list_price > (SELECT AVG(list_price) FROM products WHERE is_active = TRUE)
ORDER BY list_price DESC, product_name;

-- SQL-047 · Latest ticket per enterprise organization (correlated subquery)
SELECT t.org_id,
       t.ticket_id,
       t.created_at,
       t.priority,
       t.status
FROM support_tickets t
JOIN organizations o ON o.org_id = t.org_id
WHERE o.segment = 'Enterprise'
  AND t.ticket_id = (SELECT t2.ticket_id
                     FROM support_tickets t2
                     WHERE t2.org_id = t.org_id
                     ORDER BY t2.created_at DESC, t2.ticket_id DESC
                     LIMIT 1)
ORDER BY t.org_id;

-- SQL-048 · Active users left in fully churned organizations
SELECT u.org_id,
       COUNT(*) AS active_users
FROM users u
WHERE u.status = 'active'
  AND u.org_id IN (SELECT s.org_id FROM subscriptions s WHERE s.status = 'canceled')
  AND u.org_id NOT IN (SELECT s.org_id FROM subscriptions s WHERE s.ended_at IS NULL)
GROUP BY u.org_id
ORDER BY active_users DESC, u.org_id;

-- SQL-049 · Organizations above average 2025 revenue (CTEs)
WITH org_rev AS (
    SELECT org_id, SUM(order_total) AS revenue
    FROM orders
    WHERE status = 'completed'
      AND order_ts >= TIMESTAMP '2025-01-01 00:00:00'
      AND order_ts <  TIMESTAMP '2025-07-01 00:00:00'
    GROUP BY org_id
),
stats AS (
    SELECT AVG(revenue) AS avg_revenue FROM org_rev
)
SELECT r.org_id,
       o.org_name,
       o.segment,
       r.revenue,
       ROUND(s.avg_revenue, 2)               AS avg_org_revenue,
       ROUND(r.revenue / s.avg_revenue, 2)   AS revenue_vs_avg
FROM org_rev r
JOIN organizations o ON o.org_id = r.org_id
CROSS JOIN stats s
WHERE r.revenue > 2 * s.avg_revenue
ORDER BY r.revenue DESC, r.org_id;

-- SQL-050 · Account health dataset from several grains
WITH u AS (
    SELECT org_id, COUNT(*) AS users
    FROM users
    GROUP BY org_id
),
act AS (
    SELECT us.org_id,
           COUNT(DISTINCT s.user_id) AS active_users_30d,
           COUNT(*)                  AS sessions_30d
    FROM sessions s
    JOIN users us ON us.user_id = s.user_id
    WHERE s.started_at >= TIMESTAMP '2025-07-01 00:00:00' - INTERVAL '30' DAY
      AND s.started_at <  TIMESTAMP '2025-07-01 00:00:00'
    GROUP BY us.org_id
),
tix AS (
    SELECT org_id, COUNT(*) AS open_tickets
    FROM support_tickets
    WHERE created_at < TIMESTAMP '2025-07-01 00:00:00'
      AND (resolved_at IS NULL OR resolved_at >= TIMESTAMP '2025-07-01 00:00:00')
    GROUP BY org_id
),
rev AS (
    SELECT org_id, SUM(order_total) AS revenue_h1_2025
    FROM orders
    WHERE status = 'completed'
      AND order_ts >= TIMESTAMP '2025-01-01 00:00:00'
      AND order_ts <  TIMESTAMP '2025-07-01 00:00:00'
    GROUP BY org_id
),
mrr AS (
    SELECT org_id, SUM(mrr) AS open_mrr
    FROM subscriptions
    WHERE started_at < TIMESTAMP '2025-07-01 00:00:00'
      AND (ended_at IS NULL OR ended_at > TIMESTAMP '2025-07-01 00:00:00')
    GROUP BY org_id
)
SELECT o.org_id,
       o.segment,
       COALESCE(u.users, 0)               AS users,
       COALESCE(act.active_users_30d, 0)  AS active_users_30d,
       COALESCE(act.sessions_30d, 0)      AS sessions_30d,
       COALESCE(tix.open_tickets, 0)      AS open_tickets,
       COALESCE(rev.revenue_h1_2025, 0)   AS revenue_h1_2025,
       COALESCE(mrr.open_mrr, 0)          AS open_mrr
FROM organizations o
LEFT JOIN u   ON u.org_id = o.org_id
LEFT JOIN act ON act.org_id = o.org_id
LEFT JOIN tix ON tix.org_id = o.org_id
LEFT JOIN rev ON rev.org_id = o.org_id
LEFT JOIN mrr ON mrr.org_id = o.org_id
WHERE o.is_deleted = FALSE
  AND o.segment IN ('Mid-Market', 'Enterprise')
ORDER BY open_mrr DESC, o.org_id;

-- SQL-051 · Corporate hierarchy below a parent company (recursive CTE)
WITH RECURSIVE tree AS (
    SELECT org_id, org_name, 0 AS depth, CAST(org_id AS TEXT) AS path
    FROM organizations
    WHERE org_id = 12
    UNION ALL
    SELECT c.org_id, c.org_name, t.depth + 1, CONCAT(t.path, ' > ', c.org_id)
    FROM organizations c
    JOIN tree t ON c.parent_org_id = t.org_id
    WHERE t.depth < 10
)
SELECT org_id, org_name, depth, path
FROM tree
ORDER BY path;

-- SQL-052 · Category tree with product counts rolled up to every ancestor
WITH RECURSIVE closure AS (
    SELECT category_id AS ancestor_id, category_id AS descendant_id
    FROM product_categories
    UNION ALL
    SELECT c.ancestor_id, pc.category_id
    FROM closure c
    JOIN product_categories pc ON pc.parent_category_id = c.descendant_id
)
SELECT pc.category_id,
       pc.category_name,
       COUNT(p.product_id) AS active_products_incl_descendants
FROM product_categories pc
JOIN closure c       ON c.ancestor_id = pc.category_id
LEFT JOIN products p ON p.category_id = c.descendant_id
                    AND p.is_active = TRUE
GROUP BY pc.category_id, pc.category_name
ORDER BY pc.category_id;

-- SQL-053 · Daily sign-ups with zero days filled in (date spine)
WITH RECURSIVE spine AS (
    SELECT DATE '2025-06-01' AS day
    UNION ALL
    SELECT CAST(day + INTERVAL '1' DAY AS DATE)
    FROM spine
    WHERE day < DATE '2025-06-30'
)
SELECT s.day,
       COUNT(u.user_id) AS signups
FROM spine s
LEFT JOIN users u
       ON u.signup_at >= s.day
      AND u.signup_at <  s.day + INTERVAL '1' DAY
GROUP BY s.day
ORDER BY s.day;

-- SQL-054 · Model lineage: all ancestors of a model version
WITH RECURSIVE ancestry AS (
    SELECT model_version_id, version_label, parent_version_id, trained_at, deployed_at,
           0 AS generations_back
    FROM model_versions
    WHERE model_name = 'churn_classifier' AND version_label = 'v4'
    UNION ALL
    SELECT p.model_version_id, p.version_label, p.parent_version_id, p.trained_at, p.deployed_at,
           a.generations_back + 1
    FROM model_versions p
    JOIN ancestry a ON p.model_version_id = a.parent_version_id
)
SELECT model_version_id, version_label, generations_back, trained_at, deployed_at
FROM ancestry
ORDER BY generations_back;

-- SQL-055 · Accounts with urgent tickets and recent purchases: IN vs EXISTS vs JOIN
SELECT o.org_id,
       o.org_name
FROM organizations o
WHERE EXISTS (SELECT 1 FROM support_tickets t
              WHERE t.org_id = o.org_id
                AND t.priority = 'urgent'
                AND t.created_at >= TIMESTAMP '2025-04-01 00:00:00'
                AND t.created_at <  TIMESTAMP '2025-07-01 00:00:00')
  AND EXISTS (SELECT 1 FROM orders r
              WHERE r.org_id = o.org_id
                AND r.status = 'completed'
                AND r.order_ts >= TIMESTAMP '2025-04-01 00:00:00'
                AND r.order_ts <  TIMESTAMP '2025-07-01 00:00:00')
ORDER BY o.org_id;

-- SQL-056 · Revenue by plan at time of purchase (correlated scalar lookup)
SELECT COALESCE(p.plan_name, 'no active plan') AS plan_name,
       COUNT(*)                               AS completed_orders,
       SUM(a.order_total)                     AS revenue
FROM (
    SELECT o.order_id,
           o.order_total,
           (SELECT s.subscription_id
            FROM subscriptions s
            WHERE s.org_id = o.org_id
              AND s.started_at <= o.order_ts
              AND (s.ended_at IS NULL OR o.order_ts < s.ended_at)
            ORDER BY s.started_at DESC, s.subscription_id DESC
            LIMIT 1) AS subscription_id
    FROM orders o
    WHERE o.status = 'completed'
      AND o.order_ts >= TIMESTAMP '2025-01-01 00:00:00'
      AND o.order_ts <  TIMESTAMP '2025-07-01 00:00:00'
) a
LEFT JOIN subscriptions s ON s.subscription_id = a.subscription_id
LEFT JOIN plans p         ON p.plan_id = s.plan_id
GROUP BY COALESCE(p.plan_name, 'no active plan')
ORDER BY revenue DESC, plan_name;

-- SQL-057 · Second-highest order per enterprise customer without window functions
SELECT DISTINCT o.org_id,
       o.order_total AS second_highest_order_total
FROM orders o
JOIN organizations g ON g.org_id = o.org_id
WHERE g.segment = 'Enterprise'
  AND o.status = 'completed'
  AND (SELECT COUNT(DISTINCT o2.order_total)
       FROM orders o2
       WHERE o2.org_id = o.org_id
         AND o2.status = 'completed'
         AND o2.order_total > o.order_total) = 1
ORDER BY o.org_id;

-- SQL-058 · Number each user's sessions (ROW_NUMBER)
SELECT s.user_id,
       s.session_id,
       s.started_at,
       ROW_NUMBER() OVER (PARTITION BY s.user_id
                          ORDER BY s.started_at, s.session_id) AS session_seq
FROM sessions s
JOIN users u ON u.user_id = s.user_id
WHERE u.org_id = 12
  AND s.started_at >= TIMESTAMP '2025-04-01 00:00:00'
  AND s.started_at <  TIMESTAMP '2025-07-01 00:00:00'
ORDER BY s.user_id, session_seq;

-- SQL-059 · ROW_NUMBER vs RANK vs DENSE_RANK on tied counts
SELECT p.product_name,
       COUNT(DISTINCT oi.order_id)                                                   AS orders,
       ROW_NUMBER() OVER (ORDER BY COUNT(DISTINCT oi.order_id) DESC, p.product_name) AS row_num,
       RANK()       OVER (ORDER BY COUNT(DISTINCT oi.order_id) DESC)                 AS rnk,
       DENSE_RANK() OVER (ORDER BY COUNT(DISTINCT oi.order_id) DESC)                 AS dense_rnk
FROM order_items oi
JOIN orders o   ON o.order_id = oi.order_id
JOIN products p ON p.product_id = oi.product_id
WHERE o.status = 'completed'
  AND o.order_ts >= TIMESTAMP '2025-01-01 00:00:00'
  AND o.order_ts <  TIMESTAMP '2025-07-01 00:00:00'
GROUP BY p.product_id, p.product_name
ORDER BY orders DESC, p.product_name
LIMIT 12;

-- SQL-060 · Top 2 products by revenue within each category
WITH product_revenue AS (
    SELECT pc.category_name,
           p.product_name,
           SUM(oi.quantity * oi.unit_price - oi.discount_amount) AS net_revenue
    FROM order_items oi
    JOIN orders o              ON o.order_id = oi.order_id
    JOIN products p            ON p.product_id = oi.product_id
    JOIN product_categories pc ON pc.category_id = p.category_id
    WHERE o.status = 'completed'
      AND o.order_ts >= TIMESTAMP '2025-01-01 00:00:00'
      AND o.order_ts <  TIMESTAMP '2025-07-01 00:00:00'
    GROUP BY pc.category_name, p.product_name
),
ranked AS (
    SELECT category_name,
           product_name,
           net_revenue,
           RANK() OVER (PARTITION BY category_name ORDER BY net_revenue DESC) AS rank_in_category
    FROM product_revenue
)
SELECT category_name, product_name, net_revenue, rank_in_category
FROM ranked
WHERE rank_in_category <= 2
ORDER BY category_name, rank_in_category, product_name;

-- SQL-061 · What do new buyers buy first?
WITH first_orders AS (
    SELECT order_id, user_id
    FROM (
        SELECT order_id,
               user_id,
               ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY order_ts, order_id) AS rn
        FROM orders
        WHERE status = 'completed'
    ) x
    WHERE rn = 1
)
SELECT p.product_name,
       COUNT(*) AS first_purchases
FROM first_orders f
JOIN order_items oi ON oi.order_id = f.order_id AND oi.line_number = 1
JOIN products p     ON p.product_id = oi.product_id
GROUP BY p.product_name
ORDER BY first_purchases DESC, p.product_name
LIMIT 10;

-- SQL-062 · Average time between purchases (LAG)
SELECT user_id,
       COUNT(*)                                       AS completed_orders,
       ROUND(AVG(gap_days), 1)                        AS avg_days_between_orders,
       ROUND(MAX(gap_days), 1)                        AS max_days_between_orders
FROM (
    SELECT user_id,
           EXTRACT(EPOCH FROM order_ts - LAG(order_ts) OVER (PARTITION BY user_id
                                                             ORDER BY order_ts, order_id)) / 86400 AS gap_days
    FROM orders
    WHERE status = 'completed'
) g
GROUP BY user_id
HAVING COUNT(*) >= 4
ORDER BY avg_days_between_orders, user_id;

-- SQL-063 · Running revenue total for Q1 2025
SELECT CAST(order_ts AS DATE)                                       AS order_date,
       SUM(order_total)                                             AS revenue,
       SUM(SUM(order_total)) OVER (ORDER BY CAST(order_ts AS DATE)
                                   ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS cumulative_revenue
FROM orders
WHERE status = 'completed'
  AND order_ts >= TIMESTAMP '2025-01-01 00:00:00'
  AND order_ts <  TIMESTAMP '2025-04-01 00:00:00'
GROUP BY CAST(order_ts AS DATE)
ORDER BY order_date;

-- SQL-064 · Remove duplicate events before counting
SELECT event_name,
       COUNT(*)                                  AS raw_events,
       SUM(CASE WHEN rn = 1 THEN 1 ELSE 0 END)   AS deduped_events,
       SUM(CASE WHEN rn > 1 THEN 1 ELSE 0 END)   AS duplicates
FROM (
    SELECT event_name,
           ROW_NUMBER() OVER (PARTITION BY user_id, session_id, event_name, event_ts
                              ORDER BY event_id) AS rn
    FROM events
    WHERE event_ts >= TIMESTAMP '2025-06-01 00:00:00'
      AND event_ts <  TIMESTAMP '2025-07-01 00:00:00'
) e
GROUP BY event_name
ORDER BY raw_events DESC, event_name;

-- SQL-065 · 7-day moving average of daily active users
WITH RECURSIVE spine AS (
    SELECT DATE '2025-04-01' AS day
    UNION ALL
    SELECT CAST(day + INTERVAL '1' DAY AS DATE) FROM spine WHERE day < DATE '2025-06-30'
),
daily AS (
    SELECT CAST(event_ts AS DATE) AS day, COUNT(DISTINCT user_id) AS dau
    FROM events
    WHERE event_ts >= TIMESTAMP '2025-04-01 00:00:00'
      AND event_ts <  TIMESTAMP '2025-07-01 00:00:00'
    GROUP BY CAST(event_ts AS DATE)
),
filled AS (
    SELECT s.day, COALESCE(d.dau, 0) AS dau
    FROM spine s
    LEFT JOIN daily d ON d.day = s.day
)
SELECT day,
       dau,
       COUNT(*) OVER w AS days_in_window,
       CASE WHEN COUNT(*) OVER w = 7 THEN ROUND(AVG(dau) OVER w, 2) END AS dau_7d_avg
FROM filled
WINDOW w AS (ORDER BY day ROWS BETWEEN 6 PRECEDING AND CURRENT ROW)
ORDER BY day;

-- SQL-066 · Gaps and overlaps in subscription history (LAG)
SELECT org_id, prev_subscription_id, subscription_id, prev_ended_at, started_at, relation
FROM (
    SELECT org_id,
           subscription_id,
           started_at,
           prev_subscription_id,
           prev_ended_at,
           CASE WHEN prev_ended_at IS NULL OR started_at < prev_ended_at THEN 'overlap'
                WHEN started_at > prev_ended_at THEN 'gap'
                ELSE 'contiguous'
           END AS relation
    FROM (
        SELECT org_id,
               subscription_id,
               started_at,
               LAG(subscription_id) OVER (PARTITION BY org_id ORDER BY started_at, subscription_id) AS prev_subscription_id,
               LAG(ended_at)        OVER (PARTITION BY org_id ORDER BY started_at, subscription_id) AS prev_ended_at
        FROM subscriptions
    ) w
    WHERE prev_subscription_id IS NOT NULL
) c
WHERE relation <> 'contiguous'
ORDER BY org_id, started_at;

-- SQL-067 · First and latest ticket category per account
SELECT DISTINCT
       t.org_id,
       COUNT(*)          OVER (PARTITION BY t.org_id) AS tickets,
       FIRST_VALUE(t.category) OVER (PARTITION BY t.org_id ORDER BY t.created_at, t.ticket_id
                                     ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING) AS first_category,
       LAST_VALUE(t.category)  OVER (PARTITION BY t.org_id ORDER BY t.created_at, t.ticket_id
                                     ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING) AS latest_category
FROM support_tickets t
JOIN organizations o ON o.org_id = t.org_id
WHERE o.segment = 'Enterprise'
ORDER BY t.org_id;

-- SQL-068 · Customer value deciles (NTILE)
WITH ltv AS (
    SELECT user_id, SUM(order_total) AS ltv
    FROM orders
    WHERE status = 'completed'
    GROUP BY user_id
),
bucketed AS (
    SELECT user_id, ltv,
           NTILE(10) OVER (ORDER BY ltv DESC, user_id) AS decile
    FROM ltv
)
SELECT decile,
       COUNT(*)                                                    AS buyers,
       MIN(ltv)                                                    AS min_ltv,
       MAX(ltv)                                                    AS max_ltv,
       SUM(ltv)                                                    AS revenue,
       ROUND(100.0 * SUM(ltv) / SUM(SUM(ltv)) OVER (), 1)          AS revenue_share_pct
FROM bucketed
GROUP BY decile
ORDER BY decile;

-- SQL-069 · Month-over-month revenue change
WITH monthly AS (
    SELECT CAST(DATE_TRUNC('month', order_ts) AS DATE) AS month_start,
           SUM(order_total)                            AS revenue
    FROM orders
    WHERE status = 'completed'
      AND order_ts >= TIMESTAMP '2024-01-01 00:00:00'
      AND order_ts <  TIMESTAMP '2025-07-01 00:00:00'
    GROUP BY DATE_TRUNC('month', order_ts)
)
SELECT month_start,
       revenue,
       LAG(revenue) OVER (ORDER BY month_start)                                    AS prev_month_revenue,
       ROUND(100.0 * (revenue - LAG(revenue) OVER (ORDER BY month_start))
             / NULLIF(LAG(revenue) OVER (ORDER BY month_start), 0), 1)             AS mom_change_pct
FROM monthly
ORDER BY month_start;

-- SQL-070 · Rebuild sessions from raw events (30-minute inactivity rule)
WITH ordered AS (
    SELECT user_id,
           event_ts,
           LAG(event_ts) OVER (PARTITION BY user_id ORDER BY event_ts, event_id) AS prev_ts,
           event_id
    FROM events
    WHERE event_ts >= TIMESTAMP '2025-06-01 00:00:00'
      AND event_ts <  TIMESTAMP '2025-07-01 00:00:00'
),
flagged AS (
    SELECT user_id, event_ts, event_id,
           CASE WHEN prev_ts IS NULL OR event_ts > prev_ts + INTERVAL '30' MINUTE
                THEN 1 ELSE 0 END AS new_session
    FROM ordered
),
numbered AS (
    SELECT user_id,
           SUM(new_session) OVER (PARTITION BY user_id ORDER BY event_ts, event_id
                                  ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS session_no
    FROM flagged
)
SELECT user_id,
       COUNT(*)                                       AS events,
       COUNT(DISTINCT session_no)                     AS derived_sessions,
       ROUND(1.0 * COUNT(*) / COUNT(DISTINCT session_no), 2) AS avg_events_per_session
FROM numbered
GROUP BY user_id
ORDER BY events DESC, user_id
LIMIT 10;

-- SQL-071 · Revenue share within segment and of the total
SELECT g.segment,
       g.country_code,
       SUM(o.order_total)                                                                 AS revenue,
       ROUND(100.0 * SUM(o.order_total) / SUM(SUM(o.order_total)) OVER (PARTITION BY g.segment), 1) AS pct_of_segment,
       ROUND(100.0 * SUM(o.order_total) / SUM(SUM(o.order_total)) OVER (), 1)                       AS pct_of_total
FROM orders o
JOIN organizations g ON g.org_id = o.org_id
WHERE o.status = 'completed'
  AND o.order_ts >= TIMESTAMP '2025-01-01 00:00:00'
  AND o.order_ts <  TIMESTAMP '2025-07-01 00:00:00'
GROUP BY g.segment, g.country_code
ORDER BY g.segment, revenue DESC, g.country_code;

-- SQL-072 · Cumulative CSAT done right (weighted running average)
WITH monthly AS (
    SELECT CAST(DATE_TRUNC('month', created_at) AS DATE) AS month_start,
           COUNT(csat_score)                             AS rated,
           SUM(csat_score)                               AS score_sum
    FROM support_tickets
    WHERE created_at >= TIMESTAMP '2024-01-01 00:00:00'
      AND created_at <  TIMESTAMP '2025-07-01 00:00:00'
    GROUP BY DATE_TRUNC('month', created_at)
)
SELECT month_start,
       rated,
       ROUND(1.0 * score_sum / NULLIF(rated, 0), 3)                                   AS monthly_avg,
       ROUND(AVG(1.0 * score_sum / NULLIF(rated, 0))
             OVER (ORDER BY month_start ROWS UNBOUNDED PRECEDING), 3)                  AS naive_cumulative_avg,
       ROUND(1.0 * SUM(score_sum) OVER (ORDER BY month_start ROWS UNBOUNDED PRECEDING)
             / NULLIF(SUM(rated) OVER (ORDER BY month_start ROWS UNBOUNDED PRECEDING), 0), 3) AS cumulative_avg
FROM monthly
ORDER BY month_start;

-- SQL-073 · Longest streak of consecutive active days (gaps and islands)
WITH days AS (
    SELECT DISTINCT user_id, CAST(started_at AS DATE) AS d
    FROM sessions
    WHERE started_at >= TIMESTAMP '2025-01-01 00:00:00'
      AND started_at <  TIMESTAMP '2025-07-01 00:00:00'
),
keyed AS (
    SELECT user_id, d,
           d - CAST(ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY d) AS INT) AS island
    FROM days
),
islands AS (
    SELECT user_id, island, MIN(d) AS streak_start, MAX(d) AS streak_end, COUNT(*) AS len
    FROM keyed
    GROUP BY user_id, island
),
best AS (
    SELECT user_id, len, streak_start, streak_end,
           ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY len DESC, streak_start) AS rn
    FROM islands
)
SELECT user_id, len AS longest_streak_days, streak_start, streak_end
FROM best
WHERE rn = 1
ORDER BY longest_streak_days DESC, user_id
LIMIT 10;

-- SQL-074 · What happens after a user starts checkout? (LEAD)
SELECT COALESCE(next_event, '(none)')                                 AS next_event,
       COUNT(*)                                                       AS occurrences,
       ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1)             AS pct
FROM (
    SELECT event_name,
           event_ts,
           LEAD(event_name) OVER (PARTITION BY user_id ORDER BY event_ts, event_id) AS next_event
    FROM events
) e
WHERE event_name = 'start_checkout'
  AND event_ts >= TIMESTAMP '2025-01-01 00:00:00'
  AND event_ts <  TIMESTAMP '2025-07-01 00:00:00'
GROUP BY COALESCE(next_event, '(none)')
ORDER BY occurrences DESC, next_event;

-- SQL-075 · Score trajectories with a named window
SELECT entity_id,
       CAST(predicted_at AS DATE)                                  AS predicted_date,
       CAST(score AS DECIMAL(6,4))                                 AS score,
       CAST(LAG(score) OVER w AS DECIMAL(6,4))                     AS prev_score,
       CAST(score - LAG(score) OVER w AS DECIMAL(6,4))             AS score_change,
       CAST(MAX(score) OVER (w ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS DECIMAL(6,4)) AS max_score_so_far
FROM model_predictions
WHERE entity_id IN (5, 10, 20)
  AND model_version_id IN (1, 2, 3)
  AND batch_id LIKE '%-a'
WINDOW w AS (PARTITION BY entity_id ORDER BY predicted_at)
ORDER BY entity_id, predicted_date;

-- SQL-076 · Rolling 7-day token usage: ROWS versus RANGE frames
WITH daily AS (
    SELECT CAST(requested_at AS DATE) AS usage_date,
           SUM(input_tokens + COALESCE(output_tokens, 0)) AS tokens
    FROM llm_requests
    WHERE org_id = 195
      AND requested_at >= TIMESTAMP '2025-06-01 00:00:00'
      AND requested_at <  TIMESTAMP '2025-07-01 00:00:00'
    GROUP BY CAST(requested_at AS DATE)
)
SELECT usage_date,
       tokens,
       SUM(tokens) OVER (ORDER BY usage_date ROWS BETWEEN 6 PRECEDING AND CURRENT ROW)               AS rolling_7_rows,
       SUM(tokens) OVER (ORDER BY usage_date RANGE BETWEEN INTERVAL '6 days' PRECEDING AND CURRENT ROW) AS rolling_7_days
FROM daily
ORDER BY usage_date;

-- SQL-077 · Consecutive failure streaks per pipeline
WITH final AS (
    SELECT pipeline_name, run_date, status
    FROM (
        SELECT pipeline_name, run_date, status,
               ROW_NUMBER() OVER (PARTITION BY pipeline_name, run_date ORDER BY attempt DESC) AS rn
        FROM pipeline_runs
    ) x
    WHERE rn = 1
),
failed AS (
    SELECT pipeline_name, run_date,
           run_date - CAST(ROW_NUMBER() OVER (PARTITION BY pipeline_name ORDER BY run_date) AS INT) AS island
    FROM final
    WHERE status = 'failed'
)
SELECT pipeline_name,
       MIN(run_date) AS streak_start,
       MAX(run_date) AS streak_end,
       COUNT(*)      AS failed_days
FROM failed
GROUP BY pipeline_name, island
HAVING COUNT(*) >= 3
ORDER BY pipeline_name, streak_start;

-- SQL-078 · Monthly active users and stickiness (DAU/MAU)
WITH daily AS (
    SELECT CAST(event_ts AS DATE) AS d, COUNT(DISTINCT user_id) AS dau
    FROM events
    WHERE event_ts >= TIMESTAMP '2025-01-01 00:00:00' AND event_ts < TIMESTAMP '2025-07-01 00:00:00'
    GROUP BY CAST(event_ts AS DATE)
),
monthly AS (
    SELECT CAST(DATE_TRUNC('month', event_ts) AS DATE) AS month_start, COUNT(DISTINCT user_id) AS mau
    FROM events
    WHERE event_ts >= TIMESTAMP '2025-01-01 00:00:00' AND event_ts < TIMESTAMP '2025-07-01 00:00:00'
    GROUP BY DATE_TRUNC('month', event_ts)
),
dau_by_month AS (
    SELECT CAST(DATE_TRUNC('month', d) AS DATE) AS month_start, AVG(dau) AS avg_dau
    FROM daily
    GROUP BY DATE_TRUNC('month', d)
)
SELECT m.month_start,
       m.mau,
       ROUND(d.avg_dau, 1)                     AS avg_dau,
       ROUND(100.0 * d.avg_dau / m.mau, 1)     AS stickiness_pct
FROM monthly m
JOIN dau_by_month d ON d.month_start = m.month_start
ORDER BY m.month_start;

-- SQL-079 · Monthly sign-up cohorts: retention matrix
WITH cohort AS (
    SELECT user_id,
           EXTRACT(YEAR FROM signup_at)  AS cohort_year,
           EXTRACT(MONTH FROM signup_at) AS cohort_month,
           EXTRACT(YEAR FROM signup_at) * 12 + EXTRACT(MONTH FROM signup_at) AS cohort_idx
    FROM users
    WHERE signup_at >= TIMESTAMP '2024-07-01 00:00:00'
      AND signup_at <  TIMESTAMP '2025-04-01 00:00:00'
),
activity AS (
    SELECT DISTINCT s.user_id,
           EXTRACT(YEAR FROM s.started_at) * 12 + EXTRACT(MONTH FROM s.started_at) AS act_idx
    FROM sessions s
    JOIN cohort c ON c.user_id = s.user_id
)
SELECT c.cohort_year,
       c.cohort_month,
       COUNT(DISTINCT c.user_id) AS cohort_size,
       ROUND(100.0 * COUNT(DISTINCT CASE WHEN a.act_idx - c.cohort_idx = 1 THEN c.user_id END)
             / COUNT(DISTINCT c.user_id), 1) AS m1_pct,
       ROUND(100.0 * COUNT(DISTINCT CASE WHEN a.act_idx - c.cohort_idx = 2 THEN c.user_id END)
             / COUNT(DISTINCT c.user_id), 1) AS m2_pct,
       ROUND(100.0 * COUNT(DISTINCT CASE WHEN a.act_idx - c.cohort_idx = 3 THEN c.user_id END)
             / COUNT(DISTINCT c.user_id), 1) AS m3_pct
FROM cohort c
LEFT JOIN activity a ON a.user_id = c.user_id
GROUP BY c.cohort_year, c.cohort_month
ORDER BY c.cohort_year, c.cohort_month;

-- SQL-080 · 7-day and 30-day retention of Q1-2025 sign-ups by channel
SELECT COALESCE(u.acquisition_channel, 'unknown') AS channel,
       COUNT(*) AS signups,
       ROUND(100.0 * SUM(CASE WHEN EXISTS (SELECT 1 FROM sessions s
                                          WHERE s.user_id = u.user_id
                                            AND s.started_at >= u.signup_at + INTERVAL '1' DAY
                                            AND s.started_at <  u.signup_at + INTERVAL '8' DAY)
                              THEN 1 ELSE 0 END) / COUNT(*), 1) AS retained_d1_7_pct,
       ROUND(100.0 * SUM(CASE WHEN EXISTS (SELECT 1 FROM sessions s
                                          WHERE s.user_id = u.user_id
                                            AND s.started_at >= u.signup_at + INTERVAL '1' DAY
                                            AND s.started_at <  u.signup_at + INTERVAL '31' DAY)
                              THEN 1 ELSE 0 END) / COUNT(*), 1) AS retained_d1_30_pct,
       ROUND(100.0 * SUM(CASE WHEN EXISTS (SELECT 1 FROM sessions s
                                          WHERE s.user_id = u.user_id
                                            AND s.started_at >= u.signup_at + INTERVAL '23' DAY
                                            AND s.started_at <  u.signup_at + INTERVAL '31' DAY)
                              THEN 1 ELSE 0 END) / COUNT(*), 1) AS active_d23_30_pct
FROM users u
WHERE u.signup_at >= TIMESTAMP '2025-01-01 00:00:00'
  AND u.signup_at <  TIMESTAMP '2025-04-01 00:00:00'
GROUP BY COALESCE(u.acquisition_channel, 'unknown')
ORDER BY signups DESC, channel;

-- SQL-081 · Subscription churn within 180 days by start cohort
WITH per_org AS (
    SELECT org_id,
           MIN(started_at)                                         AS first_start,
           MIN(CASE WHEN status = 'canceled' THEN ended_at END)     AS first_cancel,
           MAX(CASE WHEN ended_at IS NULL THEN 1 ELSE 0 END)        AS active_now
    FROM subscriptions
    GROUP BY org_id
)
SELECT CONCAT(EXTRACT(YEAR FROM first_start), '-Q', EXTRACT(QUARTER FROM first_start)) AS cohort_quarter,
       COUNT(*)                                                                      AS orgs,
       SUM(CASE WHEN first_cancel < first_start + INTERVAL '180' DAY THEN 1 ELSE 0 END) AS churned_180d,
       ROUND(100.0 * SUM(CASE WHEN first_cancel < first_start + INTERVAL '180' DAY THEN 1 ELSE 0 END)
             / COUNT(*), 1)                                                          AS churn_180d_pct,
       ROUND(100.0 * SUM(active_now) / COUNT(*), 1)                                  AS active_now_pct
FROM per_org
WHERE first_start >= TIMESTAMP '2024-01-01 00:00:00'
  AND first_start <  TIMESTAMP '2025-01-01 00:00:00'
GROUP BY CONCAT(EXTRACT(YEAR FROM first_start), '-Q', EXTRACT(QUARTER FROM first_start))
ORDER BY cohort_quarter;

-- SQL-082 · Ordered three-step purchase funnel
WITH s1 AS (
    SELECT user_id, MIN(event_ts) AS t1
    FROM events
    WHERE event_name = 'view_pricing'
      AND event_ts >= TIMESTAMP '2025-04-01 00:00:00'
      AND event_ts <  TIMESTAMP '2025-07-01 00:00:00'
    GROUP BY user_id
),
s2 AS (
    SELECT s1.user_id, MIN(e.event_ts) AS t2
    FROM s1
    JOIN events e ON e.user_id = s1.user_id
                 AND e.event_name = 'start_checkout'
                 AND e.event_ts >= s1.t1
                 AND e.event_ts <  s1.t1 + INTERVAL '7' DAY
    GROUP BY s1.user_id
),
s3 AS (
    SELECT s2.user_id, MIN(e.event_ts) AS t3
    FROM s2
    JOIN events e ON e.user_id = s2.user_id
                 AND e.event_name = 'purchase'
                 AND e.event_ts >= s2.t2
                 AND e.event_ts <  s2.t2 + INTERVAL '7' DAY
    GROUP BY s2.user_id
),
steps AS (
    SELECT 1 AS step_no, 'view_pricing' AS step_name, COUNT(*) AS users FROM s1
    UNION ALL
    SELECT 2, 'start_checkout', COUNT(*) FROM s2
    UNION ALL
    SELECT 3, 'purchase', COUNT(*) FROM s3
)
SELECT step_no,
       step_name,
       users,
       ROUND(100.0 * users / MAX(CASE WHEN step_no = 1 THEN users END) OVER (), 1) AS pct_of_step1,
       ROUND(100.0 * users / LAG(users) OVER (ORDER BY step_no), 1)               AS pct_of_previous
FROM steps
ORDER BY step_no;

-- SQL-083 · Checkout abandonment by customer segment
WITH first_checkout AS (
    SELECT user_id, MIN(event_ts) AS checkout_ts
    FROM events
    WHERE event_name = 'start_checkout'
      AND event_ts >= TIMESTAMP '2025-06-01 00:00:00'
      AND event_ts <  TIMESTAMP '2025-07-01 00:00:00'
    GROUP BY user_id
)
SELECT o.segment,
       COUNT(*) AS checkout_users,
       SUM(CASE WHEN NOT EXISTS (SELECT 1 FROM events p
                                 WHERE p.user_id = f.user_id
                                   AND p.event_name = 'purchase'
                                   AND p.event_ts >= f.checkout_ts
                                   AND p.event_ts <  f.checkout_ts + INTERVAL '24' HOUR)
                THEN 1 ELSE 0 END) AS abandoned_users,
       ROUND(100.0 * SUM(CASE WHEN NOT EXISTS (SELECT 1 FROM events p
                                               WHERE p.user_id = f.user_id
                                                 AND p.event_name = 'purchase'
                                                 AND p.event_ts >= f.checkout_ts
                                                 AND p.event_ts <  f.checkout_ts + INTERVAL '24' HOUR)
                              THEN 1 ELSE 0 END) / COUNT(*), 1) AS abandonment_pct
FROM first_checkout f
JOIN users u         ON u.user_id = f.user_id
JOIN organizations o ON o.org_id = u.org_id
GROUP BY o.segment
ORDER BY o.segment;

-- SQL-084 · A/B test readout with lift and a two-proportion z-test
WITH exposed AS (
    SELECT a.variant,
           a.user_id,
           CASE WHEN EXISTS (SELECT 1 FROM events e
                             WHERE e.user_id = a.user_id
                               AND e.event_name = 'purchase'
                               AND e.event_ts >= a.assigned_at
                               AND e.event_ts <  a.assigned_at + INTERVAL '14' DAY)
                THEN 1 ELSE 0 END AS converted
    FROM experiment_assignments a
    JOIN experiments x ON x.experiment_id = a.experiment_id
    WHERE x.experiment_name = 'checkout_one_page'
),
per_variant AS (
    SELECT variant, COUNT(*) AS n, SUM(converted) AS x
    FROM exposed
    GROUP BY variant
),
ctrl AS (
    SELECT n AS n_c, x AS x_c FROM per_variant WHERE variant = 'control'
)
SELECT v.variant,
       v.n                                         AS users,
       v.x                                         AS converters,
       ROUND(100.0 * v.x / v.n, 2)                 AS conversion_pct,
       CASE WHEN v.variant <> 'control' THEN
            ROUND(100.0 * ((1.0 * v.x / v.n) / (1.0 * c.x_c / c.n_c) - 1), 1) END AS lift_pct_vs_control,
       CASE WHEN v.variant <> 'control' THEN
            ROUND((1.0 * v.x / v.n - 1.0 * c.x_c / c.n_c)
                  / SQRT((1.0 * (v.x + c.x_c) / (v.n + c.n_c))
                         * (1 - 1.0 * (v.x + c.x_c) / (v.n + c.n_c))
                         * (1.0 / v.n + 1.0 / c.n_c)), 2) END                    AS z_vs_control
FROM per_variant v
CROSS JOIN ctrl c
ORDER BY v.variant;

-- SQL-085 · Heterogeneous treatment effects across segments
WITH exposed AS (
    SELECT a.variant,
           a.user_id,
           CASE WHEN EXISTS (SELECT 1 FROM events e
                             WHERE e.user_id = a.user_id
                               AND e.event_name = 'purchase'
                               AND e.event_ts >= a.assigned_at
                               AND e.event_ts <  a.assigned_at + INTERVAL '14' DAY)
                THEN 1 ELSE 0 END AS converted
    FROM experiment_assignments a
    JOIN experiments x ON x.experiment_id = a.experiment_id
    WHERE x.experiment_name = 'checkout_one_page'
)
SELECT o.segment,
       e.variant,
       COUNT(*)                                  AS users,
       SUM(e.converted)                          AS converters,
       ROUND(100.0 * SUM(e.converted) / COUNT(*), 2) AS conversion_pct
FROM exposed e
JOIN users u         ON u.user_id = e.user_id
JOIN organizations o ON o.org_id = u.org_id
GROUP BY o.segment, e.variant
ORDER BY o.segment, e.variant;

-- SQL-086 · Sample-ratio mismatch check
SELECT x.experiment_name,
       SUM(CASE WHEN a.variant = 'control' THEN 1 ELSE 0 END)   AS control_users,
       SUM(CASE WHEN a.variant = 'treatment' THEN 1 ELSE 0 END) AS treatment_users,
       ROUND(100.0 * SUM(CASE WHEN a.variant = 'control' THEN 1 ELSE 0 END) / COUNT(*), 2) AS control_share_pct,
       ROUND(  POWER(SUM(CASE WHEN a.variant = 'control' THEN 1 ELSE 0 END) - COUNT(*) / 2.0, 2) / (COUNT(*) / 2.0)
             + POWER(SUM(CASE WHEN a.variant = 'treatment' THEN 1 ELSE 0 END) - COUNT(*) / 2.0, 2) / (COUNT(*) / 2.0), 3) AS chi_square,
       CASE WHEN   POWER(SUM(CASE WHEN a.variant = 'control' THEN 1 ELSE 0 END) - COUNT(*) / 2.0, 2) / (COUNT(*) / 2.0)
                 + POWER(SUM(CASE WHEN a.variant = 'treatment' THEN 1 ELSE 0 END) - COUNT(*) / 2.0, 2) / (COUNT(*) / 2.0) > 10.83
            THEN 1 ELSE 0 END AS srm_flag
FROM experiment_assignments a
JOIN experiments x ON x.experiment_id = a.experiment_id
GROUP BY x.experiment_name
HAVING COUNT(DISTINCT a.variant) = 2
ORDER BY x.experiment_name;

-- SQL-087 · How many customers make up 80% of revenue? (Pareto)
WITH org_rev AS (
    SELECT org_id, SUM(order_total) AS revenue
    FROM orders
    WHERE status = 'completed'
    GROUP BY org_id
),
running AS (
    SELECT org_id,
           revenue,
           SUM(revenue) OVER (ORDER BY revenue DESC, org_id ROWS UNBOUNDED PRECEDING) - revenue AS revenue_before,
           SUM(revenue) OVER () AS total_revenue
    FROM org_rev
)
SELECT COUNT(*)                                                         AS paying_orgs,
       SUM(CASE WHEN revenue_before < 0.8 * total_revenue THEN 1 ELSE 0 END) AS orgs_for_80pct,
       ROUND(100.0 * SUM(CASE WHEN revenue_before < 0.8 * total_revenue THEN 1 ELSE 0 END) / COUNT(*), 1)
                                                                        AS pct_of_orgs
FROM running;

-- SQL-088 · Products bought together (market basket analysis)
WITH basket AS (
    SELECT DISTINCT oi.order_id, p.product_name
    FROM order_items oi
    JOIN orders o   ON o.order_id = oi.order_id
    JOIN products p ON p.product_id = oi.product_id
    WHERE o.status = 'completed'
),
total AS (
    SELECT COUNT(DISTINCT order_id) AS n_orders FROM basket
),
item AS (
    SELECT product_name, COUNT(*) AS item_orders FROM basket GROUP BY product_name
),
pairs AS (
    SELECT a.product_name AS product_a, b.product_name AS product_b, COUNT(*) AS pair_orders
    FROM basket a
    JOIN basket b ON b.order_id = a.order_id AND a.product_name < b.product_name
    GROUP BY a.product_name, b.product_name
    HAVING COUNT(*) >= 5
)
SELECT pr.product_a,
       pr.product_b,
       pr.pair_orders,
       ROUND(100.0 * pr.pair_orders / t.n_orders, 2)                         AS support_pct,
       ROUND(100.0 * pr.pair_orders / ia.item_orders, 1)                     AS confidence_a_to_b_pct,
       ROUND((1.0 * pr.pair_orders / ia.item_orders) / (1.0 * ib.item_orders / t.n_orders), 2) AS lift
FROM pairs pr
JOIN item ia ON ia.product_name = pr.product_a
JOIN item ib ON ib.product_name = pr.product_b
CROSS JOIN total t
ORDER BY pr.pair_orders DESC, lift DESC, pr.product_a, pr.product_b
LIMIT 10;

-- SQL-089 · Median order value per segment, portable and native
WITH ranked AS (
    SELECT g.segment,
           o.order_total,
           ROW_NUMBER() OVER (PARTITION BY g.segment ORDER BY o.order_total) AS rn,
           COUNT(*)     OVER (PARTITION BY g.segment)                        AS n
    FROM orders o
    JOIN organizations g ON g.org_id = o.org_id
    WHERE o.status = 'completed'
)
SELECT segment,
       MAX(n)                                                                        AS orders,
       ROUND((SELECT AVG(o2.order_total) FROM orders o2
              JOIN organizations g2 ON g2.org_id = o2.org_id
              WHERE o2.status = 'completed' AND g2.segment = ranked.segment), 2)     AS mean_order_value,
       ROUND(AVG(CASE WHEN rn IN (FLOOR((n + 1) / 2.0), FLOOR((n + 2) / 2.0)) THEN order_total END), 2)
                                                                                     AS median_order_value
FROM ranked
GROUP BY segment
ORDER BY segment;

-- SQL-090 · Flag unusually large orders with per-customer z-scores
WITH stats AS (
    SELECT order_id,
           org_id,
           order_total,
           COUNT(*)                   OVER (PARTITION BY org_id) AS org_orders,
           AVG(order_total)           OVER (PARTITION BY org_id) AS org_mean,
           STDDEV_SAMP(order_total)   OVER (PARTITION BY org_id) AS org_stddev
    FROM orders
    WHERE status = 'completed'
)
SELECT order_id,
       org_id,
       order_total,
       org_orders,
       ROUND(org_mean, 2)                                                          AS org_mean,
       ROUND(CAST(org_stddev AS DECIMAL(14,4)), 2)                                 AS org_stddev,
       ROUND(CAST((order_total - org_mean) / NULLIF(org_stddev, 0) AS DECIMAL(10,4)), 2) AS z_score
FROM stats
WHERE org_orders >= 10
  AND (order_total - org_mean) / NULLIF(org_stddev, 0) > 2.5
ORDER BY z_score DESC, order_id;

-- SQL-091 · Users whose activity dropped by half
SELECT user_id,
       SUM(CASE WHEN started_at <  TIMESTAMP '2025-06-03 00:00:00' THEN 1 ELSE 0 END) AS prev_28d_sessions,
       SUM(CASE WHEN started_at >= TIMESTAMP '2025-06-03 00:00:00' THEN 1 ELSE 0 END) AS last_28d_sessions,
       ROUND(100.0 * (SUM(CASE WHEN started_at >= TIMESTAMP '2025-06-03 00:00:00' THEN 1 ELSE 0 END)
                    - SUM(CASE WHEN started_at <  TIMESTAMP '2025-06-03 00:00:00' THEN 1 ELSE 0 END))
             / SUM(CASE WHEN started_at <  TIMESTAMP '2025-06-03 00:00:00' THEN 1 ELSE 0 END), 1) AS change_pct
FROM sessions
WHERE started_at >= TIMESTAMP '2025-05-06 00:00:00'
  AND started_at <  TIMESTAMP '2025-07-01 00:00:00'
GROUP BY user_id
HAVING SUM(CASE WHEN started_at < TIMESTAMP '2025-06-03 00:00:00' THEN 1 ELSE 0 END) >= 4
   AND SUM(CASE WHEN started_at >= TIMESTAMP '2025-06-03 00:00:00' THEN 1 ELSE 0 END)
       <= 0.5 * SUM(CASE WHEN started_at < TIMESTAMP '2025-06-03 00:00:00' THEN 1 ELSE 0 END)
ORDER BY change_pct, user_id;

-- SQL-092 · Rolling 28-day active users (no COUNT DISTINCT window)
WITH RECURSIVE spine AS (
    SELECT DATE '2025-06-01' AS day
    UNION ALL
    SELECT CAST(day + INTERVAL '1' DAY AS DATE) FROM spine WHERE day < DATE '2025-06-30'
),
activity AS (
    SELECT DISTINCT user_id, CAST(event_ts AS DATE) AS activity_day
    FROM events
    WHERE event_ts >= TIMESTAMP '2025-05-04 00:00:00'
      AND event_ts <  TIMESTAMP '2025-07-01 00:00:00'
)
SELECT s.day,
       COUNT(DISTINCT CASE WHEN a.activity_day = s.day THEN a.user_id END) AS dau,
       COUNT(DISTINCT a.user_id)                                          AS active_users_28d
FROM spine s
JOIN activity a
  ON a.activity_day >  CAST(s.day - INTERVAL '28' DAY AS DATE)
 AND a.activity_day <= s.day
GROUP BY s.day
ORDER BY s.day;

-- SQL-093 · Correlation between product usage and revenue
WITH sess AS (
    SELECT u.org_id, COUNT(*) AS sessions
    FROM sessions s
    JOIN users u ON u.user_id = s.user_id
    WHERE s.started_at >= TIMESTAMP '2025-01-01 00:00:00'
      AND s.started_at <  TIMESTAMP '2025-07-01 00:00:00'
    GROUP BY u.org_id
),
rev AS (
    SELECT org_id, SUM(order_total) AS revenue
    FROM orders
    WHERE status = 'completed'
      AND order_ts >= TIMESTAMP '2025-01-01 00:00:00'
      AND order_ts <  TIMESTAMP '2025-07-01 00:00:00'
    GROUP BY org_id
),
xy AS (
    SELECT o.org_id,
           1.0 * COALESCE(s.sessions, 0) AS x,
           1.0 * COALESCE(r.revenue, 0)  AS y
    FROM organizations o
    LEFT JOIN sess s ON s.org_id = o.org_id
    LEFT JOIN rev r  ON r.org_id = o.org_id
    WHERE o.is_deleted = FALSE
)
SELECT COUNT(*) AS orgs,
       ROUND((COUNT(*) * SUM(x * y) - SUM(x) * SUM(y))
             / SQRT((COUNT(*) * SUM(x * x) - SUM(x) * SUM(x))
                    * (COUNT(*) * SUM(y * y) - SUM(y) * SUM(y))), 4) AS corr_sessions_revenue
FROM xy;

-- SQL-094 · Exact versus sampled distinct-user counts
SELECT COUNT(DISTINCT user_id)                                         AS exact_users,
       COUNT(DISTINCT CASE WHEN user_id % 10 = 0 THEN user_id END)     AS sampled_users,
       10 * COUNT(DISTINCT CASE WHEN user_id % 10 = 0 THEN user_id END) AS estimated_users,
       ROUND(100.0 * (10 * COUNT(DISTINCT CASE WHEN user_id % 10 = 0 THEN user_id END)
                      - COUNT(DISTINCT user_id)) / COUNT(DISTINCT user_id), 2) AS error_pct
FROM events
WHERE event_ts >= TIMESTAMP '2025-01-01 00:00:00'
  AND event_ts <  TIMESTAMP '2025-07-01 00:00:00';

-- SQL-095 · Weekday seasonality of product usage
SELECT EXTRACT(ISODOW FROM d)  AS iso_weekday,
       COUNT(*)               AS days,
       ROUND(AVG(events), 1)  AS avg_events_per_day
FROM (
    SELECT CAST(event_ts AS DATE) AS d, COUNT(*) AS events
    FROM events
    WHERE event_ts >= TIMESTAMP '2025-01-01 00:00:00'
      AND event_ts <  TIMESTAMP '2025-07-01 00:00:00'
    GROUP BY CAST(event_ts AS DATE)
) daily
GROUP BY EXTRACT(ISODOW FROM d)
ORDER BY iso_weekday;

-- SQL-096 · Class distribution and imbalance ratio per observation date
SELECT l.observation_date,
       COUNT(*)                                                        AS labeled_rows,
       SUM(l.label_value)                                              AS positives,
       ROUND(100.0 * SUM(l.label_value) / COUNT(*), 2)                 AS positive_rate_pct,
       ROUND(1.0 * (COUNT(*) - SUM(l.label_value)) / NULLIF(SUM(l.label_value), 0), 2) AS negatives_per_positive
FROM training_labels l
JOIN ml_entities e ON e.entity_id = l.entity_id
WHERE l.label_name = 'churned_30d'
  AND l.label_value IS NOT NULL
  AND e.is_test_account = FALSE
GROUP BY l.observation_date
ORDER BY l.observation_date;

-- SQL-097 · Duplicate and conflicting training labels
SELECT entity_id,
       observation_date,
       COUNT(*)                                   AS label_rows,
       COUNT(DISTINCT label_value)                AS distinct_values,
       MAX(CASE WHEN rn = 1 THEN label_value END) AS authoritative_label
FROM (
    SELECT entity_id, observation_date, label_value,
           ROW_NUMBER() OVER (PARTITION BY entity_id, observation_date
                              ORDER BY label_available_at DESC, label_id DESC) AS rn
    FROM training_labels
    WHERE label_name = 'churned_30d'
) x
GROUP BY entity_id, observation_date
HAVING COUNT(*) > 1
ORDER BY observation_date, entity_id;

-- SQL-098 · Rebuild the churn label from raw sessions and reconcile
WITH rebuilt AS (
    SELECT e.entity_id,
           CASE WHEN SUM(CASE WHEN s.started_at >= TIMESTAMP '2025-03-01 00:00:00'
                               AND s.started_at <  TIMESTAMP '2025-03-01 00:00:00' + INTERVAL '30' DAY
                              THEN 1 ELSE 0 END) = 0 THEN 1 ELSE 0 END AS label_value
    FROM ml_entities e
    JOIN sessions s ON s.user_id = e.user_id
    WHERE e.registered_at <= TIMESTAMP '2025-03-01 00:00:00'
    GROUP BY e.entity_id
    HAVING SUM(CASE WHEN s.started_at >= TIMESTAMP '2025-03-01 00:00:00' - INTERVAL '30' DAY
                     AND s.started_at <  TIMESTAMP '2025-03-01 00:00:00'
                    THEN 1 ELSE 0 END) >= 2
),
stored_labels AS (
    SELECT entity_id, label_value
    FROM (
        SELECT entity_id, label_value,
               ROW_NUMBER() OVER (PARTITION BY entity_id ORDER BY label_available_at DESC, label_id DESC) AS rn
        FROM training_labels
        WHERE label_name = 'churned_30d'
          AND observation_date = DATE '2025-03-01'
    ) x
    WHERE rn = 1
)
SELECT (SELECT COUNT(*) FROM rebuilt)                                              AS rebuilt_examples,
       (SELECT COUNT(*) FROM stored_labels)                                               AS stored_examples,
       (SELECT COUNT(*) FROM rebuilt r JOIN stored_labels s ON s.entity_id = r.entity_id
         WHERE s.label_value = r.label_value)                                      AS matching,
       (SELECT COUNT(*) FROM rebuilt r JOIN stored_labels s ON s.entity_id = r.entity_id
         WHERE s.label_value <> r.label_value OR s.label_value IS NULL)            AS value_mismatch,
       (SELECT COUNT(*) FROM rebuilt r
         WHERE NOT EXISTS (SELECT 1 FROM stored_labels s WHERE s.entity_id = r.entity_id)) AS only_in_rebuilt,
       (SELECT COUNT(*) FROM stored_labels s
         WHERE NOT EXISTS (SELECT 1 FROM rebuilt r WHERE r.entity_id = s.entity_id)) AS only_in_stored;

-- SQL-099 · Point-in-time-correct training set
WITH labels AS (
    SELECT entity_id, label_value
    FROM (
        SELECT l.entity_id, l.label_value,
               ROW_NUMBER() OVER (PARTITION BY l.entity_id
                                  ORDER BY l.label_available_at DESC, l.label_id DESC) AS rn
        FROM training_labels l
        WHERE l.label_name = 'churned_30d'
          AND l.observation_date = DATE '2025-03-01'
    ) x
    WHERE rn = 1 AND label_value IS NOT NULL
),
available AS (
    SELECT f.entity_id, f.as_of_ts, f.sessions_28d, f.days_since_last_session,
           f.open_tickets, f.avg_session_minutes,
           ROW_NUMBER() OVER (PARTITION BY f.entity_id ORDER BY f.as_of_ts DESC) AS rn
    FROM entity_features f
    WHERE f.as_of_ts    <= TIMESTAMP '2025-03-01 00:00:00'
      AND f.ingested_at <= TIMESTAMP '2025-03-01 00:00:00'
)
SELECT l.entity_id,
       l.label_value,
       a.as_of_ts                                    AS feature_as_of_ts,
       a.sessions_28d,
       a.days_since_last_session,
       a.open_tickets,
       CAST(a.avg_session_minutes AS DECIMAL(10,2))  AS avg_session_minutes
FROM labels l
JOIN ml_entities e ON e.entity_id = l.entity_id AND e.is_test_account = FALSE
LEFT JOIN available a ON a.entity_id = l.entity_id AND a.rn = 1
ORDER BY l.entity_id;

-- SQL-100 · Leakage audit: naive versus point-in-time feature joins
WITH examples AS (
    SELECT DISTINCT l.entity_id, l.observation_date
    FROM training_labels l
    JOIN ml_entities e ON e.entity_id = l.entity_id
    WHERE l.label_name = 'churned_30d'
      AND l.label_value IS NOT NULL
      AND e.is_test_account = FALSE
),
chosen AS (
    SELECT x.entity_id,
           x.observation_date,
           MAX(f.as_of_ts)                                                    AS naive_ts,
           MAX(CASE WHEN f.ingested_at <= x.observation_date THEN f.as_of_ts END) AS pit_ts
    FROM examples x
    LEFT JOIN entity_features f
           ON f.entity_id = x.entity_id
          AND f.as_of_ts <= x.observation_date
    GROUP BY x.entity_id, x.observation_date
)
SELECT observation_date,
       COUNT(*) AS examples,
       SUM(CASE WHEN naive_ts IS NOT NULL AND (pit_ts IS NULL OR naive_ts <> pit_ts) THEN 1 ELSE 0 END)
           AS naive_uses_unavailable_snapshot,
       SUM(CASE WHEN pit_ts IS NULL THEN 1 ELSE 0 END) AS no_available_snapshot,
       ROUND(100.0 * SUM(CASE WHEN naive_ts IS NOT NULL AND (pit_ts IS NULL OR naive_ts <> pit_ts) THEN 1 ELSE 0 END)
             / COUNT(*), 1) AS pct_leaky
FROM chosen
GROUP BY observation_date
ORDER BY observation_date;

-- SQL-101 · How future features fake model quality
WITH labels AS (
    SELECT entity_id, label_value
    FROM (
        SELECT l.entity_id, l.label_value,
               ROW_NUMBER() OVER (PARTITION BY l.entity_id ORDER BY l.label_available_at DESC, l.label_id DESC) AS rn
        FROM training_labels l
        WHERE l.label_name = 'churned_30d' AND l.observation_date = DATE '2025-04-01'
    ) x
    JOIN ml_entities e USING (entity_id)
    WHERE x.rn = 1 AND x.label_value IS NOT NULL AND e.is_test_account = FALSE
),
snap AS (
    SELECT l.entity_id,
           l.label_value,
           MAX(CASE WHEN f.as_of_ts <= TIMESTAMP '2025-04-01 00:00:00'
                     AND f.ingested_at <= TIMESTAMP '2025-04-01 00:00:00' THEN f.as_of_ts END) AS pit_ts,
           MAX(f.as_of_ts) AS latest_ts
    FROM labels l
    JOIN entity_features f ON f.entity_id = l.entity_id
    GROUP BY l.entity_id, l.label_value
),
both_joins AS (
    SELECT 'point_in_time' AS feature_join, s.label_value, f.days_since_last_session
    FROM snap s JOIN entity_features f ON f.entity_id = s.entity_id AND f.as_of_ts = s.pit_ts
    UNION ALL
    SELECT 'latest_in_table', s.label_value, f.days_since_last_session
    FROM snap s JOIN entity_features f ON f.entity_id = s.entity_id AND f.as_of_ts = s.latest_ts
)
SELECT feature_join,
       ROUND(AVG(CASE WHEN label_value = 1 THEN days_since_last_session END), 1) AS churned_avg_days_since_session,
       ROUND(AVG(CASE WHEN label_value = 0 THEN days_since_last_session END), 1) AS retained_avg_days_since_session,
       ROUND(AVG(CASE WHEN label_value = 1 THEN days_since_last_session END)
             / AVG(CASE WHEN label_value = 0 THEN days_since_last_session END), 2) AS separation_ratio
FROM both_joins
GROUP BY feature_join
ORDER BY feature_join;

-- SQL-102 · Time-based train / validation / test split
WITH labels AS (
    SELECT x.entity_id, x.observation_date, x.label_value
    FROM (
        SELECT l.entity_id, l.observation_date, l.label_value,
               ROW_NUMBER() OVER (PARTITION BY l.entity_id, l.observation_date
                                  ORDER BY l.label_available_at DESC, l.label_id DESC) AS rn
        FROM training_labels l
        WHERE l.label_name = 'churned_30d'
    ) x
    JOIN ml_entities e ON e.entity_id = x.entity_id
    WHERE x.rn = 1 AND x.label_value IS NOT NULL AND e.is_test_account = FALSE
),
split AS (
    SELECT entity_id, observation_date, label_value,
           CASE WHEN observation_date <= DATE '2025-02-01' THEN 'train'
                WHEN observation_date <= DATE '2025-04-01' THEN 'validation'
                ELSE 'test' END AS split
    FROM labels
)
SELECT s.split,
       MIN(s.observation_date)                     AS first_obs,
       MAX(s.observation_date)                     AS last_obs,
       COUNT(*)                                    AS examples,
       SUM(s.label_value)                          AS positives,
       ROUND(100.0 * SUM(s.label_value) / COUNT(*), 2) AS positive_rate_pct,
       CASE WHEN s.split = 'train' THEN NULL
            ELSE COUNT(DISTINCT CASE WHEN EXISTS (SELECT 1 FROM split t
                                                  WHERE t.split = 'train' AND t.entity_id = s.entity_id)
                                     THEN s.entity_id END)
       END                                         AS entities_also_in_train
FROM split s
GROUP BY s.split
ORDER BY first_obs;

-- SQL-103 · Feature missingness by snapshot date and source
SELECT CAST(as_of_ts AS DATE)                                              AS as_of_date,
       feature_source,
       COUNT(*)                                                            AS rows_count,
       ROUND(100.0 * (COUNT(*) - COUNT(sessions_7d)) / COUNT(*), 2)        AS null_sessions_7d_pct,
       ROUND(100.0 * (COUNT(*) - COUNT(events_28d)) / COUNT(*), 2)         AS null_events_28d_pct,
       ROUND(100.0 * (COUNT(*) - COUNT(avg_session_minutes)) / COUNT(*), 2) AS null_avg_minutes_pct,
       ROUND(100.0 * (COUNT(*) - COUNT(seats_used_pct)) / COUNT(*), 2)     AS null_seats_used_pct,
       ROUND(100.0 * (COUNT(*) - COUNT(days_since_last_session)) / COUNT(*), 2) AS null_days_since_pct
FROM entity_features
WHERE as_of_ts >= TIMESTAMP '2025-01-01 00:00:00'
  AND as_of_ts <  TIMESTAMP '2025-04-01 00:00:00'
GROUP BY CAST(as_of_ts AS DATE), feature_source
ORDER BY as_of_date, feature_source;

-- SQL-104 · Entities with incomplete features in the latest snapshot
SELECT 'missing_row' AS reason, COUNT(*) AS entities
FROM ml_entities e
WHERE e.is_test_account = FALSE
  AND e.registered_at < TIMESTAMP '2025-06-30 00:00:00'
  AND NOT EXISTS (SELECT 1 FROM entity_features f
                  WHERE f.entity_id = e.entity_id
                    AND f.as_of_ts = TIMESTAMP '2025-06-30 00:00:00')
UNION ALL
SELECT 'null_required_feature', COUNT(*)
FROM ml_entities e
JOIN entity_features f ON f.entity_id = e.entity_id
                      AND f.as_of_ts = TIMESTAMP '2025-06-30 00:00:00'
WHERE e.is_test_account = FALSE
  AND e.registered_at < TIMESTAMP '2025-06-30 00:00:00'
  AND (f.sessions_7d IS NULL OR f.sessions_28d IS NULL OR f.events_28d IS NULL
       OR f.open_tickets IS NULL OR f.seats_used_pct IS NULL)
ORDER BY reason;

-- SQL-105 · Validate stored features by recomputing them from raw sessions
WITH recomputed AS (
    SELECT f.entity_id,
           e.is_test_account,
           f.sessions_7d,
           f.sessions_28d,
           SUM(CASE WHEN s.started_at >= f.as_of_ts - INTERVAL '7' DAY THEN 1 ELSE 0 END) AS calc_7d,
           COUNT(s.user_id)                                                           AS calc_28d
    FROM entity_features f
    JOIN ml_entities e ON e.entity_id = f.entity_id
    LEFT JOIN sessions s
           ON s.user_id = e.user_id
          AND s.started_at >= f.as_of_ts - INTERVAL '28' DAY
          AND s.started_at <  f.as_of_ts
    WHERE f.as_of_ts = TIMESTAMP '2025-06-16 00:00:00'
    GROUP BY f.entity_id, e.is_test_account, f.sessions_7d, f.sessions_28d
)
SELECT is_test_account,
       COUNT(*) AS rows_checked,
       SUM(CASE WHEN sessions_7d = calc_7d AND sessions_28d = calc_28d THEN 1 ELSE 0 END) AS both_match,
       SUM(CASE WHEN sessions_7d IS NOT NULL AND sessions_28d IS NOT NULL
                 AND (sessions_7d <> calc_7d OR sessions_28d <> calc_28d) THEN 1 ELSE 0 END) AS mismatch,
       SUM(CASE WHEN sessions_7d IS NULL OR sessions_28d IS NULL THEN 1 ELSE 0 END)      AS stored_null
FROM recomputed
GROUP BY is_test_account
ORDER BY is_test_account;

-- SQL-106 · Latest valid prediction per entity
SELECT entity_id, prediction_id, predicted_at, CAST(score AS DECIMAL(6,4)) AS score, predicted_label
FROM (
    SELECT p.entity_id, p.prediction_id, p.predicted_at, p.score, p.predicted_label,
           ROW_NUMBER() OVER (PARTITION BY p.entity_id
                              ORDER BY p.predicted_at DESC, p.prediction_id DESC) AS rn
    FROM model_predictions p
    JOIN model_versions v ON v.model_version_id = p.model_version_id
    WHERE v.model_name = 'churn_classifier'
      AND v.stage = 'production'
      AND p.score IS NOT NULL
) ranked
WHERE rn = 1
ORDER BY entity_id;

-- SQL-107 · Precision, recall, accuracy and F1 per model version
WITH labels AS (
    SELECT x.entity_id, x.observation_date, x.label_value
    FROM (
        SELECT l.entity_id, l.observation_date, l.label_value,
               ROW_NUMBER() OVER (PARTITION BY l.entity_id, l.observation_date
                                  ORDER BY l.label_available_at DESC, l.label_id DESC) AS rn
        FROM training_labels l
        WHERE l.label_name = 'churned_30d'
    ) x
    JOIN ml_entities e ON e.entity_id = x.entity_id
    WHERE x.rn = 1 AND x.label_value IS NOT NULL AND e.is_test_account = FALSE
),
preds AS (
    SELECT model_version_id, entity_id, pred_date, predicted_label
    FROM (
        SELECT p.model_version_id, p.entity_id, CAST(p.predicted_at AS DATE) AS pred_date, p.predicted_label,
               ROW_NUMBER() OVER (PARTITION BY p.model_version_id, p.entity_id, CAST(p.predicted_at AS DATE)
                                  ORDER BY p.predicted_at DESC, p.prediction_id DESC) AS rn
        FROM model_predictions p
        WHERE p.score IS NOT NULL
    ) y
    WHERE rn = 1
),
cm AS (
    SELECT v.version_label,
           COUNT(*)                                                                    AS examples,
           SUM(CASE WHEN p.predicted_label = 1 AND l.label_value = 1 THEN 1 ELSE 0 END) AS tp,
           SUM(CASE WHEN p.predicted_label = 1 AND l.label_value = 0 THEN 1 ELSE 0 END) AS fp,
           SUM(CASE WHEN p.predicted_label = 0 AND l.label_value = 1 THEN 1 ELSE 0 END) AS fn,
           SUM(CASE WHEN p.predicted_label = 0 AND l.label_value = 0 THEN 1 ELSE 0 END) AS tn
    FROM preds p
    JOIN labels l         ON l.entity_id = p.entity_id AND l.observation_date = p.pred_date
    JOIN model_versions v ON v.model_version_id = p.model_version_id
    WHERE v.model_name = 'churn_classifier'
    GROUP BY v.version_label
)
SELECT version_label, examples, tp, fp, fn, tn,
       ROUND(100.0 * tp / NULLIF(tp + fp, 0), 1)                AS precision_pct,
       ROUND(100.0 * tp / NULLIF(tp + fn, 0), 1)                AS recall_pct,
       ROUND(100.0 * (tp + tn) / NULLIF(examples, 0), 1)         AS accuracy_pct,
       ROUND(2.0 * tp / NULLIF(2 * tp + fp + fn, 0), 3)          AS f1
FROM cm
ORDER BY version_label;

-- SQL-108 · Paired comparison: production v3 versus shadow v4
WITH labels AS (
    SELECT entity_id, label_value
    FROM (
        SELECT l.entity_id, l.label_value,
               ROW_NUMBER() OVER (PARTITION BY l.entity_id ORDER BY l.label_available_at DESC, l.label_id DESC) AS rn
        FROM training_labels l
        WHERE l.label_name = 'churned_30d' AND l.observation_date = DATE '2025-05-01'
    ) x
    JOIN ml_entities e USING (entity_id)
    WHERE x.rn = 1 AND x.label_value IS NOT NULL AND e.is_test_account = FALSE
),
latest AS (
    SELECT model_version_id, entity_id, predicted_label, threshold
    FROM (
        SELECT p.model_version_id, p.entity_id, p.predicted_label, p.threshold,
               ROW_NUMBER() OVER (PARTITION BY p.model_version_id, p.entity_id
                                  ORDER BY p.predicted_at DESC, p.prediction_id DESC) AS rn
        FROM model_predictions p
        WHERE p.model_version_id IN (3, 4)
          AND p.score IS NOT NULL
          AND p.predicted_at >= TIMESTAMP '2025-05-01 00:00:00'
          AND p.predicted_at <  TIMESTAMP '2025-05-02 00:00:00'
    ) y
    WHERE rn = 1
),
paired AS (
    SELECT l.entity_id, l.label_value,
           a.predicted_label AS pred_v3, a.threshold AS thr_v3,
           b.predicted_label AS pred_v4, b.threshold AS thr_v4
    FROM labels l
    JOIN latest a ON a.entity_id = l.entity_id AND a.model_version_id = 3
    JOIN latest b ON b.entity_id = l.entity_id AND b.model_version_id = 4
),
long_form AS (
    SELECT 'v3' AS version_label, thr_v3 AS threshold, pred_v3 AS pred, label_value,
           CASE WHEN pred_v3 = pred_v4 THEN 1 ELSE 0 END AS agree
    FROM paired
    UNION ALL
    SELECT 'v4', thr_v4, pred_v4, label_value,
           CASE WHEN pred_v3 = pred_v4 THEN 1 ELSE 0 END
    FROM paired
)
SELECT version_label,
       MAX(threshold)                                                                       AS threshold,
       COUNT(*)                                                                             AS examples,
       ROUND(100.0 * SUM(CASE WHEN pred = 1 AND label_value = 1 THEN 1 ELSE 0 END)
             / NULLIF(SUM(CASE WHEN pred = 1 THEN 1 ELSE 0 END), 0), 1)                     AS precision_pct,
       ROUND(100.0 * SUM(CASE WHEN pred = 1 AND label_value = 1 THEN 1 ELSE 0 END)
             / NULLIF(SUM(label_value), 0), 1)                                              AS recall_pct,
       ROUND(2.0 * SUM(CASE WHEN pred = 1 AND label_value = 1 THEN 1 ELSE 0 END)
             / NULLIF(SUM(CASE WHEN pred = 1 THEN 1 ELSE 0 END) + SUM(label_value), 0), 3)  AS f1,
       ROUND(100.0 * SUM(agree) / COUNT(*), 1)                                              AS agreement_pct
FROM long_form
GROUP BY version_label
ORDER BY version_label;

-- SQL-109 · Precision and recall across a threshold sweep
WITH labels AS (
    SELECT x.entity_id, x.observation_date, x.label_value
    FROM (
        SELECT l.entity_id, l.observation_date, l.label_value,
               ROW_NUMBER() OVER (PARTITION BY l.entity_id, l.observation_date
                                  ORDER BY l.label_available_at DESC, l.label_id DESC) AS rn
        FROM training_labels l
        WHERE l.label_name = 'churned_30d'
    ) x
    JOIN ml_entities e ON e.entity_id = x.entity_id
    WHERE x.rn = 1 AND x.label_value IS NOT NULL AND e.is_test_account = FALSE
),
scored AS (
    SELECT entity_id, pred_date, score
    FROM (
        SELECT p.entity_id, CAST(p.predicted_at AS DATE) AS pred_date, p.score,
               ROW_NUMBER() OVER (PARTITION BY p.entity_id, CAST(p.predicted_at AS DATE)
                                  ORDER BY p.predicted_at DESC, p.prediction_id DESC) AS rn
        FROM model_predictions p
        WHERE p.model_version_id = 3 AND p.score IS NOT NULL
    ) y
    WHERE rn = 1
),
evalset AS (
    SELECT s.score, l.label_value
    FROM scored s
    JOIN labels l ON l.entity_id = s.entity_id AND l.observation_date = s.pred_date
),
thresholds AS (
    SELECT 0.20 AS threshold UNION ALL SELECT 0.30 UNION ALL SELECT 0.40
    UNION ALL SELECT 0.50 UNION ALL SELECT 0.60 UNION ALL SELECT 0.70
)
SELECT t.threshold,
       ROUND(100.0 * SUM(CASE WHEN e.score >= t.threshold THEN 1 ELSE 0 END) / COUNT(*), 1) AS flagged_pct,
       ROUND(100.0 * SUM(CASE WHEN e.score >= t.threshold AND e.label_value = 1 THEN 1 ELSE 0 END)
             / NULLIF(SUM(CASE WHEN e.score >= t.threshold THEN 1 ELSE 0 END), 0), 1)        AS precision_pct,
       ROUND(100.0 * SUM(CASE WHEN e.score >= t.threshold AND e.label_value = 1 THEN 1 ELSE 0 END)
             / NULLIF(SUM(e.label_value), 0), 1)                                             AS recall_pct,
       ROUND(2.0 * SUM(CASE WHEN e.score >= t.threshold AND e.label_value = 1 THEN 1 ELSE 0 END)
             / NULLIF(SUM(CASE WHEN e.score >= t.threshold THEN 1 ELSE 0 END) + SUM(e.label_value), 0), 3) AS f1
FROM evalset e
CROSS JOIN thresholds t
GROUP BY t.threshold
ORDER BY t.threshold;

-- SQL-110 · Score distribution drift with the Population Stability Index
WITH scores AS (
    SELECT batch_id, LEAST(FLOOR(score * 10), 9) AS bucket
    FROM model_predictions
    WHERE model_version_id = 3
      AND score IS NOT NULL
      AND batch_id IN ('churn-2025-05-01-a', 'churn-2025-06-01-a')
),
counts AS (
    SELECT bucket,
           SUM(CASE WHEN batch_id = 'churn-2025-05-01-a' THEN 1 ELSE 0 END) AS n_may,
           SUM(CASE WHEN batch_id = 'churn-2025-06-01-a' THEN 1 ELSE 0 END) AS n_june
    FROM scores
    GROUP BY bucket
),
shares AS (
    SELECT bucket,
           GREATEST(1.0 * n_may  / SUM(n_may)  OVER (), 0.0001) AS p_may,
           GREATEST(1.0 * n_june / SUM(n_june) OVER (), 0.0001) AS p_june
    FROM counts
)
SELECT bucket,
       ROUND(100 * p_may, 2)                                   AS may_pct,
       ROUND(100 * p_june, 2)                                  AS june_pct,
       ROUND((p_june - p_may) * LN(p_june / p_may), 4)          AS psi_contribution,
       ROUND(SUM((p_june - p_may) * LN(p_june / p_may)) OVER (), 4) AS psi_total
FROM shares
ORDER BY bucket;

-- SQL-111 · Build the batch-inference input for the next run
WITH eligible AS (
    SELECT e.entity_id
    FROM ml_entities e
    JOIN sessions s ON s.user_id = e.user_id
    WHERE e.is_test_account = FALSE
      AND e.registered_at <= TIMESTAMP '2025-07-01 00:00:00'
      AND s.started_at >= TIMESTAMP '2025-06-01 00:00:00'
      AND s.started_at <  TIMESTAMP '2025-07-01 00:00:00'
    GROUP BY e.entity_id
    HAVING COUNT(*) >= 2
),
available AS (
    SELECT f.*,
           ROW_NUMBER() OVER (PARTITION BY f.entity_id ORDER BY f.as_of_ts DESC) AS rn
    FROM entity_features f
    WHERE f.ingested_at <= TIMESTAMP '2025-07-01 02:00:00'
)
SELECT el.entity_id,
       a.as_of_ts                                    AS feature_as_of_ts,
       a.sessions_28d,
       a.days_since_last_session,
       a.open_tickets,
       CAST(a.avg_session_minutes AS DECIMAL(10,2))  AS avg_session_minutes,
       CAST(a.seats_used_pct AS DECIMAL(10,3))       AS seats_used_pct
FROM eligible el
LEFT JOIN available a ON a.entity_id = el.entity_id AND a.rn = 1
ORDER BY el.entity_id;

-- SQL-112 · Stale features at scoring time and delayed labels
WITH runs AS (
    SELECT CAST(predicted_at AS DATE)                                                       AS run_date,
           COUNT(*)                                                                         AS predictions,
           SUM(CASE WHEN feature_as_of_ts < predicted_at - INTERVAL '14' DAY THEN 1 ELSE 0 END) AS stale_feature_predictions,
           SUM(CASE WHEN feature_as_of_ts IS NULL THEN 1 ELSE 0 END)                        AS unlogged_feature_snapshot
    FROM model_predictions
    WHERE model_version_id IN (1, 2, 3)
      AND batch_id LIKE 'churn-%-a'
    GROUP BY CAST(predicted_at AS DATE)
),
lab AS (
    SELECT observation_date,
           COUNT(*) AS labels,
           SUM(CASE WHEN label_available_at > observation_date + INTERVAL '33' DAY THEN 1 ELSE 0 END) AS delayed_labels
    FROM (
        SELECT l.*,
               ROW_NUMBER() OVER (PARTITION BY entity_id, observation_date
                                  ORDER BY label_available_at DESC, label_id DESC) AS rn
        FROM training_labels l
        WHERE label_name = 'churned_30d'
    ) x
    WHERE rn = 1 AND label_value IS NOT NULL
    GROUP BY observation_date
)
SELECT r.run_date,
       r.predictions,
       r.stale_feature_predictions,
       r.unlogged_feature_snapshot,
       COALESCE(l.labels, 0)         AS labels,
       COALESCE(l.delayed_labels, 0) AS delayed_labels
FROM runs r
LEFT JOIN lab l ON l.observation_date = r.run_date
ORDER BY r.run_date;

-- SQL-113 · Features that changed after the prediction was made
SELECT p.batch_id,
       COUNT(*) AS predictions,
       SUM(CASE WHEN f.ingested_at > p.predicted_at THEN 1 ELSE 0 END) AS logged_snapshot_not_yet_ingested,
       SUM(CASE WHEN EXISTS (SELECT 1 FROM entity_features n
                             WHERE n.entity_id = p.entity_id
                               AND n.as_of_ts > COALESCE(p.feature_as_of_ts, TIMESTAMP '1900-01-01 00:00:00')
                               AND n.as_of_ts <= p.predicted_at
                               AND n.ingested_at > p.predicted_at)
                THEN 1 ELSE 0 END) AS newer_snapshot_arrived_later
FROM model_predictions p
LEFT JOIN entity_features f
       ON f.entity_id = p.entity_id
      AND f.as_of_ts = p.feature_as_of_ts
WHERE p.model_version_id IN (1, 2, 3, 4)
GROUP BY p.batch_id
ORDER BY p.batch_id;

-- SQL-114 · ROC AUC in SQL with the rank-sum formula
WITH labels AS (
    SELECT x.entity_id, x.observation_date, x.label_value
    FROM (
        SELECT l.entity_id, l.observation_date, l.label_value,
               ROW_NUMBER() OVER (PARTITION BY l.entity_id, l.observation_date
                                  ORDER BY l.label_available_at DESC, l.label_id DESC) AS rn
        FROM training_labels l
        WHERE l.label_name = 'churned_30d'
    ) x
    JOIN ml_entities e ON e.entity_id = x.entity_id
    WHERE x.rn = 1 AND x.label_value IS NOT NULL AND e.is_test_account = FALSE
),
preds AS (
    SELECT model_version_id, entity_id, pred_date, score
    FROM (
        SELECT p.model_version_id, p.entity_id, CAST(p.predicted_at AS DATE) AS pred_date, p.score,
               ROW_NUMBER() OVER (PARTITION BY p.model_version_id, p.entity_id, CAST(p.predicted_at AS DATE)
                                  ORDER BY p.predicted_at DESC, p.prediction_id DESC) AS rn
        FROM model_predictions p
        WHERE p.score IS NOT NULL
    ) y
    WHERE rn = 1
),
ranked AS (
    SELECT v.version_label,
           l.label_value,
           RANK() OVER (PARTITION BY v.version_label ORDER BY p.score)
             + (COUNT(*) OVER (PARTITION BY v.version_label, p.score) - 1) / 2.0 AS avg_rank
    FROM preds p
    JOIN labels l         ON l.entity_id = p.entity_id AND l.observation_date = p.pred_date
    JOIN model_versions v ON v.model_version_id = p.model_version_id
    WHERE v.model_name = 'churn_classifier'
)
SELECT version_label,
       SUM(label_value)                    AS positives,
       COUNT(*) - SUM(label_value)         AS negatives,
       ROUND((SUM(CASE WHEN label_value = 1 THEN avg_rank ELSE 0 END)
              - SUM(label_value) * (SUM(label_value) + 1) / 2.0)
             / NULLIF(SUM(label_value) * (COUNT(*) - SUM(label_value)), 0), 4) AS auc
FROM ranked
GROUP BY version_label
ORDER BY version_label;

-- SQL-115 · Offline test metrics versus production performance
WITH labels AS (
    SELECT x.entity_id, x.observation_date, x.label_value
    FROM (
        SELECT l.entity_id, l.observation_date, l.label_value,
               ROW_NUMBER() OVER (PARTITION BY l.entity_id, l.observation_date
                                  ORDER BY l.label_available_at DESC, l.label_id DESC) AS rn
        FROM training_labels l
        WHERE l.label_name = 'churned_30d'
    ) x
    JOIN ml_entities e ON e.entity_id = x.entity_id
    WHERE x.rn = 1 AND x.label_value IS NOT NULL AND e.is_test_account = FALSE
),
preds AS (
    SELECT model_version_id, entity_id, pred_date, predicted_label
    FROM (
        SELECT p.model_version_id, p.entity_id, CAST(p.predicted_at AS DATE) AS pred_date, p.predicted_label,
               ROW_NUMBER() OVER (PARTITION BY p.model_version_id, p.entity_id, CAST(p.predicted_at AS DATE)
                                  ORDER BY p.predicted_at DESC, p.prediction_id DESC) AS rn
        FROM model_predictions p
        WHERE p.score IS NOT NULL AND p.model_version_id IN (1, 2, 3)
    ) y
    WHERE rn = 1
),
cm AS (
    SELECT p.model_version_id,
           SUM(CASE WHEN p.predicted_label = 1 AND l.label_value = 1 THEN 1 ELSE 0 END) AS tp,
           SUM(CASE WHEN p.predicted_label = 1 AND l.label_value = 0 THEN 1 ELSE 0 END) AS fp,
           SUM(CASE WHEN p.predicted_label = 0 AND l.label_value = 1 THEN 1 ELSE 0 END) AS fn
    FROM preds p
    JOIN labels l ON l.entity_id = p.entity_id AND l.observation_date = p.pred_date
    GROUP BY p.model_version_id
),
online AS (
    SELECT model_version_id, 'precision' AS metric_name, 1.0 * tp / NULLIF(tp + fp, 0) AS online FROM cm
    UNION ALL
    SELECT model_version_id, 'recall', 1.0 * tp / NULLIF(tp + fn, 0) FROM cm
    UNION ALL
    SELECT model_version_id, 'f1', 2.0 * tp / NULLIF(2 * tp + fp + fn, 0) FROM cm
)
SELECT v.version_label,
       o.metric_name,
       ROUND(CAST(ev.metric_value AS DECIMAL(10,4)), 3)            AS offline_test,
       ROUND(o.online, 3)                                          AS online,
       ROUND(o.online - CAST(ev.metric_value AS DECIMAL(10,4)), 3) AS gap
FROM online o
JOIN model_versions v     ON v.model_version_id = o.model_version_id
JOIN model_evaluations ev ON ev.model_version_id = o.model_version_id
                         AND ev.metric_name = o.metric_name
                         AND ev.eval_split = 'test'
ORDER BY v.version_label, o.metric_name;

-- SQL-116 · Daily LLM request volume by feature
SELECT CAST(requested_at AS DATE)                                  AS request_date,
       SUM(CASE WHEN feature = 'support_bot' THEN 1 ELSE 0 END)    AS support_bot,
       SUM(CASE WHEN feature = 'sql_copilot' THEN 1 ELSE 0 END)    AS sql_copilot,
       SUM(CASE WHEN feature = 'doc_summary' THEN 1 ELSE 0 END)    AS doc_summary,
       COUNT(*)                                                    AS total
FROM llm_requests
WHERE requested_at >= TIMESTAMP '2025-06-17 00:00:00'
  AND requested_at <  TIMESTAMP '2025-07-01 00:00:00'
GROUP BY CAST(requested_at AS DATE)
ORDER BY request_date;

-- SQL-117 · p50 / p95 / p99 latency per model
WITH ranked AS (
    SELECT model_name,
           latency_ms,
           ROW_NUMBER() OVER (PARTITION BY model_name ORDER BY latency_ms) AS rn,
           COUNT(*)     OVER (PARTITION BY model_name)                     AS n
    FROM llm_requests
    WHERE status = 'success'
      AND cache_hit = FALSE
      AND requested_at >= TIMESTAMP '2025-04-01 00:00:00'
      AND requested_at <  TIMESTAMP '2025-07-01 00:00:00'
)
SELECT model_name,
       MAX(n)                                                AS requests,
       MIN(CASE WHEN rn >= CEIL(0.50 * n) THEN latency_ms END) AS p50_ms,
       MIN(CASE WHEN rn >= CEIL(0.95 * n) THEN latency_ms END) AS p95_ms,
       MIN(CASE WHEN rn >= CEIL(0.99 * n) THEN latency_ms END) AS p99_ms
FROM ranked
GROUP BY model_name
ORDER BY p95_ms, model_name;

-- SQL-118 · Monthly token cost with time-varying prices
SELECT CAST(DATE_TRUNC('month', r.requested_at) AS DATE) AS month_start,
       r.model_name,
       COUNT(*) AS requests,
       ROUND(SUM(CASE WHEN r.cache_hit THEN 0
                      ELSE r.input_tokens / 1000.0 * p.input_usd_per_1k
                         + COALESCE(r.output_tokens, 0) / 1000.0 * p.output_usd_per_1k
                 END), 2) AS cost_usd
FROM llm_requests r
JOIN llm_pricing p
  ON p.model_name = r.model_name
 AND CAST(r.requested_at AS DATE) BETWEEN p.effective_from AND COALESCE(p.effective_to, DATE '9999-12-31')
WHERE r.requested_at >= TIMESTAMP '2025-01-01 00:00:00'
  AND r.requested_at <  TIMESTAMP '2025-07-01 00:00:00'
GROUP BY DATE_TRUNC('month', r.requested_at), r.model_name
ORDER BY month_start, r.model_name;

-- SQL-119 · Most expensive prompt versions
SELECT CASE WHEN pr.prompt_version_id IS NULL THEN 'ad-hoc'
            ELSE CONCAT(pr.prompt_name, ' v', pr.version) END                 AS prompt,
       COUNT(*)                                                               AS requests,
       ROUND(SUM(CASE WHEN r.cache_hit THEN 0
                      ELSE r.input_tokens / 1000.0 * p.input_usd_per_1k
                         + COALESCE(r.output_tokens, 0) / 1000.0 * p.output_usd_per_1k END), 2) AS total_cost_usd,
       ROUND(SUM(CASE WHEN r.cache_hit THEN 0
                      ELSE r.input_tokens / 1000.0 * p.input_usd_per_1k
                         + COALESCE(r.output_tokens, 0) / 1000.0 * p.output_usd_per_1k END) / COUNT(*), 4) AS cost_per_request_usd,
       ROUND(SUM(CASE WHEN r.cache_hit THEN 0
                      ELSE r.input_tokens / 1000.0 * p.input_usd_per_1k
                         + COALESCE(r.output_tokens, 0) / 1000.0 * p.output_usd_per_1k END)
             / NULLIF(SUM(CASE WHEN r.status = 'success' THEN 1 ELSE 0 END), 0), 4) AS cost_per_success_usd
FROM llm_requests r
JOIN llm_pricing p
  ON p.model_name = r.model_name
 AND CAST(r.requested_at AS DATE) BETWEEN p.effective_from AND COALESCE(p.effective_to, DATE '9999-12-31')
LEFT JOIN prompts pr ON pr.prompt_version_id = r.prompt_version_id
WHERE r.requested_at >= TIMESTAMP '2025-04-01 00:00:00'
  AND r.requested_at <  TIMESTAMP '2025-07-01 00:00:00'
GROUP BY CASE WHEN pr.prompt_version_id IS NULL THEN 'ad-hoc'
              ELSE CONCAT(pr.prompt_name, ' v', pr.version) END
ORDER BY total_cost_usd DESC, prompt;

-- SQL-120 · Detect a failure-rate spike against a trailing baseline
WITH daily AS (
    SELECT CAST(requested_at AS DATE)                                         AS request_date,
           COUNT(*)                                                           AS requests,
           SUM(CASE WHEN status <> 'success' THEN 1 ELSE 0 END)               AS failures,
           100.0 * SUM(CASE WHEN status <> 'success' THEN 1 ELSE 0 END) / COUNT(*) AS rate
    FROM llm_requests
    WHERE model_name = 'nimbus-pro'
      AND requested_at >= TIMESTAMP '2025-03-10 00:00:00'
      AND requested_at <  TIMESTAMP '2025-04-11 00:00:00'
    GROUP BY CAST(requested_at AS DATE)
),
with_base AS (
    SELECT request_date, requests, failures, rate,
           AVG(rate) OVER (ORDER BY request_date ROWS BETWEEN 7 PRECEDING AND 1 PRECEDING) AS baseline
    FROM daily
)
SELECT request_date,
       requests,
       failures,
       ROUND(rate, 1)     AS failure_rate_pct,
       ROUND(baseline, 1) AS baseline_pct,
       CASE WHEN requests >= 10 AND rate > 3 * baseline THEN 1 ELSE 0 END AS alert
FROM with_base
ORDER BY request_date;

-- SQL-121 · Requests with abnormal input token counts
WITH ranked AS (
    SELECT feature, input_tokens,
           ROW_NUMBER() OVER (PARTITION BY feature ORDER BY input_tokens) AS rn,
           COUNT(*)     OVER (PARTITION BY feature)                       AS n
    FROM llm_requests
),
medians AS (
    SELECT feature,
           AVG(CASE WHEN rn IN (FLOOR((n + 1) / 2.0), FLOOR((n + 2) / 2.0)) THEN input_tokens END) AS feature_median
    FROM ranked
    GROUP BY feature
)
SELECT r.request_id,
       r.feature,
       r.model_name,
       r.input_tokens,
       ROUND(m.feature_median, 1)                       AS feature_median,
       ROUND(r.input_tokens / m.feature_median, 1)      AS ratio_to_median
FROM llm_requests r
JOIN medians m ON m.feature = r.feature
WHERE r.input_tokens > 10 * m.feature_median
ORDER BY ratio_to_median DESC, r.request_id;

-- SQL-122 · Users experiencing repeated failures
WITH q2 AS (
    SELECT user_id, org_id, status
    FROM llm_requests
    WHERE user_id IS NOT NULL
      AND requested_at >= TIMESTAMP '2025-04-01 00:00:00'
      AND requested_at <  TIMESTAMP '2025-07-01 00:00:00'
),
totals AS (
    SELECT user_id, org_id,
           COUNT(*)                                            AS requests,
           SUM(CASE WHEN status <> 'success' THEN 1 ELSE 0 END) AS failures
    FROM q2
    GROUP BY user_id, org_id
),
modes AS (
    SELECT user_id, status,
           ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY COUNT(*) DESC, status) AS rn
    FROM q2
    WHERE status <> 'success'
    GROUP BY user_id, status
)
SELECT t.user_id,
       t.org_id,
       t.requests,
       t.failures,
       ROUND(100.0 * t.failures / t.requests, 1) AS failure_rate_pct,
       m.status                                  AS most_common_failure
FROM totals t
JOIN modes m ON m.user_id = t.user_id AND m.rn = 1
WHERE t.failures >= 3
ORDER BY t.failures DESC, t.user_id;

-- SQL-123 · Missing trace IDs and incomplete request metadata
SELECT CAST(requested_at AS DATE) AS request_date,
       COUNT(*) AS requests,
       ROUND(100.0 * SUM(CASE WHEN trace_id IS NULL THEN 1 ELSE 0 END) / COUNT(*), 1) AS missing_trace_pct,
       ROUND(100.0 * SUM(CASE WHEN request_metadata IS NULL THEN 1 ELSE 0 END) / COUNT(*), 1) AS missing_metadata_pct,
       ROUND(100.0 * SUM(CASE WHEN request_metadata IS NOT NULL AND NOT (request_metadata ? 'region')
                              THEN 1 ELSE 0 END) / COUNT(*), 1) AS missing_region_pct
FROM llm_requests
WHERE requested_at >= TIMESTAMP '2025-04-01 00:00:00'
  AND requested_at <  TIMESTAMP '2025-05-01 00:00:00'
GROUP BY CAST(requested_at AS DATE)
HAVING SUM(CASE WHEN trace_id IS NULL THEN 1 ELSE 0 END) > 0.10 * COUNT(*)
    OR SUM(CASE WHEN request_metadata IS NULL THEN 1 ELSE 0 END) > 0.10 * COUNT(*)
    OR SUM(CASE WHEN request_metadata IS NOT NULL AND NOT (request_metadata ? 'region') THEN 1 ELSE 0 END) > 0.10 * COUNT(*)
ORDER BY request_date;

-- SQL-124 · Chunks of the latest published document versions
WITH latest AS (
    SELECT document_id, doc_key, source_type
    FROM (
        SELECT document_id, doc_key, source_type,
               ROW_NUMBER() OVER (PARTITION BY doc_key ORDER BY version_number DESC) AS rn
        FROM documents
        WHERE status = 'published'
          AND is_deleted = FALSE
    ) x
    WHERE rn = 1
)
SELECT l.source_type,
       COUNT(DISTINCT l.document_id)                      AS documents,
       COUNT(DISTINCT c.document_id)                      AS documents_with_chunks,
       COUNT(c.chunk_id)                                  AS embedded_chunks,
       ROUND(AVG(c.token_count), 1)                       AS avg_tokens_per_chunk
FROM latest l
LEFT JOIN document_chunks c
       ON c.document_id = l.document_id
      AND c.embedding_model IS NOT NULL
GROUP BY l.source_type
ORDER BY l.source_type;

-- SQL-125 · What is in the index that should not be?
SELECT CASE WHEN d.is_deleted = TRUE        THEN 'deleted_document'
            WHEN d.status = 'draft'         THEN 'unpublished_draft'
            WHEN d.status = 'archived'      THEN 'superseded_version'
            WHEN c.embedding_model IS NULL  THEN 'embedding_failed'
            ELSE 'servable' END              AS chunk_status,
       COUNT(DISTINCT c.document_id)         AS documents,
       COUNT(*)                              AS chunks
FROM document_chunks c
JOIN documents d ON d.document_id = c.document_id
GROUP BY CASE WHEN d.is_deleted = TRUE        THEN 'deleted_document'
              WHEN d.status = 'draft'         THEN 'unpublished_draft'
              WHEN d.status = 'archived'      THEN 'superseded_version'
              WHEN c.embedding_model IS NULL  THEN 'embedding_failed'
              ELSE 'servable' END
ORDER BY chunk_status;

-- SQL-126 · Documents not re-indexed after their last update
SELECT document_id,
       doc_key,
       version_number,
       updated_at,
       last_indexed_at,
       CASE WHEN last_indexed_at IS NULL THEN 'never_indexed' ELSE 'stale_index' END AS issue
FROM documents
WHERE status = 'published'
  AND is_deleted = FALSE
  AND (last_indexed_at IS NULL OR last_indexed_at < updated_at)
ORDER BY issue, updated_at DESC, document_id;

-- SQL-127 · Answers grounded in content that was already superseded
WITH per_request AS (
    SELECT r.request_id,
           r.requested_at,
           MAX(CASE WHEN EXISTS (SELECT 1 FROM documents newer
                                 WHERE newer.doc_key = d.doc_key
                                   AND newer.version_number > d.version_number
                                   AND newer.status <> 'draft'
                                   AND newer.created_at <= r.requested_at)
                    THEN 1 ELSE 0 END) AS has_superseded
    FROM llm_requests r
    JOIN llm_request_chunks rc ON rc.request_id = r.request_id
    JOIN document_chunks c     ON c.chunk_id = rc.chunk_id
    JOIN documents d           ON d.document_id = c.document_id
    WHERE r.feature = 'support_bot'
      AND r.requested_at >= TIMESTAMP '2025-01-01 00:00:00'
      AND r.requested_at <  TIMESTAMP '2025-07-01 00:00:00'
    GROUP BY r.request_id, r.requested_at
)
SELECT CAST(DATE_TRUNC('month', requested_at) AS DATE) AS month_start,
       COUNT(*)                                         AS rag_requests,
       SUM(has_superseded)                              AS requests_with_superseded_chunk,
       ROUND(100.0 * SUM(has_superseded) / COUNT(*), 1) AS pct
FROM per_request
GROUP BY DATE_TRUNC('month', requested_at)
ORDER BY month_start;

-- SQL-128 · Duplicate chunks: within documents, across versions, across documents
WITH c AS (
    SELECT ch.chunk_id, ch.document_id, ch.content_hash, d.doc_key
    FROM document_chunks ch
    JOIN documents d ON d.document_id = ch.document_id
),
within_version AS (
    SELECT document_id, content_hash, COUNT(*) AS n
    FROM c GROUP BY document_id, content_hash HAVING COUNT(*) > 1
),
across_versions AS (
    SELECT doc_key, content_hash, COUNT(*) AS n
    FROM c GROUP BY doc_key, content_hash HAVING COUNT(DISTINCT document_id) > 1
),
across_docs AS (
    SELECT content_hash, COUNT(*) AS n
    FROM c GROUP BY content_hash HAVING COUNT(DISTINCT doc_key) > 1
)
SELECT 'across_documents' AS duplicate_scope, COUNT(*) AS duplicate_hashes, SUM(n) AS chunks_involved FROM across_docs
UNION ALL
SELECT 'across_versions_same_doc', COUNT(*), SUM(n) FROM across_versions
UNION ALL
SELECT 'within_version', COUNT(*), SUM(n) FROM within_version
ORDER BY duplicate_scope;

-- SQL-129 · Retrieval hit rate at K and MRR per configuration
WITH first_hit AS (
    SELECT config_id,
           query_id,
           MIN(CASE WHEN is_relevant = TRUE THEN rank_position END) AS first_rank
    FROM retrieval_evaluations
    GROUP BY config_id, query_id
)
SELECT c.config_name,
       COUNT(*)                                                                     AS queries,
       ROUND(100.0 * SUM(CASE WHEN f.first_rank <= 1 THEN 1 ELSE 0 END) / COUNT(*), 1) AS hit_at_1_pct,
       ROUND(100.0 * SUM(CASE WHEN f.first_rank <= 3 THEN 1 ELSE 0 END) / COUNT(*), 1) AS hit_at_3_pct,
       ROUND(100.0 * SUM(CASE WHEN f.first_rank <= 5 THEN 1 ELSE 0 END) / COUNT(*), 1) AS hit_at_5_pct,
       ROUND(AVG(CASE WHEN f.first_rank <= 5 THEN 1.0 / f.first_rank ELSE 0 END), 4)   AS mrr_at_5
FROM first_hit f
JOIN retrieval_configs c ON c.config_id = f.config_id
GROUP BY c.config_name
ORDER BY c.config_name;

-- SQL-130 · Retrieval quality by query type
WITH hits AS (
    SELECT config_id,
           query_id,
           MAX(CASE WHEN is_relevant = TRUE AND rank_position <= 5 THEN 1 ELSE 0 END) AS hit5
    FROM retrieval_evaluations
    GROUP BY config_id, query_id
)
SELECT q.query_type,
       COUNT(DISTINCT h.query_id)                                            AS queries,
       ROUND(100.0 * AVG(CASE WHEN h.config_id = 1 THEN h.hit5 END), 1)       AS cfg1_hit5_pct,
       ROUND(100.0 * AVG(CASE WHEN h.config_id = 2 THEN h.hit5 END), 1)       AS cfg2_hit5_pct,
       ROUND(100.0 * AVG(CASE WHEN h.config_id = 3 THEN h.hit5 END), 1)       AS cfg3_hit5_pct
FROM hits h
JOIN eval_queries q ON q.query_id = h.query_id
GROUP BY q.query_type
ORDER BY q.query_type;

-- SQL-131 · Answer acceptance rate from final user feedback
WITH final_fb AS (
    SELECT request_id, feedback_type
    FROM (
        SELECT request_id, feedback_type,
               ROW_NUMBER() OVER (PARTITION BY request_id ORDER BY created_at DESC, feedback_id DESC) AS rn
        FROM ai_feedback
    ) x
    WHERE rn = 1
)
SELECT r.feature,
       r.model_name,
       COUNT(*)                                                                      AS answers,
       COUNT(f.request_id)                                                           AS with_feedback,
       ROUND(100.0 * COUNT(f.request_id) / COUNT(*), 1)                              AS feedback_coverage_pct,
       ROUND(100.0 * SUM(CASE WHEN f.feedback_type = 'thumbs_up' THEN 1 ELSE 0 END)
             / NULLIF(COUNT(f.request_id), 0), 1)                                    AS acceptance_pct,
       SUM(CASE WHEN f.feedback_type = 'flag' THEN 1 ELSE 0 END)                     AS flagged
FROM llm_requests r
LEFT JOIN final_fb f ON f.request_id = r.request_id
WHERE r.status = 'success'
  AND r.requested_at >= TIMESTAMP '2025-04-01 00:00:00'
  AND r.requested_at <  TIMESTAMP '2025-07-01 00:00:00'
GROUP BY r.feature, r.model_name
HAVING COUNT(*) >= 50
ORDER BY r.feature, r.model_name;

-- SQL-132 · Compare prompt versions during their rollout overlap
WITH versions AS (
    SELECT prompt_version_id, version, created_at,
           ROW_NUMBER() OVER (ORDER BY version DESC) AS recency
    FROM prompts
    WHERE prompt_name = 'support_answer'
),
win AS (
    SELECT created_at AS win_start, created_at + INTERVAL '14' DAY AS win_end
    FROM versions WHERE recency = 1
),
final_fb AS (
    SELECT request_id, feedback_type
    FROM (
        SELECT request_id, feedback_type,
               ROW_NUMBER() OVER (PARTITION BY request_id ORDER BY created_at DESC, feedback_id DESC) AS rn
        FROM ai_feedback
    ) x
    WHERE rn = 1
)
SELECT CONCAT('support_answer v', v.version)                                         AS prompt_version,
       COUNT(*)                                                                      AS requests,
       ROUND(100.0 * SUM(CASE WHEN r.status = 'success' THEN 1 ELSE 0 END) / COUNT(*), 1) AS success_pct,
       ROUND(AVG(CASE WHEN r.status = 'success' THEN r.output_tokens END), 1)         AS avg_output_tokens,
       COUNT(f.request_id)                                                           AS feedback_requests,
       ROUND(100.0 * SUM(CASE WHEN f.feedback_type = 'thumbs_up' THEN 1 ELSE 0 END)
             / NULLIF(COUNT(f.request_id), 0), 1)                                    AS thumbs_up_pct
FROM llm_requests r
JOIN versions v ON v.prompt_version_id = r.prompt_version_id AND v.recency <= 2
CROSS JOIN win
LEFT JOIN final_fb f ON f.request_id = r.request_id
WHERE r.requested_at >= win.win_start
  AND r.requested_at <  win.win_end
GROUP BY v.version
ORDER BY prompt_version;

-- SQL-133 · Week-over-week cost regressions per model
WITH weekly AS (
    SELECT CAST(DATE_TRUNC('week', r.requested_at) AS DATE) AS week_start,
           r.model_name,
           SUM(CASE WHEN r.status = 'success' THEN 1 ELSE 0 END) AS successful_requests,
           SUM(CASE WHEN r.cache_hit THEN 0
                    ELSE r.input_tokens / 1000.0 * p.input_usd_per_1k
                       + COALESCE(r.output_tokens, 0) / 1000.0 * p.output_usd_per_1k END) AS cost_usd
    FROM llm_requests r
    JOIN llm_pricing p
      ON p.model_name = r.model_name
     AND CAST(r.requested_at AS DATE) BETWEEN p.effective_from AND COALESCE(p.effective_to, DATE '9999-12-31')
    WHERE r.requested_at >= TIMESTAMP '2025-01-06 00:00:00'
      AND r.requested_at <  TIMESTAMP '2025-06-30 00:00:00'
    GROUP BY DATE_TRUNC('week', r.requested_at), r.model_name
),
with_prev AS (
    SELECT week_start, model_name, successful_requests, cost_usd,
           cost_usd / NULLIF(successful_requests, 0) AS cps,
           LAG(cost_usd / NULLIF(successful_requests, 0)) OVER (PARTITION BY model_name ORDER BY week_start) AS prev_cps,
           LAG(successful_requests) OVER (PARTITION BY model_name ORDER BY week_start) AS prev_success
    FROM weekly
)
SELECT week_start, model_name, successful_requests,
       ROUND(cost_usd, 2)                        AS cost_usd,
       ROUND(cps, 4)                             AS cost_per_success,
       ROUND(prev_cps, 4)                        AS prev_cost_per_success,
       ROUND(100.0 * (cps / prev_cps - 1), 1)    AS change_pct
FROM with_prev
WHERE successful_requests >= 20
  AND prev_success >= 20
  AND cps > 1.2 * prev_cps
ORDER BY week_start, model_name;

-- SQL-134 · Build a RAG ingestion manifest from document metadata
SELECT document_id,
       doc_key,
       version_number,
       COALESCE(language, 'unknown')                         AS language,
       access_level,
       COALESCE(metadata->>'product_area', 'unknown')        AS product_area,
       metadata->>'tags'                                     AS tags,
       word_count,
       CEIL(word_count / 90.0)                               AS estimated_chunks,
       CASE WHEN last_indexed_at IS NULL THEN 'never_indexed' ELSE 'stale_index' END AS reason
FROM documents
WHERE status = 'published'
  AND is_deleted = FALSE
  AND (last_indexed_at IS NULL OR last_indexed_at < updated_at)
ORDER BY document_id;

-- SQL-135 · Did citations improve answer acceptance? (AI experiment readout)
WITH exp AS (
    SELECT a.user_id, a.variant, a.assigned_at
    FROM experiment_assignments a
    JOIN experiments x ON x.experiment_id = a.experiment_id
    WHERE x.experiment_name = 'rag_answer_citations'
),
final_fb AS (
    SELECT request_id, feedback_type
    FROM (
        SELECT request_id, feedback_type,
               ROW_NUMBER() OVER (PARTITION BY request_id ORDER BY created_at DESC, feedback_id DESC) AS rn
        FROM ai_feedback
    ) x
    WHERE rn = 1
),
answers AS (
    SELECT e.variant, r.request_id, f.feedback_type
    FROM exp e
    JOIN llm_requests r ON r.user_id = e.user_id
                       AND r.feature = 'support_bot'
                       AND r.status = 'success'
                       AND r.requested_at >= e.assigned_at
    LEFT JOIN final_fb f ON f.request_id = r.request_id
),
users_per_variant AS (
    SELECT variant, COUNT(*) AS users
    FROM exp
    GROUP BY variant
),
answer_stats AS (
    SELECT variant,
           COUNT(*)                                               AS answers,
           COUNT(feedback_type)                                   AS rated,
           SUM(CASE WHEN feedback_type = 'thumbs_up' THEN 1 ELSE 0 END) AS ups
    FROM answers
    GROUP BY variant
),
agg AS (
    SELECT u.variant, u.users,
           COALESCE(s.answers, 0) AS answers,
           COALESCE(s.rated, 0)   AS rated,
           COALESCE(s.ups, 0)     AS ups
    FROM users_per_variant u
    LEFT JOIN answer_stats s ON s.variant = u.variant
),
ctrl AS (
    SELECT rated AS n_c, ups AS x_c FROM agg WHERE variant = 'control'
)
SELECT g.variant,
       g.users,
       g.answers,
       g.rated AS rated_answers,
       g.ups   AS thumbs_up,
       ROUND(100.0 * g.ups / NULLIF(g.rated, 0), 1) AS thumbs_up_pct,
       CASE WHEN g.variant <> 'control' THEN
            ROUND((1.0 * g.ups / g.rated - 1.0 * c.x_c / c.n_c)
                  / SQRT((1.0 * (g.ups + c.x_c) / (g.rated + c.n_c))
                         * (1 - 1.0 * (g.ups + c.x_c) / (g.rated + c.n_c))
                         * (1.0 / g.rated + 1.0 / c.n_c)), 2) END AS z_vs_control
FROM agg g
CROSS JOIN ctrl c
ORDER BY g.variant;

-- SQL-136 · UNION versus UNION ALL for a contact list
SELECT
  (SELECT COUNT(*) FROM (
       SELECT LOWER(TRIM(email)) AS email FROM users WHERE role = 'admin' AND status = 'active'
       UNION ALL
       SELECT LOWER(TRIM(u.email)) FROM support_tickets t JOIN users u ON u.user_id = t.user_id
       WHERE t.priority = 'urgent'
         AND t.created_at >= TIMESTAMP '2025-01-01 00:00:00'
         AND t.created_at <  TIMESTAMP '2025-07-01 00:00:00'
   ) a) AS union_all_rows,
  (SELECT COUNT(*) FROM (
       SELECT LOWER(TRIM(email)) AS email FROM users WHERE role = 'admin' AND status = 'active'
       UNION
       SELECT LOWER(TRIM(u.email)) FROM support_tickets t JOIN users u ON u.user_id = t.user_id
       WHERE t.priority = 'urgent'
         AND t.created_at >= TIMESTAMP '2025-01-01 00:00:00'
         AND t.created_at <  TIMESTAMP '2025-07-01 00:00:00'
   ) b) AS union_rows;

-- SQL-137 · Users who use AI features and buy (INTERSECT)
SELECT o.segment,
       COUNT(*) AS ai_buyers
FROM (
    SELECT user_id FROM llm_requests
    WHERE status = 'success' AND user_id IS NOT NULL
      AND requested_at >= TIMESTAMP '2025-04-01 00:00:00'
      AND requested_at <  TIMESTAMP '2025-07-01 00:00:00'
    INTERSECT
    SELECT user_id FROM orders
    WHERE status = 'completed'
      AND order_ts >= TIMESTAMP '2025-04-01 00:00:00'
      AND order_ts <  TIMESTAMP '2025-07-01 00:00:00'
) both_sets
JOIN users u         ON u.user_id = both_sets.user_id
JOIN organizations o ON o.org_id = u.org_id
GROUP BY o.segment
ORDER BY o.segment;

-- SQL-138 · Paying but inactive customers (EXCEPT)
SELECT o.org_id,
       o.org_name,
       o.segment,
       SUM(s.mrr) AS open_mrr
FROM (
    SELECT org_id FROM subscriptions WHERE ended_at IS NULL
    EXCEPT
    SELECT u.org_id
    FROM sessions se
    JOIN users u ON u.user_id = se.user_id
    WHERE se.started_at >= TIMESTAMP '2025-07-01 00:00:00' - INTERVAL '30' DAY
      AND se.started_at <  TIMESTAMP '2025-07-01 00:00:00'
) inactive
JOIN organizations o ON o.org_id = inactive.org_id
JOIN subscriptions s ON s.org_id = inactive.org_id AND s.ended_at IS NULL
GROUP BY o.org_id, o.org_name, o.segment
ORDER BY open_mrr DESC, o.org_id;

-- SQL-139 · Reconcile order headers with order lines (symmetric difference)
SELECT 'header_only' AS side, order_id, amount
FROM (
    SELECT order_id, order_total AS amount FROM orders
    EXCEPT
    SELECT order_id, SUM(quantity * unit_price - discount_amount) FROM order_items GROUP BY order_id
) h
UNION ALL
SELECT 'lines_only', order_id, amount
FROM (
    SELECT order_id, SUM(quantity * unit_price - discount_amount) AS amount FROM order_items GROUP BY order_id
    EXCEPT
    SELECT order_id, order_total FROM orders
) l
ORDER BY order_id, side;

-- SQL-140 · Orders billed to an organization other than the buyer's
SELECT o.order_id,
       o.order_ts,
       o.org_id AS order_org_id,
       u.org_id AS user_org_id,
       CASE WHEN uo.parent_org_id = o.org_id THEN 'billed_to_parent'
            WHEN oo.parent_org_id = u.org_id THEN 'billed_to_subsidiary'
            ELSE 'unrelated' END AS relationship
FROM orders o
JOIN users u          ON u.user_id = o.user_id
JOIN organizations uo ON uo.org_id = u.org_id
JOIN organizations oo ON oo.org_id = o.org_id
WHERE o.org_id <> u.org_id
ORDER BY o.order_id;

-- SQL-141 · A data-quality scorecard in one query
SELECT check_name,
       failing_rows,
       CASE WHEN failing_rows = 0 THEN 'PASS' ELSE 'FAIL' END AS status
FROM (
    SELECT 'email_whitespace' AS check_name, COUNT(*) AS failing_rows
    FROM users WHERE email <> TRIM(email)
    UNION ALL
    SELECT 'duplicate_person_accounts', COALESCE(SUM(n - 1), 0)
    FROM (SELECT COUNT(*) AS n FROM users GROUP BY LOWER(TRIM(email)) HAVING COUNT(*) > 1) d
    UNION ALL
    SELECT 'order_total_mismatch', COUNT(*)
    FROM orders o
    JOIN (SELECT order_id, SUM(quantity * unit_price - discount_amount) AS s
          FROM order_items GROUP BY order_id) i ON i.order_id = o.order_id
    WHERE ABS(o.order_total - i.s) > 0.005
    UNION ALL
    SELECT 'completed_without_payment', COUNT(*)
    FROM orders o
    WHERE o.status = 'completed'
      AND NOT EXISTS (SELECT 1 FROM payments p WHERE p.order_id = o.order_id)
    UNION ALL
    SELECT 'order_org_mismatch', COUNT(*)
    FROM orders o JOIN users u ON u.user_id = o.user_id
    WHERE o.org_id <> u.org_id
    UNION ALL
    SELECT 'overlapping_subscriptions', COUNT(*)
    FROM subscriptions a
    JOIN subscriptions b
      ON b.org_id = a.org_id
     AND a.subscription_id < b.subscription_id
     AND a.started_at < COALESCE(b.ended_at, TIMESTAMP '9999-12-31 00:00:00')
     AND b.started_at < COALESCE(a.ended_at, TIMESTAMP '9999-12-31 00:00:00')
    UNION ALL
    SELECT 'duplicate_client_events', COALESCE(SUM(n - 1), 0)
    FROM (SELECT COUNT(*) AS n FROM events
          WHERE session_id IS NOT NULL
          GROUP BY user_id, session_id, event_name, event_ts
          HAVING COUNT(*) > 1) e
    UNION ALL
    SELECT 'response_after_resolution', COUNT(*)
    FROM support_tickets
    WHERE first_response_at > resolved_at
) checks
ORDER BY check_name;

-- SQL-142 · Person-level clusters of duplicate accounts
SELECT MIN(u.user_id)                                              AS canonical_user_id,
       LOWER(TRIM(u.email))                                        AS normalized_email,
       COUNT(*)                                                    AS accounts,
       STRING_AGG(CAST(u.user_id AS TEXT), ',' ORDER BY u.user_id) AS account_ids,
       COALESCE(SUM(o.n), 0)                                       AS completed_orders
FROM users u
LEFT JOIN (SELECT user_id, COUNT(*) AS n FROM orders WHERE status = 'completed' GROUP BY user_id) o
       ON o.user_id = u.user_id
GROUP BY LOWER(TRIM(u.email))
HAVING COUNT(*) > 1
ORDER BY canonical_user_id;

-- SQL-143 · Validate the evaluation set against the document corpus
SELECT status, COUNT(*) AS queries
FROM (
    SELECT q.query_id,
           CASE WHEN NOT EXISTS (SELECT 1 FROM documents d WHERE d.doc_key = q.gold_doc_key)
                     THEN 'unknown_doc_key'
                WHEN NOT EXISTS (SELECT 1
                                 FROM documents d
                                 JOIN document_chunks c ON c.document_id = d.document_id
                                 WHERE d.doc_key = q.gold_doc_key
                                   AND d.status = 'published'
                                   AND d.is_deleted = FALSE
                                   AND c.embedding_model IS NOT NULL)
                     THEN 'no_servable_chunks'
                ELSE 'ok' END AS status
    FROM eval_queries q
) s
GROUP BY status
ORDER BY status;

-- SQL-144 · Create a feature registry table with constraints
DROP TABLE IF EXISTS sb_feature_registry;
CREATE TABLE sb_feature_registry (
    feature_name            VARCHAR(60) NOT NULL,
    entity_type             VARCHAR(20) NOT NULL,
    value_type              VARCHAR(10) NOT NULL,
    owner_team              VARCHAR(40) NOT NULL,
    first_model_version_id  INT,
    is_active               BOOLEAN     NOT NULL DEFAULT TRUE,
    CONSTRAINT pk_sb_feature_registry PRIMARY KEY (feature_name),
    CONSTRAINT ck_sb_fr_entity_type   CHECK (entity_type IN ('user', 'org')),
    CONSTRAINT ck_sb_fr_value_type    CHECK (value_type IN ('int', 'float', 'bool')),
    CONSTRAINT fk_sb_fr_model_version FOREIGN KEY (first_model_version_id)
        REFERENCES model_versions (model_version_id)
);
INSERT INTO sb_feature_registry (feature_name, entity_type, value_type, owner_team, first_model_version_id) VALUES
    ('sessions_7d',             'user', 'int',   'growth-data',  1),
    ('sessions_28d',            'user', 'int',   'growth-data',  1),
    ('events_28d',              'user', 'int',   'growth-data',  2),
    ('days_since_last_session', 'user', 'int',   'growth-data',  1),
    ('avg_session_minutes',     'user', 'float', 'growth-data',  3),
    ('open_tickets',            'org',  'int',   'support-data', 2),
    ('seats_used_pct',          'org',  'float', 'billing-data', 3);
SELECT entity_type,
       COUNT(*)                                       AS features,
       SUM(CASE WHEN is_active THEN 1 ELSE 0 END)     AS active_features
FROM sb_feature_registry
GROUP BY entity_type
ORDER BY entity_type;
DROP TABLE IF EXISTS sb_feature_registry;

-- SQL-145 · Materialize a monthly revenue summary with INSERT ... SELECT
DROP TABLE IF EXISTS sb_monthly_revenue;
CREATE TABLE sb_monthly_revenue (
    month_start       DATE           NOT NULL PRIMARY KEY,
    completed_orders  INT            NOT NULL,
    revenue           DECIMAL(14,2)  NOT NULL
);
INSERT INTO sb_monthly_revenue (month_start, completed_orders, revenue)
SELECT CAST(DATE_TRUNC('month', order_ts) AS DATE), COUNT(*), SUM(order_total)
FROM orders
WHERE status = 'completed'
  AND order_ts >= TIMESTAMP '2024-01-01 00:00:00'
  AND order_ts <  TIMESTAMP '2025-07-01 00:00:00'
GROUP BY DATE_TRUNC('month', order_ts);
SELECT COUNT(*)          AS months,
       SUM(revenue)      AS total_revenue,
       MIN(month_start)  AS first_month,
       MAX(month_start)  AS last_month
FROM sb_monthly_revenue;
DROP TABLE IF EXISTS sb_monthly_revenue;

-- SQL-146 · Deactivate users of deleted organizations (UPDATE with a join)
DROP TABLE IF EXISTS sb_users;
CREATE TABLE sb_users AS SELECT user_id, org_id, status FROM users;
UPDATE sb_users u
SET status = 'inactive'
FROM organizations o
WHERE o.org_id = u.org_id
  AND o.is_deleted = TRUE
  AND u.status = 'active';
SELECT o.is_deleted AS org_deleted,
       u.status,
       COUNT(*)     AS users
FROM sb_users u
JOIN organizations o ON o.org_id = u.org_id
GROUP BY o.is_deleted, u.status
ORDER BY org_deleted, u.status;
DROP TABLE IF EXISTS sb_users;

-- SQL-147 · Delete duplicate events but keep one copy
DROP TABLE IF EXISTS sb_events;
CREATE TABLE sb_events AS
SELECT event_id, user_id, session_id, event_name, event_ts
FROM events
WHERE event_ts >= TIMESTAMP '2025-06-01 00:00:00'
  AND event_ts <  TIMESTAMP '2025-07-01 00:00:00';
DELETE FROM sb_events
WHERE event_id IN (
    SELECT event_id
    FROM (
        SELECT event_id,
               ROW_NUMBER() OVER (PARTITION BY user_id, session_id, event_name, event_ts
                                  ORDER BY event_id) AS rn
        FROM sb_events
    ) ranked
    WHERE ranked.rn > 1
);
SELECT (SELECT COUNT(*) FROM sb_events) AS rows_left,
       (SELECT COUNT(*) FROM (SELECT 1 AS x FROM sb_events
                              GROUP BY user_id, session_id, event_name, event_ts
                              HAVING COUNT(*) > 1) d) AS duplicate_groups;
DROP TABLE IF EXISTS sb_events;

-- SQL-148 · Credit transfers with transactions and savepoints
DROP TABLE IF EXISTS sb_credit_balances;
CREATE TABLE sb_credit_balances (
    org_id   INT NOT NULL PRIMARY KEY,
    credits  INT NOT NULL,
    CONSTRAINT ck_sb_credits_nonnegative CHECK (credits >= 0)
);
INSERT INTO sb_credit_balances (org_id, credits) VALUES (12, 500), (49, 100), (94, 0);

START TRANSACTION;
UPDATE sb_credit_balances SET credits = credits - 200 WHERE org_id = 12;
UPDATE sb_credit_balances SET credits = credits + 200 WHERE org_id = 49;
COMMIT;

START TRANSACTION;
UPDATE sb_credit_balances SET credits = credits - 50 WHERE org_id = 49;
SAVEPOINT after_debit;
UPDATE sb_credit_balances SET credits = credits + 50 WHERE org_id = 12;
ROLLBACK TO SAVEPOINT after_debit;
UPDATE sb_credit_balances SET credits = credits + 50 WHERE org_id = 94;
COMMIT;

START TRANSACTION;
UPDATE sb_credit_balances SET credits = credits - 300 WHERE org_id = 12;
UPDATE sb_credit_balances SET credits = credits + 300 WHERE org_id = 94;
ROLLBACK;
SELECT org_id, credits
FROM sb_credit_balances
ORDER BY org_id;
DROP TABLE IF EXISTS sb_credit_balances;

-- SQL-149 · Idempotent daily usage loads with an upsert
DROP TABLE IF EXISTS sb_daily_usage;
CREATE TABLE sb_daily_usage (
    org_id      INT    NOT NULL,
    usage_date  DATE   NOT NULL,
    requests    INT    NOT NULL,
    tokens      BIGINT NOT NULL,
    CONSTRAINT pk_sb_daily_usage PRIMARY KEY (org_id, usage_date)
);
INSERT INTO sb_daily_usage (org_id, usage_date, requests, tokens)
SELECT org_id, CAST(requested_at AS DATE), COUNT(*), SUM(input_tokens + COALESCE(output_tokens, 0))
FROM llm_requests
WHERE requested_at >= TIMESTAMP '2025-06-28 00:00:00' AND requested_at < TIMESTAMP '2025-06-30 00:00:00'
GROUP BY org_id, CAST(requested_at AS DATE);
INSERT INTO sb_daily_usage (org_id, usage_date, requests, tokens)
SELECT org_id, CAST(requested_at AS DATE), COUNT(*), SUM(input_tokens + COALESCE(output_tokens, 0))
FROM llm_requests
WHERE requested_at >= TIMESTAMP '2025-06-29 00:00:00' AND requested_at < TIMESTAMP '2025-07-01 00:00:00'
GROUP BY org_id, CAST(requested_at AS DATE)
ON CONFLICT (org_id, usage_date)
DO UPDATE SET requests = EXCLUDED.requests,
              tokens   = EXCLUDED.tokens;
SELECT usage_date,
       COUNT(*)       AS orgs,
       SUM(requests)  AS requests,
       SUM(tokens)    AS tokens
FROM sb_daily_usage
GROUP BY usage_date
ORDER BY usage_date;
DROP TABLE IF EXISTS sb_daily_usage;

-- SQL-150 · A view for servable RAG chunks
CREATE OR REPLACE VIEW sb_v_servable_chunks AS
SELECT c.chunk_id,
       c.document_id,
       d.doc_key,
       d.source_type,
       c.token_count
FROM document_chunks c
JOIN documents d ON d.document_id = c.document_id
WHERE d.status = 'published'
  AND d.is_deleted = FALSE
  AND c.embedding_model IS NOT NULL;
SELECT source_type,
       COUNT(DISTINCT doc_key) AS documents,
       COUNT(*)                AS chunks,
       SUM(token_count)        AS tokens
FROM sb_v_servable_chunks
GROUP BY source_type
ORDER BY source_type;
DROP VIEW IF EXISTS sb_v_servable_chunks;

-- SQL-151 · Reuse an intermediate result with a temporary table
CREATE TEMPORARY TABLE tmp_q2_active AS
SELECT DISTINCT user_id
FROM sessions
WHERE started_at >= TIMESTAMP '2025-04-01 00:00:00'
  AND started_at <  TIMESTAMP '2025-07-01 00:00:00';
SELECT o.segment,
       COUNT(*) AS active_users,
       SUM(CASE WHEN EXISTS (SELECT 1 FROM orders x
                             WHERE x.user_id = t.user_id
                               AND x.status = 'completed'
                               AND x.order_ts >= TIMESTAMP '2025-04-01 00:00:00'
                               AND x.order_ts <  TIMESTAMP '2025-07-01 00:00:00')
                THEN 1 ELSE 0 END) AS buyers,
       ROUND(100.0 * SUM(CASE WHEN EXISTS (SELECT 1 FROM orders x
                                           WHERE x.user_id = t.user_id
                                             AND x.status = 'completed'
                                             AND x.order_ts >= TIMESTAMP '2025-04-01 00:00:00'
                                             AND x.order_ts <  TIMESTAMP '2025-07-01 00:00:00')
                              THEN 1 ELSE 0 END) / COUNT(*), 1) AS buyer_pct
FROM tmp_q2_active t
JOIN users u         ON u.user_id = t.user_id
JOIN organizations o ON o.org_id = u.org_id
GROUP BY o.segment
ORDER BY o.segment;

-- SQL-152 · Normalize a flat ticket import into dimension and fact tables
DROP TABLE IF EXISTS sb_fact_ticket;
DROP TABLE IF EXISTS sb_dim_org;
DROP TABLE IF EXISTS sb_ticket_import;
CREATE TABLE sb_ticket_import AS
SELECT t.ticket_id,
       t.org_id                   AS source_org_id,
       o.org_name,
       o.country_code,
       o.segment,
       t.category,
       t.priority,
       CAST(t.created_at AS DATE) AS created_date
FROM support_tickets t
JOIN organizations o ON o.org_id = t.org_id
WHERE t.created_at >= TIMESTAMP '2025-04-01 00:00:00'
  AND t.created_at <  TIMESTAMP '2025-07-01 00:00:00';
CREATE TABLE sb_dim_org (
    org_key        INT          NOT NULL,
    source_org_id  INT          NOT NULL,
    org_name       VARCHAR(120) NOT NULL,
    country_code   CHAR(2)      NOT NULL,
    segment        VARCHAR(20)  NOT NULL,
    CONSTRAINT pk_sb_dim_org PRIMARY KEY (org_key),
    CONSTRAINT uq_sb_dim_org_source UNIQUE (source_org_id)
);
INSERT INTO sb_dim_org (org_key, source_org_id, org_name, country_code, segment)
SELECT ROW_NUMBER() OVER (ORDER BY source_org_id), source_org_id, org_name, country_code, segment
FROM (SELECT DISTINCT source_org_id, org_name, country_code, segment FROM sb_ticket_import) d;
CREATE TABLE sb_fact_ticket (
    ticket_id     INT         NOT NULL,
    org_key       INT         NOT NULL,
    category      VARCHAR(30) NOT NULL,
    priority      VARCHAR(10) NOT NULL,
    created_date  DATE        NOT NULL,
    CONSTRAINT pk_sb_fact_ticket PRIMARY KEY (ticket_id),
    CONSTRAINT fk_sb_fact_ticket_org FOREIGN KEY (org_key) REFERENCES sb_dim_org (org_key)
);
INSERT INTO sb_fact_ticket (ticket_id, org_key, category, priority, created_date)
SELECT i.ticket_id, d.org_key, i.category, i.priority, i.created_date
FROM sb_ticket_import i
JOIN sb_dim_org d ON d.source_org_id = i.source_org_id;
SELECT (SELECT COUNT(*) FROM sb_ticket_import) AS import_rows,
       (SELECT COUNT(*) FROM sb_dim_org)       AS dim_rows,
       (SELECT COUNT(*) FROM sb_fact_ticket)   AS fact_rows,
       (SELECT COUNT(*) FROM sb_ticket_import i
         WHERE NOT EXISTS (SELECT 1
                           FROM sb_fact_ticket f
                           JOIN sb_dim_org d ON d.org_key = f.org_key
                           WHERE f.ticket_id = i.ticket_id
                             AND d.org_name = i.org_name
                             AND d.country_code = i.country_code
                             AND d.segment = i.segment
                             AND f.category = i.category
                             AND f.priority = i.priority
                             AND f.created_date = i.created_date)) AS unreconstructable_rows;
DROP TABLE IF EXISTS sb_fact_ticket;
DROP TABLE IF EXISTS sb_dim_org;
DROP TABLE IF EXISTS sb_ticket_import;

-- SQL-153 · Create, inspect and drop indexes
DROP TABLE IF EXISTS sb_requests;
CREATE TABLE sb_requests AS
SELECT request_id, model_name, requested_at, trace_id FROM llm_requests;
CREATE INDEX ix_sb_requests_model ON sb_requests (model_name);
CREATE INDEX ix_sb_requests_model_time ON sb_requests (model_name, requested_at);
CREATE UNIQUE INDEX ux_sb_requests_trace ON sb_requests (trace_id);
DROP INDEX ix_sb_requests_model;
SELECT ic.relname AS index_name,
       k.ord      AS column_position,
       a.attname  AS column_name
FROM pg_class t
JOIN pg_index ix ON ix.indrelid = t.oid
JOIN pg_class ic ON ic.oid = ix.indexrelid
CROSS JOIN LATERAL unnest(CAST(ix.indkey AS SMALLINT[])) WITH ORDINALITY AS k(attnum, ord)
JOIN pg_attribute a ON a.attrelid = t.oid AND a.attnum = k.attnum
WHERE t.relname = 'sb_requests'
ORDER BY index_name, column_position;
DROP TABLE IF EXISTS sb_requests;

-- SQL-154 · Read your first execution plan: index versus full scan
DROP TABLE IF EXISTS sb_req_perf;
CREATE TABLE sb_req_perf AS SELECT * FROM llm_requests;
CREATE INDEX ix_sb_req_perf_trace ON sb_req_perf (trace_id);
ANALYZE sb_req_perf;
EXPLAIN (COSTS OFF)
SELECT COUNT(*) FROM sb_req_perf WHERE trace_id = '00000000-0000-4000-a000-000000000000'
UNION ALL
SELECT COUNT(*) FROM sb_req_perf WHERE error_code = 'gateway_timeout';
DROP TABLE IF EXISTS sb_req_perf;

-- SQL-155 · SELECT * versus a covering index
DROP TABLE IF EXISTS sb_req_perf;
CREATE TABLE sb_req_perf AS SELECT * FROM llm_requests;
CREATE INDEX ix_sb_req_perf_cover ON sb_req_perf (model_name, requested_at, latency_ms);
VACUUM ANALYZE sb_req_perf;
EXPLAIN (COSTS OFF)
SELECT COUNT(*) FROM (SELECT requested_at, latency_ms FROM sb_req_perf
                      WHERE model_name = 'nimbus-pro'
                        AND requested_at >= TIMESTAMP '2025-06-01 00:00:00'
                        AND requested_at <  TIMESTAMP '2025-07-01 00:00:00') narrow
UNION ALL
SELECT COUNT(*) FROM (SELECT * FROM sb_req_perf
                      WHERE model_name = 'nimbus-pro'
                        AND requested_at >= TIMESTAMP '2025-06-01 00:00:00'
                        AND requested_at <  TIMESTAMP '2025-07-01 00:00:00'
                        AND input_tokens > 0) wide;
DROP TABLE IF EXISTS sb_req_perf;

-- SQL-156 · Sargable versus non-sargable date filters
DROP TABLE IF EXISTS sb_events_perf;
CREATE TABLE sb_events_perf AS SELECT event_id, user_id, event_ts, event_name FROM events;
CREATE INDEX ix_sb_events_perf_ts ON sb_events_perf (event_ts);
VACUUM ANALYZE sb_events_perf;
EXPLAIN (COSTS OFF)
SELECT COUNT(*) FROM sb_events_perf WHERE CAST(event_ts AS DATE) = DATE '2025-06-15'
UNION ALL
SELECT COUNT(*) FROM sb_events_perf
WHERE event_ts >= TIMESTAMP '2025-06-15 00:00:00' AND event_ts < TIMESTAMP '2025-06-16 00:00:00';
DROP TABLE IF EXISTS sb_events_perf;

-- SQL-157 · Composite index column order
DROP TABLE IF EXISTS sb_req_perf;
CREATE TABLE sb_req_perf AS SELECT * FROM llm_requests;
CREATE INDEX ix_sb_req_perf_model_time ON sb_req_perf (model_name, requested_at);
VACUUM ANALYZE sb_req_perf;
EXPLAIN (COSTS OFF)
SELECT COUNT(*) FROM sb_req_perf
WHERE model_name = 'nimbus-pro'
  AND requested_at >= TIMESTAMP '2025-06-01 00:00:00' AND requested_at < TIMESTAMP '2025-07-01 00:00:00'
UNION ALL
SELECT COUNT(*) FROM sb_req_perf
WHERE requested_at >= TIMESTAMP '2025-06-01 00:00:00' AND requested_at < TIMESTAMP '2025-07-01 00:00:00';
DROP TABLE IF EXISTS sb_req_perf;

-- SQL-158 · When an index is not useful (selectivity)
DROP TABLE IF EXISTS sb_req_perf;
CREATE TABLE sb_req_perf AS SELECT * FROM llm_requests;
CREATE INDEX ix_sb_req_perf_status ON sb_req_perf (status);
VACUUM ANALYZE sb_req_perf;
EXPLAIN (COSTS OFF)
SELECT COUNT(latency_ms) FROM sb_req_perf WHERE status = 'success'
UNION ALL
SELECT COUNT(latency_ms) FROM sb_req_perf WHERE status = 'content_filtered';
DROP TABLE IF EXISTS sb_req_perf;

-- SQL-159 · EXPLAIN ANALYZE: correlated subquery versus window function
EXPLAIN (ANALYZE, COSTS OFF, TIMING OFF, SUMMARY OFF, BUFFERS OFF)
SELECT COUNT(*)
FROM support_tickets t
WHERE t.ticket_id = (SELECT t2.ticket_id FROM support_tickets t2
                     WHERE t2.org_id = t.org_id
                     ORDER BY t2.created_at DESC, t2.ticket_id DESC
                     LIMIT 1)
UNION ALL
SELECT COUNT(*)
FROM (SELECT ROW_NUMBER() OVER (PARTITION BY org_id ORDER BY created_at DESC, ticket_id DESC) AS rn
      FROM support_tickets) r
WHERE rn = 1;

-- SQL-160 · Let the index provide the order (avoiding a sort)
DROP TABLE IF EXISTS sb_req_perf;
CREATE TABLE sb_req_perf AS SELECT * FROM llm_requests;
CREATE INDEX ix_sb_req_perf_org_time ON sb_req_perf (org_id, requested_at);
VACUUM ANALYZE sb_req_perf;
EXPLAIN (COSTS OFF)
(SELECT request_id, requested_at FROM sb_req_perf WHERE org_id = 195 ORDER BY requested_at DESC LIMIT 20)
UNION ALL
(SELECT request_id, requested_at FROM sb_req_perf WHERE org_id = 195 ORDER BY latency_ms DESC LIMIT 20);
DROP TABLE IF EXISTS sb_req_perf;

-- SQL-161 · Compute once: repeated subqueries versus a single derived table
EXPLAIN (COSTS OFF)
SELECT o.segment,
       SUM(CASE WHEN EXISTS (SELECT 1 FROM llm_requests r
                             WHERE r.org_id = o.org_id AND r.status = 'success'
                               AND r.requested_at >= TIMESTAMP '2025-04-01 00:00:00')
                THEN 1 ELSE 0 END) AS adopting_orgs,
       ROUND(100.0 * SUM(CASE WHEN EXISTS (SELECT 1 FROM llm_requests r
                                           WHERE r.org_id = o.org_id AND r.status = 'success'
                                             AND r.requested_at >= TIMESTAMP '2025-04-01 00:00:00')
                              THEN 1 ELSE 0 END) / COUNT(*), 1) AS adoption_pct
FROM organizations o
WHERE o.is_deleted = FALSE
GROUP BY o.segment;

-- SQL-162 · Query event properties stored as JSONB
SELECT event_name, properties->>'referrer' AS property_value, COUNT(*) AS events
FROM events
WHERE event_name = 'view_pricing'
  AND event_ts >= TIMESTAMP '2025-04-01 00:00:00' AND event_ts < TIMESTAMP '2025-07-01 00:00:00'
GROUP BY event_name, properties->>'referrer'
UNION ALL
SELECT event_name, properties->>'feature', COUNT(*)
FROM events
WHERE event_name = 'ai_assist_used'
  AND event_ts >= TIMESTAMP '2025-04-01 00:00:00' AND event_ts < TIMESTAMP '2025-07-01 00:00:00'
GROUP BY event_name, properties->>'feature'
UNION ALL
SELECT event_name, 'sql_copilot (@>)', COUNT(*)
FROM events
WHERE event_name = 'ai_assist_used'
  AND properties @> '{"feature": "sql_copilot"}'
  AND event_ts >= TIMESTAMP '2025-04-01 00:00:00' AND event_ts < TIMESTAMP '2025-07-01 00:00:00'
GROUP BY event_name
ORDER BY event_name, events DESC, property_value;

-- SQL-163 · Generated column for a normalized e-mail key
DROP TABLE IF EXISTS sb_user_emails;
CREATE TABLE sb_user_emails (
    user_id     INT          NOT NULL PRIMARY KEY,
    email       VARCHAR(255) NOT NULL,
    email_norm  VARCHAR(255) GENERATED ALWAYS AS (LOWER(TRIM(email))) STORED
);
CREATE INDEX ix_sb_user_emails_norm ON sb_user_emails (email_norm);
INSERT INTO sb_user_emails (user_id, email)
SELECT user_id, email FROM users;
SELECT email_norm, COUNT(*) AS accounts
FROM sb_user_emails
GROUP BY email_norm
HAVING COUNT(*) > 1
ORDER BY email_norm;
DROP TABLE IF EXISTS sb_user_emails;

-- SQL-164 · Sign-ups per local calendar day (time zones)
WITH americas_users AS (
    SELECT u.user_id,
           u.signup_at,
           CAST((u.signup_at AT TIME ZONE 'UTC') AT TIME ZONE o.timezone AS DATE) AS local_date
    FROM users u
    JOIN organizations o ON o.org_id = u.org_id
    WHERE o.timezone LIKE 'America/%'
)
SELECT l.local_signup_date,
       l.signups,
       (SELECT COUNT(*) FROM americas_users n2
         WHERE CAST(n2.signup_at AS DATE) = l.local_signup_date) AS utc_date_signups
FROM (
    SELECT local_date AS local_signup_date, COUNT(*) AS signups
    FROM americas_users
    WHERE local_date >= DATE '2025-03-01' AND local_date < DATE '2025-04-01'
    GROUP BY local_date
) l
ORDER BY l.local_signup_date;

-- SQL-165 · Extract numeric limits from document text (regular expressions)
SELECT CAST(SUBSTRING(chunk_text FROM 'limit is ([0-9]+)') AS INT) AS limit_value,
       COUNT(*)                                                    AS chunks,
       COUNT(DISTINCT document_id)                                 AS documents
FROM document_chunks
WHERE chunk_text ~ 'limit is [0-9]+'
GROUP BY CAST(SUBSTRING(chunk_text FROM 'limit is ([0-9]+)') AS INT)
ORDER BY limit_value;

-- SQL-166 · Keyword search over chunks with PostgreSQL full-text search
SELECT c.chunk_id,
       d.doc_key,
       ROUND(CAST(ts_rank(to_tsvector('english', c.chunk_text),
                          websearch_to_tsquery('english', 'rotate API token')) AS NUMERIC), 4) AS rank
FROM document_chunks c
JOIN documents d ON d.document_id = c.document_id
WHERE d.status = 'published'
  AND d.is_deleted = FALSE
  AND c.embedding_model IS NOT NULL
  AND to_tsvector('english', c.chunk_text) @@ websearch_to_tsquery('english', 'rotate API token')
ORDER BY rank DESC, c.chunk_id
LIMIT 10;

-- SQL-168 · Explode JSON tag arrays into rows with JSON_TABLE
SELECT t.tag,
       COUNT(DISTINCT d.document_id) AS documents
FROM documents d
CROSS JOIN LATERAL jsonb_array_elements_text(d.metadata->'tags') AS t(tag)
WHERE d.status = 'published'
  AND d.is_deleted = FALSE
GROUP BY t.tag
ORDER BY documents DESC, t.tag
LIMIT 10;

-- SQL-169 · Synchronize index state with MERGE
DROP TABLE IF EXISTS sb_index_state;
CREATE TABLE sb_index_state (
    doc_key          VARCHAR(100) NOT NULL PRIMARY KEY,
    document_id      INT          NOT NULL,
    version_number   INT          NOT NULL,
    last_indexed_at  TIMESTAMP
);
INSERT INTO sb_index_state (doc_key, document_id, version_number, last_indexed_at)
SELECT doc_key, document_id, version_number, last_indexed_at
FROM documents
WHERE version_number = 1 AND is_deleted = FALSE AND doc_key LIKE 'help/%';
MERGE INTO sb_index_state t
USING (
    SELECT doc_key, document_id, version_number, last_indexed_at
    FROM (SELECT d.*,
                 ROW_NUMBER() OVER (PARTITION BY doc_key ORDER BY version_number DESC) AS rn
          FROM documents d
          WHERE status = 'published' AND is_deleted = FALSE) x
    WHERE rn = 1
) s
ON t.doc_key = s.doc_key
WHEN MATCHED AND t.version_number <> s.version_number THEN
    UPDATE SET document_id = s.document_id,
               version_number = s.version_number,
               last_indexed_at = s.last_indexed_at
WHEN NOT MATCHED THEN
    INSERT (doc_key, document_id, version_number, last_indexed_at)
    VALUES (s.doc_key, s.document_id, s.version_number, s.last_indexed_at);
SELECT CASE WHEN t.version_number = s.version_number THEN 'current' ELSE 'outdated' END AS action_summary,
       COUNT(*) AS rows_count
FROM sb_index_state t
LEFT JOIN (SELECT doc_key, MAX(version_number) AS version_number
           FROM documents WHERE status = 'published' AND is_deleted = FALSE
           GROUP BY doc_key) s ON s.doc_key = t.doc_key
GROUP BY CASE WHEN t.version_number = s.version_number THEN 'current' ELSE 'outdated' END
ORDER BY action_summary;
DROP TABLE IF EXISTS sb_index_state;

-- SQL-170 · PostgreSQL shortcuts: DISTINCT ON, FILTER and generate_series
WITH final_fb AS (
    SELECT DISTINCT ON (request_id)
           request_id, feedback_type, CAST(created_at AS DATE) AS feedback_date
    FROM ai_feedback
    ORDER BY request_id, created_at DESC, feedback_id DESC
),
daily AS (
    SELECT feedback_date,
           COUNT(*) FILTER (WHERE feedback_type = 'thumbs_up')   AS final_thumbs_up,
           COUNT(*) FILTER (WHERE feedback_type = 'thumbs_down') AS final_thumbs_down,
           COUNT(*) FILTER (WHERE feedback_type = 'flag')        AS final_flags
    FROM final_fb
    GROUP BY feedback_date
)
SELECT CAST(g.d AS DATE)                    AS feedback_date,
       COALESCE(daily.final_thumbs_up, 0)   AS final_thumbs_up,
       COALESCE(daily.final_thumbs_down, 0) AS final_thumbs_down,
       COALESCE(daily.final_flags, 0)       AS final_flags
FROM generate_series(DATE '2025-06-01', DATE '2025-06-30', INTERVAL '1 day') AS g(d)
LEFT JOIN daily ON daily.feedback_date = CAST(g.d AS DATE)
ORDER BY feedback_date;

-- SQL-171 · Top requests per organization with LATERAL joins
SELECT o.org_id,
       top3.request_id,
       top3.total_tokens,
       top3.token_rank
FROM organizations o
CROSS JOIN LATERAL (
    SELECT r.request_id,
           r.input_tokens + COALESCE(r.output_tokens, 0) AS total_tokens,
           ROW_NUMBER() OVER (ORDER BY r.input_tokens + COALESCE(r.output_tokens, 0) DESC, r.request_id) AS token_rank
    FROM llm_requests r
    WHERE r.org_id = o.org_id
      AND r.requested_at >= TIMESTAMP '2025-06-01 00:00:00'
      AND r.requested_at <  TIMESTAMP '2025-07-01 00:00:00'
    ORDER BY total_tokens DESC, r.request_id
    LIMIT 3
) AS top3
WHERE o.segment = 'Enterprise'
ORDER BY o.org_id, top3.token_rank;

-- CAP-DS · Capstone (Data Science): quarterly business review by segment
WITH seg AS (
    SELECT DISTINCT segment FROM organizations
),
rev AS (
    SELECT g.segment,
           SUM(CASE WHEN o.order_ts >= TIMESTAMP '2025-01-01 00:00:00' AND o.order_ts < TIMESTAMP '2025-04-01 00:00:00'
                    THEN o.order_total ELSE 0 END) AS q1_revenue,
           SUM(CASE WHEN o.order_ts >= TIMESTAMP '2025-04-01 00:00:00' AND o.order_ts < TIMESTAMP '2025-07-01 00:00:00'
                    THEN o.order_total ELSE 0 END) AS q2_revenue,
           SUM(CASE WHEN o.order_ts >= TIMESTAMP '2025-04-01 00:00:00' AND o.order_ts < TIMESTAMP '2025-07-01 00:00:00'
                    THEN 1 ELSE 0 END)             AS q2_orders,
           COUNT(DISTINCT CASE WHEN o.order_ts >= TIMESTAMP '2025-04-01 00:00:00' AND o.order_ts < TIMESTAMP '2025-07-01 00:00:00'
                               THEN o.org_id END)  AS q2_paying_orgs
    FROM orders o
    JOIN organizations g ON g.org_id = o.org_id
    WHERE o.status = 'completed'
      AND o.order_ts >= TIMESTAMP '2025-01-01 00:00:00'
      AND o.order_ts <  TIMESTAMP '2025-07-01 00:00:00'
    GROUP BY g.segment
),
new_orgs AS (
    SELECT segment, COUNT(*) AS q2_new_orgs
    FROM organizations
    WHERE created_at >= TIMESTAMP '2025-04-01 00:00:00' AND created_at < TIMESTAMP '2025-07-01 00:00:00'
    GROUP BY segment
),
churn AS (
    SELECT g.segment, COUNT(DISTINCT s.org_id) AS q2_churned_orgs
    FROM subscriptions s
    JOIN organizations g ON g.org_id = s.org_id
    WHERE s.status = 'canceled'
      AND s.ended_at >= TIMESTAMP '2025-04-01 00:00:00'
      AND s.ended_at <  TIMESTAMP '2025-07-01 00:00:00'
      AND NOT EXISTS (SELECT 1 FROM subscriptions o2
                      WHERE o2.org_id = s.org_id AND o2.ended_at IS NULL)
    GROUP BY g.segment
),
csat AS (
    SELECT g.segment, AVG(t.csat_score) AS q2_avg_csat
    FROM support_tickets t
    JOIN organizations g ON g.org_id = t.org_id
    WHERE t.created_at >= TIMESTAMP '2025-04-01 00:00:00' AND t.created_at < TIMESTAMP '2025-07-01 00:00:00'
    GROUP BY g.segment
),
ai AS (
    SELECT g.segment,
           COUNT(*) AS orgs,
           SUM(CASE WHEN EXISTS (SELECT 1 FROM llm_requests r
                                 WHERE r.org_id = g.org_id AND r.status = 'success'
                                   AND r.requested_at >= TIMESTAMP '2025-04-01 00:00:00'
                                   AND r.requested_at <  TIMESTAMP '2025-07-01 00:00:00')
                    THEN 1 ELSE 0 END) AS adopting
    FROM organizations g
    WHERE g.is_deleted = FALSE
    GROUP BY g.segment
)
SELECT seg.segment,
       COALESCE(rev.q1_revenue, 0)                                              AS q1_revenue,
       COALESCE(rev.q2_revenue, 0)                                              AS q2_revenue,
       ROUND(100.0 * (rev.q2_revenue - rev.q1_revenue) / NULLIF(rev.q1_revenue, 0), 1) AS qoq_growth_pct,
       COALESCE(rev.q2_paying_orgs, 0)                                          AS q2_paying_orgs,
       ROUND(rev.q2_revenue / NULLIF(rev.q2_orders, 0), 2)                      AS q2_aov,
       COALESCE(new_orgs.q2_new_orgs, 0)                                        AS q2_new_orgs,
       COALESCE(churn.q2_churned_orgs, 0)                                       AS q2_churned_orgs,
       ROUND(csat.q2_avg_csat, 2)                                               AS q2_avg_csat,
       ROUND(100.0 * ai.adopting / NULLIF(ai.orgs, 0), 1)                       AS q2_ai_adoption_pct
FROM seg
LEFT JOIN rev      ON rev.segment = seg.segment
LEFT JOIN new_orgs ON new_orgs.segment = seg.segment
LEFT JOIN churn    ON churn.segment = seg.segment
LEFT JOIN csat     ON csat.segment = seg.segment
LEFT JOIN ai       ON ai.segment = seg.segment
ORDER BY seg.segment;

-- CAP-ML · Capstone (ML Engineering): leakage-safe training snapshot for a new churn model
WITH labels AS (
    SELECT x.entity_id, x.observation_date, x.label_value
    FROM (
        SELECT l.entity_id, l.observation_date, l.label_value,
               ROW_NUMBER() OVER (PARTITION BY l.entity_id, l.observation_date
                                  ORDER BY l.label_available_at DESC, l.label_id DESC) AS rn
        FROM training_labels l
        WHERE l.label_name = 'churned_30d'
          AND l.observation_date IN (DATE '2025-03-01', DATE '2025-04-01', DATE '2025-05-01')
    ) x
    JOIN ml_entities e ON e.entity_id = x.entity_id
    WHERE x.rn = 1 AND x.label_value IS NOT NULL AND e.is_test_account = FALSE
),
examples AS (
    SELECT entity_id, observation_date, label_value,
           CASE WHEN observation_date < DATE '2025-05-01' THEN 'train' ELSE 'validation' END AS split
    FROM labels
),
ranked AS (
    SELECT x.entity_id, x.observation_date, f.as_of_ts, f.sessions_7d, f.sessions_28d,
           f.days_since_last_session,
           ROW_NUMBER() OVER (PARTITION BY x.entity_id, x.observation_date ORDER BY f.as_of_ts DESC) AS rn
    FROM examples x
    JOIN entity_features f
      ON f.entity_id = x.entity_id
     AND f.as_of_ts    <= x.observation_date
     AND f.ingested_at <= x.observation_date
),
dataset AS (
    SELECT x.split, x.entity_id, x.observation_date, x.label_value,
           r.as_of_ts, r.sessions_28d, r.days_since_last_session,
           r.sessions_7d * 4.0 / NULLIF(r.sessions_28d, 0) AS session_trend
    FROM examples x
    LEFT JOIN ranked r
           ON r.entity_id = x.entity_id
          AND r.observation_date = x.observation_date
          AND r.rn = 1
)
SELECT split,
       label_value,
       COUNT(*)                                          AS examples,
       ROUND(100.0 * COUNT(as_of_ts) / COUNT(*), 1)      AS pct_with_features,
       ROUND(AVG(sessions_28d), 2)                       AS avg_sessions_28d,
       ROUND(AVG(days_since_last_session), 2)            AS avg_days_since_last_session,
       ROUND(AVG(session_trend), 2)                      AS avg_session_trend
FROM dataset
GROUP BY split, label_value
ORDER BY CASE split WHEN 'train' THEN 1 ELSE 2 END, label_value;

-- CAP-AI · Capstone (AI Engineering): weekly RAG health report
WITH base AS (
    SELECT r.*, CAST(DATE_TRUNC('week', r.requested_at) AS DATE) AS week_start
    FROM llm_requests r
    WHERE r.feature = 'support_bot'
      AND r.requested_at >= TIMESTAMP '2025-06-02 00:00:00'
      AND r.requested_at <  TIMESTAMP '2025-06-30 00:00:00'
),
lat AS (
    SELECT week_start, latency_ms,
           ROW_NUMBER() OVER (PARTITION BY week_start ORDER BY latency_ms) AS rn,
           COUNT(*)     OVER (PARTITION BY week_start)                     AS n
    FROM base
    WHERE status = 'success' AND cache_hit = FALSE
),
p95 AS (
    SELECT week_start, MIN(CASE WHEN rn >= CEIL(0.95 * n) THEN latency_ms END) AS p95_latency_ms
    FROM lat GROUP BY week_start
),
cost AS (
    SELECT b.request_id,
           CASE WHEN b.cache_hit THEN 0
                ELSE b.input_tokens / 1000.0 * p.input_usd_per_1k
                   + COALESCE(b.output_tokens, 0) / 1000.0 * p.output_usd_per_1k END AS cost_usd
    FROM base b
    JOIN llm_pricing p
      ON p.model_name = b.model_name
     AND CAST(b.requested_at AS DATE) BETWEEN p.effective_from AND COALESCE(p.effective_to, DATE '9999-12-31')
),
stale AS (
    SELECT rc.request_id,
           MAX(CASE WHEN d.status <> 'published' OR d.is_deleted = TRUE THEN 1 ELSE 0 END) AS has_stale
    FROM llm_request_chunks rc
    JOIN document_chunks c ON c.chunk_id = rc.chunk_id
    JOIN documents d       ON d.document_id = c.document_id
    GROUP BY rc.request_id
),
final_fb AS (
    SELECT request_id, feedback_type
    FROM (SELECT request_id, feedback_type,
                 ROW_NUMBER() OVER (PARTITION BY request_id ORDER BY created_at DESC, feedback_id DESC) AS rn
          FROM ai_feedback) x
    WHERE rn = 1
)
SELECT b.week_start,
       COUNT(*)                                                                       AS requests,
       ROUND(100.0 * SUM(CASE WHEN b.status = 'success' THEN 1 ELSE 0 END) / COUNT(*), 1) AS success_pct,
       MAX(p95.p95_latency_ms)                                                        AS p95_latency_ms,
       ROUND(SUM(c.cost_usd), 2)                                                      AS cost_usd,
       ROUND(100.0 * SUM(s.has_stale) / NULLIF(COUNT(s.request_id), 0), 1)            AS stale_retrieval_pct,
       ROUND(100.0 * SUM(CASE WHEN b.status = 'success' AND f.feedback_type = 'thumbs_up' THEN 1 ELSE 0 END)
             / NULLIF(SUM(CASE WHEN b.status = 'success' AND f.feedback_type IS NOT NULL THEN 1 ELSE 0 END), 0), 1)
                                                                                      AS acceptance_pct
FROM base b
JOIN cost c          ON c.request_id = b.request_id
LEFT JOIN stale s    ON s.request_id = b.request_id
LEFT JOIN final_fb f ON f.request_id = b.request_id
JOIN p95             ON p95.week_start = b.week_start
GROUP BY b.week_start
ORDER BY b.week_start;

-- ASM-01 · Share of users by role
SELECT role,
       COUNT(*)                                          AS users,
       ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1) AS pct_of_users
FROM users
GROUP BY role
ORDER BY users DESC, role;

-- ASM-02 · Requests without prompt version or trace ID
SELECT feature,
       COUNT(*) AS requests,
       ROUND(100.0 * SUM(CASE WHEN prompt_version_id IS NULL THEN 1 ELSE 0 END) / COUNT(*), 2) AS no_prompt_pct,
       ROUND(100.0 * SUM(CASE WHEN trace_id IS NULL THEN 1 ELSE 0 END) / COUNT(*), 2)          AS no_trace_pct
FROM llm_requests
WHERE requested_at >= TIMESTAMP '2025-06-01 00:00:00'
  AND requested_at <  TIMESTAMP '2025-07-01 00:00:00'
GROUP BY feature
ORDER BY feature;

-- ASM-03 · Paying customers who never contact support
SELECT o.segment,
       COUNT(*) AS paying_orgs,
       SUM(CASE WHEN NOT EXISTS (SELECT 1 FROM support_tickets t
                                 WHERE t.org_id = o.org_id
                                   AND t.created_at >= TIMESTAMP '2025-01-01 00:00:00')
                THEN 1 ELSE 0 END) AS quiet_paying_orgs
FROM organizations o
WHERE EXISTS (SELECT 1 FROM subscriptions s WHERE s.org_id = o.org_id AND s.ended_at IS NULL)
GROUP BY o.segment
ORDER BY o.segment;

-- ASM-04 · Repeat purchase within 90 days
WITH numbered AS (
    SELECT user_id, order_ts,
           ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY order_ts, order_id) AS rn
    FROM orders
    WHERE status = 'completed'
),
firsts AS (
    SELECT user_id,
           MAX(CASE WHEN rn = 1 THEN order_ts END) AS first_ts,
           MAX(CASE WHEN rn = 2 THEN order_ts END) AS second_ts
    FROM numbered
    WHERE rn <= 2
    GROUP BY user_id
)
SELECT COUNT(*) AS first_time_buyers,
       SUM(CASE WHEN second_ts < first_ts + INTERVAL '90' DAY THEN 1 ELSE 0 END) AS repeat_within_90d,
       ROUND(100.0 * SUM(CASE WHEN second_ts < first_ts + INTERVAL '90' DAY THEN 1 ELSE 0 END) / COUNT(*), 1) AS repeat_pct
FROM firsts
WHERE first_ts >= TIMESTAMP '2024-07-01 00:00:00'
  AND first_ts <  TIMESTAMP '2025-01-01 00:00:00';

-- ASM-05 · Churn base rate by customer segment
SELECT o.segment,
       COUNT(*)                                AS examples,
       ROUND(100.0 * AVG(l.label_value), 2)    AS positive_rate_pct
FROM (
    SELECT entity_id, label_value,
           ROW_NUMBER() OVER (PARTITION BY entity_id ORDER BY label_available_at DESC, label_id DESC) AS rn
    FROM training_labels
    WHERE label_name = 'churned_30d' AND observation_date = DATE '2025-05-01'
) l
JOIN ml_entities e   ON e.entity_id = l.entity_id
JOIN organizations o ON o.org_id = e.org_id
WHERE l.rn = 1 AND l.label_value IS NOT NULL AND e.is_test_account = FALSE
GROUP BY o.segment
ORDER BY o.segment;

-- ASM-06 · Documents whose newest version is an unpublished draft
SELECT doc_key,
       MAX(CASE WHEN status = 'published' THEN version_number END) AS published_version,
       MAX(CASE WHEN status = 'draft' THEN version_number END)     AS draft_version
FROM documents
WHERE is_deleted = FALSE
GROUP BY doc_key
HAVING MAX(CASE WHEN status = 'draft' THEN version_number END)
     > MAX(CASE WHEN status = 'published' THEN version_number END)
ORDER BY doc_key;

-- ASM-07 · Paying organizations and MRR at each month end
WITH snaps AS (
    SELECT DATE '2025-01-31' AS month_end, TIMESTAMP '2025-02-01 00:00:00' AS t
    UNION ALL SELECT DATE '2025-02-28', TIMESTAMP '2025-03-01 00:00:00'
    UNION ALL SELECT DATE '2025-03-31', TIMESTAMP '2025-04-01 00:00:00'
    UNION ALL SELECT DATE '2025-04-30', TIMESTAMP '2025-05-01 00:00:00'
    UNION ALL SELECT DATE '2025-05-31', TIMESTAMP '2025-06-01 00:00:00'
    UNION ALL SELECT DATE '2025-06-30', TIMESTAMP '2025-07-01 00:00:00'
)
SELECT s.month_end,
       COUNT(DISTINCT sub.org_id) AS paying_orgs,
       SUM(sub.mrr)               AS mrr
FROM snaps s
JOIN subscriptions sub
  ON sub.started_at < s.t
 AND (sub.ended_at IS NULL OR sub.ended_at >= s.t)
GROUP BY s.month_end
ORDER BY s.month_end;

-- ASM-08 · Audit the logged feature snapshot of a scoring run
WITH recomputed AS (
    SELECT p.prediction_id,
           p.feature_as_of_ts,
           MAX(f.as_of_ts) AS available_as_of_ts
    FROM model_predictions p
    LEFT JOIN entity_features f
           ON f.entity_id = p.entity_id
          AND f.as_of_ts <= p.predicted_at
          AND f.ingested_at <= p.predicted_at
    WHERE p.batch_id = 'churn-2025-06-01-a'
    GROUP BY p.prediction_id, p.feature_as_of_ts
)
SELECT COUNT(*) AS predictions,
       SUM(CASE WHEN feature_as_of_ts = available_as_of_ts THEN 1 ELSE 0 END) AS logged_matches,
       SUM(CASE WHEN feature_as_of_ts IS NOT NULL
                 AND (available_as_of_ts IS NULL OR feature_as_of_ts <> available_as_of_ts) THEN 1 ELSE 0 END) AS logged_differs,
       SUM(CASE WHEN feature_as_of_ts IS NULL THEN 1 ELSE 0 END) AS not_logged
FROM recomputed;

-- ASM-09 · Day-over-day drops in SQL copilot success rate
WITH daily AS (
    SELECT CAST(requested_at AS DATE) AS request_date,
           COUNT(*) AS requests,
           100.0 * SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) / COUNT(*) AS success_pct
    FROM llm_requests
    WHERE feature = 'sql_copilot'
      AND requested_at >= TIMESTAMP '2025-04-01 00:00:00'
      AND requested_at <  TIMESTAMP '2025-07-01 00:00:00'
    GROUP BY CAST(requested_at AS DATE)
),
w AS (
    SELECT request_date, requests, success_pct,
           LAG(success_pct) OVER (ORDER BY request_date) AS prev_success_pct,
           LAG(requests)    OVER (ORDER BY request_date) AS prev_requests
    FROM daily
)
SELECT request_date,
       requests,
       ROUND(success_pct, 1)                    AS success_pct,
       ROUND(prev_success_pct, 1)               AS prev_success_pct,
       ROUND(success_pct - prev_success_pct, 1) AS change_pts
FROM w
WHERE requests >= 15
  AND prev_requests >= 15
  AND success_pct < prev_success_pct - 5
ORDER BY request_date;

-- ASM-10 · Top 2 ticket categories per segment (with ties)
SELECT segment, category, tickets, category_rank
FROM (
    SELECT o.segment,
           t.category,
           COUNT(*) AS tickets,
           DENSE_RANK() OVER (PARTITION BY o.segment ORDER BY COUNT(*) DESC) AS category_rank
    FROM support_tickets t
    JOIN organizations o ON o.org_id = t.org_id
    WHERE t.created_at >= TIMESTAMP '2025-01-01 00:00:00'
    GROUP BY o.segment, t.category
) ranked
WHERE category_rank <= 2
ORDER BY segment, category_rank, category;

-- ASM-11 · Top-decile lift of the production churn model
WITH labels AS (
    SELECT entity_id, label_value
    FROM (SELECT entity_id, label_value,
                 ROW_NUMBER() OVER (PARTITION BY entity_id ORDER BY label_available_at DESC, label_id DESC) AS rn
          FROM training_labels
          WHERE label_name = 'churned_30d' AND observation_date = DATE '2025-05-01') x
    WHERE rn = 1 AND label_value IS NOT NULL
),
evalset AS (
    SELECT p.entity_id, p.score, l.label_value,
           NTILE(10) OVER (ORDER BY p.score DESC, p.entity_id) AS decile
    FROM model_predictions p
    JOIN labels l      ON l.entity_id = p.entity_id
    JOIN ml_entities e ON e.entity_id = p.entity_id AND e.is_test_account = FALSE
    WHERE p.model_version_id = 3
      AND p.batch_id = 'churn-2025-05-01-a'
      AND p.score IS NOT NULL
)
SELECT COUNT(*) AS examples,
       SUM(CASE WHEN decile = 1 THEN 1 ELSE 0 END) AS top_decile_examples,
       ROUND(100.0 * AVG(CASE WHEN decile = 1 THEN label_value END), 2) AS top_decile_positive_rate_pct,
       ROUND(100.0 * AVG(label_value), 2) AS base_rate_pct,
       ROUND(AVG(CASE WHEN decile = 1 THEN label_value END) / AVG(label_value), 2) AS lift
FROM evalset;

-- ASM-12 · Pooled recall@5 across retrieval configurations
WITH pool AS (
    SELECT query_id, COUNT(DISTINCT chunk_id) AS pool_size
    FROM retrieval_evaluations
    WHERE is_relevant = TRUE
    GROUP BY query_id
),
found AS (
    SELECT config_id, query_id, COUNT(DISTINCT chunk_id) AS found_top5
    FROM retrieval_evaluations
    WHERE is_relevant = TRUE AND rank_position <= 5
    GROUP BY config_id, query_id
)
SELECT c.config_name,
       COUNT(*)                                                          AS queries_evaluated,
       ROUND(100.0 * AVG(1.0 * COALESCE(f.found_top5, 0) / p.pool_size), 1) AS recall_at_5_pct
FROM retrieval_configs c
CROSS JOIN pool p
LEFT JOIN found f ON f.config_id = c.config_id AND f.query_id = p.query_id
GROUP BY c.config_name
ORDER BY c.config_name;

-- ASM-13 · Users who tried to buy but never completed
SELECT COUNT(*) AS users_with_orders,
       SUM(CASE WHEN completed = 0 THEN 1 ELSE 0 END) AS never_completed,
       ROUND(100.0 * SUM(CASE WHEN completed = 0 THEN 1 ELSE 0 END) / COUNT(*), 2) AS never_completed_pct
FROM (
    SELECT user_id, SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) AS completed
    FROM orders
    GROUP BY user_id
) per_user;

-- ASM-14 · Reactivated customers and time away
SELECT org_id, prev_ended_at AS canceled_at, started_at AS returned_at,
       CAST(started_at AS DATE) - CAST(prev_ended_at AS DATE) AS days_away
FROM (
    SELECT org_id, started_at,
           LAG(status)   OVER (PARTITION BY org_id ORDER BY started_at, subscription_id) AS prev_status,
           LAG(ended_at) OVER (PARTITION BY org_id ORDER BY started_at, subscription_id) AS prev_ended_at
    FROM subscriptions
) s
WHERE prev_status = 'canceled'
ORDER BY days_away DESC, org_id;

-- ASM-15 · Scoring-run health summary
SELECT batch_id,
       COUNT(*)                                 AS predictions,
       COUNT(*) - COUNT(score)                  AS null_scores,
       COUNT(*) - COUNT(feature_as_of_ts)       AS unlogged_features,
       ROUND(100.0 * AVG(predicted_label), 1)   AS predicted_positive_pct
FROM model_predictions
WHERE batch_id LIKE 'churn-%'
GROUP BY batch_id
ORDER BY batch_id;

-- ASM-16 · Cost per accepted answer by model
WITH cost AS (
    SELECT r.request_id, r.model_name,
           CASE WHEN r.cache_hit THEN 0
                ELSE r.input_tokens / 1000.0 * p.input_usd_per_1k
                   + COALESCE(r.output_tokens, 0) / 1000.0 * p.output_usd_per_1k END AS cost_usd
    FROM llm_requests r
    JOIN llm_pricing p
      ON p.model_name = r.model_name
     AND CAST(r.requested_at AS DATE) BETWEEN p.effective_from AND COALESCE(p.effective_to, DATE '9999-12-31')
    WHERE r.feature = 'support_bot'
      AND r.requested_at >= TIMESTAMP '2025-04-01 00:00:00'
      AND r.requested_at <  TIMESTAMP '2025-07-01 00:00:00'
),
final_fb AS (
    SELECT request_id, feedback_type
    FROM (SELECT request_id, feedback_type,
                 ROW_NUMBER() OVER (PARTITION BY request_id ORDER BY created_at DESC, feedback_id DESC) AS rn
          FROM ai_feedback) x
    WHERE rn = 1
)
SELECT c.model_name,
       COUNT(*)                                                         AS requests,
       ROUND(SUM(c.cost_usd), 2)                                        AS cost_usd,
       SUM(CASE WHEN f.feedback_type = 'thumbs_up' THEN 1 ELSE 0 END)   AS accepted_answers,
       ROUND(SUM(c.cost_usd) / NULLIF(SUM(CASE WHEN f.feedback_type = 'thumbs_up' THEN 1 ELSE 0 END), 0), 4)
                                                                        AS cost_per_accepted_usd
FROM cost c
LEFT JOIN final_fb f ON f.request_id = c.request_id
GROUP BY c.model_name
ORDER BY cost_per_accepted_usd, c.model_name;

