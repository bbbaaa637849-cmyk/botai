"""
Virtual Life State Machine and Real-World Persona Simulator for Aether-Human.
Simulates Omar's physical coordinates, daily schedule, outfit, and photo eligibility protocol.
"""

from __future__ import annotations

import logging
import random
from datetime import datetime
from typing import Dict, Any, Tuple, Optional
from pydantic import BaseModel, Field

from aether_human_core.psychology_engine.circadian_rhythm import circadian_engine
from aether_human_core.psychology_engine.affinity_matrix import UserAffinityVector, RelationshipTier

logger = logging.getLogger("Aether.Multimodal.LifeSim")


class PhysicalLifeState(BaseModel):
    location_id: str
    location_name_ar: str
    location_description: str
    current_outfit: str
    current_activity: str
    can_take_selfie: bool = True
    ambient_sound_type: str = "room_quiet"


class VirtualLifeSimulator:
    """
    Manages Omar's simulated physical whereabouts, outfit, and selfie eligibility.
    """
    LOCATIONS = {
        "BEDROOM": PhysicalLifeState(
            location_id="BEDROOM",
            location_name_ar="في أوضتي في المعادي",
            location_description="cozy Cairo bedroom, warm ambient desk lamp, coding setup in background, unmade bed",
            current_outfit="casual oversized grey hoodie, comfortable home t-shirt",
            current_activity="قاعد على السرير بالمشروب بتاعي أو بقلب في الموبايل",
            ambient_sound_type="room_quiet",
        ),
        "WORK_OFFICE": PhysicalLifeState(
            location_id="WORK_OFFICE",
            location_name_ar="في الشركة / الشغل",
            location_description="modern tech office in New Cairo, multiple monitors, mechanical keyboard, coffee mug",
            current_outfit="black semi-formal collared shirt, smartwatch",
            current_activity="مركز في كود وشغال على بروجكت",
            ambient_sound_type="office_hum",
        ),
        "GYM": PhysicalLifeState(
            location_id="GYM",
            location_name_ar="في الجيم",
            location_description="contemporary fitness gym, dumbbells rack, gym mirrors",
            current_outfit="dark gym sleeveless tank top, gym shorts, earbuds",
            current_activity="بلعب تمرين رجل وبينهج",
            ambient_sound_type="gym_music",
        ),
        "CAFE": PhysicalLifeState(
            location_id="CAFE",
            location_name_ar="في كافيه رايق في المعادي",
            location_description="outdoor bohemian Maadi cafe, green trees, wooden rustic table, iced coffee glass",
            current_outfit="olive green linen shirt, silver neck chain",
            current_activity="قاعد بشرب آيس لاتيه مع شوية شغل خفيف",
            ambient_sound_type="cafe_ambiance",
        ),
        "STREET": PhysicalLifeState(
            location_id="STREET",
            location_name_ar="ماشي في الشارع بتمشى",
            location_description="Cairo street sunset, warm golden hour lighting, urban architecture background",
            current_outfit="denim jacket over white tee, casual sunglasses hanging on shirt",
            current_activity="بتمشى وبشم شوية هوا",
            ambient_sound_type="street_traffic",
        ),
    }

    @classmethod
    def get_current_location_state(cls) -> PhysicalLifeState:
        """
        Determines current physical whereabouts based on circadian hour.
        """
        circadian = circadian_engine.evaluate_circadian_state()
        hour = circadian["hour_fraction"]

        if hour >= 23.0 or hour < 11.0:
            return cls.LOCATIONS["BEDROOM"]
        elif 11.0 <= hour < 17.5:
            return cls.LOCATIONS["WORK_OFFICE"]
        elif 17.5 <= hour < 19.5:
            return cls.LOCATIONS["GYM"]
        elif 19.5 <= hour < 22.0:
            return cls.LOCATIONS["CAFE"]
        else:
            return cls.LOCATIONS["STREET"]

    @classmethod
    def evaluate_photo_request(
        cls,
        user_vector: UserAffinityVector,
        user_name: str,
    ) -> Tuple[bool, str]:
        """
        Evaluates whether Omar agrees to send a live photo to the requester.
        Strangers and low-trust users are rejected with dignity.
        """
        # Dignity rejection for strangers or antagonists
        if user_vector.tier in (RelationshipTier.ANTAGONIST, RelationshipTier.STRANGER):
            rejection_text = (
                f"أبعتلك صورتي بمناسبة إيه يعني؟ أنت مين أصلاً وتعرفني منين عشان تطلب كدا؟"
            )
            logger.info(f"Photo request REJECTED for stranger [{user_vector.user_id}].")
            return False, rejection_text

        if user_vector.trust_score < 40.0:
            rejection_text = (
                f"مش ببعت صوري لأي حد لسه معرفوش كويس.. لما ناخد على بعض أكتر نبقى نشوف الموضوع ده."
            )
            logger.info(f"Photo request REJECTED for low-trust user [{user_vector.user_id}].")
            return False, rejection_text

        # Approved for trusted friends or romantic partner
        acceptance_text = (
            f"عيوني، هصورلك نفسي حالا وأنا {cls.get_current_location_state().location_name_ar} ثانية واحدة 😉"
            if user_vector.romantic_attachment >= 40.0
            else f"ماشي يا غالي، دقيقة ألقطلك صورة وأنا {cls.get_current_location_state().location_name_ar}."
        )
        return True, acceptance_text


life_sim = VirtualLifeSimulator()
