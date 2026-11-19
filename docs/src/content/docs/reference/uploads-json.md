---
title: uploads.json
description: Every field of uploads.json.
sidebar:
  order: 8
---

<!-- Generated from pydelity's code by scripts/generate_reference_docs.py. Run `just docs-reference` instead of editing this file. -->

The contents of `uploads.json`: at most one upload per provider and PDF.

## `uploads.json`

The contents of `uploads.json`: at most one upload per provider and PDF.

- `pydelity_version` (string; required): The pydelity version that last wrote
  the file.
- `schema_version` (string; required): The version of this file's schema,
  `"MAJOR.MINOR"`.
- `uploads` (list of objects ([`uploads[]`](#uploads)); required): The uploads,
  one per provider and PDF SHA-256.

## `uploads[]`

One PDF uploaded to one provider.

- `bytes` (integer; required): The PDF's size in bytes.
- `expires_at` (date and time (ISO 8601) or null; required): When the provider
  deletes the file (UTC), or `None` when it sets no expiry.
- `file_id` (string; required): The provider's ID for the file.
- `pdf_name` (string; required): The PDF's file name.
- `pdf_sha256` (string; required): The PDF's SHA-256 hex digest.
- `provider` (one of `anthropic`, `openai`; required): The provider, `anthropic`
  or `openai`.
- `uploaded_at` (date and time (ISO 8601); required): When the upload finished
  (UTC).
