"""
Bot sozlamalari.
Barcha maxfiy ma'lumotlar .env faylidan o'qiladi.
"""
from dataclasses import dataclass, field
from typing import List

from environs import Env


@dataclass
class Channel:
    """Majburiy a'zolik uchun kanal."""
    username: str      # @kanal_username yoki -100... ID
    title: str         # Ko'rsatiladigan nom
    url: str           # Havola (https://t.me/...)


@dataclass
class Config:
    bot_token: str
    admin_ids: List[int]
    operator_ids: List[int]          # reklama yubora oladigan operatorlar
    admin_group_id: int              # murojaatlar tushadigan guruh
    channels: List[Channel] = field(default_factory=list)
    db_url: str = "sqlite+aiosqlite:///bot.db"
    broadcast_delay: float = 1.0     # reklama: har yuborish orasidagi soniya
    throttle_rate: float = 1.0       # spam himoya: 1 foydalanuvchi / soniya

    def is_admin(self, user_id: int) -> bool:
        return user_id in self.admin_ids

    def can_broadcast(self, user_id: int) -> bool:
        return user_id in self.admin_ids or user_id in self.operator_ids


def load_config() -> Config:
    env = Env()
    env.read_env()

    channels: List[Channel] = []
    raw = env.str("CHANNELS", "").strip()
    # Format: @username|Nomi|https://t.me/username ;; @kanal2|Nomi2|https://t.me/kanal2
    if raw:
        for part in raw.split(";;"):
            part = part.strip()
            if not part:
                continue
            username, title, url = [p.strip() for p in part.split("|")]
            channels.append(Channel(username=username, title=title, url=url))

    return Config(
        bot_token=env.str("BOT_TOKEN"),
        admin_ids=[int(x) for x in env.list("ADMIN_IDS", [])],
        operator_ids=[int(x) for x in env.list("OPERATOR_IDS", [])],
        admin_group_id=env.int("ADMIN_GROUP_ID"),
        channels=channels,
        db_url=env.str("DB_URL", "sqlite+aiosqlite:///bot.db"),
        broadcast_delay=env.float("BROADCAST_DELAY", 1.0),
        throttle_rate=env.float("THROTTLE_RATE", 1.0),
    )
