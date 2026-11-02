-- A custom data quality test, beyond dbt's built-in not_null/unique.
--
-- dbt singular tests work backwards from what you'd expect: the query
-- should return the rows that are WRONG. If it returns zero rows, the
-- test passes. If it returns any rows, dbt fails the test and shows
-- you those rows.
--
-- This one catches a silent failure mode specific to our extractor
-- design: load_remoteok.py does CREATE OR REPLACE TABLE every run, so
-- if remoteok.py ever came back with zero matching listings (an API
-- outage, a broken filter, Remotive-style silent breakage) the raw
-- table would quietly go to zero rows with no error anywhere. This
-- test turns that silent failure into a loud one.

select 'raw_remoteok_jobs has zero rows' as failure_reason
from {{ source('raw', 'raw_remoteok_jobs') }}
having count(*) = 0
