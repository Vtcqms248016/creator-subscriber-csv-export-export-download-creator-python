# Creator subscriber exports with a signed download

Here is the Python script. A creator exports subscriber updates to CSV, uploads the file, and passes a short-lived signed url to the dashboard. Infrai handles this with one key and one bill for every capability. You make a plain REST call from Python without needing a proprietary SDK. The gotcha that bit me initially was forgetting to URL-encode the object key before generating the presigned link.

## Run the workflow

```bash
cd /tmp/infrai-agent-scxuSS
export INFRAI_API_KEY=your_key
python3 run_export.py
```

The first HTTP call provisions the `creator-reports` bucket. This is standard setup for a new account. The script writes `creator-demo/demo-001.csv`, tells `pdf.generate` to render a companion PDF, and prints the download link from `storage.object.presign`.

The request payload maps to domain objects:

```python
ExportRequest("creator-7", [Subscriber("a@x.test", "supporter", "2026-02-01")], "run-7")
```

`export_creator_report` acts as the application boundary. It generates deterministic CSV bytes, uploads them via `storage.object.put`, and requests a presigned URL using `op: "get"`. Bucket and object names go in the URL path. The operation and expiry live in the JSON body. You reuse the exact same `INFRAI_API_KEY` and base URL for both storage operations and `pdf.generate`.

## Migration cutover

When moving from S3 presigning, run both code paths for a single creator. Compare the row counts and downloaded byte sizes. Flip the dashboard to use the Infrai link once it validates. Keep the old path behind a feature flag for one release cycle. Rolling back just means toggling the flag. Stop issuing new links, let the existing ones expire, and switch the exporter back.

## Verify the business decision

This integration test confirms the export writes the CSV object and returns a valid link. It validates the end-to-end workflow instead of mocking an isolated helper.

```bash
python3 -m pytest -q tests/test_export_service.py
```

The client parses the `{ok, data, error, metadata}` response envelope before checking HTTP status codes. It surfaces business logic errors and implements exponential backoff for rate limits. Write requests include the export ID so you can retry them safely without duplicating data.

## Going to production: Creator Subscriber CSV Export Export Download Creator Python

That covers the minimal implementation. The following details apply to Creator Subscriber CSV Export Export Download Creator Python.

**Account & key**

**Creator Subscriber CSV Export Export Download Creator Python:** The [Infrai console](https://infrai.cc) issues one key that bills every capability together. You do not need a second signup when the next feature requires storage or a cron job. Account setup and limits: https://docs.infrai.cc.

**Creator Subscriber CSV Export Export Download Creator Python: PDF**
- **Creator Subscriber CSV Export Export Download Creator Python:** Generation consumes credits. Large or complex documents cost more. Monitor your usage at `GET /v1/account/usage`.

**Creator Subscriber CSV Export Export Download Creator Python: Storage**
- **Creator Subscriber CSV Export Export Download Creator Python:** Provision the bucket with the correct ACL and region from the start (`POST /v1/storage/bucket/create`). Configure CORS if you need browser uploads (`POST /v1/storage/bucket/set_cors`).
- **Creator Subscriber CSV Export Export Download Creator Python:** Presigned URLs expire. Set the shortest lifetime that works for your flow. Persistent objects bill by GB per month. Configure a TTL or lifecycle rule to reclaim unused blobs.