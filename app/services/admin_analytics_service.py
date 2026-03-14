from collections import Counter, defaultdict
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.resume_roast import UserActivityLog
from app.models.user import User
from app.schemas.admin_analytics import (
    AnalyticsOverviewResponse,
    CommonQuestionItem,
    FeatureOverviewItem,
    FeatureQuestionsResponse,
    FeatureUserUsage,
    FeatureUsersResponse,
    TopUser,
)


class AdminAnalyticsService:
    FEATURE_MAP: Dict[str, Dict[str, List[str] | str]] = {
        "cringe_meter": {
            "label": "LinkedIn Cringe-o-Meter",
            "activity_types": ["linkedin_cringe_analysis"],
        },
        "resume_roast": {
            "label": "Resume Roast",
            "activity_types": ["resume_roast_text", "resume_roast_upload"],
        },
        "skill_assessment": {
            "label": "Skill Assessment",
            "activity_types": ["skill_assessment_start", "skill_assessment_submit"],
        },
        "stock_analysis": {
            "label": "Stock Analysis",
            "activity_types": ["stock_analysis_create"],
        },
        "email_smoothener": {
            "label": "Email Smoothener",
            "activity_types": ["esm_smoothen"],
        },
    }

    @classmethod
    def _get_feature_meta(cls, feature_key: str) -> Tuple[str, List[str]]:
        feature = cls.FEATURE_MAP.get(feature_key)
        if not feature:
            raise ValueError("Invalid feature key")

        return str(feature["label"]), list(feature["activity_types"])

    @staticmethod
    def _normalize_question(text: str) -> str:
        return " ".join((text or "").strip().lower().split())

    @classmethod
    def _extract_question_text(cls, request_data: dict | None) -> Optional[str]:
        if not request_data or not isinstance(request_data, dict):
            return None

        keys = ["user_question", "content", "resume_text", "topic"]
        for key in keys:
            value = request_data.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()

        return None

    @classmethod
    async def get_overview(cls, db: AsyncSession) -> AnalyticsOverviewResponse:
        all_activity_types = [
            activity
            for feature in cls.FEATURE_MAP.values()
            for activity in feature["activity_types"]
        ]

        result = await db.execute(
            select(
                UserActivityLog.activity_type,
                User.id,
                User.email,
                User.full_name,
                func.count(UserActivityLog.id).label("usage_count"),
            )
            .join(User, User.id == UserActivityLog.user_id)
            .where(
                UserActivityLog.response_status == "success",
                UserActivityLog.activity_type.in_(all_activity_types),
            )
            .group_by(UserActivityLog.activity_type, User.id, User.email, User.full_name)
        )

        feature_user_counts: Dict[str, Dict[int, Dict[str, str | int | None]]] = defaultdict(dict)
        feature_totals: Dict[str, int] = defaultdict(int)

        activity_to_feature = {}
        for key, value in cls.FEATURE_MAP.items():
            for activity_type in value["activity_types"]:
                activity_to_feature[activity_type] = key

        for activity_type, user_id, email, full_name, usage_count in result.fetchall():
            feature_key = activity_to_feature.get(activity_type)
            if not feature_key:
                continue

            feature_totals[feature_key] += int(usage_count)
            current = feature_user_counts[feature_key].get(user_id)
            if current:
                current["usage_count"] = int(current["usage_count"]) + int(usage_count)
            else:
                feature_user_counts[feature_key][user_id] = {
                    "user_id": int(user_id),
                    "email": email,
                    "full_name": full_name,
                    "usage_count": int(usage_count),
                }

        features: List[FeatureOverviewItem] = []
        for feature_key, meta in cls.FEATURE_MAP.items():
            user_map = feature_user_counts.get(feature_key, {})
            users = list(user_map.values())
            users_sorted = sorted(users, key=lambda item: int(item["usage_count"]), reverse=True)
            top_user = (
                TopUser(
                    user_id=int(users_sorted[0]["user_id"]),
                    email=str(users_sorted[0]["email"]),
                    full_name=(str(users_sorted[0]["full_name"]) if users_sorted[0]["full_name"] else None),
                    usage_count=int(users_sorted[0]["usage_count"]),
                )
                if users_sorted
                else None
            )

            features.append(
                FeatureOverviewItem(
                    feature_key=feature_key,
                    feature_label=str(meta["label"]),
                    total_uses=int(feature_totals.get(feature_key, 0)),
                    unique_users=len(user_map),
                    top_user=top_user,
                )
            )

        features.sort(key=lambda item: item.total_uses, reverse=True)

        return AnalyticsOverviewResponse(
            generated_at=datetime.utcnow(),
            total_events=sum(item.total_uses for item in features),
            features=features,
        )

    @classmethod
    async def get_feature_users(cls, db: AsyncSession, feature_key: str, limit: int = 20) -> FeatureUsersResponse:
        feature_label, activity_types = cls._get_feature_meta(feature_key)

        result = await db.execute(
            select(
                User.id,
                User.email,
                User.full_name,
                func.count(UserActivityLog.id).label("usage_count"),
            )
            .join(User, User.id == UserActivityLog.user_id)
            .where(
                UserActivityLog.response_status == "success",
                UserActivityLog.activity_type.in_(activity_types),
            )
            .group_by(User.id, User.email, User.full_name)
            .order_by(func.count(UserActivityLog.id).desc())
            .limit(limit)
        )

        users = [
            FeatureUserUsage(
                user_id=int(user_id),
                email=email,
                full_name=full_name,
                usage_count=int(usage_count),
            )
            for user_id, email, full_name, usage_count in result.fetchall()
        ]

        return FeatureUsersResponse(
            feature_key=feature_key,
            feature_label=feature_label,
            users=users,
        )

    @classmethod
    async def get_feature_common_questions(
        cls,
        db: AsyncSession,
        feature_key: str,
        limit: int = 15,
    ) -> FeatureQuestionsResponse:
        feature_label, activity_types = cls._get_feature_meta(feature_key)

        result = await db.execute(
            select(UserActivityLog.request_data)
            .where(
                UserActivityLog.response_status == "success",
                UserActivityLog.activity_type.in_(activity_types),
            )
        )

        normalized_counter: Counter[str] = Counter()
        display_texts: Dict[str, str] = {}

        for (request_data,) in result.fetchall():
            question = cls._extract_question_text(request_data)
            if not question:
                continue

            normalized = cls._normalize_question(question)
            if not normalized:
                continue

            normalized_counter[normalized] += 1
            if normalized not in display_texts:
                display_texts[normalized] = question[:240]

        common_questions = [
            CommonQuestionItem(question=display_texts[key], frequency=int(freq))
            for key, freq in normalized_counter.most_common(limit)
        ]

        return FeatureQuestionsResponse(
            feature_key=feature_key,
            feature_label=feature_label,
            common_questions=common_questions,
        )


admin_analytics_service = AdminAnalyticsService()
