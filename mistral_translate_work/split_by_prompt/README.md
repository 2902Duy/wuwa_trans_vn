# Split By Prompt Excel Pack

- Source dir: `mistral_translate_work\review_translated_only`
- Output dir: `mistral_translate_work\split_by_prompt`
- Total rows: 242385
- Excel chunks: 564
- Vietnamese translations from the original split JSON have been removed.
- TXT batch files have been removed.

## Folders

- `json/<domain>/<source_file>/...`: metadata chunks without old `translation_vi`.
- `excel/<domain>/<source_file>/...`: Excel chunks for retranslation.
- `manifest.json`: mapping data for applying translations back to the original files.

## Excel Columns

- `split_id`
- `prompt_domain`
- `prompt_file`
- `source_file`
- `original_index`
- `database`
- `table`
- `primary_key_column`
- `primary_key`
- `column`
- `category`
- `source_en`
- `new_translation_vi`
- `translator_note`

Fill only `new_translation_vi` for the new Vietnamese translation.
