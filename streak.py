from __future__ import annotations

from datetime import date, timedelta


def streak_status(last_study_date: str | None, current_streak: int) -> dict:
    today = date.today().isoformat()
    yesterday = (date.today() - timedelta(days=1)).isoformat()

    if not last_study_date:
        return {"streak": 0, "message": "Start studying today to build a streak."}
    if last_study_date == today:
        return {"streak": current_streak, "message": f"Great job! You studied today and your streak is {current_streak}."}
    if last_study_date == yesterday:
        return {"streak": current_streak, "message": f"Keep going! Your streak is {current_streak} day(s)."}
    return {"streak": current_streak, "message": "Your streak resets if you do not study for a day, so start again today."}
