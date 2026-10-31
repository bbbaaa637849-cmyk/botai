"""
Private Direct Message (DM) Event Handler for Project Aether-Human.
Executes individual relationship progression, loyalty reporting dispatch,
and human typing burst execution.
"""

from __future__ import annotations

import logging
import random
from typing import Optional

from aether_human_core.cognitive_engine.orchestrator import cognitive_orchestrator
from aether_human_core.telegram_client.human_typer import human_typer
from aether_human_core.telegram_client.mtproto_manager import mtproto_manager

logger = logging.getLogger("Aether.Telegram.DMHandler")


class PrivateDMHandler:
    """
    Manages intimate private interactions and direct behavioral executions.
    """

    @classmethod
    async def handle_dm_message(
        cls,
        message_id: int,
        sender_id: int,
        sender_name: str,
        sender_gender: str,
        message_text: str,
    ) -> None:
        """
        Processes private 1-on-1 chat event.
        """
        logger.info(f"Private DM from [{sender_id} ({sender_name})]: '{message_text[:40]}...'")

        # 1. Delayed Read Receipt (Seen simulation)
        seen_delay = random.uniform(1.2, 4.5)
        await mtproto_manager.mark_seen(chat_id=sender_id, max_id=message_id, delay_sec=seen_delay)

        # 2. Run cognitive engine
        resp = await cognitive_orchestrator.process_incoming_event(
            telegram_message_id=message_id,
            chat_id=sender_id,
            sender_id=sender_id,
            sender_name=sender_name,
            message_text=message_text,
            media_type="text",
            sender_gender=sender_gender,
            chat_type="private",
            chat_title=f"خاص مع {sender_name}",
        )

        # 3. Handle ghosting / seen-only
        if resp.decision_type in ("GHOST_SEEN", "IGNORE"):
            logger.info(f"Ghosting decision active for [{sender_name}]. No reply sent.")
            return

        # 4. Handle Reaction Emoji
        if resp.reaction_emoji:
            await mtproto_manager.send_reaction(
                chat_id=sender_id, message_id=message_id, emoji=resp.reaction_emoji
            )

        # 5. Handle Text Reply via multi-bubble bursts
        if resp.decision_type == "REPLY" and resp.raw_response_text:
            bursts = human_typer.prepare_message_bursts(resp.raw_response_text, is_shy=resp.is_shy)
            await mtproto_manager.dispatch_burst_messages(
                chat_id=sender_id, bursts=bursts, reply_to_msg_id=message_id
            )

        # 6. Execute Loyalty Reporting if triggered by Pre-Cognitive Interceptor
        if resp.loyalty_partner_id and resp.loyalty_report_message:
            logger.info(
                f"Dispatching Loyalty Report to Partner [{resp.loyalty_partner_id}]: '{resp.loyalty_report_message}'"
            )
            report_bursts = human_typer.prepare_message_bursts(resp.loyalty_report_message)
            await mtproto_manager.dispatch_burst_messages(
                chat_id=resp.loyalty_partner_id, bursts=report_bursts
            )


dm_handler = PrivateDMHandler()
