"""
SQLAlchemy Relational Database Schema Models for Project Aether-Human.
Includes Users, Chats, Messages, Neuro-Hormone Records, Behavioral Constraints, and Secrets.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional, List
from sqlalchemy import (
    Column,
    Integer,
    BigInteger,
    String,
    Float,
    Boolean,
    DateTime,
    Text,
    ForeignKey,
    JSON,
    Index,
)
from sqlalchemy.orm import relationship

from aether_human_core.database.postgres.connection import Base


class UserModel(Base):
    """
    Unified User Profile tracking cross-context identity, demographics,
    affinity coordinates, and social hierarchy status.
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    telegram_id = Column(BigInteger, unique=True, nullable=False, index=True)
    username = Column(String(128), nullable=True, index=True)
    first_name = Column(String(128), nullable=False, default="")
    last_name = Column(String(128), nullable=True, default="")
    phone_number = Column(String(32), nullable=True)
    gender = Column(String(16), nullable=False, default="unknown")  # male, female, unknown

    # Multi-dimensional Affinity Coordinates
    affinity_score = Column(Float, nullable=False, default=0.0)      # [-100.0, 100.0]
    trust_score = Column(Float, nullable=False, default=20.0)         # [0.0, 100.0]
    romantic_attachment = Column(Float, nullable=False, default=0.0)  # [0.0, 100.0]
    respect_dominance = Column(Float, nullable=False, default=0.0)    # [-50.0, 50.0]

    relationship_tier = Column(String(32), nullable=False, default="STRANGER")
    role = Column(String(32), nullable=False, default="MEMBER")  # SUPER_ADMIN, ADMIN, MODERATOR, VIP, MEMBER
    role_assigned_by = Column(BigInteger, nullable=True)
    custom_title = Column(String(64), nullable=True)
    is_blocked = Column(Boolean, nullable=False, default=False)
    is_vip = Column(Boolean, nullable=False, default=False)
    notes = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    last_interaction_at = Column(DateTime, nullable=True)

    # Relationships
    messages = relationship("MessageRecordModel", back_populates="sender", cascade="all, delete-orphan")
    behavioral_rules = relationship("BehavioralRuleModel", back_populates="commander", foreign_keys="BehavioralRuleModel.user_id")
    owned_secrets = relationship("SecretItemModel", back_populates="owner", foreign_keys="SecretItemModel.owner_user_id")

    __table_args__ = (
        Index("idx_users_affinity", "affinity_score"),
        Index("idx_users_tier", "relationship_tier"),
    )


class ChatModel(Base):
    """
    Chat container tracking private DMs, supergroups, and channels.
    """
    __tablename__ = "chats"

    id = Column(Integer, primary_key=True, autoincrement=True)
    chat_id = Column(BigInteger, unique=True, nullable=False, index=True)
    title = Column(String(256), nullable=True)
    chat_type = Column(String(32), nullable=False, default="private")  # private, group, supergroup
    is_active = Column(Boolean, nullable=False, default=True)
    participant_count = Column(Integer, nullable=True, default=0)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_message_at = Column(DateTime, nullable=True)

    messages = relationship("MessageRecordModel", back_populates="chat", cascade="all, delete-orphan")


class MessageRecordModel(Base):
    """
    Chronological ledger of cross-context chat messages and perceptual interpretations.
    """
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    telegram_message_id = Column(BigInteger, nullable=False, index=True)
    chat_id = Column(BigInteger, ForeignKey("chats.chat_id", ondelete="CASCADE"), nullable=False, index=True)
    sender_id = Column(BigInteger, ForeignKey("users.telegram_id", ondelete="CASCADE"), nullable=False, index=True)

    text = Column(Text, nullable=True)
    media_type = Column(String(32), nullable=False, default="text")  # text, voice, photo, video, sticker
    sentiment = Column(String(32), nullable=True)
    perceived_emotion = Column(String(64), nullable=True)
    is_from_bot = Column(Boolean, nullable=False, default=False)
    reply_to_msg_id = Column(BigInteger, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    chat = relationship("ChatModel", back_populates="messages")
    sender = relationship("UserModel", back_populates="messages")


class NeuroHormoneHistoryModel(Base):
    """
    Time-series audit trail of biological endocrine hormones and psychological shocks.
    """
    __tablename__ = "neuro_hormone_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    dopamine = Column(Float, nullable=False)
    oxytocin = Column(Float, nullable=False)
    cortisol = Column(Float, nullable=False)
    serotonin = Column(Float, nullable=False)
    energy = Column(Float, nullable=False, default=1.0)
    trigger_event = Column(String(128), nullable=False)
    trigger_user_id = Column(BigInteger, nullable=True)
    notes = Column(Text, nullable=True)


class BehavioralRuleModel(Base):
    """
    Compiled dynamic social directives enforced by high-affinity romantic/dominant commanders.
    Example: 'Do not talk to other girls', 'Ignore user X'.
    """
    __tablename__ = "behavioral_rules"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.telegram_id", ondelete="CASCADE"), nullable=False, index=True)
    rule_type = Column(String(64), nullable=False)  # RESTRICT_FEMALE_TALK, COLD_MODE, IGNORE_USER, LOYALTY_REPORT
    target_user_id = Column(BigInteger, nullable=True)
    target_gender = Column(String(16), nullable=True)  # female, male, any
    target_keywords = Column(JSON, nullable=True)
    instruction_text = Column(Text, nullable=False)
    is_active = Column(Boolean, nullable=False, default=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=True)

    commander = relationship("UserModel", back_populates="behavioral_rules", foreign_keys=[user_id])


class SecretItemModel(Base):
    """
    Confidential disclosures, gossip elements, and betrayal records.
    """
    __tablename__ = "secrets"

    id = Column(Integer, primary_key=True, autoincrement=True)
    owner_user_id = Column(BigInteger, ForeignKey("users.telegram_id", ondelete="CASCADE"), nullable=False, index=True)
    secret_content = Column(Text, nullable=False)
    confidentiality_score = Column(Integer, nullable=False, default=5)  # [1..10]
    leaked_to_user_ids = Column(JSON, nullable=False, default=list)      # List[int]
    is_betrayed = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    owner = relationship("UserModel", back_populates="owned_secrets", foreign_keys=[owner_user_id])


class AuditLogModel(Base):
    """
    System-wide operations and cognitive introspection events log.
    """
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    component = Column(String(64), nullable=False, index=True)
    action = Column(String(64), nullable=False)
    details = Column(JSON, nullable=True)
