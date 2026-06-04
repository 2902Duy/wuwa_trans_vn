# Translation Report

## Source

- Source DB directory: `db_en`
- Output DB directory: `work_db_vi_mistral`
- Translation cache: `mistral_translate_work/cache_mistral.json`
- Review files: `mistral_translate_work/review_translated_only`

## Translation Coverage

- Unique source strings: `173,949 / 173,949`
- DB text rows translated/imported: `242,385 / 242,385`
- Missing rows: `0`
- Empty translations: `0`
- Failed batches remaining: `0`

## Audit

- Rule audit PASS: `169,502`
- Rule audit REVIEW: `3,648`
- Rule audit RETRY: `799`
- Review rows marked `needs_review`: `2,698`

## Import QA

- Source DB count: `111`
- Output DB count: `111`
- Schema mismatches: `0`
- Rows checked after import: `242,385`
- Rows still identical to English source: `11,470`
- Empty rows after import: `0`
- Strict mojibake suspects: `0`

## Notes

The output DBs were created as a copy in `work_db_vi_mistral`; the original `db_en` directory was not modified.

Rows identical to the English source are not automatically wrong. They can include names, codes, acronyms, punctuation-only text, UI symbols, or terms intentionally preserved in English.
