-- Which skills show up in the jobs that are open right now?
--
-- Each job's skills list is split into one row per skill, then counted.
-- Only jobs that are open today count (closed jobs stay in the AI table
-- but are left out here), and only jobs the AI has actually read.

with read_jobs as (
    select
        e.job_id,
        e.open_to_nigeria,
        unnest(e.skills) as skill
    from "warehouse"."main"."stg_job_enrichment" as e
    inner join "warehouse"."main"."stg_remoteok_jobs" as j
        on j.job_id = e.job_id
),

job_total as (
    select count(*) as n
    from "warehouse"."main"."stg_job_enrichment" as e
    inner join "warehouse"."main"."stg_remoteok_jobs" as j
        on j.job_id = e.job_id
)

select
    skill,
    count(distinct job_id) as open_jobs,
    round(100.0 * count(distinct job_id) / (select n from job_total), 1) as pct_of_open_jobs,
    count(distinct job_id) filter (where open_to_nigeria = 'yes') as open_to_nigeria_jobs
from read_jobs
group by skill
order by open_jobs desc, skill