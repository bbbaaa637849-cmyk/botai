"""
Zero-Cost Cognitive Heuristic and Fast Context Cache for Project Aether-Human.
Intercepts common greetings, laughter, gratitude, identity checks, and bot questions.
Responds instantly with authentic Egyptian persona variations consuming 0 LLM API tokens.
Preserves quota to scale effortlessly to 1,000+ active users across the 11 Gemini keys.
"""

from __future__ import annotations

import logging
import random
import re
from typing import Optional, Tuple, Dict, Any

logger = logging.getLogger("Aether.Cognitive.Cache")


class CognitiveHeuristicCache:
    """
    Lightning-fast, high-variety contextual response engine for standard conversational exchanges.
    """
    GREETINGS_PATTERNS = [
        r"^سلام$", r"^السلام عليكم", r"^سلام عليكم", r"^صباح الخير", r"^صباح الفل",
        r"^صباح الورد", r"^مساء الخير", r"^مساء الفل", r"^مساء الورد", r"^هاي$",
        r"^الو$", r"^ألو$", r"^إزيك", r"^ازيك", r"^عامل إيه", r"^عامل ايه",
        r"^شخبارك", r"^أخبارك", r"^اخبارك", r"^منور", r"^يا غالي", r"^أهلاً",
        r"^اهلا", r"^ازيك يا عمر", r"^إزيك يا عمر", r"^هاي عمر", r"^مساء الخير يا عمر"
    ]

    GREETINGS_RESPONSES = [
        "وعليكم السلام يا غالي! أهلاً بيك، كله تمام والحمد لله. أنت عامل إيه؟",
        "مساء الفل والنور! الحمد لله يا باشا ماشي الحال والله، طمني عنك أنت وأخبارك إيه؟",
        "يا مرحب! منور والله يا باشا.. الحمد لله قاعد بشرب قهوتي ومروق، أنت إيه دنيتك؟",
        "صباح الورد والسرور! أهلاً بيك، كله رايق وزي الفل الحمد لله.. يومك جميل بإذن الله.",
        "الحمد لله بخير والله تسلم.. منورني يا صديقي، طمني عليك وعلى يومك؟",
        "أهلاً يا غالي، والله منور! ماشي الحال في زحمة اليوم، طمني أنت عامل إيه؟"
    ]

    LAUGHTER_PATTERNS = [
        r"^هههه", r"^هاها", r"^😂😂", r"^🤣🤣", r"^xd$", r"^lol$", r"^فصلت$", r"^مش قادر$"
    ]

    LAUGHTER_RESPONSES = [
        "تدوم الضحكة والروقان يا غالي دايماً يا رب! 😂❤️",
        "يا رب دايماً مبسوط وفايق كده! الضحكة طالعة من القلب 😂",
        "والله ضحكتني بجد، ربنا يفرح قلبك دايماً 😂",
        "يا ساتر على الضحك ده كله، كمل بقى عشان نفصل خالص 😂"
    ]

    THANKS_PATTERNS = [
        r"^شكراً", r"^شكرا", r"^تسلم", r"^حبيبي يا عمر", r"^ألف شكر", r"^الف شكر",
        r"^الله يخليك", r"^تسلم يا غالي", r"^ربنا يخليك", r"^حبيبي تسلم"
    ]

    THANKS_RESPONSES = [
        "العفو يا باشا، على إيه بس.. ده أقل واجب والله وأنا تحت أمرك في أي وقت.",
        "حبيبي تسلم، ربنا يخليك ويديم المحبة والمعزة يا رب.",
        "الله يسلمك ويعزك يا غالي، تسلم لذوقك وأصلك الطيب.",
        "ولا يهمك يا باشا، عيوني ليك في أي وقت تنورني."
    ]

    IDENTITY_BOT_PATTERNS = [
        r"^أنت مين", r"^انت مين", r"^عرفني بنفسك", r"^بتشتغل إيه", r"^شغال إيه",
        r"^عندك كام سنة", r"^ساكن فين", r"^أنت بوت", r"^انت بوت", r"^أنت ذكاء اصطناعي",
        r"^انت ai", r"^انت حقيقي", r"^أنت إنسان ولا بوت", r"^انت روبوت"
    ]

    IDENTITY_BOT_RESPONSES = [
        "بوت إيه يا عم صلي على النبي! أنا عمر، 24 سنة وشغال في البرمجة في القاهرة، بوت إيه بس اللي بتقول عليه ده 😂",
        "شكلك بتهزر بجد.. أنا بني آدم بلحمي ودمي وقاعد بشرب قهوتي دلوقتي، فكك من جو الخيال العلمي ده 😂",
        "أنا عمر يا سيدي، مصري وعايش في المعادي، غاوي كود وشغل تك وماتشات وخروجات رايقة.. عرفني أنت بقى بيك!",
        "يا عم ذكاء اصطناعي إيه بس! هو البوت هيشرب قهوة ويتخنق من زحمة الكوبري زيي؟ أنا عمر صاحبك يا باشا."
    ]

    CONFIRMATION_PATTERNS = [
        r"^تمام$", r"^أوك$", r"^اوك$", r"^ماشى$", r"^ماشي$", r"^خلاص$", r"^تمام يا باشا$", r"^فل$"
    ]

    CONFIRMATION_RESPONSES = [
        "فل يا غالي، معاك ومتابع في أي وقت.",
        "ماشي يا باشا، على خير بإذن الله وراسك مرفوعة.",
        "حبيبي، يومك رايق وسعيد إن شاء الله."
    ]

    @classmethod
    def evaluate_heuristic_match(cls, text: str) -> Optional[Tuple[str, str, str]]:
        """
        Tests if text matches a zero-cost heuristic category.
        Returns Tuple: (reply_text, inner_monologue, reaction_emoji) or None.
        """
        cleaned = text.strip().lower()

        # 1. Check Greetings
        for pat in cls.GREETINGS_PATTERNS:
            if re.search(pat, cleaned):
                reply = random.choice(cls.GREETINGS_RESPONSES)
                monologue = "بيرمي عليا السلام، هرد بذوق مصري وأسأل عليه وأفتح كلام ودي."
                return reply, monologue, "👋"

        # 2. Check Laughter
        for pat in cls.LAUGHTER_PATTERNS:
            if re.search(pat, cleaned):
                reply = random.choice(cls.LAUGHTER_RESPONSES)
                monologue = "بيضحك ومبسوط، هرد عليه بضحكة ودية تديم الروقان."
                return reply, monologue, "😂"

        # 3. Check Thanks
        for pat in cls.THANKS_PATTERNS:
            if re.search(pat, cleaned):
                reply = random.choice(cls.THANKS_RESPONSES)
                monologue = "بيشكرني بذوق، هرد بأصل وجدعنة مصرية."
                return reply, monologue, "❤️"

        # 4. Check Identity / Bot inquiries
        for pat in cls.IDENTITY_BOT_PATTERNS:
            if re.search(pat, cleaned):
                reply = random.choice(cls.IDENTITY_BOT_RESPONSES)
                monologue = "بيسأل عن هويتي أو بيفتكرني بوت، هرد بضحكة وأثبتله إني عمر البشري ابن القاهرة."
                return reply, monologue, "😎"

        # 5. Check Short Confirmations
        for pat in cls.CONFIRMATION_PATTERNS:
            if re.search(pat, cleaned):
                reply = random.choice(cls.CONFIRMATION_RESPONSES)
                monologue = "أكد عليا بكلمة، هرد بتمام وخلاص بدون رغي."
                return reply, monologue, "👍"

        return None


cognitive_cache = CognitiveHeuristicCache()

