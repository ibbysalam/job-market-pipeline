
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    

select
    skill as unique_field,
    count(*) as n_records

from "warehouse"."main"."skill_demand"
where skill is not null
group by skill
having count(*) > 1



  
  
      
    ) dbt_internal_test