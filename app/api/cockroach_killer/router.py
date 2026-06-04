import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc

from app.core.database import get_db
from app.core.security import get_current_active_user
from app.schemas.cockroach_killer import (
    CockroachScoreRequest,
    CockroachScoreResponse,
    CockroachLeaderboardResponse,
    CockroachLeaderboardEntry,
    CockroachUserStatsResponse,
)
from app.schemas.user import User
from app.models.cockroach_killer import CockroachKillRecord
from app.models.user import User as UserModel

logger = logging.getLogger(__name__)
router = APIRouter(prefix='/cockroach-killer', tags=['cockroach-killer'])


@router.post('/score', response_model=CockroachScoreResponse)
async def submit_score(
    request: CockroachScoreRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        record = CockroachKillRecord(
            user_id=current_user.id,
            score=request.score,
            player_name=request.player_name,
            theme=request.theme,
        )
        db.add(record)
        await db.commit()
        await db.refresh(record)

        result = await db.execute(
            select(
                func.count(CockroachKillRecord.id).label('plays'),
                func.max(CockroachKillRecord.score).label('best_score'),
            ).where(CockroachKillRecord.user_id == current_user.id)
        )

        row = result.one()
        plays = int(row.plays or 0)
        best_score = int(row.best_score or 0)

        title = next((entry['title'] for entry in [
            {'max': 15, 'title': 'Stressed Intern'},
            {'max': 35, 'title': 'SDE-2'},
            {'max': 50, 'title': 'Tech Lead'},
            {'max': float('inf'), 'title': 'Principal Architect'},
        ] if request.score <= entry['max']), 'Stressed Intern')

        return {
            'message': 'Score recorded successfully',
            'score': request.score,
            'best_score': best_score,
            'plays': plays,
            'title': title,
        }
    except Exception as exc:
        logger.error('Failed to submit cockroach killer score: %s', exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail='Unable to record score at this time',
        )


@router.get('/leaderboard', response_model=CockroachLeaderboardResponse)
async def get_leaderboard(db: AsyncSession = Depends(get_db)):
    try:
        result = await db.execute(
            select(
                CockroachKillRecord.user_id,
                UserModel.full_name,
                UserModel.email,
                func.max(CockroachKillRecord.score).label('best_score'),
                func.count(CockroachKillRecord.id).label('total_plays'),
            )
            .join(UserModel, UserModel.id == CockroachKillRecord.user_id)
            .group_by(CockroachKillRecord.user_id, UserModel.full_name, UserModel.email)
            .order_by(desc('best_score'), desc('total_plays'))
            .limit(12)
        )

        entries = [
            CockroachLeaderboardEntry(
                user_id=row.user_id,
                player_name=row.full_name,
                email=row.email,
                best_score=int(row.best_score or 0),
                total_plays=int(row.total_plays or 0),
            )
            for row in result.fetchall()
        ]

        return {'entries': entries}
    except Exception as exc:
        logger.error('Failed to load cockroach killer leaderboard: %s', exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail='Unable to load leaderboard at this time',
        )


@router.get('/me', response_model=CockroachUserStatsResponse)
async def get_my_stats(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        count_result = await db.execute(
            select(
                func.count(CockroachKillRecord.id).label('plays'),
                func.max(CockroachKillRecord.score).label('best_score'),
            ).where(CockroachKillRecord.user_id == current_user.id)
        )
        last_result = await db.execute(
            select(CockroachKillRecord.score)
            .where(CockroachKillRecord.user_id == current_user.id)
            .order_by(CockroachKillRecord.created_at.desc())
            .limit(1)
        )

        counts = count_result.one()
        last_row = last_result.one_or_none()
        return {
            'plays': int(counts.plays or 0),
            'best_score': int(counts.best_score or 0),
            'last_score': int(last_row.score if last_row else 0),
        }
    except Exception as exc:
        logger.error('Failed to load cockroach killer stats: %s', exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail='Unable to load user stats at this time',
        )
