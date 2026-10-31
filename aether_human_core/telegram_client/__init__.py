"""
Telegram MTProto Client & Human UX Layer.
"""

from aether_human_core.telegram_client.mtproto_manager import mtproto_manager, TelegramMTProtoManager
from aether_human_core.telegram_client.human_typer import human_typer, HumanTyperSimulator, BurstMessage

__all__ = [
    "mtproto_manager",
    "TelegramMTProtoManager",
    "human_typer",
    "HumanTyperSimulator",
    "BurstMessage",
]
