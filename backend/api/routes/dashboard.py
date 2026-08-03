from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database.session import get_db
from schemas.dashboard.response import DashboardResponse
from schemas.dashboard.request import DashboardRangeRequest
from services.dashboard.dashboard_service import DashboardService
from api.dependencies import RoleRequired
from core.permissions import UserRole
from models.user import User

router = APIRouter()

@router.post("", response_model=DashboardResponse)
def get_dashboard(
    range_req: DashboardRangeRequest,
    current_user: User = Depends(RoleRequired([UserRole.ADMIN])),
    db: Session = Depends(get_db)
):
    dashboard_service = DashboardService(db)
    return dashboard_service.get_dashboard_data(range_req.start_date, range_req.end_date)