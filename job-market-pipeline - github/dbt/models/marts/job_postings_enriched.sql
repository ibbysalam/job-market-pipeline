-- One row per job that is open right now, with what the AI found in it.
-- A job the AI has not read yet still shows up (is_enriched = false), so
-- gaps are visible instead of silently missing.

select
    j.job_id,
    j.job_title,
    j.company,
    j.location,
    j.posted_at,
    e.seniority,
    e.years_experience_min,
    e.open_to_nigeria,
    e.nigeria_evidence,
    e.skills,
    e.summary,
    e.job_id is not null as is_enriched
from {{ ref('stg_remoteok_jobs') }} as j
left join {{ ref('stg_job_enrichment') }} as e
    on e.job_id = j.job_id
