-- Cleaned copy of the AI's answers, one row per job it has read.
-- No reshaping needed here. The value of this model is that it gives the
-- AI output a name and a place to be tested (see schema.yml and tests/).

select
    job_id,
    model,
    skills,
    seniority,
    years_experience_min,
    open_to_nigeria,
    nigeria_evidence,
    summary,
    enriched_at
from {{ source('raw', 'raw_job_enrichment') }}
