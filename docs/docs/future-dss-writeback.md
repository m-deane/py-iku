# Future DSS Write-back Design Doc

Placeholder — design doc content arrives in M9.

Topics to cover:
- Auth model (API key vs OAuth, key rotation, scope minimization)
- Idempotency strategy (deterministic recipe ids, content-hash check, upsert-or-skip)
- Rollback (snapshot of previous DSS project state, reverse-diff apply, manual restore button)
- Permissions matrix (admin vs editor vs viewer x create/update/delete recipe/dataset/connection)
- Required dataikuapi surface
- Validation pre-flight
- Telemetry and audit hooks
