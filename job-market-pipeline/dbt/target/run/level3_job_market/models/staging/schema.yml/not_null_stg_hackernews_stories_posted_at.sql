
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select posted_at
from "warehouse"."main"."stg_hackernews_stories"
where posted_at is null



  
  
      
    ) dbt_internal_test