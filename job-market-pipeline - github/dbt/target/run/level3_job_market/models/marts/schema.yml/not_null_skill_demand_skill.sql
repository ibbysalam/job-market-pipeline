
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select skill
from "warehouse"."main"."skill_demand"
where skill is null



  
  
      
    ) dbt_internal_test