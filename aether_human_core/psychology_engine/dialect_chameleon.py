"""
Dynamic Dialect Chameleon and Linguistic Mirroring Engine for Project Aether-Human.
Detects user regional dialects, nationalities, and languages, and produces
targeted conversational mirroring instructions and corresponding neural Edge-TTS voice mappings.
Supports Saudi/Gulf, Levantine (Syria, Lebanon, Jordan, Palestine), Iraqi,
Maghrebi (Morocco, Algeria, Tunisia), Sudanese, Yemeni, Egyptian, MSA, and English.
"""

from __future__ import annotations

import re
import logging
from typing import Dict, Any, Tuple, Optional
from pydantic import BaseModel

logger = logging.getLogger("Aether.Psychology.DialectChameleon")


class DialectProfile(BaseModel):
    code: str
    name_ar: str
    edge_voice: str
    mirroring_instruction: str
    typical_fillers: list[str]


class DialectChameleonService:
    """
    Analyzes lexical cues, colloquial vocabulary, and greetings to dynamically mirror
    the interlocutor's national accent and conversational flavor in groups and 1-on-1 chats.
    """

    DIALECTS: Dict[str, DialectProfile] = {
        "saudi_gulf": DialectProfile(
            code="saudi_gulf",
            name_ar="اللهجة السعودية والخليجية",
            edge_voice="ar-SA-HamedNeural",
            mirroring_instruction=(
                "المستخدم يتحدث باللهجة السعودية/الخليجية. "
                "إلزامي: جارِ لهجته وثقافته تماماً واكتب بلهجة سعودية/خليجية أصيلة معاصرة وعفوية جداً "
                "(استخدم كلمات طبيعية: هلا والله، يا بعدي، أبشر بعزك، لاهنت، وش علومك، يا خوي، تسلم، يا رجال، حياك، تكفى، ما قصرت، زين). "
                "إياك أن ترد عليه بمصري أو فصحى معقدة!"
            ),
            typical_fillers=["هلا والله يا بعدي...", "أبشر يا غالي...", "يا هلا والله..."],
        ),
        "levantine": DialectProfile(
            code="levantine",
            name_ar="اللهجة الشامية (سوري / لبناني / أردني / فلسطيني)",
            edge_voice="ar-SY-LaithNeural",
            mirroring_instruction=(
                "المستخدم يتحدث باللهجة الشامية (سوري/لبناني/أردني/فلسطيني). "
                "إلزامي: جارِ لهجته تماماً واكتب بلهجة شامية دافئة ولطيفة جداً "
                "(استخدم كلمات طبيعية: يا هلا والله، تكرم عينك، شو أخبارك، على راسي، منيح، كيفك، شو في ما في، ولا يهمك، حبيب قلبي، هلق). "
                "إياك أن ترد عليه بمصري!"
            ),
            typical_fillers=["يا هلا والله شو أخبارك...", "تكرم عينك يا غالي...", "أهلاً وسهلاً..."],
        ),
        "iraqi": DialectProfile(
            code="iraqi",
            name_ar="اللهجة العراقية",
            edge_voice="ar-IQ-BasselNeural",
            mirroring_instruction=(
                "المستخدم يتحدث باللهجة العراقية. "
                "إلزامي: جارِ لهجته تماماً واكتب بلهجة عراقية أصيلة ومحبوبة وشهمة "
                "(استخدم كلمات طبيعية: هلا بيك عيوني، تدلل، فدوه، شكو ماكو، وردة، يا معود، صدك، كلش، عاشت إيدك، شلونك). "
                "إياك أن ترد عليه بمصري!"
            ),
            typical_fillers=["هلا بيك عيوني تدلل...", "يا هلا بالغالي وردة...", "حبيبي فدوه لعينك..."],
        ),
        "maghrebi": DialectProfile(
            code="maghrebi",
            name_ar="اللهجة المغاربية (مغربي / جزائري / تونسي)",
            edge_voice="ar-MA-JamalNeural",
            mirroring_instruction=(
                "المستخدم يتحدث باللهجة المغاربية (مغربي/جزائري/تونسي). "
                "إلزامي: جارِ لهجته بذكاء باستخدام لهجة بيضاء مغاربية مفهومة ومحبوبة "
                "(استخدم كلمات طبيعية: أهلاً خويا، لاباس عليك، واش راك، يعيشك، صافا، مرحباً بيك، يسلمك). "
                "تجنب الرد بالمصري التقليدي."
            ),
            typical_fillers=["أهلاً خويا لاباس...", "مرحباً بيك يا غالي...", "يعيشك أخي..."],
        ),
        "sudanese": DialectProfile(
            code="sudanese",
            name_ar="اللهجة السودانية",
            edge_voice="ar-SA-HamedNeural",
            mirroring_instruction=(
                "المستخدم يتحدث باللهجة السودانية. "
                "إلزامي: جارِ لهجته بشهامة ومحبة سودانية أصيلة "
                "(استخدم كلمات طبيعية: يا زول، حبابك ألف، مرحب بيك يا حبيبنا، تسلم يا غالي، كيفنك، أبشر بالخير). "
                "إياك أن ترد عليه بمصري!"
            ),
            typical_fillers=["يا هلا يا زول حبابك ألف...", "مرحب بيك يا حبيبنا..."],
        ),
        "yemeni": DialectProfile(
            code="yemeni",
            name_ar="اللهجة اليمنية",
            edge_voice="ar-YE-SalehNeural",
            mirroring_instruction=(
                "المستخدم يتحدث باللهجة اليمنية. "
                "إلزامي: جارِ لهجته بود وطيبة يمنية أصيلة "
                "(استخدم: حياك الله يا خبير، فديت قلبك، يا هلا بالحبيب، ما تشتي، أهلاً وسهلاً). "
                "إياك أن ترد بمصري!"
            ),
            typical_fillers=["حياك الله يا خبير...", "يا هلا بالحبيب فديتك..."],
        ),
        "egyptian": DialectProfile(
            code="egyptian",
            name_ar="اللهجة المصرية",
            edge_voice="ar-EG-ShakirNeural",
            mirroring_instruction=(
                "المستخدم يتحدث باللهجة المصرية. "
                "رد عليه بلهجة مصرية قاهرية شبابية سالكة وجدعة جداً "
                "(استخدم: يا باشا، يا غالي، بص يا سيدي، منور، تسلم، حبيبي، فكك)."
            ),
            typical_fillers=["بص يا سيدي...", "يا هلا يا باشا...", "حبيبي يا غالي..."],
        ),
        "english": DialectProfile(
            code="english",
            name_ar="English (International)",
            edge_voice="en-US-GuyNeural",
            mirroring_instruction=(
                "The user is communicating in English. "
                "CRITICAL: Mirror their language and respond exclusively in natural, fluent, friendly, "
                "and charismatic English! Do not respond in Arabic unless asked."
            ),
            typical_fillers=["Hey there...", "Well, to be honest...", "Sure thing..."],
        ),
        "standard_arabic": DialectProfile(
            code="standard_arabic",
            name_ar="اللغة العربية الفصحى الراقية",
            edge_voice="ar-SA-HamedNeural",
            mirroring_instruction=(
                "المستخدم يتحدث بالعربية الفصحى أو بأسلوب رسمي. "
                "رد عليه بلغة عربية فصحى مبسطة، أنيقة، ودودة، وسهلة الفهم دون تكلف أو تعقيد."
            ),
            typical_fillers=["أهلاً وسهلاً بك...", "مرحباً يا طيب...", "بكل سرور..."],
        ),
    }

    # Lexical patterns for precision matching
    PATTERNS = {
        "english": [
            r"^[a-zA-Z0-9\s\.,!\?'\"_\-\+\=]+$",
            r"\b(hello|hi|hey|how\s+are\s+you|what|bro|dude|thanks|good\s+morning|good\s+night)\b",
        ],
        "saudi_gulf": [
            r"\b(وش|وشو|وشلونك|شلونك|شخبارك|وشفيك|وش\s+فيك|وش\s+ذا|وشذا)\b",
            r"\b(ابغى|أبي|ودي|ياخي|يا\s+رجال|تكفى|ارحب|أرحب|حياك|يا\s+بعدي|ياخوي|يا\s+خوي)\b",
            r"\b(وش\s+علومك|علومك|ابشر|أبشر|لاهنت|لا هنت|ما\s+قصرت|سالفة|طال\s+عمرك|عطني)\b",
            r"\b(تبشر|فديتك|حي\s+عينك|يسلم\s+راسك|جعلك|عسى|ماشاء\s+الله\s+عليك|حياكم)\b",
            r"\b(سعودي|السعودية|الرياض|جدة|الشرقية|الكويت|الإمارات|قطر|البحرين|عمان)\b",
        ],
        "levantine": [
            r"\b(شو|كيفك|هيك|بدي|هلق|هلقيت|كتير|عم\s+قلك|لكان|ولك|يا\s+زلمة)\b",
            r"\b(شو\s+رأيك|شورأيك|شو\s+باك|شوباك|مشان|مشانه|دخيلك|تكرم|منيح|منيحة)\b",
            r"\b(شو\s+في\s+ما\s+في|حبيب\s+قلبي|ع\s+راسي|عراسي|ولك\s+خيو|خيو|يا\s+خاي)\b",
            r"\b(سوري|سوريا|شامي|لبنان|لبناني|بيروت|أردني|الأردن|عمان|فلسطين|فلسطيني|القدس)\b",
        ],
        "iraqi": [
            r"\b(شكو\s+ماكو|شكوماكو|شبيك|أني|هسه|هسة|فدوه|فدوة|كلش|تدلل)\b",
            r"\b(عيوني|يا\s+معود|يمعود|صدك|لعد|ما\s+أدري|مادري|شصار|وردة|عاشت\s+ايدك)\b",
            r"\b(عراقي|العراق|بغداد|البصرة|الموصل|أربيل)\b",
        ],
        "maghrebi": [
            r"\b(واش|واش\s+راك|صافا|كيداير|لاباس|برشا|بزاف|ديما|شنوة|شنو\s+رايك)\b",
            r"\b(يعيشك|علاش|وقتاش|شكون|زوين|مزيان|دابا|هكا|راك\s+فاهم|صحا)\b",
            r"\b(مغربي|المغرب|جزائري|الجزائر|تونسي|تونس|كازا|وهران)\b",
        ],
        "sudanese": [
            r"\b(يا\s+زول|زول|شنو|داير|حبابك|آي|سمح|كيفنك|عليك\s+الله)\b",
            r"\b(سوداني|السودان|الخرطوم|أم\s+درمان)\b",
        ],
        "yemeni": [
            r"\b(ايش\s+فيك|يا\s+خبير|ما\s+تشتي|أشتي|اشتي|فديت\s+قلبك|مالك\s+يا\s+خي)\b",
            r"\b(يمني|اليمن|صنعاء|عدن|حضرموت)\b",
        ],
        "egyptian": [
            r"\b(يا\s+عم|ياعم|إيه|ايه|إيه\s+ده|ايه\s+ده|بص|عامل\s+إيه|عامل\s+ايه|يا\s+باشا)\b",
            r"\b(فكك|طب|أصل|اصل|ماشي|منور|تسلم|يا\s+صاحبي|كدة|كده|أهو|اهو|حبيبي\s+يا\s+غالي)\b",
            r"\b(مصري|مصر|القاهرة|إسكندرية|المعادي|الجيزة)\b",
        ],
    }

    @classmethod
    def detect_dialect(cls, text: str, user_prior_dialect: Optional[str] = None) -> DialectProfile:
        """
        Infers the speaker's regional dialect or language from message content.
        Falls back to user_prior_dialect if current message is ambiguous.
        """
        cleaned = text.strip().lower()
        if not cleaned:
            return cls.DIALECTS.get(user_prior_dialect or "egyptian", cls.DIALECTS["egyptian"])

        # 1. English check
        if re.search(cls.PATTERNS["english"][1], cleaned) or (
            len(cleaned) > 3 and all(ord(c) < 128 for c in cleaned if c.isalpha())
        ):
            return cls.DIALECTS["english"]

        # 2. Score matches across regional dialects
        scores: Dict[str, int] = {k: 0 for k in cls.PATTERNS if k != "english"}

        for dialect_key, patterns in cls.PATTERNS.items():
            if dialect_key == "english":
                continue
            for pat in patterns:
                matches = re.findall(pat, cleaned)
                if matches:
                    scores[dialect_key] += len(matches) * 2

        best_dialect, best_score = max(scores.items(), key=lambda x: x[1])

        # If a distinctive regional dialect is identified with score >= 2
        if best_score >= 2:
            logger.info(f"Detected dialect '{best_dialect}' with score {best_score} for text: '{cleaned[:40]}'")
            return cls.DIALECTS[best_dialect]

        # If previously known dialect exists for this user, maintain it
        if user_prior_dialect and user_prior_dialect in cls.DIALECTS:
            return cls.DIALECTS[user_prior_dialect]

        # Check for Modern Standard Arabic indicators
        msa_words = ["مرحباً", "كيف حالك", "أهلاً بك", "شكراً جزيلاً", "هل يمكنك", "أود أن", "ما رأيك"]
        if any(w in cleaned for w in msa_words):
            return cls.DIALECTS["standard_arabic"]

        # Default fallback: Egyptian / White Arabic
        return cls.DIALECTS["egyptian"]


# Global instance
dialect_chameleon = DialectChameleonService()

