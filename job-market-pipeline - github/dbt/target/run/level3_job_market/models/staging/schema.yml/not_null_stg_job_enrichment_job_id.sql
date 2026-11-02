
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select job_id
from "warehouse"."main"."stg_job_enrichment"
where job_id is null



  
  
      
    ) dbt_internal_test