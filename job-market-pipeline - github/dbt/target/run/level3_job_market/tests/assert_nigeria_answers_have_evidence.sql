
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  -- Every "yes" or "no" about Nigeria must come with a quoted piece of
-- evidence. enrich_jobs.py already enforces this before saving. This test
-- is the second lock: if anyone changes the script, loads rows another
-- way, or edits the table by hand, the warehouse still refuses it.

select
    job_id,
    open_to_nigeria,
    'answered ' || open_to_nigeria || ' without evidence' as failure_reason
from "warehouse"."main"."stg_job_enrichment"
where open_to_nigeria in ('yes', 'no')
  and (
      nigeria_evidence is null
      or trim(nigeria_evidence) = ''
      or lower(trim(nigeria_evidence)) in ('none', 'n/a')
  )
  
  
      
    ) dbt_internal_test