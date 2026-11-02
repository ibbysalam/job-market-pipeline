
    
    

with all_values as (

    select
        seniority as value_field,
        count(*) as n_records

    from "warehouse"."main"."stg_job_enrichment"
    group by seniority

)

select *
from all_values
where value_field not in (
    'intern','junior','mid','senior','lead','unknown'
)


