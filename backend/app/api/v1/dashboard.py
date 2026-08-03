"""HTTP endpoints for the admin dashboard."""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.responses import StandardResponse, success_response
from app.core.permissions import require_admin
from app.database.session import get_db
from app.models.user import User
from app.schemas.dashboard import DashboardRange, DashboardResponse
from app.services.dashboard_service import DashboardService

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


def _service(db: AsyncSession = Depends(get_db)) -> DashboardService:
    """Build a :class:`DashboardService` bound to the request session."""
    return DashboardService(db)


@router.post(
    "",
    response_model=StandardResponse,
    summary="Get aggregate dashboard statistics (admin)",
)
async def get_dashboard(
    payload: DashboardRange,
    service: DashboardService = Depends(_service),
    _admin: User = Depends(require_admin),
):
    dashboard = await service.get_dashboard_data(payload.start_date, payload.end_date)
    return success_response(
        data=DashboardResponse.model_validate(dashboard), message="Dashboard fetched."
    )
