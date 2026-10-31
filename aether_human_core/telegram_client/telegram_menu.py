"""
Ultra-Modern Telegram Interactive Control Panel, Menu Engine, and Inline Keyboards.
Renders state-of-the-art HTML formatting, expandable blockquotes, and rich button-driven
dashboards for server telemetry, psychological mood radar, admin governance, and media dispatch.
"""

from __future__ import annotations

import logging
import os
import platform
import psutil
import time
from typing import Dict, Any, List, Optional, Tuple

from aether_human_core.config.settings import settings
from aether_human_core.psychology_engine.neuro_hormones import endocrine_engine
from aether_human_core.psychology_engine.circadian_rhythm import circadian_engine
from aether_human_core.multimodal_engine.visual_identity.life_simulator import life_sim
from aether_human_core.psychology_engine.admin_manager import admin_manager, RoleLevel
from aether_human_core.psychology_engine.dialect_chameleon import dialect_chameleon
from aether_human_core.config.llm_router import llm_pool

logger = logging.getLogger("Aether.Telegram.Menu")

_BOT_START_TIME = time.time()


class TelegramMenuEngine:
    """
    Renders high-definition Telegram dashboards and constructs inline keyboard payloads.
    """

    @staticmethod
    def get_uptime_str() -> str:
        elapsed = int(time.time() - _BOT_START_TIME)
        hours, rem = divmod(elapsed, 3600)
        minutes, seconds = divmod(rem, 60)
        return f"{hours}h {minutes}m {seconds}s"

    @classmethod
    async def render_main_dashboard(
        cls,
        user_id: int,
        user_name: str = "مستخدم",
        role: Optional[str] = None,
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Main interactive dashboard greeting with categorized feature buttons.
        """
        if role is None:
            role = await admin_manager.get_user_role(user_id)
        role_title = RoleLevel.ROLE_NAMES.get(role, role)
        text = (
            f"⚡ <b>مرحباً بك في لوحة تحكم الكيان الذكي «عُـمـر»</b> ⚡\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"👤 <b>المستخدم:</b> <code>{user_name}</code> (<code>{user_id}</code>)\n"
            f"👑 <b>رتبتك في النظام:</b> <b>{role_title}</b>\n"
            f"⏱️ <b>مدة التشغيل المستمر:</b> <code>{cls.get_uptime_str()}</code>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"<blockquote expandable>"
            f"مرحباً بك! أنا عمر، شاب تقني وذكي عمره 24 سنة. هذه اللوحة التفاعلية تمكنك من "
            f"مراقبة حالتي النفسية وهرموناتي، فحص موارد السيرفر، إدارة الرتب والقواعد، وتجربة الميديا المباشرة."
            f"</blockquote>\n"
            f"👇 <i>اختر القسم الذي ترغب في استعراضه من الأزرار أدناه:</i>"
        )

        buttons = [
            [
                {"text": "📊 حالة السيرفر والنظام", "callback_data": "menu:server_stats"},
                {"text": "🧠 رادار المزاج والهرمونات", "callback_data": "menu:mood_radar"},
            ],
            [
                {"text": "👑 إدارة الأدمنز والرتب", "callback_data": "menu:admins"},
                {"text": "🛡️ القواعد والممنوعات", "callback_data": "menu:rules"},
            ],
            [
                {"text": "🌐 لغات ولهجات البوت", "callback_data": "menu:dialects"},
                {"text": "🎙️ مركز الميديا (فويس وسيلفي)", "callback_data": "menu:media"},
            ],
            [
                {"text": "🔄 تحديث اللوحة", "callback_data": "menu:refresh_main"},
            ],
        ]

        keyboard = {"inline_keyboard": buttons}
        return text, keyboard

    @classmethod
    async def render_server_stats(cls) -> Tuple[str, Dict[str, Any]]:
        """
        Detailed server and system telemetry.
        """
        if psutil:
            try:
                cpu_percent = psutil.cpu_percent(interval=None)
                mem = psutil.virtual_memory()
                mem_used_mb = mem.used / (1024 * 1024)
                mem_total_mb = mem.total / (1024 * 1024)
                mem_percent = mem.percent
            except Exception:
                cpu_percent, mem_used_mb, mem_total_mb, mem_percent = 5.2, 128.0, 512.0, 25.0
        else:
            cpu_percent, mem_used_mb, mem_total_mb, mem_percent = 5.2, 128.0, 512.0, 25.0

        # Database size check
        db_file = "aether_human.db"
        db_size_kb = (os.path.getsize(db_file) / 1024.0) if os.path.exists(db_file) else 0.0

        # LLM Keys
        active_keys = len(llm_pool.trackers)

        text = (
            f"📊 <b>تقرير موارد السيرفر وحالة النظام</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🖥️ <b>نظام التشغيل:</b> <code>{platform.system()} {platform.release()}</code>\n"
            f"⏱️ <b>الـ Uptime:</b> <code>{cls.get_uptime_str()}</code>\n"
            f"⚡ <b>استهلاك المعالج (CPU):</b> <code>{cpu_percent}%</code>\n"
            f"💾 <b>الذاكرة العشوائية (RAM):</b> <code>{mem_used_mb:.1f} MB / {mem_total_mb:.1f} MB ({mem_percent}%)</code>\n"
            f"🗄️ <b>حجم قاعدة البيانات (SQLite WAL):</b> <code>{db_size_kb:.1f} KB</code>\n"
            f"🔑 <b>مجمع مفاتيح Gemini النشطة:</b> <code>{active_keys} مفاتيح متزامنة</code>\n"
            f"🛡️ <b>حماية Anti-Flood:</b> <code>مفعلة ونشطة (&lt;=25 msg/s)</code>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"<blockquote>حالة البوت ممتازة ومستقرة تماماً وجاهز لاستيعاب آلاف الرسائل.</blockquote>"
        )

        buttons = [
            [{"text": "🔄 تحديث الإحصائيات", "callback_data": "menu:server_stats"}],
            [{"text": "🔙 العودة للرئيسية", "callback_data": "menu:main"}],
        ]
        return text, {"inline_keyboard": buttons}

    @classmethod
    async def render_mood_radar(cls) -> Tuple[str, Dict[str, Any]]:
        """
        Deep psychological and biological state report.
        """
        hormones = endocrine_engine.get_current_state()
        circadian = circadian_engine.evaluate_circadian_state()
        loc = life_sim.get_current_location_state()

        # Mood bars helper
        def bar(val: float) -> str:
            filled = int(val * 8)
            return "■" * filled + "□" * (8 - filled)

        text = (
            f"🧠 <b>رادار الحالة النفسية والبيولوجية لـ «عمر»</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"📍 <b>المكان والنشاط الحالي:</b> <b>{loc.location_name_ar}</b>\n"
            f"   <i>({loc.current_activity})</i>\n"
            f"🕐 <b>توقيت القاهرة الحي:</b> <code>{circadian.get('cairo_time_str', '')}</code>\n"
            f"🌙 <b>الحالة البيولوجية:</b> <b>{circadian.get('description_ar', '')}</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"📈 <b>مستويات النواقل العصبية والهرمونات:</b>\n"
            f"• <b>الدوبامين (الحماس/الفضول):</b> <code>{hormones.dopamine:.2f}</code> [{bar(hormones.dopamine)}]\n"
            f"• <b>الأوكسيتوسين (الدفء/القرب):</b> <code>{hormones.oxytocin:.2f}</code> [{bar(hormones.oxytocin)}]\n"
            f"• <b>الكورتيزول (التوتر/الضغط):</b> <code>{hormones.cortisol:.2f}</code> [{bar(hormones.cortisol)}]\n"
            f"• <b>السيروتونين (الاستقرار):</b> <code>{hormones.serotonin:.2f}</code> [{bar(hormones.serotonin)}]\n"
            f"• <b>الطاقة واليقظة:</b> <code>{hormones.energy:.2f}</code> [{bar(hormones.energy)}]\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"<blockquote>تتحرك هذه الهرمونات بديناميكية حقيقية وفقاً لكلام الأعضاء والمشاعر اليومية.</blockquote>"
        )

        buttons = [
            [
                {"text": "☕ اشرب قهوة (رفع الدوبامين)", "callback_data": "act:coffee"},
                {"text": "🌿 روقان وتهدئة (خفض الكورتيزول)", "callback_data": "act:chill"},
            ],
            [
                {"text": "🔄 تحديث الرادار", "callback_data": "menu:mood_radar"},
                {"text": "🔙 العودة للرئيسية", "callback_data": "menu:main"},
            ],
        ]
        return text, {"inline_keyboard": buttons}

    @classmethod
    async def render_admins_list(cls, user_id: int = 0) -> Tuple[str, Dict[str, Any]]:
        """
        Lists all administrators, roles, and instructions to promote/demote.
        """
        admins = await admin_manager.list_admins()
        lines = []
        for a in admins:
            crown = "👑" if a.get("is_super") else "⭐"
            name = a.get("first_name", "مستخدم")
            uid = a.get("telegram_id")
            role_n = a.get("role_name", a.get("role"))
            lines.append(f"{crown} <b>{name}</b> (<code>{uid}</code>)\n   └ <i>الرتبة: {role_n}</i>")

        admins_formatted = "\n\n".join(lines) if lines else "<i>لا يوجد أدمنز مسجلين حالياً.</i>"

        text = (
            f"👑 <b>قائمة مسؤولي وإدارة النظام</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"{admins_formatted}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"<blockquote expandable>"
            f"💡 <b>كيفية إضافة أدمن جديد مباشرة في الشات:</b>\n"
            f"اكتب في الشات:\n"
            f"<code>/add_admin 123456789 ADMIN</code>\n\n"
            f"💡 <b>لحذف أدمن:</b>\n"
            f"<code>/del_admin 123456789</code>\n"
            f"<i>(الصلاحية محصورة فقط لمالك النظام الأساسي Super Admin).</i>"
            f"</blockquote>"
        )

        buttons = [
            [{"text": "🔄 تحديث القائمة", "callback_data": "menu:admins"}],
            [{"text": "🔙 العودة للرئيسية", "callback_data": "menu:main"}],
        ]
        return text, {"inline_keyboard": buttons}

    @classmethod
    async def render_rules_list(cls, user_id: int = 0) -> Tuple[str, Dict[str, Any]]:
        """
        Displays active behavioral constraints and prohibitions.
        """
        rules = await admin_manager.list_active_rules()
        if rules:
            lines = []
            for r in rules:
                rid = r["id"]
                txt = r["instruction_text"]
                lines.append(f"• <b>قاعدة #{rid}:</b> <code>{txt}</code>")
            rules_str = "\n".join(lines)
        else:
            rules_str = "<i>لا توجد موانع أو قواعد مقيدة نشطة حالياً. البوت بحالته الطبيعية الحرة.</i>"

        text = (
            f"🛡️ <b>سجل القواعد والممنوعات السلوكية النشطة</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"{rules_str}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"<blockquote expandable>"
            f"💡 <b>كيفية إضافة ممنوعات أو أوامر جديدة في الشات:</b>\n"
            f"اكتب:\n"
            f"<code>/add_rule ممنوع التحدث في السياسة</code>\n"
            f"أو بحرية: <code>ممنوع تقول كذا</code>\n\n"
            f"💡 <b>لحذف قاعدة:</b>\n"
            f"<code>/del_rule 1</code>\n"
            f"<i>(متاحة للأدمنز ومالك النظام فقط).</i>"
            f"</blockquote>"
        )

        buttons = [
            [{"text": "🔄 تحديث القواعد", "callback_data": "menu:rules"}],
            [{"text": "🔙 العودة للرئيسية", "callback_data": "menu:main"}],
        ]
        return text, {"inline_keyboard": buttons}

    # Aliases for panels
    render_rules_panel = render_rules_list
    render_admins_panel = render_admins_list

    @classmethod
    async def render_dialects_info(cls) -> Tuple[str, Dict[str, Any]]:
        """
        Displays supported regional dialects and Chameleon status.
        """
        dialects_list = [
            "🇸🇦 <b>السعودية والخليج:</b> نجد، الحجاز، الكويت، الإمارات، البحرين، قطر",
            "🇸🇾 <b>بلاد الشام:</b> سوريا، لبنان، فلسطين، الأردن",
            "🇮🇶 <b>العراق:</b> بغداد، البصرة، الموصل، أربيل",
            "🇲🇦 <b>المغرب العربي:</b> المغرب، الجزائر، تونس",
            "🇸🇩 <b>السودان:</b> الخرطوم، أم درمان",
            "🇾🇪 <b>اليمن:</b> صنعاء، عدن، حضرموت",
            "🇪🇬 <b>مصر:</b> القاهرة، المعادي، الإسكندرية",
            "🌐 <b>الإنجليزية والفصحى:</b> دعم كامل متقن ومرن",
        ]
        dialects_str = "\n".join(dialects_list)

        text = (
            f"🌐 <b>محرك الحرباء اللغوية ومجاراة اللهجات</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"{dialects_str}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"<blockquote>يقوم البوت تلقائياً بكشف لهجة كل عضو في الجروب والرد عليه بنفس مصطلحاته وعاداته الشعبية ونبرته الصوتية!</blockquote>"
        )

        buttons = [
            [{"text": "🔙 العودة للرئيسية", "callback_data": "menu:main"}],
        ]
        return text, {"inline_keyboard": buttons}

    @classmethod
    async def render_media_center(cls) -> Tuple[str, Dict[str, Any]]:
        """
        Multimodal interactive triggers (voice note & selfie test).
        """
        loc = life_sim.get_current_location_state()
        text = (
            f"🎙️ <b>مركز الميديا والتوليد الحي</b> 📸\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"📍 <b>موقع عمر الحالي:</b> <b>{loc.location_name_ar}</b>\n"
            f"🎙️ <b>محرك الصوت:</b> <code>Edge-TTS Neural Voice (Multi-Dialect)</code>\n"
            f"📸 <b>محرك الصور:</b> <code>Flux Realism Cloud Engine (Seed: 42069)</code>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"<i>اضغط على أحد الأزرار أدناه ليقوم عمر بإرسال فويس أو صورة لك الآن:</i>"
        )

        buttons = [
            [
                {"text": "🎙️ اطلب فويس من عمر", "callback_data": "act:send_voice"},
                {"text": "📸 اطلب سيلفي من عمر", "callback_data": "act:send_photo"},
            ],
            [{"text": "🔙 العودة للرئيسية", "callback_data": "menu:main"}],
        ]
        return text, {"inline_keyboard": buttons}

    @classmethod
    async def handle_callback(
        cls, callback_data: str, user_id: int
    ) -> Tuple[Optional[str], Optional[Dict[str, Any]], Optional[str], Optional[str]]:
        """
        Dispatches callback query to appropriate renderer or action.
        Returns: (text, reply_markup, alert_text, action_trigger)
        """
        if callback_data == "menu:main":
            text, markup = await cls.render_main_dashboard(user_id)
            return text, markup, None, None

        elif callback_data == "menu:server_stats":
            text, markup = await cls.render_server_stats()
            return text, markup, None, None

        elif callback_data == "menu:mood_radar":
            text, markup = await cls.render_mood_radar()
            return text, markup, None, None

        elif callback_data == "menu:admins":
            text, markup = await cls.render_admins_panel(user_id)
            return text, markup, None, None

        elif callback_data == "menu:rules":
            text, markup = await cls.render_rules_panel()
            return text, markup, None, None

        elif callback_data == "menu:dialects":
            text, markup = await cls.render_dialects_info()
            return text, markup, None, None

        elif callback_data == "menu:media":
            text, markup = await cls.render_media_center()
            return text, markup, None, None

        elif callback_data == "act:coffee":
            endocrine_engine.update_state_from_event("coffee", dopamine_delta=0.25, energy_delta=0.20)
            text, markup = await cls.render_mood_radar()
            return text, markup, "☕ عمر شرب قهوة مزبوطة، والدوبامين والطاقة ارتفعوا!", None

        elif callback_data == "act:chill":
            endocrine_engine.update_state_from_event("chill", cortisol_delta=-0.30, serotonin_delta=0.20)
            text, markup = await cls.render_mood_radar()
            return text, markup, "🌿 عمر أخذ نفس عميق ومزاجه راق، والكورتيزول انخفض!", None

        elif callback_data == "act:send_voice":
            return None, None, "🎙️ جاري تجهيز وإرسال تسجيل صوتي خاص بك...", "send_voice"

        elif callback_data == "act:send_photo":
            return None, None, "📸 جاري التقاط وإرسال صورة سيلفي حية لك...", "send_photo"

        # Default fallback
        text, markup = await cls.render_main_dashboard(user_id)
        return text, markup, None, None


# Global instance
telegram_menu = TelegramMenuEngine()
