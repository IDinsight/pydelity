"""The schema version of each file pydelity writes, as ``"MAJOR.MINOR"``.

A change that only adds fields raises the minor version. A change that removes,
renames or redefines a field raises the major version.
"""

# ``pdf_facts.json``: the measured facts and their summary.
FACTS_SCHEMA_VERSION = "1.0"

# Each line of ``cost.jsonl``: one model request and its cost.
LEDGER_SCHEMA_VERSION = "1.0"

# ``report/manifest.json``: the rendered page images.
MANIFEST_SCHEMA_VERSION = "1.0"

# ``pages/<NNNN>.json``: one page's extracted items and their checks.
PAGE_SCHEMA_VERSION = "1.0"

# ``run.json``: one run on one PDF.
RUN_SCHEMA_VERSION = "1.0"

# ``pdf_survey.json``: the checked survey of one PDF.
SURVEY_SCHEMA_VERSION = "1.0"

# ``uploads.json``: the PDF's uploads to each provider.
UPLOADS_SCHEMA_VERSION = "1.0"
