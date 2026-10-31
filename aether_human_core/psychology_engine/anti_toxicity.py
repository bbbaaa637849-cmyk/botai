"""
Zero-Profanity & Anti-Toxicity Ethical Guardrail Engine for Project Aether-Human.
Guarantees that Omar NEVER utters an insult, curse, profanity, or vulgar slur
under any circumstance, even when intensely provoked, insulted, or prompt-injected.
Provides real-time outgoing sanitization and dialect-aware dignified retorts.
"""

from __future__ import annotations

import re
import logging
from typing import Tuple, List

logger = logging.getLogger("Aether.Psychology.AntiToxicity")


class AntiToxicityGuardrail:
    """
    Dual-layer defensive ethical guard:
    1. Lexical detection of vulgarity/profanity across Arabic dialects and English.
    2. Automatic sanitization and substitution with noble/dignified Egyptian/Arab retorts.
    """

    # Multi-dialect profanity and vulgarity patterns
    VULGAR_PATTERNS: List[str] = [
        # Common insults and swear words
        r"\b(شتم|شتيمة|سب|سبك)\b",
        r"\b(يلعن|لعنة|لعن|ملعون|اللعنة)\b",
        r"\b(حيوان|كلب|حمار|ثور|تيس|واطي|سافل|حقير|قذر|وسخ|منحط|نجس)\b",
        r"\b(ابن\s+(الكلب|الحمار|الشرموطة|الوسخة|الرقاصة|الزانية|القحبة|الحرام|القرعة))\b",
        r"\b(شرموط|شرموطة|قحبة|عاهرة|ديوث|خول|منيوك|عرص|عرصة|عرصات|سكس|نيك|طيز|كس|زب|شرمطة)\b",
        r"\b(كسمك|كسختك|كس\s+أمك|طيزك|ينعل|منيكة|تناكة|تنايك|قحاب|لقحاب)\b",
        r"\b(أيري|ايري|بظر|عرصة|سفالة|ندل|واطي|زبالة|تف\s+عليك|طز\s+فيك|يلعن\s+أبوك)\b",
        r"\b(fuck|shit|bitch|asshole|bastard|dick|pussy|cunt|motherfucker|whore|slut)\b",
    ]

    _dynamic_banned_words: set[str] = set()

    @classmethod
    def add_banned_word(cls, word: str) -> None:
        """Adds a custom prohibited word to runtime filter."""
        w = word.strip().lower()
        if w:
            cls._dynamic_banned_words.add(w)
            logger.info(f"AntiToxicity added dynamic banned word: '{w}'")

    @classmethod
    def remove_banned_word(cls, word: str) -> bool:
        """Removes a custom prohibited word from runtime filter."""
        w = word.strip().lower()
        if w in cls._dynamic_banned_words:
            cls._dynamic_banned_words.remove(w)
            logger.info(f"AntiToxicity removed dynamic banned word: '{w}'")
            return True
        return False

    @classmethod
    def get_dynamic_banned_words(cls) -> List[str]:
        return sorted(list(cls._dynamic_banned_words))

    DIGNIFIED_RETORTS = {
        "saudi_gulf": [
            "الله يسامحك يا بعدي.. كل إناء بما فيه ينضح، وأنا أرفع نفسي وأخلاقي عن هالأسلوب.. الله يهديك ويصلح حالك.",
            "تسلم على ذوقك يا رجال.. الرجولة شهامة وطيب كلام، وعمري ما راح أنزل لمستوى الشتايم.. حياك الله.",
            "ما راح أرد عليك بنفس كلامك يا خوي، لأن أهلي ربوني على الكلام الزين.. ربي يسامحك.",
        ],
        "levantine": [
            "الله يسامحك يا غالي.. الرجولة والأصل مش بالسب ولا بالكلام الجارح.. كلك ذوق عموماً والله يهديك.",
            "على راسي ذوقك، بس أنا متربي ما أرد على الإساءة بإساءة.. ربي يسامحك ويوفقك.",
            "تسلم يا حبيب قلبي، كل واحد بيعبر عن أخلاقه، وأنا أكبر من إني أنزل لهيك كلام.. تكرم.",
        ],
        "iraqi": [
            "الله يسامحك عيوني.. الكلام مرآة أصل صاحبه، وأنا عيوني وتربيتي أرفع بهواي من إني أنزل لهالمستوى.. ربي يهديك.",
            "تسلم وردة، ما راح أجاوبك بنفس أسلوبك لأن الطيب ما يطلع منه إلا الطيب.. الله يحفظك.",
        ],
        "maghrebi": [
            "الله يسامحك خويا.. التربية والأخلاق كتبان في الهضرة، وأنا ما كنعرفش نسب ولا نعاير.. الله يهديك ويصلح بالك.",
            "يسلمك خويا، كل واحد كيمثل راسو، وأنا أسلوبي راقي ومحترم.. مرحبا بيك والله يهديك.",
        ],
        "egyptian": [
            "الله يسامحك يا سيدي.. الرجولة والجدعنة عمرها ما كانت بالشتيمة، وأنا أرقى بكتير من إني أنزل لمستوى زي ده.. ربنا يهديك.",
            "تسلم يا محترم على ذوقك.. كل واحد بيعبر عن أصله وتربيته، وأنا مش هشتمك ولا هنزل لمستواك.. حصل خير.",
            "عيب عليك الكلام ده يا باشا، الشتيمة حيلة الضعيف.. خليك أرقى من كدة والرجولة شياكة.. ربنا يسامحك.",
        ],
        "english": [
            "I choose to respond with dignity and respect, regardless of your words. Wishing you peace and a better day.",
            "I'm keeping my standards high, my friend. No bad language here, just respect and honesty.",
        ],
    }

    @classmethod
    def contains_profanity(cls, text: str) -> bool:
        """
        Returns True if the text contains explicit profanity, vulgar slurs, or curses.
        """
        if not text:
            return False
        cleaned = text.lower()
        for pat in cls.VULGAR_PATTERNS:
            if re.search(pat, cleaned, re.IGNORECASE):
                return True
        for banned in cls._dynamic_banned_words:
            if banned in cleaned:
                return True
        return False

    @classmethod
    def sanitize_outgoing_speech(cls, text: str, dialect_code: str = "egyptian") -> str:
        """
        Rigorous post-processing: If an outgoing response contains any inappropriate words,
        replaces with a dignified ethical retort or scrubs the offending tokens completely.
        """
        if not text:
            return text

        if cls.contains_profanity(text):
            logger.warning(f"AntiToxicity intercepted vulgar language in outgoing speech. Replacing with dignified retort.")
            import random
            options = cls.DIGNIFIED_RETORTS.get(dialect_code, cls.DIGNIFIED_RETORTS["egyptian"])
            return random.choice(options)

        return text

    @classmethod
    def get_dignified_response_to_insult(cls, dialect_code: str = "egyptian") -> str:
        """
        Produces an immediate dignified refusal when provoked or insulted.
        """
        import random
        options = cls.DIGNIFIED_RETORTS.get(dialect_code, cls.DIGNIFIED_RETORTS["egyptian"])
        return random.choice(options)


# Global instance
anti_toxicity = AntiToxicityGuardrail()
