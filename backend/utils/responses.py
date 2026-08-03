from fastapi.responses import JSONResponse
from typing import Any

def success_response(data: Any, message: str = "Operation successful", status_code: int = 200) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "success": True,
            "message": message,
            "data": data
        }
    )

def error_response(message: str, errors: Any = None, status_code: int = 400) -> JSONResponse:
    content = {
        "success": False,
        "message": message
    }
    if errors is not None:
        content["errors"] = errors
    return JSONResponse(
        status_code=status_code,
        content=content
    )
