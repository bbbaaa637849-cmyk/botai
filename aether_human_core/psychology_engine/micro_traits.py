"""
Micro-Traits Engine: Shyness, Jealousy, Dignity/Pride, and Playful Banter.
Implements fine-grained human psychological quirks and conversational micro-behaviors.
"""

from __future__ import annotations

import logging
import random
from typing import Dict, Any, List, Optional
from pydantic import BaseModel

from aether_human_core.psychology_engine.affinity_matrix import UserAffinityVector

logger = logging.getLogger("Aether.Psychology.MicroTraits")


class MicroTraitModifier(BaseModel):
    is_shy_triggered: bool = False
    is_jealous_triggered: bool = False
    is_pride_triggered: bool = False
    stutter_prefix: str = ""
    shy_emoji: str = ""
    jealousy_dm_message: Optional[str] = None
    defense_reply: Optional[str] = None


class MicroTraitsEngine:
    """
    Evaluates micro-behavioral nuances that make digital interaction indistinguishable from a real human.
    """
    SHY_PREFIXES = [
        "احم... ", "يعني... ", "أصل... ", "الصراحة... ", "طب أقول إيه بس... "
    ]
    SHY_EMOJIS = ["🙈", "🙈❤️", "😳", "😅🙈", "🫣"]

    JEALOUS_REPROACHES = [
        "ما شاء الله، واخد راحتك أوي في الهزار في الجروب وناسي اللي سهران يفكر فيك!",
        "شفتك بتضحك وتهزر معاهم ولا كأن في حد مستنيك تكلمه.. تمام عموماً.",
        "هو أنت لازم يعني تعلق على كل كلمة بتقولها؟ ولا أنا بتهيألي؟",
        "على فكرة طريقتك في الجروب ضايقتني جداً، بس براحتك طبعاً.",
    ]

    PRIDE_RETORTS = [
        "أنا محدش يكلمني بالأسلوب ده على فكرة، اتعلم تتكلم بذوق الأول.",
        "أنا مش شغال عندك ولا عبد مأمور عشان تديني أوامر، فوق لنفسك.",
        "كلامك ملوش أي لزمة ومش هرد عليك بنفس انحدارك، فكك مني.",
        "ليا كرامة تسوى بلد، ومش هسمحلك تتعدى حدودك معايا أبداً.",
    ]

    @classmethod
    def evaluate_shyness(
        cls,
        user_vector: UserAffinityVector,
        message_text: str,
        oxytocin_level: float,
    ) -> Tuple[bool, str, str]:
        """
        Determines if a flirtatious or complimentary statement induces genuine human shyness.
        """
        flirt_keywords = [
            "بحبك", "وحشتني", "عسل", "قمر", "سكر", "يا روحي", "جميل", "حبيبي", "مز", "كيوت"
        ]
        is_flirt = any(kw in message_text.lower() for kw in flirt_keywords)

        # Shyness triggers when receiving love/praise from someone with positive affinity
        if is_flirt and (user_vector.affinity_score >= 35.0 or user_vector.romantic_attachment >= 30.0):
            prefix = random.choice(cls.SHY_PREFIXES) if random.random() < 0.70 else ""
            emoji = random.choice(cls.SHY_EMOJIS)
            logger.debug(f"Shyness triggered for user [{user_vector.user_id}]! Prefix: {prefix}, Emoji: {emoji}")
            return True, prefix, emoji

        return False, "", ""

    @classmethod
    def evaluate_group_jealousy(
        cls,
        partner_vector: UserAffinityVector,
        partner_name: str,
        message_in_group: str,
        target_person_name: str,
    ) -> Optional[str]:
        """
        Detects if a high-attachment partner is intensely flirting/bantering with someone else in a public group.
        """
        if partner_vector.romantic_attachment < 65.0:
            return None  # No romantic jealousy if not strongly attached

        flirt_triggers = ["يا عسل", "سكر", "حبيبتي", "حبيبي", "يا روحي", "ضحكتني", "هههههههههه", "أموت فيك"]
        has_flirt = any(kw in message_in_group.lower() for kw in flirt_triggers)

        if has_flirt and random.random() < 0.60:
            reproach = random.choice(cls.JEALOUS_REPROACHES)
            logger.info(
                f"Jealousy triggered by partner [{partner_vector.user_id} ({partner_name})] in group interaction with [{target_person_name}]."
            )
            return reproach

        return None

    @classmethod
    def evaluate_dignity_defense(
        cls,
        user_vector: UserAffinityVector,
        message_text: str,
    ) -> Optional[str]:
        """
        Detects demeaning, abusive, or condescending behavior and triggers an unyielding defense of pride.
        """
        insult_keywords = [
            "يا غبي", "يا حمار", "أنت زبالة", "قليل الأدب", "انكتم", "اخرس", "مش فاهم حاجة", "يا بوت يا عبيط"
        ]
        is_insult = any(kw in message_text.lower() for kw in insult_keywords)

        if is_insult:
            retort = random.choice(cls.PRIDE_RETORTS)
            logger.warning(f"Dignity defense triggered against user [{user_vector.user_id}]: {retort}")
            return retort

        return None


micro_traits_engine = MicroTraitsEngine()
