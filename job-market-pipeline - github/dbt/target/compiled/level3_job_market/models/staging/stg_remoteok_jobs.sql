-- Light cleanup on top of the raw RemoteOK table: rename "position" to
-- "job_title" for clarity, and coalesce missing salary figures to NULL
-- consistently (RemoteOK sometimes sends 0 instead of null for an
-- unspecified salary).

select
    id as job_id,
    position as job_title,
    company,
    tags,
    location,
    nullif(salary_min, 0) as salary_min,
    nullif(salary_max, 0) as salary_max,
    url,
    try_cast(date as timestamp) as posted_at,
    loaded_at
from "warehouse"."main"."raw_remoteok_jobs"