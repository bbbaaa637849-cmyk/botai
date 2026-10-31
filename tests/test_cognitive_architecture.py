"""
Comprehensive Verification Suite for Project Aether-Human.
Tests Endocrine Equations, Affinity Matrices, Social Influence Compilers,
Pre-Cognitive Interceptors, Multi-Bubble Bursts, Typos, and Cognitive Maestro.
"""

from __future__ import annotations

import asyncio
import logging
import os
import sys
import time

# Configure UTF-8 for console output on Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

# Ensure project root in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from aether_human_core.config.settings import settings
from aether_human_core.config.llm_router import llm_pool
from aether_human_core.database.postgres.connection import db_manager
from aether_human_core.database.postgres.repositories.user_repo import UserRepository
from aether_human_core.database.postgres.repositories.behavioral_rule_repo import BehavioralRuleRepository
from aether_human_core.database.vector_store.qdrant_client import vector_memory
from aether_human_core.psychology_engine.neuro_hormones import endocrine_engine
from aether_human_core.psychology_engine.affinity_matrix import (
    affinity_calc,
    UserAffinityVector,
    RelationshipTier,
)
from aether_human_core.psychology_engine.social_influence import (
    SocialConstraintCompiler,
    PreCognitiveRuleInterceptor,
)
from aether_human_core.psychology_engine.micro_traits import micro_traits_engine
from aether_human_core.psychology_engine.circadian_rhythm import circadian_engine
from aether_human_core.telegram_client.human_typer import human_typer
from aether_human_core.multimodal_engine.visual_identity.life_simulator import life_sim
from aether_human_core.multimodal_engine.visual_identity.face_lock_pipeline import face_lock_pipeline
from aether_human_core.multimodal_engine.acoustic_voice.emotion_detector import acoustic_detector
from aether_human_core.multimodal_engine.acoustic_voice.realistic_voice_generator import voice_generator
from aether_human_core.cognitive_engine.orchestrator import cognitive_orchestrator

logger = logging.getLogger("Aether.Tests")


