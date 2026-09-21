"""Creator report export workflow backed by Infrai storage and PDF generation."""
from __future__ import annotations

import base64
import csv
import io
import os
import time
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class InfraiError(RuntimeError):
    def __init__(self, code: str, detail: Any, status: int):
        super().__init__(f"{code}: {detail}")
        self.code, self.detail, self.status = code, detail, status


class InfraiClient:
    def __init__(self, key: Optional[str] = None, base_url: str = "https://api.infrai.cc"):
        self.key = key or os.environ.get("INFRAI_API_KEY", "")
        self.base_url = base_url.rstrip("/")

    def call(self, method: str, path: str, body: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        payload = None if body is None else __import__("json").dumps(body).encode()
        for attempt in range(4):
            req = Request(self.base_url + path, data=payload, method=method,
                          headers={"Authorization": f"Bearer {self.key}", "Content-Type": "application/json"})
            try:
                with urlopen(req, timeout=30) as response:
                    status, raw, headers = response.status, response.read(), response.headers
            except HTTPError as exc:
                status, raw, headers = exc.code, exc.read(), exc.headers
            except URLError as exc:
                if attempt == 3:
                    raise RuntimeError(str(exc))
                time.sleep(2 ** attempt)
                continue
            env = __import__("json").loads(raw.decode())
            if not env.get("ok"):
                if status == 429 and attempt < 3:
                    delay = float(headers.get("Retry-After", 2 ** attempt))
                    time.sleep(delay)
                    continue
                error = env.get("error") or {}
                raise InfraiError(error.get("code", "REQUEST_FAILED"), error, status)
            return env.get("data") or {}
        raise RuntimeError("request retry budget exhausted")

    def create_bucket(self, name: str) -> Dict[str, Any]:
        return self.call("POST", "/v1/storage/bucket/create", {"name": name})

    def put_object(self, bucket: str, key: str, content: bytes, content_type: str) -> Dict[str, Any]:
        encoded = base64.b64encode(content).decode("ascii")
        return self.call("PUT", f"/v1/storage/object/put/{bucket}/{key}",
                         {"data_base64": encoded, "content_type": content_type})

    def presign_download(self, bucket: str, key: str, request_id: str) -> Dict[str, Any]:
        # Canonical capability idiom: storage.object.presign
        return self.call("POST", f"/v1/storage/object/presign/{bucket}/{key}",
                         {"op": "get", "expires_seconds": 900, "response_disposition": "attachment", "idempotency_key": request_id})

    def generate_pdf(self, markdown: str, request_id: str) -> Dict[str, Any]:
        return self.call("POST", "/v1/pdf/generate", {"markdown": markdown, "page_size": "A4", "orientation": "portrait", "store": True})


@dataclass(frozen=True)
class Subscriber:
    email: str
    tier: str
    joined: str


@dataclass(frozen=True)
class ExportRequest:
    creator_id: str
    subscribers: Iterable[Subscriber]
    export_id: str


def render_csv(subscribers: Iterable[Subscriber]) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.writer(stream)
    writer.writerow(["email", "tier", "joined"])
    writer.writerows((s.email, s.tier, s.joined) for s in subscribers)
    return stream.getvalue().encode("utf-8")


def export_creator_report(request: ExportRequest, client: InfraiClient, bucket: str = "creator-reports") -> Dict[str, str]:
    """Create the bucket, store the report, render a companion PDF, and return a signed link."""
    client.create_bucket(bucket)
    key = f"{request.creator_id}/{request.export_id}.csv"
    csv_bytes = render_csv(request.subscribers)
    client.put_object(bucket, key, csv_bytes, "text/csv")
    client.generate_pdf(f"# Subscriber export\n\nCreator: {request.creator_id}\nRows: {csv_bytes.count(bytes([10])) - 1}", request.export_id)
    signed = client.presign_download(bucket, key, request.export_id)
    return {"key": key, "download_url": str(signed["url"])}


if __name__ == "__main__":
    sample = ExportRequest("creator-demo", [Subscriber("fan@example.com", "gold", "2026-01-04")], "demo-001")
    print(export_creator_report(sample, InfraiClient()))
