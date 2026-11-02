
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select seniority
from "warehouse"."main"."stg_job_enrichment"
where seniority is null



  
  
      
    ) dbt_internal_test