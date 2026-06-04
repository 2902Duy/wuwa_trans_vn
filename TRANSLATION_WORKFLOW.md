# Mistral Game Translation Workflow

This workflow keeps `db_en` unchanged and writes all generated translation files to `mistral_translate_work/`.

## 1. Add API keys

Create a local file named `.env` in this folder. It is ignored by git.

```text
MISTRAL_API_KEYS=key_from_account_1,key_from_account_2,key_from_account_3,key_from_account_4,key_from_account_5
```

You can copy the template:

```powershell
Copy-Item .env.example .env
```

Another supported option is `.mistral_keys.txt`, one key per line:

```text
key_from_account_1
key_from_account_2
key_from_account_3
key_from_account_4
key_from_account_5
```

Alternatively, set keys through an environment variable:

```powershell
$env:MISTRAL_API_KEYS="key1,key2,key3,key4,key5"
```

## 2. Export clean English source

```powershell
python mistral_game_translate.py export
```

Output:

- `mistral_translate_work/export/`

## 3. Translate with up to 5 keys in parallel

Small test:

```powershell
python mistral_game_translate.py translate --limit 100 --max-keys 5
```

Larger run:

```powershell
python mistral_game_translate.py translate --limit 5000 --max-keys 5 --batch-size 12 --max-chars 3600
```

Full run:

```powershell
python mistral_game_translate.py translate --max-keys 5 --batch-size 12 --max-chars 3600
```

Outputs:

- `mistral_translate_work/cache_mistral.json`
- `mistral_translate_work/review/`
- `mistral_translate_work/review_translated_only/`

## 4. Review before import

Open CSV files in:

```text
mistral_translate_work/review_translated_only/
```

Rows with `status=needs_review` have token, format, or encoding warnings.

Run the free rule-based audit after each translation batch:

```powershell
python mistral_game_translate.py audit
```

Run selective AI review for risky lines only:

```powershell
python mistral_game_translate.py review-ai --limit 500
```

Recommended quality workflow:

```powershell
python mistral_game_translate.py translate --limit 5000 --max-keys 5 --batch-size 12 --max-chars 3600
python mistral_game_translate.py audit
python mistral_game_translate.py review-ai --limit 500
```

Use `review-ai` on dialogue, lore, quest, token-heavy, or rule-flagged lines. Do not AI-review the entire cache by default unless time and cost are acceptable.

## 5. Import into a copied DB folder

This does not modify `db_en`.

```powershell
python mistral_game_translate.py import --out-db-dir work_db_vi_mistral --force
```