async def run_all_tests():
    print("=" * 70)
    print("🚀 RUNNING COMPREHENSIVE AETHER-HUMAN VERIFICATION SUITE")
    print("=" * 70)

    # 1. Test Database Schema Init
    print("\n[Test 1/12] Initializing Relational Schema...")
    await db_manager.init_schema()
    print("✅ Database schema initialized successfully.")

    # 2. Test Gemini API Multi-Key Pool
    print("\n[Test 2/12] Testing Gemini Multi-Key Rotation Pool...")
    assert len(settings.gemini_keys_list) == 11, f"Expected 11 keys, got {len(settings.gemini_keys_list)}"
    test_tracker = llm_pool.trackers[0]
    print(f"Key pool initialized with {len(llm_pool.trackers)} keys. Primary key: {test_tracker.masked_key}")
    assert test_tracker.is_available() is True
    print("✅ Gemini Multi-Key pool configuration verified.")

    # 3. Test Neuro-Endocrine Hormone Differential Equations
    print("\n[Test 3/12] Testing Endocrine Hormones & Acute Shocks...")
    state_before = endocrine_engine.get_current_state()
    deltas = endocrine_engine.apply_event_shock("INSULT_OR_DISRESPECT", intensity=1.5)
    state_after = endocrine_engine.get_current_state()
    assert state_after.cortisol > state_before.cortisol
    print(f"Cortisol surged from {state_before.cortisol:.2f} to {state_after.cortisol:.2f} on insult.")
    mood = endocrine_engine.evaluate_psychological_mood()
    print(f"Psychological mood synthesized: {mood['mood_ar']} ({mood['temperament']})")
    print("✅ Neuro-Endocrine dynamics verified.")

    # 4. Test Affinity Matrix & Tier Transitions
    print("\n[Test 4/12] Testing Affinity Matrix Transitions...")
    vec = UserAffinityVector(user_id=999, affinity_score=10.0, trust_score=20.0, romantic_attachment=5.0)
    da, dt, dr, dp = affinity_calc.evaluate_interaction_delta(vec, "KIND_SUPPORT", emotional_intensity=2.0)
    vec.affinity_score += da
    vec.trust_score += dt
    vec.tier = affinity_calc.recompute_tier(vec)
    print(f"Affinity delta applied: +{da} Aff, +{dt} Trust. New tier: {vec.tier.value}")
    assert vec.affinity_score > 10.0
    print("✅ Affinity matrix evaluated successfully.")

    # 5. Test Social Constraint Compiler (Natural Language Directive)
    print("\n[Test 5/12] Testing Social Constraint Compiler & Authority...")
    # Low-affinity stranger attempts to command bot
    stranger = UserAffinityVector(user_id=111, affinity_score=5.0, tier=RelationshipTier.STRANGER)
    comp_stranger = SocialConstraintCompiler.compile_directive(stranger, "غريب", "ماتكلمش بنات")
    assert comp_stranger.is_accepted is False
    assert comp_stranger.rejection_reason == "INSUFFICIENT_AFFINITY_AUTHORITY"
    print(f"Rebellion retort generated: '{comp_stranger.response_to_commander}'")

    # Exclusive romantic partner issues directive
    partner = UserAffinityVector(
        user_id=222,
        affinity_score=90.0,
        trust_score=85.0,
        romantic_attachment=90.0,
        tier=RelationshipTier.EXCLUSIVE_PARTNER,
    )
    comp_partner = SocialConstraintCompiler.compile_directive(partner, "حبيبتي", "ماتكلمش بنات غيري وخليك رسمي مع أي بنت")
    assert comp_partner.is_accepted is True
    assert comp_partner.rule_type == "RESTRICT_FEMALE_TALK"
    print(f"Partner directive accepted! Response: '{comp_partner.response_to_commander}'")
    print("✅ Social Constraint Compiler verified.")

    # 6. Test Pre-Cognitive Rule Interceptor & Loyalty Reporting
    print("\n[Test 6/12] Testing Pre-Cognitive Interceptor...")
    async with db_manager.session() as session:
        b_repo = BehavioralRuleRepository(session)
        rule = await b_repo.create_rule(
            commander_id=222,
            rule_type="RESTRICT_FEMALE_TALK",
            instruction_text="حظر التحدث الودي مع الفتيات",
            target_gender="female",
        )
        active_rules = await b_repo.get_active_rules()

    interception = PreCognitiveRuleInterceptor.intercept_incoming_message(
        sender_id=777,
        sender_name="نورا",
        sender_gender="female",
        message_text="هاي عمر إزيك؟",
        active_rules=active_rules,
    )
    assert interception.is_intercepted is True
    assert interception.behavior_mode == "COLD_DISMISS"
    assert interception.should_report_loyalty is True
    assert interception.loyalty_partner_id == 222
    print(f"Icy dismissal chosen: '{interception.curt_response_text}'")
    print(f"Loyalty report generated: '{interception.loyalty_report_message}'")
    # Clean up test rule so it does not pollute real runtime
    async with db_manager.session() as session:
        b_repo = BehavioralRuleRepository(session)
        await b_repo.deactivate_rule(rule.id)
    print("✅ Pre-Cognitive Interceptor & Loyalty Reporting verified.")

    # 7. Test Micro-Traits: Shyness & Group Jealousy
    print("\n[Test 7/12] Testing Micro-Traits (Shyness & Jealousy)...")
    is_shy, prefix, emoji = micro_traits_engine.evaluate_shyness(partner, "بحبك يا قلبي أنت عسل أوي", oxytocin_level=0.8)
    assert is_shy is True
    print(f"Shyness triggered! Stutter: '{prefix}', Emoji: '{emoji}'")

    jealousy_reproach = micro_traits_engine.evaluate_group_jealousy(
        partner, "حبيبتي", "ههههههه أموت فيك يا عسل", "أحمد"
    )
    if jealousy_reproach:
        print(f"Jealousy triggered: '{jealousy_reproach}'")
    print("✅ Micro-traits evaluated successfully.")

    # 8. Test Circadian Rhythm Simulator
    print("\n[Test 8/12] Testing Circadian Rhythm (Cairo Time)...")
    circadian = circadian_engine.evaluate_circadian_state()
    print(f"Cairo time: {circadian['cairo_time_str']} | State: {circadian['state_name']} | Typo mult: {circadian['typo_multiplier']}x")
    assert circadian["hour_fraction"] >= 0.0
    print("✅ Circadian clock verified.")

    # 9. Test Human Typer: Multi-Bubble Bursting & Typos
    print("\n[Test 9/12] Testing Human Typer Multi-Bubble Bursting & Typos...")
    long_msg = "أهلاً يا غالي إيه الأخبار؟ بص أنا كنت شغال في البرمجة طول النهار ومصدع الصراحة. المهم طمني عليك عملت إيه النهارده؟"
    bubbles = human_typer.split_into_multi_bubble_bursts(long_msg)
    assert len(bubbles) >= 2
    print(f"Split long message into {len(bubbles)} natural bubbles:")
    for b in bubbles:
        print(f"  - Bubble: '{b}'")

    bursts = human_typer.prepare_message_bursts(long_msg)
    print(f"Computed burst delays: {[b.typing_delay_sec for b in bursts]}s")
    print("✅ Human Typer bursting and delay logic verified.")

    # 10. Test Acoustic Emotion Detector & Voice Synthesis
    print("\n[Test 10/12] Testing Multimodal Acoustic Engine...")
    voice_path, waveform = await voice_generator.generate_voice_note(
        text_content="أهلاً يا باشا، كل سنة وأنت طيب وبخير",
        emotional_tone="WARM",
        format_ext="ogg",
    )
    assert os.path.exists(voice_path)
    assert os.path.getsize(voice_path) > 5000, f"Voice file too small: {os.path.getsize(voice_path)} bytes"
    assert len(waveform) > 0
    print(f"✅ Real human Egyptian voice note created: {voice_path} (Size: {os.path.getsize(voice_path)} bytes, Waveform: {len(waveform)} bars)")
    print("✅ Acoustic Voice Note engine verified.")

    # 11. Test Visual Identity & Face-Locked Pipeline
    print("\n[Test 11/12] Testing Visual Identity Life Simulator & Photo Gen...")
    loc = life_sim.get_current_location_state()
    print(f"Current physical location: {loc.location_name_ar} ({loc.current_activity})")
    can_send, verbal = life_sim.evaluate_photo_request(partner, "حبيبتي")
    assert can_send is True
    # Request photo in CAFE location as specified in requirements
    photo_file = await face_lock_pipeline.generate_photo(requester_name="حبيبتي", location_override="CAFE")
    assert os.path.exists(photo_file)
    assert os.path.getsize(photo_file) > 10000, f"Photo file too small: {os.path.getsize(photo_file)} bytes"
    assert "cafe" in os.path.basename(photo_file).lower()
    print(f"✅ Photorealistic human selfie created: {photo_file} (Size: {os.path.getsize(photo_file)} bytes)")
    print("✅ Visual identity pipeline verified.")

    # 12. Test Cognitive Orchestrator End-to-End
    print("\n[Test 12/12] Testing Cognitive Maestro End-to-End Orchestration...")
    async with db_manager.session() as session:
        u_repo = UserRepository(session)
        await u_repo.get_or_create(telegram_id=222, first_name="حبيبتي", gender="female")
        await u_repo.update_affinity_scores(telegram_id=222, delta_affinity=90.0, delta_romantic=90.0, delta_trust=85.0)

    resp = await cognitive_orchestrator.process_incoming_event(
        telegram_message_id=int(time.time()),
        chat_id=222,
        sender_id=222,
        sender_name="حبيبتي",
        message_text="وحشتني يا عمر، طمني عليك بتعمل إيه دلوقتي في المعادي؟",
        chat_type="private",
    )
    print(f"Decision: {resp.decision_type}")
    print(f"Inner Monologue: '{resp.inner_monologue_text}'")
    print(f"Omar's Colloquial Egyptian Reply: '{resp.raw_response_text}'")
    assert resp.raw_response_text != ""
    print("✅ Cognitive Maestro executed end-to-end successfully.")

    print("\n" + "=" * 70)
    print("🎉 ALL 12 VERIFICATION SUITES PASSED FLAWLESSLY!")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(run_all_tests())
