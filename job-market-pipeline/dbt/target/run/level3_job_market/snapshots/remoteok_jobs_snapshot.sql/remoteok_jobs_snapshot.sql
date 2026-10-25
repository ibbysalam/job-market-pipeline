
      update "warehouse"."snapshots"."remoteok_jobs_snapshot" as DBT_INTERNAL_TARGET
    set dbt_valid_to = DBT_INTERNAL_SOURCE.dbt_valid_to
    from "remoteok_jobs_snapshot__dbt_tmp20261024160610701300" as DBT_INTERNAL_SOURCE
    where DBT_INTERNAL_SOURCE.dbt_scd_id::text = DBT_INTERNAL_TARGET.dbt_scd_id::text
      and DBT_INTERNAL_SOURCE.dbt_change_type::text in ('update'::text, 'delete'::text)
      
        and DBT_INTERNAL_TARGET.dbt_valid_to is null;
      

    insert into "warehouse"."snapshots"."remoteok_jobs_snapshot" ("job_id", "job_title", "company", "tags", "location", "salary_min", "salary_max", "url", "posted_at", "loaded_at", "dbt_updated_at", "dbt_valid_from", "dbt_valid_to", "dbt_scd_id")
    select DBT_INTERNAL_SOURCE."job_id",DBT_INTERNAL_SOURCE."job_title",DBT_INTERNAL_SOURCE."company",DBT_INTERNAL_SOURCE."tags",DBT_INTERNAL_SOURCE."location",DBT_INTERNAL_SOURCE."salary_min",DBT_INTERNAL_SOURCE."salary_max",DBT_INTERNAL_SOURCE."url",DBT_INTERNAL_SOURCE."posted_at",DBT_INTERNAL_SOURCE."loaded_at",DBT_INTERNAL_SOURCE."dbt_updated_at",DBT_INTERNAL_SOURCE."dbt_valid_from",DBT_INTERNAL_SOURCE."dbt_valid_to",DBT_INTERNAL_SOURCE."dbt_scd_id"
    from "remoteok_jobs_snapshot__dbt_tmp20261024160610701300" as DBT_INTERNAL_SOURCE
    where DBT_INTERNAL_SOURCE.dbt_change_type::text = 'insert'::text;


  