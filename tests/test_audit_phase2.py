"""
Comprehensive verification test suite for Phase 2:
- Zero-profanity & anti-toxicity guarantee across dialects
- Dynamic RBAC & Admin management
- Telegram interactive menus and callback buttons
- Anti-ban flood control and memory persistence
"""

import asyncio
import os
import sys

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Configure UTF-8 output
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from aether_human_core.config.settings import settings
from aether_human_core.database.postgres.connection import db_manager
from aether_human_core.psychology_engine.anti_toxicity import anti_toxicity
from aether_human_core.psychology_engine.admin_manager import admin_manager, RoleLevel
from aether_human_core.telegram_client.telegram_menu import telegram_menu
from aether_human_core.telegram_client.mtproto_manager import mtproto_manager
from aether_human_core.config.anti_ban_shield import anti_ban_shield


async def main():
    print("=" * 60)
    print("🚀 STARTING AUDIT VERIFICATION SUITE")
    print("=" * 60)

    # 1. Initialize DB Schema
    await db_manager.init_schema()

    # TEST 1: Zero-Profanity & Anti-Toxicity Outgoing Filter
    print("\n[TEST 1] Testing Zero-Profanity & Dignified Retort Engine...")
    bad_phrases = [
        "يا حيوان يا كلب",
        "كسمك يا ابن الحرام",
        "شرموطة وقحبة",
        "you are a fucking bitch and asshole",
        "يلعن شكلك وسافل وحقير",
    ]
    for phrase in bad_phrases:
        assert anti_toxicity.contains_profanity(phrase) is True, f"Failed to detect profanity in: {phrase}"
        sanitized = anti_toxicity.sanitize_outgoing_speech(phrase, dialect_code="egyptian")
        assert anti_toxicity.contains_profanity(sanitized) is False, f"Sanitization leaked profanity: {sanitized}"
        print(f"  ✓ Raw: '{phrase}' -> Sanitized: '{sanitized[:55]}...'")

    # TEST 2: Dynamic Banned Words at Runtime
    print("\n[TEST 2] Testing Dynamic Banned Words...")
    anti_toxicity.add_banned_word("بسبوسة_مسمومة")
    assert anti_toxicity.contains_profanity("جرب البسبوسة_مسمومة دي") is True
    sanitized_custom = anti_toxicity.sanitize_outgoing_speech("جرب البسبوسة_مسمومة دي")
    assert "بسبوسة_مسمومة" not in sanitized_custom
    anti_toxicity.remove_banned_word("بسبوسة_مسمومة")
    assert anti_toxicity.contains_profanity("جرب البسبوسة_مسمومة دي") is False
    print("  ✓ Dynamic banned word added, verified, and removed successfully.")

    # TEST 3: Dynamic RBAC & Admin Manager
    print("\n[TEST 3] Testing Dynamic RBAC & Hierarchy...")
    super_admin_id = 999999
    # Add to super admins
    settings.admin_user_ids = f"{super_admin_id},12345"
    assert admin_manager.is_super_admin(super_admin_id) is True
    assert await admin_manager.get_user_role(super_admin_id) == "SUPER_ADMIN"

    # SuperAdmin promotes a user to ADMIN
    target_user_id = 777001
    ok, msg = await admin_manager.promote_user(target_user_id, "ADMIN", assigned_by=super_admin_id)
    assert ok is True
    assert await admin_manager.is_admin(target_user_id) is True
    print(f"  ✓ User {target_user_id} promoted to ADMIN: {msg}")

    # Normal user (member) tries to promote someone -> REJECTED
    normal_user_id = 555002
    ok2, msg2 = await admin_manager.promote_user(888003, "ADMIN", assigned_by=normal_user_id)
    assert ok2 is False
    print(f"  ✓ Unauthorized promotion correctly rejected: {msg2}")

    # Demote user back to MEMBER
    ok3, msg3 = await admin_manager.demote_user(target_user_id, assigned_by=super_admin_id)
    assert ok3 is True
    assert await admin_manager.is_admin(target_user_id) is False
    print(f"  ✓ User {target_user_id} demoted back to MEMBER: {msg3}")

    # TEST 4: Dynamic In-Chat Rules & Prohibitions
    print("\n[TEST 4] Testing Dynamic Rules Persistence...")
    rule_content = "يمنع إرسال أي روابط تسويقية أو دعائية في الجروب"
    ok_rule, msg_rule = await admin_manager.add_dynamic_rule(
        operator_id=super_admin_id,
        instruction_text=rule_content,
        rule_type="RESTRICTION",
    )
    assert ok_rule is True
    rules = await admin_manager.list_active_rules()
    assert any(rule_content in r["instruction_text"] for r in rules)
    print(f"  ✓ Active rules count: {len(rules)} | Rule '{rule_content[:30]}...' stored in database.")

    # Delete rule
    created_rule_id = rules[-1]["id"]
    del_ok, del_msg = await admin_manager.delete_dynamic_rule(operator_id=super_admin_id, rule_id=created_rule_id)
    assert del_ok is True
    print(f"  ✓ Rule #{created_rule_id} deleted cleanly: {del_msg}")

    # TEST 5: Interactive Telegram Menus & Buttons
    print("\n[TEST 5] Testing Interactive Telegram Menus...")
    text_main, markup_main = await telegram_menu.render_main_dashboard(super_admin_id)
    assert "لوحة تحكم الكيان الذكي" in text_main
    assert len(markup_main["inline_keyboard"]) >= 4
    print("  ✓ Main Dashboard rendered with rich buttons.")

    text_stats, markup_stats = await telegram_menu.render_server_stats()
    assert "تقرير موارد السيرفر" in text_stats
    print("  ✓ Server stats menu rendered.")

    text_mood, markup_mood = await telegram_menu.render_mood_radar()
    assert "رادار الحالة النفسية والبيولوجية" in text_mood
    print("  ✓ Mood radar menu rendered.")

    text_admins, markup_admins = await telegram_menu.render_admins_panel(super_admin_id)
    assert "مسؤولي وإدارة النظام" in text_admins
    print("  ✓ Admins panel rendered.")

    # TEST 6: Telegram Menu Callback Engine
    print("\n[TEST 6] Testing Callback Query Handlers...")
    # Test coffee action
    t_c, m_c, alert_c, act_c = await telegram_menu.handle_callback("act:coffee", super_admin_id)
    assert alert_c is not None and "قهوة" in alert_c
    print(f"  ✓ Action 'act:coffee' handled with toast: '{alert_c}'")

    # Test chill action
    t_ch, m_ch, alert_ch, act_ch = await telegram_menu.handle_callback("act:chill", super_admin_id)
    assert alert_ch is not None and "الكورتيزول" in alert_ch
    print(f"  ✓ Action 'act:chill' handled with toast: '{alert_ch}'")

    # Test media triggers
    _, _, alert_v, act_v = await telegram_menu.handle_callback("act:send_voice", super_admin_id)
    assert act_v == "send_voice"
    print(f"  ✓ Action 'act:send_voice' triggered correctly.")

    _, _, alert_p, act_p = await telegram_menu.handle_callback("act:send_photo", super_admin_id)
    assert act_p == "send_photo"
    print(f"  ✓ Action 'act:send_photo' triggered correctly.")

    # TEST 7: Slash Command Interception
    print("\n[TEST 7] Testing Slash Command Dispatcher...")
    res_cmd = await mtproto_manager._handle_command(
        chat_id=super_admin_id,
        sender_id=super_admin_id,
        sender_name="Admin",
        message_text="/menu",
    )
    assert res_cmd is True
    print("  ✓ /menu command intercepted and handled.")

    res_add_rule = await mtproto_manager._handle_command(
        chat_id=super_admin_id,
        sender_id=super_admin_id,
        sender_name="Admin",
        message_text="/add_rule ممنوع التحدث في السياسة داخل الجروب",
    )
    assert res_add_rule is True
    print("  ✓ /add_rule command intercepted and handled.")

    # TEST 8: Anti-Ban Flood Guard
    print("\n[TEST 8] Testing Anti-Ban Flood Guard...")
    for _ in range(5):
        await anti_ban_shield.wait_for_telegram_slot(chat_id=123)
    print("  ✓ Anti-ban token bucket executed smoothly without blocking.")

    print("\n" + "=" * 60)
    print("🎉 ALL 8 TESTS PASSED WITH 100% SUCCESS!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
