
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select story_id
from "warehouse"."main"."stg_hackernews_stories"
where story_id is null



  
  
      
    ) dbt_internal_test