from sqlalchemy.future import select

from src.database.models.report import Report, ReportStatus
from .db_fixture import db_session, db_fill_data


async def test_create_report(db_session, db_fill_data):
    report = db_fill_data["report"]

    stmt = select(Report).where(Report.id == 1)
    result = await db_session.execute(stmt)
    is_report = result.scalar_one()

    assert is_report is not None
    assert is_report.title == report.title
    assert is_report.status == ReportStatus.ACTIVE
    assert is_report.region == None
    assert is_report.user == report.user and is_report.user.username == "artyombn"
    assert is_report.pet == report.pet and is_report.pet.name == "Douglas"
