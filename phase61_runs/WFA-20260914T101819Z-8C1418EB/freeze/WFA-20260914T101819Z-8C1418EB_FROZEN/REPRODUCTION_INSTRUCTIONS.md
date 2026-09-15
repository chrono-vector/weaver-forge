# Reproduction instructions — WFA-20260914T101819Z-8C1418EB

## Operator inputs (only)
Provide an audit request JSON with:
- `target_path`
- `claim` (id, statement, adapter, adapter_params)
- `policy` (optional)
- `protected_paths` / `prior_freeze_sums` (optional)

Do **not** manually construct manifests, hash inventories, decision documents, or freeze structure unless policy assigns a Human Review action.

## Command
```
python -m audit_lifecycle.cli run --request <request.json> --out <runs_parent_dir>
```
If `policy.human_review_required` is true, after decision and before freeze the workflow requires:
```
# write HUMAN_REVIEW.json into the run directory, then:
python -m audit_lifecycle.cli freeze --run <run_dir>
```

## Verify sealed package
```
python -m audit_lifecycle.cli verify --run <run_dir>
```
