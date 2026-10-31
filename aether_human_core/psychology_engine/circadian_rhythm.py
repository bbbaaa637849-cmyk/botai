"""
Circadian Rhythm and Biological Sleep Schedule Simulation for Aether-Human.
Calculates energy levels, alertness, sleep cycles, and late-night typographical error multipliers.
Synchronized with Egyptian timezone (UTC+2 / Africa/Cairo).
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Tuple

logger = logging.getLogger("Aether.Psychology.Circadian")


class CircadianRhythmEngine:
    """
    Simulates the biological day-night cycle of a 24-year-old living in Cairo.
    """
    CAIRO_OFFSET_HOURS = 2  # Standard Egypt UTC+2

    # Schedule definitions (Hours in 24h format)
    SLEEP_START_HOUR = 3.5    # 03:30 AM
    WAKE_UP_HOUR = 10.0       # 10:00 AM
    GROGGY_END_HOUR = 11.5    # 11:30 AM
    PEAK_START_HOUR = 13.0    # 01:00 PM
    DROWSY_START_HOUR = 1.0   # 01:00 AM

    @classmethod
    def get_cairo_now(cls) -> datetime:
        cairo_tz = timezone(timedelta(hours=cls.CAIRO_OFFSET_HOURS))
        return datetime.now(cairo_tz)

    @classmethod
    def evaluate_circadian_state(cls) -> Dict[str, Any]:
        """
        Analyzes the current biological clock phase and returns operational modifiers.
        """
        cairo_now = cls.get_cairo_now()
        hour_fraction = cairo_now.hour + (cairo_now.minute / 60.0)

        is_sleeping = False
        is_groggy = False
        is_drowsy = False
        alertness = 1.0
        typo_multiplier = 1.0
        wpm_multiplier = 1.0
        state_name = "ACTIVE_DAY"
        description_ar = "في كامل نشاطه الطبيعي"

        # Check Sleep Phase (03:30 AM to 10:00 AM)
        if cls.SLEEP_START_HOUR <= hour_fraction < cls.WAKE_UP_HOUR:
            is_sleeping = True
            alertness = 0.05
            typo_multiplier = 4.0
            wpm_multiplier = 0.3
            state_name = "ASLEEP"
            description_ar = "نائم بعمق ولا يرد إلا في الحالات القصوى"

        # Morning Grogginess (10:00 AM to 11:30 AM)
        elif cls.WAKE_UP_HOUR <= hour_fraction < cls.GROGGY_END_HOUR:
            is_groggy = True
            alertness = 0.55
            typo_multiplier = 2.0
            wpm_multiplier = 0.7
            state_name = "MORNING_GROGGY"
            description_ar = "لسه صاحي من النوم وبيدور على فنجان القهوة"

        # Late Night Drowsiness (01:00 AM to 03:30 AM)
        elif hour_fraction >= cls.DROWSY_START_HOUR and hour_fraction < cls.SLEEP_START_HOUR:
            is_drowsy = True
            alertness = 0.40
            typo_multiplier = 2.8
            wpm_multiplier = 0.6
            state_name = "LATE_NIGHT_DROWSY"
            description_ar = "نعسان جداً وعينيه بتقفل من السهر"

        # Peak Evening / Social (07:00 PM to 01:00 AM)
        elif hour_fraction >= 19.0 or hour_fraction < cls.DROWSY_START_HOUR:
            alertness = 0.95
            typo_multiplier = 1.0
            wpm_multiplier = 1.15
            state_name = "EVENING_SOCIAL"
            description_ar = "فترة المساء، رايق ومستعد للشات والرغي"

        else:
            # Normal afternoon
            alertness = 0.85
            state_name = "AFTERNOON_FOCUSED"
            description_ar = "فترة النهار والتركيز في الشغل"

        return {
            "cairo_time_str": cairo_now.strftime("%Y-%m-%d %H:%M:%S"),
            "hour_fraction": round(hour_fraction, 2),
            "state_name": state_name,
            "description_ar": description_ar,
            "is_sleeping": is_sleeping,
            "is_groggy": is_groggy,
            "is_drowsy": is_drowsy,
            "alertness": alertness,
            "typo_multiplier": typo_multiplier,
            "wpm_multiplier": wpm_multiplier,
        }


circadian_engine = CircadianRhythmEngine()
