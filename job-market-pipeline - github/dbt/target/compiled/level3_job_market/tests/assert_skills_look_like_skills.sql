-- A skill should be a short, lowercase name like "python" or "power bi".
-- Models sometimes return whole sentences, empty strings or stray capitals.
-- This catches the answers that have the right shape but the wrong content.

select
    job_id,
    skill,
    'skill is empty, not lowercase, or too long to be a name' as failure_reason
from (
    select job_id, unnest(skills) as skill
    from "warehouse"."main"."stg_job_enrichment"
)
where trim(skill) = ''
   or skill != lower(skill)
   or length(skill) > 40