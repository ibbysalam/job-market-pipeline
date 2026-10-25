{#
  This is the whole point of the Level 3 project: SCD Type 2 history on
  job listings.

  stg_remoteok_jobs always reflects "what's open right now" (the loader
  replaces it wholesale every run). On its own, that table can't tell
  you a listing used to exist. A dbt snapshot fixes that: each time you
  run `dbt snapshot`, dbt compares the current source rows against what
  it saw last time, and:
    - a brand new job_id gets a new row, valid from now
    - a job_id with changed check_cols gets its old row closed out and
      a new row opened (a real content change, not just a resend)
    - a job_id that's MISSING from the current source entirely gets its
      row marked invalid (hard_deletes='invalidate') — this is how we
      detect a listing closed/filled, without the extractor or loader
      having to figure that out themselves.

  Query this later with:
    select * from remoteok_jobs_snapshot
    where dbt_valid_to is null   -- currently open listings
  or
    where dbt_valid_to is not null  -- listings that have since closed
#}

{% snapshot remoteok_jobs_snapshot %}

{{
    config(
      target_schema='snapshots',
      unique_key='job_id',
      strategy='check',
      check_cols=['job_title', 'company', 'tags', 'location', 'salary_min', 'salary_max', 'url'],
      hard_deletes='invalidate',
    )
}}

select *
from {{ ref('stg_remoteok_jobs') }}

{% endsnapshot %}
