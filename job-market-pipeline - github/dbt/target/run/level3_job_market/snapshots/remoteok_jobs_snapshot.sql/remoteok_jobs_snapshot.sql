
      
    

    create  table
      "warehouse"."snapshots"."remoteok_jobs_snapshot"
  
    
    as (
      
    

    select *,
        md5(coalesce(cast(job_id as varchar ), '')
         || '|' || coalesce(cast(now()::timestamp as varchar ), '')
        ) as dbt_scd_id,
        now()::timestamp as dbt_updated_at,
        now()::timestamp as dbt_valid_from,
        
  
  coalesce(nullif(now()::timestamp, now()::timestamp), null)
  as dbt_valid_to
from (
        



select *
from "warehouse"."main"."stg_remoteok_jobs"

    ) sbq



    );
    
  
  