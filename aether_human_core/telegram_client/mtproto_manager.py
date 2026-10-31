"""
Telegram MTProto Client and Bot API Manager for Project Aether-Human.
Handles real-time message reception, read receipts, human typing presence,
reactions, voice notes, photos, and burst dispatching.
Supports both Telegram Bot API Polling (via BOT_TOKEN) and MTProto Userbot Client (Telethon).
"""

from __future__ import annotations

import logging
import asyncio
import os
import random
from typing import Optional, List, Any, Dict
import httpx
from telethon import TelegramClient, events
from telethon.tl.types import (
    DocumentAttributeAudio,
    ReactionEmoji,
)

from aether_human_core.config.settings import settings
from aether_human_core.telegram_client.human_typer import BurstMessage, human_typer

logger = logging.getLogger("Aether.Telegram.MTProto")


class TelegramMTProtoManager:
    """
    Manages Telegram communication with authentic human UX timings.
    Supports official Bot API long-polling and Telethon MTProto userbot.
    """
    def __init__(self):
        self.api_id = settings.telegram_api_id
        self.api_hash = settings.telegram_api_hash
        self.bot_token = settings.telegram_bot_token
        self.session_name = settings.telegram_session_name
        self.client: Optional[TelegramClient] = None
        self._is_running: bool = False
        self._mock_mode: bool = False
        self._bot_polling_task: Optional[asyncio.Task] = None
        self._last_update_id: int = 0
        self.bot_api_url = f"https://api.telegram.org/bot{self.bot_token}" if self.bot_token else ""
        self._http_client: Optional[httpx.AsyncClient] = None

    async def _get_http(self) -> httpx.AsyncClient:
        if self._http_client is None or self._http_client.is_closed:
            self._http_client = httpx.AsyncClient(timeout=40.0)
        return self._http_client

    async def initialize(self) -> None:
        """
        Initializes Telegram connectivity:
        1. If TELEGRAM_BOT_TOKEN is provided: launches real-time Telegram Bot API long-polling.
        2. If MTProto Userbot is configured & authorized: hooks Telethon event handlers.
        3. If neither: runs in Simulation / Sandbox mode.
        """
        if self.bot_token:
            # Active Telegram Bot mode via official Telegram Bot API
            try:
                http = await self._get_http()
                res = await http.get(f"{self.bot_api_url}/getMe")
                if res.status_code == 200 and res.json().get("ok"):
                    bot_info = res.json()["result"]
                    self.bot_id = bot_info.get("id")
                    self.bot_username = bot_info.get("username", "omarggforbot").lower()
                    logger.info(
                        f"🚀 Telegram Bot authenticated successfully! "
                        f"Username: @{self.bot_username} | Name: '{bot_info.get('first_name')}'"
                    )
                    self._is_running = True
                    self._mock_mode = False
                    # Start polling background daemon
                    self._bot_polling_task = asyncio.create_task(self._start_bot_polling())
                    return
                else:
                    logger.warning(f"Telegram Bot Token check returned {res.status_code}: {res.text}")
            except Exception as exc:
                logger.error(f"Failed to verify Telegram Bot Token: {exc}")

        # Fallback to Telethon MTProto Userbot
        if self.api_id and self.api_hash and self.api_id != 0:
            try:
                self.client = TelegramClient(self.session_name, self.api_id, self.api_hash)
                await self.client.connect()
                if await self.client.is_user_authorized():
                    logger.info("Telethon MTProto client connected and authorized as Userbot.")
                    self._is_running = True
                    self._mock_mode = False
                    self._register_telethon_handlers()
                    return
                elif self.bot_token:
                    await self.client.start(bot_token=self.bot_token)
                    logger.info("Telethon connected using Bot Token fallback.")
                    self._is_running = True
                    self._mock_mode = False
                    self._register_telethon_handlers()
                    return
                else:
                    logger.warning("Telegram Userbot not authorized. Authorization required via phone.")
            except Exception as exc:
                logger.error(f"Failed to start MTProto client: {exc}")

        logger.warning("Operating Telegram Manager in Simulation/Sandbox mode.")
        self._mock_mode = True
        self._is_running = True

    async def _start_bot_polling(self) -> None:
        """
        Long-polling loop receiving incoming Telegram messages and routing to cognitive handlers.
        """
        logger.info("Listening for real-time Telegram messages (Long-Polling Active)...")
        http = await self._get_http()

        # Advance past historical unhandled updates to start fresh or process recent
        try:
            init_res = await http.get(f"{self.bot_api_url}/getUpdates", params={"limit": 100})
            if init_res.status_code == 200:
                results = init_res.json().get("result", [])
                if results:
                    # Catch up with unread messages
                    logger.info(f"Processing {len(results)} pending incoming message(s) from Telegram...")
                    for u in results:
                        self._last_update_id = u["update_id"]
                        await self._process_telegram_update(u)
        except Exception as exc:
            logger.warning(f"Error fetching initial update batch: {exc}")

        while self._is_running:
            try:
                params = {"timeout": 25, "offset": self._last_update_id + 1}
                res = await http.get(f"{self.bot_api_url}/getUpdates", params=params, timeout=35.0)
                if res.status_code == 200:
                    data = res.json()
                    for update in data.get("result", []):
                        self._last_update_id = update["update_id"]
                        await self._process_telegram_update(update)
                elif res.status_code == 409:
                    logger.warning("Telegram Bot conflict: another instance might be polling. Waiting 5s...")
                    await asyncio.sleep(5.0)
            except asyncio.CancelledError:
                break
            except Exception as exc:
                logger.debug(f"Polling network exception: {exc}")
                await asyncio.sleep(2.0)

    async def _process_telegram_update(self, update: Dict[str, Any]) -> None:
        """
        Parses incoming Telegram event and delegates to appropriate domain handler.
        """
        msg = update.get("message")
        if not msg:
            return

        chat = msg.get("chat", {})
        chat_id = chat.get("id")
        chat_type = chat.get("type", "private")
        message_id = msg.get("message_id")
        sender = msg.get("from", {})
        sender_id = sender.get("id", chat_id)
        sender_name = sender.get("first_name", "صديق")
        message_text = msg.get("text", "") or msg.get("caption", "")

        # Guess gender from first name heuristics or default unknown
        name_lower = sender_name.lower().strip()
        common_female = ("سارة", "نورا", "مريم", "آية", "فاطمة", "حبيبتي", "ياسمين", "سلمى", "هدى", "رنا", "دينا", "منى", "مي", "نور")
        common_male = ("محمد", "أحمد", "مصطفى", "يوسف", "علي", "محمود", "عمر", "كريم", "حسن", "حسين", "خالد", "طارق", "هيثم", "سيف", "إسلام", "إبراهيم", "عمرو", "زياد", "فارس", "معاذ", "عبد", "mustafa", "mohamed", "ahmed", "youssef", "marcel", "v7x", "joo")
        if any(f in name_lower for f in common_female):
            sender_gender = "female"
        elif any(m in name_lower for m in common_male):
            sender_gender = "male"
        else:
            sender_gender = "unknown"

        logger.info(f"📩 [Telegram Message] From [{sender_name} ({sender_id})]: '{message_text[:40]}...'")

        # Import handlers locally to prevent circular imports
        from aether_human_core.telegram_client.handlers.dm_handler import dm_handler
        from aether_human_core.telegram_client.handlers.group_handler import group_handler
        from aether_human_core.telegram_client.handlers.media_handler import media_handler

        # 1. Voice note detection
        if msg.get("voice") or msg.get("audio"):
            file_id = (msg.get("voice") or msg.get("audio"))["file_id"]
            http = await self._get_http()
            file_info = await http.get(f"{self.bot_api_url}/getFile", params={"file_id": file_id})
            if file_info.status_code == 200:
                file_path_tg = file_info.json()["result"]["file_path"]
                download_url = f"https://api.telegram.org/file/bot{self.bot_token}/{file_path_tg}"
                dl_res = await http.get(download_url)
                if dl_res.status_code == 200:
                    local_voice = os.path.join(os.getcwd(), "artifacts", "voice_notes", f"incoming_{file_id}.ogg")
                    with open(local_voice, "wb") as f:
                        f.write(dl_res.content)
                    await media_handler.handle_incoming_voice(
                        message_id=message_id,
                        chat_id=chat_id,
                        sender_id=sender_id,
                        sender_name=sender_name,
                        voice_file_path=local_voice,
                    )
                    return

        # 2. Photo request detection
        handled_photo = await media_handler.handle_photo_request(
            message_id=message_id,
            chat_id=chat_id,
            sender_id=sender_id,
            sender_name=sender_name,
            message_text=message_text,
        )
        if handled_photo:
            return

        # 3. Voice note request detection
        handled_voice = await media_handler.handle_voice_request(
            message_id=message_id,
            chat_id=chat_id,
            sender_id=sender_id,
            sender_name=sender_name,
            message_text=message_text,
        )
        if handled_voice:
            return

        # 3. Private DM handling
        if chat_type == "private":
            await dm_handler.handle_dm_message(
                message_id=message_id,
                sender_id=sender_id,
                sender_name=sender_name,
                sender_gender=sender_gender,
                message_text=message_text,
            )

        # 4. Group handling
        elif chat_type in ("group", "supergroup"):
            chat_title = chat.get("title", "جروب عام")
            reply_to = msg.get("reply_to_message", {})
            reply_from = reply_to.get("from", {})
            is_reply = False
            if reply_from:
                is_reply = bool(reply_from.get("id") == getattr(self, "bot_id", 0) or reply_from.get("is_bot"))

            bot_tag = f"@{getattr(self, 'bot_username', 'omarggforbot')}".lower()
            is_tagged = bot_tag in message_text.lower()

            await group_handler.handle_group_message(
                message_id=message_id,
                chat_id=chat_id,
                sender_id=sender_id,
                sender_name=sender_name,
                sender_gender=sender_gender,
                message_text=message_text,
                chat_title=chat_title,
                is_reply_to_bot=is_reply,
                is_bot_mentioned=is_tagged,
            )

    def _register_telethon_handlers(self) -> None:
        """
        Registers event handlers on active Telethon client.
        """
        if not self.client:
            return

        @self.client.on(events.NewMessage(incoming=True))
        async def on_new_message(event):
            sender = await event.get_sender()
            sender_id = event.sender_id
            sender_name = getattr(sender, "first_name", "صديق") or "صديق"
            sender_gender = "female" if sender_name in ("سارة", "نورا", "حبيبتي") else "unknown"
            msg_text = event.raw_text

            from aether_human_core.telegram_client.handlers.dm_handler import dm_handler
            from aether_human_core.telegram_client.handlers.group_handler import group_handler
            from aether_human_core.telegram_client.handlers.media_handler import media_handler

            if event.is_private:
                # Check photo request
                is_photo_req = await media_handler.handle_photo_request(
                    message_id=event.id,
                    chat_id=sender_id,
                    sender_id=sender_id,
                    sender_name=sender_name,
                    message_text=msg_text,
                )
                if is_photo_req:
                    return

                # Check voice note request
                is_voice_req = await media_handler.handle_voice_request(
                    message_id=event.id,
                    chat_id=sender_id,
                    sender_id=sender_id,
                    sender_name=sender_name,
                    message_text=msg_text,
                )
                if is_voice_req:
                    return

                await dm_handler.handle_dm_message(
                    message_id=event.id,
                    sender_id=sender_id,
                    sender_name=sender_name,
                    sender_gender=sender_gender,
                    message_text=msg_text,
                )
            elif event.is_group:
                chat = await event.get_chat()
                title = getattr(chat, "title", "جروب عام")
                await group_handler.handle_group_message(
                    message_id=event.id,
                    chat_id=event.chat_id,
                    sender_id=sender_id,
                    sender_name=sender_name,
                    sender_gender=sender_gender,
                    message_text=msg_text,
                    chat_title=title,
                    is_reply_to_bot=event.is_reply,
                    is_bot_mentioned="عمر" in msg_text,
                )

    async def send_typing_indicator(self, chat_id: int, duration_sec: float) -> None:
        """
        Broadcasts human typing indicator.
        """
        if self._mock_mode:
            logger.debug(f"[Simulation] Typing in chat {chat_id} for {duration_sec}s...")
            await asyncio.sleep(min(duration_sec, 2.0))
            return

        if self.bot_token:
            try:
                http = await self._get_http()
                await http.post(
                    f"{self.bot_api_url}/sendChatAction",
                    json={"chat_id": chat_id, "action": "typing"},
                )
                await asyncio.sleep(min(duration_sec, 4.0))
            except Exception as exc:
                logger.debug(f"Typing action exception: {exc}")
        elif self.client:
            try:
                async with self.client.action(chat_id, "typing"):
                    await asyncio.sleep(min(duration_sec, 4.0))
            except Exception as exc:
                logger.debug(f"Telethon typing action exception: {exc}")

    async def mark_seen(self, chat_id: int, max_id: int, delay_sec: float = 2.0) -> None:
        """
        Simulates delayed read receipt (Seen).
        """
        await asyncio.sleep(delay_sec)
        logger.debug(f"Simulated read receipt in chat [{chat_id}] (Msg ID: {max_id}).")

    async def send_reaction(self, chat_id: int, message_id: int, emoji: str) -> None:
        """
        Attaches emoji reaction to a message.
        """
        if self._mock_mode:
            logger.info(f"[Simulation] Reacted with '{emoji}' to msg {message_id} in chat {chat_id}.")
            return

        if self.bot_token:
            try:
                http = await self._get_http()
                await http.post(
                    f"{self.bot_api_url}/setMessageReaction",
                    json={
                        "chat_id": chat_id,
                        "message_id": message_id,
                        "reaction": [{"type": "emoji", "emoji": emoji}],
                    },
                )
                logger.info(f"Attached reaction '{emoji}' to message [{message_id}] in chat [{chat_id}].")
            except Exception as exc:
                logger.debug(f"Bot reaction not supported or chat too restricted: {exc}")
        elif self.client:
            try:
                from telethon.tl.functions.messages import SendReactionRequest
                await self.client(
                    SendReactionRequest(
                        peer=chat_id,
                        msg_id=message_id,
                        reaction=[ReactionEmoji(emoticon=emoji)],
                    )
                )
            except Exception as exc:
                logger.debug(f"Telethon reaction exception: {exc}")

    async def dispatch_burst_messages(
        self,
        chat_id: int,
        bursts: List[BurstMessage],
        reply_to_msg_id: Optional[int] = None,
    ) -> None:
        """
        Sends sequential message bubbles with realistic typing latencies and typo self-corrections.
        """
        http = await self._get_http() if self.bot_token else None

        for i, burst in enumerate(bursts):
            # 1. Simulate human typing latency
            await self.send_typing_indicator(chat_id, burst.typing_delay_sec)

            # 2. Transmit message bubble
            reply_target = reply_to_msg_id if i == 0 else None

            if self._mock_mode or (not self.bot_token and not self.client):
                logger.info(f"[Simulation Outgoing] Chat {chat_id} -> '{burst.text}'")
            elif self.bot_token and http:
                try:
                    payload: Dict[str, Any] = {"chat_id": chat_id, "text": burst.text}
                    if reply_target:
                        payload["reply_to_message_id"] = reply_target
                    res = await http.post(f"{self.bot_api_url}/sendMessage", json=payload)
                    if res.status_code == 200:
                        logger.info(f"📤 [Telegram Sent] Chat [{chat_id}]: '{burst.text}'")
                    else:
                        logger.warning(f"Failed to send message: {res.text}")
                except Exception as exc:
                    logger.error(f"Error dispatching burst message via Bot API: {exc}")
            elif self.client:
                try:
                    await self.client.send_message(chat_id, burst.text, reply_to=reply_target)
                except Exception as exc:
                    logger.error(f"Failed to send burst message via Telethon: {exc}")

            # 3. Handle typo self-correction
            if burst.has_typo and burst.correction_text:
                await asyncio.sleep(random.uniform(1.2, 2.5))
                if self.bot_token and http:
                    try:
                        await http.post(
                            f"{self.bot_api_url}/sendMessage",
                            json={"chat_id": chat_id, "text": burst.correction_text},
                        )
                        logger.info(f"📤 [Typo Self-Correction] Chat [{chat_id}]: '{burst.correction_text}'")
                    except Exception:
                        pass
                elif self.client:
                    try:
                        await self.client.send_message(chat_id, burst.correction_text)
                    except Exception:
                        pass

            # Micro-pause between bubbles
            if i < len(bursts) - 1:
                await asyncio.sleep(random.uniform(0.6, 1.8))

    async def send_voice_note(
        self,
        chat_id: int,
        file_path: str,
        waveform: bytes,
        reply_to_msg_id: Optional[int] = None,
    ) -> None:
        """
        Sends audio note as native Telegram voice note.
        """
        if self._mock_mode or (not self.bot_token and not self.client):
            logger.info(f"[Simulation Outgoing Voice] Chat {chat_id} -> File: {file_path}")
            return

        if self.bot_token:
            try:
                http = await self._get_http()
                await http.post(
                    f"{self.bot_api_url}/sendChatAction",
                    json={"chat_id": chat_id, "action": "record_voice"},
                )
                await asyncio.sleep(1.5)

                mime_type = "audio/ogg" if file_path.endswith(".ogg") else "audio/mpeg"
                with open(file_path, "rb") as f:
                    files = {"voice": (os.path.basename(file_path), f, mime_type)}
                    data: Dict[str, Any] = {"chat_id": str(chat_id)}
                    if reply_to_msg_id:
                        data["reply_to_message_id"] = str(reply_to_msg_id)
                    res = await http.post(f"{self.bot_api_url}/sendVoice", data=data, files=files)
                    if res.status_code == 200:
                        logger.info(f"🎙️ [Voice Sent] Dispatched native Egyptian voice note to chat [{chat_id}].")
                    else:
                        logger.warning(f"Failed to send voice note: {res.text}")
            except Exception as exc:
                logger.error(f"Error sending voice note via Bot API: {exc}")

        elif self.client:
            try:
                async with self.client.action(chat_id, "record-audio"):
                    await asyncio.sleep(2.0)
                await self.client.send_file(
                    chat_id,
                    file_path,
                    voice_note=True,
                    reply_to=reply_to_msg_id,
                    attributes=[DocumentAttributeAudio(voice=True, waveform=waveform, duration=5)],
                )
                logger.info(f"Dispatched native voice note via Telethon to [{chat_id}].")
            except Exception as exc:
                logger.error(f"Error sending voice note via Telethon: {exc}")

    async def send_photo(
        self,
        chat_id: int,
        photo_path: str,
        caption: Optional[str] = None,
        reply_to_msg_id: Optional[int] = None,
    ) -> None:
        """
        Sends selfie or photo with caption.
        """
        if self._mock_mode or (not self.bot_token and not self.client):
            logger.info(f"[Simulation Outgoing Photo] Chat {chat_id} -> {photo_path} (Caption: '{caption}')")
            return

        if self.bot_token:
            try:
                http = await self._get_http()
                await http.post(
                    f"{self.bot_api_url}/sendChatAction",
                    json={"chat_id": chat_id, "action": "upload_photo"},
                )
                await asyncio.sleep(1.2)

                with open(photo_path, "rb") as f:
                    files = {"photo": (os.path.basename(photo_path), f, "image/jpeg")}
                    data: Dict[str, Any] = {"chat_id": str(chat_id), "caption": caption or ""}
                    if reply_to_msg_id:
                        data["reply_to_message_id"] = str(reply_to_msg_id)
                    res = await http.post(f"{self.bot_api_url}/sendPhoto", data=data, files=files)
                    if res.status_code == 200:
                        logger.info(f"📸 [Photo Sent] Dispatched real photographic selfie to chat [{chat_id}].")
                    else:
                        logger.warning(f"Failed to send photo: {res.text}")
            except Exception as exc:
                logger.error(f"Error sending photo via Bot API: {exc}")

        elif self.client:
            try:
                async with self.client.action(chat_id, "photo"):
                    await asyncio.sleep(2.0)
                await self.client.send_file(
                    chat_id,
                    photo_path,
                    caption=caption or "",
                    reply_to=reply_to_msg_id,
                )
                logger.info(f"Dispatched photo via Telethon to chat [{chat_id}].")
            except Exception as exc:
                logger.error(f"Error sending photo via Telethon: {exc}")

    async def close(self) -> None:
        self._is_running = False
        if self._bot_polling_task and not self._bot_polling_task.done():
            self._bot_polling_task.cancel()
        if self._http_client and not self._http_client.is_closed:
            await self._http_client.aclose()
        if self.client and not self._mock_mode:
            await self.client.disconnect()
            logger.info("Telegram client disconnected.")


mtproto_manager = TelegramMTProtoManager()
