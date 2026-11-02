
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select summary
from "warehouse"."main"."stg_job_enrichment"
where summary is null



  
  
      
    ) dbt_internal_test