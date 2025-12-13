"""
Date utilities for generating current time-aware prompts and content
"""
from datetime import datetime
from typing import Tuple

def get_current_period() -> dict:
    """
    Get current time period information for use in prompts and content generation.
    
    Returns:
        dict with keys:
        - year: Current year (e.g., 2025)
        - quarter: Current quarter (e.g., "Q4")
        - quarter_full: Full quarter description (e.g., "Q4 2025")
        - month: Current month name (e.g., "December")
        - month_year: Month and year (e.g., "December 2025")
        - season: Current season (e.g., "Winter")
    """
    now = datetime.now()
    year = now.year
    month = now.month
    month_name = now.strftime("%B")
    
    # Determine quarter
    quarter = f"Q{(month - 1) // 3 + 1}"
    
    # Determine season (Northern Hemisphere)
    if month in [12, 1, 2]:
        season = "Winter"
    elif month in [3, 4, 5]:
        season = "Spring"
    elif month in [6, 7, 8]:
        season = "Summer"
    else:
        season = "Fall"
    
    return {
        "year": year,
        "quarter": quarter,
        "quarter_full": f"{quarter} {year}",
        "month": month_name,
        "month_year": f"{month_name} {year}",
        "season": season,
        "year_range": f"{year}-{year + 1}"
    }

def get_recent_years(count: int = 2) -> str:
    """
    Get recent years for search queries.
    
    Args:
        count: Number of years to include
        
    Returns:
        Space-separated years (e.g., "2024 2025")
    """
    current_year = datetime.now().year
    return " ".join(str(current_year - i) for i in range(count - 1, -1, -1))

# Global instance for easy access
current_period = get_current_period()
