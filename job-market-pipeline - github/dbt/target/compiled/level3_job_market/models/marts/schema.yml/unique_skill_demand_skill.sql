
    
    

select
    skill as unique_field,
    count(*) as n_records

from "warehouse"."main"."skill_demand"
where skill is not null
group by skill
having count(*) > 1


