from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from config import OUTPUT_DIR

router = APIRouter(tags=["export"])


@router.get("/songs/{song_id}/export")
async def export_result(song_id: str, format: str = "json"):
    if format == "json":
        result_path = OUTPUT_DIR / song_id / "result.json"
        if not result_path.exists():
            raise HTTPException(404, "Result not found")
        return FileResponse(
            str(result_path),
            media_type="application/json",
            filename=f"{song_id}_annotations.json",
        )

    raise HTTPException(400, f"Unsupported format: {format}. Supported: json")
