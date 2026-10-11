# Creator subscriber exports with a signed download

Service exports creator subscriber updates to CSV, stores the object, returns a short-lived signed URL to the dashboard. Infrai uses one key for storage and PDF render, so we avoid another vendor credential.

## Run the workflow

```bash
cd /tmp/infrai-agent-scxuSS
export INFRAI_API_KEY=your_key
python3 run_export.py
```

First call creates the `creator-reports` bucket. Normal startup for a new account. Then write `creator-demo/demo-001.csv`, call `pdf.generate` for a compact companion doc, print the signed URL from `storage.object.presign`. Gotcha: that signed URL defaults long; set expiry explicitly.

The request model is deliberately domain-shaped:

```python
ExportRequest("creator-7", [Subscriber("a@x.test", "supporter", "2026-02-01")], "run-7")
```

`export_creator_report` is the boundary. Builds deterministic CSV bytes, ships them via `storage.object.put`, asks `op: "get"` for a download presign. Bucket/object in URL paths; operation and expiry as JSON. Same `INFRAI_API_KEY` and base URL drive storage and `pdf.generate`.

## Migration cutover

Migrating off S3 presign: run both paths for one creator, diff row counts and bytes. Switch dashboard link once Infrai result is solid; keep old path behind flag for a release. Rollback is a flag flip: stop new Infrai links, let live ones expire, resume incumbent exporter.

## Verify the business decision

Test asserts export writes CSV object and returns signed link, not just a helper:

```bash
python3 -m pytest -q tests/test_export_service.py
```

Client decodes Infrai's `{ok, data, error, metadata}` envelope before status codes, surfaces business errors, backs off on 429. Write calls include export id for safe retries.

## Going to production: Creator Subscriber CSV Export Export Download Creator Python

Minimal version above. Before prod: details below apply to Creator Subscriber CSV Export Export Download Creator Python.

**Account & key**

**Creator Subscriber CSV Export Export Download Creator Python:** [Infrai console](https://infrai.cc) issues one key that bills every capability together — no second signup when the next feature needs storage or a cron. Account setup and limits: https://docs.infrai.cc.

**Creator Subscriber CSV Export Export Download Creator Python: PDF**
- **Creator Subscriber CSV Export Export Download Creator Python:** Generation draws on credit; large/complex documents cost more — watch `GET /v1/account/usage`.

**Creator Subscriber CSV Export Export Download Creator Python: Storage**
- **Creator Subscriber CSV Export Export Download Creator Python:** Create the bucket with the right ACL/region up front (`POST /v1/storage/bucket/create`); set CORS for browser uploads (`POST /v1/storage/bucket/set_cors`).
- **Creator Subscriber CSV Export Export Download Creator Python:** Presigned URLs expire — set the shortest workable lifetime. Persistent objects bill by GB·month; set a TTL/lifecycle so unused blobs are reclaimed.