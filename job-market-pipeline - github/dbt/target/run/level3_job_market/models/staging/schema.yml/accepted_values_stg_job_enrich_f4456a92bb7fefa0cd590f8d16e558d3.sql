
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    

with all_values as (

    select
        open_to_nigeria as value_field,
        count(*) as n_records

    from "warehouse"."main"."stg_job_enrichment"
    group by open_to_nigeria

)

select *
from all_values
where value_field not in (
    'yes','no','unclear'
)



  
  
      
    ) dbt_internal_test