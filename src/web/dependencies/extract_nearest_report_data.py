from src.schemas import GeolocationNearestResponseWithReports
from src.schemas.report import ReportBasePhoto


def extract_data(
        report: ReportBasePhoto,
        geo_schema: GeolocationNearestResponseWithReports,
) -> dict:
    report_id = report.id
    report_title = report.title
    report_content = report.content
    report_status = report.status
    report_first_photo_url = report.photos[0].url if report.photos else None
    report_region = geo_schema.region
    geo = geo_schema.home_location
    geo_distance = round(geo_schema.distance / 1000)

    return {
        "report_id": report_id,
        "report_title": report_title,
        "report_content": report_content,
        "report_status": report_status,
        "report_first_photo_url": report_first_photo_url,
        "report_region": report_region,
        "geo": geo,
        "geo_distance": geo_distance,
    }
