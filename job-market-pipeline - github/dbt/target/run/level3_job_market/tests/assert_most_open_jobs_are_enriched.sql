
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  

-- If the AI step stops running (expired key, quota, a bug), the pipeline
-- keeps going and the numbers quietly get worse. This turns that into a
-- warning when more than 20 percent of the jobs open right now have not
-- been read by the AI yet.

select
    missing,
    total,
    'more than 20 percent of open jobs have no AI enrichment' as failure_reason
from (
    select
        count(*) filter (where e.job_id is null) as missing,
        count(*) as total
    from "warehouse"."main"."stg_remoteok_jobs" as j
    left join "warehouse"."main"."stg_job_enrichment" as e
        on e.job_id = j.job_id
)
where total > 0
  and missing * 1.0 / total > 0.2
  
  
      
    ) dbt_internal_test