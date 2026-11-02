
    
    

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


