"""
Media, Acoustic Voice Note, and Selfie Request Event Handler.
Handles voice perception, emotional empathy responses, direct voice note requests,
and face-locked selfie deliveries.
"""

from __future__ import annotations

import logging
import random
from typing import Optional

from aether_human_core.database.postgres.connection import db_manager
from aether_human_core.database.postgres.repositories.user_repo import UserRepository
from aether_human_core.multimodal_engine.acoustic_voice.emotion_detector import acoustic_detector
from aether_human_core.multimodal_engine.acoustic_voice.realistic_voice_generator import voice_generator
from aether_human_core.multimodal_engine.visual_identity.life_simulator import life_sim
from aether_human_core.multimodal_engine.visual_identity.face_lock_pipeline import face_lock_pipeline
from aether_human_core.cognitive_engine.orchestrator import cognitive_orchestrator
from aether_human_core.psychology_engine.neuro_hormones import endocrine_engine
from aether_human_core.telegram_client.human_typer import human_typer
from aether_human_core.telegram_client.mtproto_manager import mtproto_manager
from aether_human_core.psychology_engine.affinity_matrix import UserAffinityVector, RelationshipTier

logger = logging.getLogger("Aether.Telegram.MediaHandler")


class MediaEventHandler:
    """
    Orchestrates multimodal reception and transmission across Telegram.
    """

    @classmethod
    async def handle_incoming_voice(
        cls,
        message_id: int,
        chat_id: int,
        sender_id: int,
        sender_name: str,
        voice_file_path: str,
    ) -> None:
        """
        Handles incoming voice message: extracts emotion and responds empathetically.
        """
        logger.info(f"Received Voice Note from [{sender_name}] in Chat [{chat_id}].")

        # 1. Acoustic Emotion Recognition
        analysis = await acoustic_detector.analyze_voice_note(
            audio_file_path=voice_file_path, sender_name=sender_name
        )

        # 2. Craft contextual human response
        if analysis.empathy_dialogue_cue:
            reply_text = analysis.empathy_dialogue_cue
        else:
            reply_text = f"سمعت الريكورد يا غالي.. تمام فهمتك، {analysis.transcript}"

        # 3. Always reply via authentic Voice Note when user talks in voice
        should_reply_voice = True

        if should_reply_voice:
            voice_path, waveform = await voice_generator.generate_voice_note(
                text_content=reply_text,
                emotional_tone=analysis.detected_emotion,
                format_ext="ogg",
            )
            await mtproto_manager.send_voice_note(
                chat_id=chat_id,
                file_path=voice_path,
                waveform=waveform,
                reply_to_msg_id=message_id,
            )
        else:
            bursts = human_typer.prepare_message_bursts(reply_text)
            await mtproto_manager.dispatch_burst_messages(
                chat_id=chat_id, bursts=bursts, reply_to_msg_id=message_id
            )

    @classmethod
    async def handle_voice_request(
        cls,
        message_id: int,
        chat_id: int,
        sender_id: int,
        sender_name: str,
        message_text: str,
    ) -> bool:
        """
        Detects if user asks for a voice note / record, synthesizes real speech,
        and dispatches native Telegram voice note.
        """
        voice_triggers = [
            "ابعت فويس", "ابعتلي فويس", "سمعني صوتك", "قولي ريكورد",
            "ابعت ريكورد", "اتكلم فويس", "سجل فويس", "عايز اسمع صوتك",
            "عايزة اسمع صوتك", "فويس نوت", "سجل ريكورد", "قول فويس",
            "ابعت صوت", "صوتك", "ريكورد"
        ]
        text_clean = message_text.lower().strip()
        is_request = any(trig in text_clean for trig in voice_triggers)
        if not is_request:
            return False

        logger.info(f"Detected explicit voice note request from [{sender_name}]: '{message_text}'")

        # 1. Run cognitive orchestrator to generate what Omar would say naturally
        resp = await cognitive_orchestrator.process_incoming_event(
            telegram_message_id=message_id,
            chat_id=chat_id,
            sender_id=sender_id,
            sender_name=sender_name,
            message_text=message_text,
            media_type="text",
            chat_type="private",
            chat_title=f"خاص مع {sender_name}",
        )

        reply_content = resp.raw_response_text
        if not reply_content or len(reply_content.strip()) < 5:
            reply_content = f"يا مرحب بيك يا {sender_name}، منور والله والدنيا رايقة معايا الحمد لله."

        # 2. Synthesize authentic voice note via Edge-TTS
        mood = endocrine_engine.evaluate_psychological_mood()
        voice_path, waveform = await voice_generator.generate_voice_note(
            text_content=reply_content,
            emotional_tone=mood.get("temperament", "WARM"),
            format_ext="ogg",
            dialect_code=getattr(resp, "detected_dialect", "egyptian"),
        )

        # 3. Dispatch native voice note
        await mtproto_manager.send_voice_note(
            chat_id=chat_id,
            file_path=voice_path,
            waveform=waveform,
            reply_to_msg_id=message_id,
        )
        return True

    @classmethod
    async def handle_photo_request(
        cls,
        message_id: int,
        chat_id: int,
        sender_id: int,
        sender_name: str,
        message_text: str,
    ) -> bool:
        """
        Checks if user is requesting a selfie and evaluates eligibility.
        Returns True if request was handled.
        """
        photo_request_triggers = [
            "ابعت صورتك", "ابعتلي صورتك", "عايز أشوفك", "عايزة أشوفك",
            "إنت فين دلوقتي", "صور نفسك", "ابعت سيلفي", "وريني شكلك",
            "صورتك", "سيلفي"
        ]
        is_request = any(trig in message_text.lower() for trig in photo_request_triggers)
        if not is_request:
            return False

        logger.info(f"Detected photo request from [{sender_name}]: '{message_text}'")

        async with db_manager.session() as session:
            user_repo = UserRepository(session)
            user_record = await user_repo.get_or_create(telegram_id=sender_id, first_name=sender_name)

        user_vector = UserAffinityVector(
            user_id=sender_id,
            affinity_score=user_record.affinity_score,
            trust_score=user_record.trust_score,
            romantic_attachment=user_record.romantic_attachment,
            respect_dominance=user_record.respect_dominance,
            tier=RelationshipTier(user_record.relationship_tier),
        )

        can_send, verbal_response = life_sim.evaluate_photo_request(user_vector, sender_name)

        if not can_send:
            # Dignity rejection
            bursts = human_typer.prepare_message_bursts(verbal_response)
            await mtproto_manager.dispatch_burst_messages(
                chat_id=chat_id, bursts=bursts, reply_to_msg_id=message_id
            )
            return True

        # Approved: Send verbal lead-in first
        lead_bursts = human_typer.prepare_message_bursts(verbal_response)
        await mtproto_manager.dispatch_burst_messages(chat_id=chat_id, bursts=lead_bursts)

        # Generate face-locked photo
        photo_file = await face_lock_pipeline.generate_photo(requester_name=sender_name)
        location = life_sim.get_current_location_state()
        caption = f"سيلفي سريع من {location.location_name_ar} 😉"

        await mtproto_manager.send_photo(
            chat_id=chat_id,
            photo_path=photo_file,
            caption=caption,
            reply_to_msg_id=message_id,
        )
        return True


media_handler = MediaEventHandler()
