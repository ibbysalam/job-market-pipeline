{{ config(severity='warn') }}

-- Garbled characters (like "Ã" in "Ã–sterreich") mean broken encoding
-- somewhere upstream. This is a WARNING and not an error on purpose: the
-- pipeline still works, but a person should look. Choosing warn or error
-- is a decision about how bad each problem really is.

select
    job_id,
    'AI answer contains garbled characters' as failure_reason
from {{ ref('stg_job_enrichment') }}
where regexp_matches(
    coalesce(summary, '') || ' ' || coalesce(nigeria_evidence, ''),
    '[\x{C3}\x{C2}]'
)
