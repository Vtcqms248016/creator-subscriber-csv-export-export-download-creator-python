from src.export_service import ExportRequest, InfraiClient, Subscriber, export_creator_report, render_csv


class FakeClient(InfraiClient):
    def __init__(self):
        self.calls = []

    def call(self, method, path, body=None):
        self.calls.append((method, path, body))
        if "presign" in path:
            return {"url": "https://download.test/report.csv"}
        return {"accepted": True}


def test_export_uploads_csv_and_returns_download_link():
    request = ExportRequest("creator-7", [Subscriber("a@x.test", "supporter", "2026-02-01")], "run-7")
    client = FakeClient()
    result = export_creator_report(request, client)
    assert result["download_url"].startswith("https://download.test/")
    assert any(path.endswith("/creator-7/run-7.csv") and method == "PUT" for method, path, _ in client.calls)
    put = next(body for method, path, body in client.calls if method == "PUT")
    assert "data_base64" in put and put["content_type"] == "text/csv"


def test_csv_has_stable_headers():
    assert render_csv([]).decode() == "email,tier,joined\r\n"
