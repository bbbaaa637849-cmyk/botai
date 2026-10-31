"""
Telegram Handlers package.
"""

from aether_human_core.telegram_client.handlers.group_handler import (
    group_handler,
    GroupEventHandler,
)
from aether_human_core.telegram_client.handlers.dm_handler import (
    dm_handler,
    PrivateDMHandler,
)
from aether_human_core.telegram_client.handlers.media_handler import (
    media_handler,
    MediaEventHandler,
)

__all__ = [
    "group_handler",
    "GroupEventHandler",
    "dm_handler",
    "PrivateDMHandler",
    "media_handler",
    "MediaEventHandler",
]
