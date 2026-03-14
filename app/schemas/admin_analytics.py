from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class TopUser(BaseModel):
    user_id: int
    email: str
    full_name: Optional[str] = None
    usage_count: int


class FeatureOverviewItem(BaseModel):
    feature_key: str
    feature_label: str
    total_uses: int
    unique_users: int
    top_user: Optional[TopUser] = None


class AnalyticsOverviewResponse(BaseModel):
    generated_at: datetime
    total_events: int
    features: List[FeatureOverviewItem]


class FeatureUserUsage(BaseModel):
    user_id: int
    email: str
    full_name: Optional[str] = None
    usage_count: int


class FeatureUsersResponse(BaseModel):
    feature_key: str
    feature_label: str
    users: List[FeatureUserUsage]


class CommonQuestionItem(BaseModel):
    question: str
    frequency: int


class FeatureQuestionsResponse(BaseModel):
    feature_key: str
    feature_label: str
    common_questions: List[CommonQuestionItem]
