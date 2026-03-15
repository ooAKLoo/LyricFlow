from fastapi import APIRouter, HTTPException

from api.schemas import TaskStatusResponse, TaskStatus
from workers.celery_app import celery_app

router = APIRouter(tags=["tasks"])


@router.get("/tasks/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(task_id: str):
    result = celery_app.AsyncResult(task_id)

    if result.state == "PENDING":
        return TaskStatusResponse(
            task_id=task_id,
            status=TaskStatus.PENDING,
            progress=0,
            current_stage="Waiting in queue",
        )
    elif result.state == "PROGRESS":
        info = result.info or {}
        stage_map = {
            "preprocessing": (TaskStatus.PREPROCESSING, 15),
            "lyrics_fetching": (TaskStatus.LYRICS_FETCHING, 30),
            "aligning": (TaskStatus.ALIGNING, 50),
            "phonetics": (TaskStatus.PHONETICS, 65),
            "detecting": (TaskStatus.DETECTING, 80),
            "output": (TaskStatus.COMPLETED, 95),
        }
        stage = info.get("stage", "preprocessing")
        status, progress = stage_map.get(stage, (TaskStatus.PREPROCESSING, 10))
        return TaskStatusResponse(
            task_id=task_id,
            status=status,
            progress=progress,
            current_stage=info.get("message", stage),
        )
    elif result.state == "SUCCESS":
        info = result.result or {}
        return TaskStatusResponse(
            task_id=task_id,
            status=TaskStatus.COMPLETED,
            progress=100,
            current_stage="Complete",
            song_id=info.get("song_id", task_id),
        )
    elif result.state == "FAILURE":
        return TaskStatusResponse(
            task_id=task_id,
            status=TaskStatus.ERROR,
            progress=0,
            current_stage="Error",
            error_message=str(result.info) if result.info else "Unknown error",
        )

    raise HTTPException(404, "Task not found")
