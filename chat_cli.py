"""
Interactive Local Terminal Chat with Omar (عمر).
Allows immediate real-time colloquial conversation, inner monologue observation,
voice note generation, and photo requests directly from the console without needing Telegram.
"""

from __future__ import annotations

import asyncio
import os
import sys

# Configure UTF-8 for console output on Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

from aether_human_core.database.postgres.connection import db_manager
from aether_human_core.database.postgres.repositories.user_repo import UserRepository
from aether_human_core.psychology_engine.neuro_hormones import endocrine_engine
from aether_human_core.psychology_engine.circadian_rhythm import circadian_engine
from aether_human_core.cognitive_engine.orchestrator import cognitive_orchestrator
from aether_human_core.multimodal_engine.visual_identity.face_lock_pipeline import face_lock_pipeline
from aether_human_core.multimodal_engine.visual_identity.life_simulator import life_sim
from aether_human_core.multimodal_engine.acoustic_voice.realistic_voice_generator import voice_generator


async def interactive_chat():
    print("=" * 65)
    print("🌟 مرحباً بك في المحادثة المباشرة مع 'عمر' (Aether-Human CLI) 🌟")
    print("عمر: شاب مصري 24 سنة، عايش في القاهرة، له مشاعر وساعة بيولوجية وهرمونات حية.")
    print("اكتب رسالتك وتكلم معاه عادي كأنه صاحبك على تيليجرام.")
    print("أوامر خاصة:")
    print("  - اكتب 'ابعت صورتك' أو 'سيلفي' عشان يبعتلك صورته الفوتوغرافية.")
    print("  - اكتب 'فويس' أو 'ريكورد' مع أي جملة عشان يسجلهالك بصوته المصري.")
    print("  - اكتب 'حالة' عشان تشوف هرموناته ومكانه الحالي والساعة في القاهرة.")
    print("  - اكتب 'خروج' أو 'exit' للإنهاء.")
    print("=" * 65)

    # 1. Initialize schema
    await db_manager.init_schema()

    user_name = input("\n👤 اسمك إيه؟ (أو اضغط Enter لـ 'حبيبتي' / 'صاحبي'): ").strip() or "حبيبتي"
    gender = "female" if user_name in ("حبيبتي", "سارة", "نورا", "مريم") else "male"
    user_id = 99999

    print(f"\nتم بدء المحادثة بصفتك: [{user_name}] | جاري استحضار وعي عمر...\n")

    msg_counter = 1000

    while True:
        try:
            user_input = input(f"[{user_name}]: ").strip()
            if not user_input:
                continue

            if user_input.lower() in ("خروج", "exit", "quit"):
                print("\nمع السلامة يا غالي! أشوفك على خير 👋")
                break

            if user_input == "حالة":
                mood = endocrine_engine.evaluate_psychological_mood()
                circ = circadian_engine.evaluate_circadian_state()
                loc = life_sim.get_current_location_state()
                h = endocrine_engine.get_current_state()
                print("\n" + "-" * 50)
                print(f"🕒 توقيت القاهرة: {circ['cairo_time_str']} ({circ['state_name']})")
                print(f"📍 مكانه الحالي: {loc.location_name_ar} - {loc.current_activity}")
                print(f"🧠 حالته النفسية: {mood['mood_ar']} ({mood['temperament']})")
                print(f"🧪 الهرمونات: دوبامين={h.dopamine:.2f} | أوكسيتوسين={h.oxytocin:.2f} | كورتيزول={h.cortisol:.2f} | سيروتونين={h.serotonin:.2f}")
                print("-" * 50 + "\n")
                continue

            # Check if user specifically asks for photo
            if any(w in user_input for w in ["ابعت صورتك", "سيلفي", "عايز اشوفك", "عايزة اشوفك", "صورتك"]):
                print("\n[عمر بيفكر]: بيطلبوا صورتي.. ثواني أظبط الكاميرا وآخد سيلفي...")
                photo_path = await face_lock_pipeline.generate_photo(requester_name=user_name)
                print(f"📸 [عمر بعتلك صورة سيلفي]: {photo_path}")
                print(f"حجم الصورة: {os.path.getsize(photo_path):,} بايت | فوتوغرافية حقيقية بدون علامات مائية.")

            # Check if voice note requested
            elif any(w in user_input for w in ["فويس", "ريكورد", "صوتك"]):
                print("\n[عمر بيسجل فويس نوت بصوته الحقيقي ar-EG-ShakirNeural...]")
                voice_path, _ = await voice_generator.generate_voice_note(
                    text_content="أهلاً يا غالي، والله منور وواحشني، ثواني أكون معاك يا باشا",
                    emotional_tone="WARM",
                    format_ext="ogg",
                )
                print(f"🎙️ [عمر بعتلك ريكورد فويس]: {voice_path}")
                print(f"حجم الصوت: {os.path.getsize(voice_path):,} بايت | شغال بلهجة مصرية مسموعة.")

            # Normal cognitive process
            msg_counter += 1
            resp = await cognitive_orchestrator.process_incoming_event(
                telegram_message_id=msg_counter,
                chat_id=user_id,
                sender_id=user_id,
                sender_name=user_name,
                message_text=user_input,
                sender_gender=gender,
                chat_type="private",
            )

            # Display Omar's inner monologue & answer
            print(f"\n💭 [مونولوج عمر الداخلي السري]: \"{resp.inner_monologue_text}\"")
            print(f"🗣️ [عمر]: {resp.raw_response_text}\n")

        except (KeyboardInterrupt, EOFError):
            print("\nتم إنهاء المحادثة.")
            break
        except Exception as e:
            print(f"\n⚠️ حدث خطأ أثناء المعالجة: {e}\n")


if __name__ == "__main__":
    asyncio.run(interactive_chat())

