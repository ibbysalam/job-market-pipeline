
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    

select
    story_id as unique_field,
    count(*) as n_records

from "warehouse"."main"."stg_hackernews_stories"
where story_id is not null
group by story_id
having count(*) > 1



  
  
      
    ) dbt_internal_test