# Future Work: DSS Write-back

This document describes the design for direct Dataiku DSS write-back from py-iku Studio. This feature is planned for Milestone M10 and is not yet implemented. The `DSSApiSink` class exists as a stub in `apps/api/app/sinks.py` and raises `NotImplementedError`. The `/settings/connections` page in the web UI is built but disabled behind a feature flag.

Estimated implementation scope: 3–4 weeks for a production-ready initial version against DSS 14.

---

## 1. Authentication model

### API key approach

Dataiku DSS uses API keys for programmatic access (`dataikuapi.DSSClient`). Each key is scoped to a DSS user account and inherits that user's project permissions.

The Studio integration will:

1. Accept a DSS API key from the user via the `/settings/connections` UI page.
2. POST the key to `apps/api`, which encrypts it at rest using [Fernet](https://cryptography.io/en/latest/fernet/) symmetric encryption before persisting.
3. Never return the plaintext key to the browser — the settings drawer shows only the last 4 characters as confirmation.
4. Inject the decrypted key into `DSSApiSink` at request time.

```python
# apps/api/app/security/secrets.py (existing stub)
def store_dss_key(connection_id: str, raw_key: str) -> None:
    """Encrypt and persist a DSS API key."""
    fernet = Fernet(settings.FERNET_KEY)
    encrypted = fernet.encrypt(raw_key.encode())
    # Store encrypted bytes in SQLite connections table
    connections_repo.upsert(connection_id, encrypted_key=encrypted)

def load_dss_key(connection_id: str) -> str:
    """Retrieve and decrypt a DSS API key."""
    fernet = Fernet(settings.FERNET_KEY)
    record = connections_repo.get(connection_id)
    return fernet.decrypt(record.encrypted_key).decode()
```

### Key rotation

API keys should be rotatable without downtime:

1. User generates a new key in DSS (`Settings → API Keys → Create Key`).
2. User updates the key in Studio's `/settings/connections` page.
3. Studio immediately starts using the new key for subsequent requests.
4. Old key can be revoked in DSS after confirming the new key works.

There is no background refresh mechanism — key rotation is a manual, explicit action. The `/audit` log records a `connection.key_rotated` event when a key is updated.

### OAuth (future)

DSS 14 does not ship a built-in OAuth 2.0 server. OAuth integration would require a DSS plugin or a custom identity provider. This is out of scope for M10 — API keys are sufficient for the target use-case (internal teams, self-hosted).

### Scope minimization

DSS API keys are account-scoped (they carry all permissions of the owning user). To minimize blast radius:

- Create a dedicated service account in DSS for Studio (e.g. `py-iku-studio-bot`).
- Grant the service account only `WRITE` access to the specific projects it needs to modify.
- Document this recommendation prominently in the `/settings/connections` UI.

---

## 2. Idempotency strategy

Write-back must be safe to retry. A failed write (network error, DSS API error, partial failure) should not leave the project in an inconsistent state, and a successful retry should not create duplicate recipes.

### Deterministic recipe IDs

`py2dataiku` generates recipe names by sanitising the output dataset name (e.g. `groupby_output_csv_1` for a GROUPING recipe with output `output.csv`). These names are deterministic: the same Python code, converted twice, produces the same recipe names.

```python
# py2dataiku/generators/base.py
def _sanitize_name(self, raw: str) -> str:
    """Produce a stable, filesystem-safe recipe name."""
    return re.sub(r"[^a-z0-9_]", "_", raw.lower())[:63]
```

Recipe names serve as natural idempotency keys.

### Content-hash check (upsert-or-skip)

Before writing a recipe, `DSSApiSink` will:

1. Call `project.get_recipe(recipe_name)` to check if the recipe already exists.
2. If it exists, compute a SHA-256 hash of the recipe definition payload.
3. Compare against the hash stored in the recipe's `userMeta.py_iku_hash` field.
4. If the hashes match, skip the write (no-op).
5. If the hashes differ (updated conversion), proceed with `recipe.set_definition_and_payload()`.

```python
import hashlib, json
from dataikuapi import DSSClient

def _compute_payload_hash(payload: dict) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode()).hexdigest()

def _write_recipe_idempotent(
    project,
    recipe_name: str,
    recipe_type: str,
    payload: dict,
) -> str:
    """Write a recipe, skipping if the content hash matches. Returns 'created', 'updated', or 'skipped'."""
    new_hash = _compute_payload_hash(payload)
    try:
        recipe = project.get_recipe(recipe_name)
        settings = recipe.get_settings()
        existing_hash = settings.obj_data.get("userMeta", {}).get("py_iku_hash")
        if existing_hash == new_hash:
            return "skipped"
        # Hash mismatch — update
        settings.obj_data["userMeta"]["py_iku_hash"] = new_hash
        settings.save()
        recipe.set_definition_and_payload(settings.get_recipe_raw_definition(), payload)
        return "updated"
    except Exception:
        # Recipe does not exist — create it
        recipe = project.create_recipe(recipe_type, recipe_name, inputs=[], outputs=[])
        settings = recipe.get_settings()
        settings.obj_data.setdefault("userMeta", {})["py_iku_hash"] = new_hash
        settings.save()
        recipe.set_definition_and_payload(settings.get_recipe_raw_definition(), payload)
        return "created"
```

### Transactional write order

To avoid leaving the flow in a partially-written state, write in dependency order (topological sort of the `FlowGraph`): datasets first, then recipes leaf-to-root. If any write fails, the already-written nodes remain but the flow is incomplete — the dry-run report will flag this on the next attempt.

---

## 3. Rollback

### Pre-write snapshot

Before writing any recipe or dataset to DSS, `DSSApiSink` takes a snapshot of the current project state:

```python
def _snapshot_project(project) -> dict:
    """Capture all recipe definitions for rollback."""
    snapshot = {}
    for recipe in project.list_recipes():
        rcp = project.get_recipe(recipe["name"])
        snapshot[recipe["name"]] = {
            "type": recipe["type"],
            "definition": rcp.get_settings().get_recipe_raw_definition(),
            "payload": rcp.get_settings().get_payload(),
        }
    return snapshot
```

The snapshot is stored in the `audit_repo` alongside the write event, so it can be retrieved even after the API server restarts.

### Reverse-diff restore

The rollback mechanism applies the snapshot in reverse:

```python
def _rollback(project, snapshot: dict, added_recipe_names: list[str]) -> None:
    """Restore recipes to pre-write state. Delete any newly added recipes."""
    for name in added_recipe_names:
        try:
            project.get_recipe(name).delete()
        except Exception:
            pass  # Already gone
    for name, state in snapshot.items():
        try:
            recipe = project.get_recipe(name)
            recipe.set_definition_and_payload(state["definition"], state["payload"])
        except Exception:
            pass  # Log but continue rollback
```

### Manual restore button

The Studio UI will expose a **Restore Previous State** button on the deployment status panel. This calls a new API endpoint `POST /flows/{id}/restore/{audit_event_id}` which retrieves the snapshot from the audit log and triggers `_rollback`.

---

## 4. Permissions matrix

DSS permissions are project-level and role-based. The matrix below shows what the Studio service account needs for each write-back operation:

| Operation | DSS permission | API call |
|-----------|---------------|----------|
| Create recipe | `WRITE_CONF` on project | `project.create_recipe()` |
| Update recipe | `WRITE_CONF` on recipe | `recipe.set_definition_and_payload()` |
| Delete recipe | `ADMIN` on recipe | `recipe.delete()` |
| Create dataset | `WRITE_CONF` on project | `project.create_dataset()` |
| Update dataset schema | `WRITE_CONF` on dataset | `dataset.set_schema()` |
| Replace flow connections | `WRITE_CONF` on project | `flow.replace_input()`, `flow.replace_output()` |
| Read project metadata | `READ` on project | `project.get_metadata()` |

The service account should be granted `WRITE_CONF` on the target project. `ADMIN` is only needed if delete-and-recreate rollback is required; prefer update-in-place to avoid needing `ADMIN`.

Studio will check effective permissions before attempting a write, via `dataikuapi` permission introspection (planned; may require DSS API extension).

---

## 5. Required `dataikuapi` surface

The M10 implementation targets `dataikuapi >= 14.0.0`. Key calls:

```python
from dataikuapi import DSSClient

# Connect
client = DSSClient("https://dss.example.com", "api_key")
project = client.get_project("MY_PROJECT")

# List recipes
for recipe in project.list_recipes():
    print(recipe["name"], recipe["type"])

# Create a new recipe
recipe = project.create_recipe(
    recipe_type="grouping",
    name="groupby_by_region",
    inputs=[{"ref": "input_csv"}],
    outputs=[{"ref": "output_grouped"}],
)

# Set recipe definition and payload
settings = recipe.get_settings()
settings.get_recipe_raw_definition()["params"] = {
    "groupingKeys": [{"column": "region"}],
    "aggregations": [{"column": "amount", "type": "SUM"}],
}
settings.save()

# Set dataset schema
dataset = project.get_dataset("output_grouped")
dataset.set_schema({
    "columns": [
        {"name": "region", "type": "string"},
        {"name": "amount_sum", "type": "double"},
    ]
})

# Replace flow connections (for re-routing)
flow = project.get_flow()
flow.replace_input(recipe_name="join_step", old_input="old_ds", new_input="new_ds")
flow.replace_output(recipe_name="groupby_step", old_output="old_out", new_output="new_out")
```

### Error taxonomy

`dataikuapi` raises `dataikuapi.utils.DataikuException` for API errors. Key cases to handle:

| Exception message / status | Meaning | Studio action |
|---------------------------|---------|--------------|
| `404 Recipe not found` | Recipe does not exist yet | Create it |
| `409 Recipe already exists` | Name collision | Use upsert logic |
| `403 Forbidden` | Insufficient permissions | Surface in UI with permission guidance |
| `502 Bad Gateway` | DSS server unreachable | Retry with backoff; surface connection error |
| `500 Internal Server Error` | DSS-side bug | Log to audit, surface error message |

---

## 6. Validation pre-flight

Before attempting any write, `DSSApiSink.dry_run()` performs a validation pass:

### Connection reachability

```python
def _check_reachability(host: str, api_key: str) -> bool:
    client = DSSClient(host, api_key)
    try:
        client.get_instance_info()  # fast health check
        return True
    except Exception:
        return False
```

### Schema compatibility

For each output dataset, check that the `DataikuDataset` schema (as inferred by `py2dataiku`) is compatible with any existing DSS dataset schema:

1. If the dataset does not exist in DSS, no check needed (will be created).
2. If it exists, compare column names and types.
3. Flag type mismatches as errors (e.g. `string` in py-iku vs `double` in DSS).
4. Flag added columns as warnings (safe to add, but may break downstream recipes).
5. Flag removed columns as errors (will break existing downstream recipes).

### Recipe-type version match (DSS 14)

DSS 14 supports all 37 `RecipeType` values in `py2dataiku`. However, some types require specific DSS plugins or feature flags:

| Recipe type | DSS 14 requirement |
|------------|-------------------|
| FUZZY_JOIN | Requires `fuzzy-join` plugin |
| GEO_JOIN | Requires geographic processing plugin |
| AI_ASSISTANT_GENERATE | Requires AI Assistant feature flag |
| PREDICTION_SCORING, CLUSTERING_SCORING, EVALUATION | Require a trained model saved in the project |

`DSSApiSink.dry_run()` will call `client.get_plugin("fuzzy-join").is_installed()` (or equivalent) for relevant recipe types and include unsatisfied prerequisites in the `DryRunReport.warnings`.

---

## 7. Telemetry and audit hooks

All write-back events are appended to the Studio audit log (`/audit`). The event payload includes:

| Field | Description |
|-------|-------------|
| `event_type` | `dss.write`, `dss.dry_run`, `dss.rollback`, `dss.write.failed` |
| `actor` | Authenticated user (or `anonymous` in unauthenticated mode) |
| `dss_host` | DSS instance hostname (truncated, no auth) |
| `dss_project_key` | Target DSS project key |
| `diff_hash` | SHA-256 of the `DataikuFlow.to_dict()` payload being written |
| `write_summary` | `{created: N, updated: N, skipped: N}` |
| `error` | RFC 7807 problem object if the write failed |

API keys, Fernet keys, and bearer tokens are **never** included in audit payloads.

```python
# apps/api/app/routes/flows.py (sketch)
async def write_to_dss(flow_id: str, connection_id: str, request: Request):
    flow = flows_repo.get(flow_id)
    sink = DSSApiSink(connection_id=connection_id)
    result = await sink.write(flow, opts=SinkOptions(dry_run=False))
    audit_repo.append({
        "event_type": "dss.write",
        "actor": request.state.actor,
        "dss_project_key": sink.project_key,
        "diff_hash": hashlib.sha256(json.dumps(flow.to_dict(), sort_keys=True).encode()).hexdigest(),
        "write_summary": result.summary,
    })
    return result
```

The `/audit` UI page will include a dedicated `dss.write` filter to let users review all write-back operations.

---

## 8. Reference: existing stubs

The following are already in the codebase as stubs for M10 to fill in:

**`apps/api/app/sinks.py`** — `DSSApiSink` stub:

```python
class DSSApiSink(FlowSink):
    """Stub. Raises NotImplementedError. Implement in M10."""
    def write(self, flow, opts):
        raise NotImplementedError(
            "DSS write-back is not yet implemented. "
            "See docs/future-dss-writeback.md for the design."
        )
    def dry_run(self, flow, opts):
        return DryRunReport(
            supported=False,
            next_steps=["Install dataikuapi >= 14.0.0", "Configure /settings/connections"],
        )
    def capabilities(self):
        return SinkCapabilities(supported=False, reason="Planned for M10")
```

**`apps/web/src/features/deploy/`** — UI stubs (disabled by feature flag `VITE_DSS_WRITEBACK_ENABLED`):
- Connections page at `/settings/connections` — lists DSS instances.
- Per-node deployment status badge in `FlowCanvas`.
- "Preview Deploy" CTA that opens the dry-run diff modal.

These stubs allow the M10 implementation to focus on backend logic, with UI affordances already in place.
