from typing import List, Literal

from pydantic import BaseModel, Field


class IdeaSparkRequest(BaseModel):
    phrase: str = Field(..., min_length=2, max_length=160, description="Short phrase to spark ideas")
    time_available: Literal["30 minutes", "1-2 hours", "3-5 hours", "Weekend project"] = Field(
        default="1-2 hours",
        description="How much time user can spend",
    )
    create_type: Literal[
        "Small app/tool",
        "Content (blog/video/post)",
        "Automation",
        "Study project",
        "Anything interesting",
    ] = Field(
        default="Anything interesting",
        description="What kind of output user wants to create",
    )
    skill_area: Literal[
        "Programming",
        "AI/GenAI",
        "Productivity",
        "Business/startup",
        "Design",
        "Anything",
    ] = Field(
        default="Anything",
        description="Preferred skill area",
    )
    difficulty_level: Literal["Beginner", "Intermediate", "Challenge me"] = Field(
        default="Beginner",
        description="Desired challenge level",
    )


class IdeaSparkResponse(BaseModel):
    phrase: str = Field(..., description="Normalized input phrase")
    ideas: List[str] = Field(..., min_length=10, max_length=10, description="Exactly 10 micro-ideas")
