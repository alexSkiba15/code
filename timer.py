from datetime import datetime
from typing import Annotated
from uuid import UUID

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, HTTPException, Query, status

from timer_service.api.schemas.timer import TimerRequestSchema
from timer_service.domain.callback_config.errors import CallbackConfigNotFoundError
from timer_service.domain.models import TimerModel
from timer_service.domain.timer.errors import TimerNotFoundError, TimerNotInPendingStatusError
from timer_service.domain.timer.interfaces import (
    CreateTimerUseCase,
    DeleteTimerUseCase,
    GetTimersUseCase,
    GetTimerUseCase,
)
from timer_service.enums import TimerStatus

router = APIRouter(prefix='/timer', tags=['timer'])


@router.post('/', response_model=TimerModel, status_code=status.HTTP_201_CREATED)
@inject
async def create_timer(
    timer: TimerRequestSchema,
    create_timer_u_c: CreateTimerUseCase = Depends(Provide['create_timer_use_case']),
) -> TimerModel:
    try:
        return await create_timer_u_c(timer=timer)
    except CallbackConfigNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.get('/{timer_id}', response_model=TimerModel)
@inject
async def get_timer(
    timer_id: UUID,
    get_timer_u_c: GetTimerUseCase = Depends(Provide['get_timer_use_case']),
) -> TimerModel:
    try:
        return await get_timer_u_c(timer_id=timer_id)
    except TimerNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.delete('/{timer_id}', status_code=status.HTTP_204_NO_CONTENT)
@inject
async def delete_timer(
    timer_id: UUID,
    delete_timer_u_c: DeleteTimerUseCase = Depends(Provide['delete_timer_use_case']),
) -> None:
    try:
        await delete_timer_u_c(timer_id=timer_id)
    except TimerNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except TimerNotInPendingStatusError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@router.get('/')
@inject
async def get_timers(
    timer_status: Annotated[
        TimerStatus | None,
        Query(description=f"Statuses: {', '.join(TimerStatus.values())}")
    ] = None,
    start_timer: datetime | None = None,
    end_timer: datetime | None = None,
    timer_ids: Annotated[list[UUID] | None, Query()] = None,
    page: int = 1,
    per_page: int = 100,
    get_timers_u_c: GetTimersUseCase = Depends(Provide['get_timers_use_case']),
) -> list[TimerModel]:
    try:
        return await get_timers_u_c(
            status=timer_status,
            start_timer=start_timer,
            end_timer=end_timer,
            ids=timer_ids,
            page=page,
            per_page=per_page,
        )
    except TimerNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
