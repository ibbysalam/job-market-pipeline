-- Light cleanup on top of the raw HN table: rename "by" (a reserved
-- SQL keyword in the raw table) to a normal column name, and convert
-- the Unix timestamp into an actual timestamp dbt/BI tools can use.

select
    id as story_id,
    "by" as author,
    descendants as comment_count,
    score,
    to_timestamp(time) as posted_at,
    title,
    type as story_type,
    url,
    text,
    loaded_at
from {{ source('raw', 'raw_hackernews_stories') }}
