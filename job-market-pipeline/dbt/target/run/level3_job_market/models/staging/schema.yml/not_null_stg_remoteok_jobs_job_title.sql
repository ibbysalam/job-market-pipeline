
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select job_title
from "warehouse"."main"."stg_remoteok_jobs"
where job_title is null



  
  
      
    ) dbt_internal_test