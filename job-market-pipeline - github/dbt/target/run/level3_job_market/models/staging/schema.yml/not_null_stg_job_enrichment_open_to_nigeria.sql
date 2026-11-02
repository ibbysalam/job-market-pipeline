
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select open_to_nigeria
from "warehouse"."main"."stg_job_enrichment"
where open_to_nigeria is null



  
  
      
    ) dbt_internal_test