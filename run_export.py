from src.export_service import ExportRequest, InfraiClient, Subscriber, export_creator_report


if __name__ == "__main__":
    request = ExportRequest("creator-demo", [Subscriber("fan@example.com", "gold", "2026-01-04")], "demo-001")
    print(export_creator_report(request, InfraiClient()))
