"""
Dynamic Role-Based Access Control (RBAC), Admin Hierarchy, and Rule Management Engine.
Manages Super Admins (immutable root authority via env/db), runtime-appointed Admins,
Moderators, VIPs, and dynamic behavioral constraints/prohibitions.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy import select, update, delete

from aether_human_core.config.settings import settings
from aether_human_core.database.postgres.connection import db_manager
from aether_human_core.database.postgres.models import UserModel, BehavioralRuleModel

logger = logging.getLogger("Aether.Psychology.AdminManager")


class RoleLevel:
    SUPER_ADMIN = 100
    ADMIN = 80
    MODERATOR = 50
    VIP = 30
    MEMBER = 10

    ROLE_NAMES = {
        "SUPER_ADMIN": "👑 مالك النظام (Super Admin)",
        "ADMIN": "⭐ مسؤول معتمد (Admin)",
        "MODERATOR": "🛡️ مشرف (Moderator)",
        "VIP": "💎 عضو مميز (VIP)",
        "MEMBER": "👤 عضو عادي (Member)",
    }


class AdminManagerService:
    """
    Coordinates multi-tier authorization and runtime dynamic rules/prohibitions.
    """

    def is_super_admin(self, user_id: int) -> bool:
        """
        Validates if the user is a hardcoded/configured Root Super Admin.
        """
        return user_id in settings.super_admin_ids_list

    async def is_admin(self, user_id: int) -> bool:
        """
        Returns True if the user is a Super Admin or has an appointed ADMIN role.
        """
        if self.is_super_admin(user_id):
            return True
        role = await self.get_user_role(user_id)
        return role in ("SUPER_ADMIN", "ADMIN")

    async def is_moderator(self, user_id: int) -> bool:
        """
        Returns True if the user has staff privileges (Super Admin, Admin, or Moderator).
        """
        if self.is_super_admin(user_id):
            return True
        role = await self.get_user_role(user_id)
        return role in ("SUPER_ADMIN", "ADMIN", "MODERATOR")

    async def get_user_role(self, user_id: int) -> str:
        """
        Retrieves the effective role string of a user from DB or SuperAdmin configuration.
        """
        if self.is_super_admin(user_id):
            return "SUPER_ADMIN"

        async with db_manager.session() as session:
            stmt = select(UserModel.role).where(UserModel.telegram_id == user_id)
            res = (await session.execute(stmt)).scalar()
            return res or "MEMBER"

    async def can_manage_admins(self, operator_id: int) -> bool:
        """
        Only Root Super Admins can appoint or dismiss other Admins.
        """
        return self.is_super_admin(operator_id)

    async def can_manage_rules(self, operator_id: int) -> bool:
        """
        Super Admins and appointed Admins can add or delete behavioral rules and prohibitions.
        """
        if self.is_super_admin(operator_id):
            return True
        role = await self.get_user_role(operator_id)
        return role in ("SUPER_ADMIN", "ADMIN")

    async def promote_user(
        self,
        operator_id: int,
        target_id: Optional[int] = None,
        role: str = "ADMIN",
        custom_title: Optional[str] = None,
        assigned_by: Optional[int] = None,
    ) -> Tuple[bool, str]:
        """
        Promotes a user to a specified role (ADMIN, MODERATOR, VIP).
        Supports both (operator_id, target_id, role) and (target_id, role, assigned_by=...) signatures.
        """
        if assigned_by is not None:
            op_id = assigned_by
            tgt_id = operator_id
            role_val = target_id if isinstance(target_id, str) else role
        else:
            op_id = operator_id
            tgt_id = target_id if target_id is not None else 0
            role_val = role

        if not await self.can_manage_admins(op_id):
            return False, "⚠️ عذراً يا غالي، صلاحية تعيين وإدارة الرتب محصورة فقط لمالك النظام الأساسي (Super Admin)."

        role_clean = role_val.upper().strip()
        if role_clean not in ("ADMIN", "MODERATOR", "VIP", "MEMBER"):
            return False, f"⚠️ الرتبة '{role_val}' غير معروفة. الرتب المتاحة: ADMIN, MODERATOR, VIP, MEMBER."

        if tgt_id in settings.super_admin_ids_list and role_clean != "SUPER_ADMIN":
            return False, "⚠️ لا يمكن تعديل أو تخفيض رتبة مالك النظام الأساسي."

        async with db_manager.session() as session:
            stmt = select(UserModel).where(UserModel.telegram_id == tgt_id)
            user = (await session.execute(stmt)).scalars().first()
            if not user:
                # Create stub record
                user = UserModel(
                    telegram_id=tgt_id,
                    first_name=f"User_{tgt_id}",
                    role=role_clean,
                    role_assigned_by=op_id,
                    custom_title=custom_title,
                )
                session.add(user)
            else:
                user.role = role_clean
                user.role_assigned_by = op_id
                if custom_title:
                    user.custom_title = custom_title
                user.updated_at = datetime.utcnow()

            await session.commit()

        role_display = RoleLevel.ROLE_NAMES.get(role_clean, role_clean)
        logger.info(f"Operator [{op_id}] promoted user [{tgt_id}] to '{role_clean}'.")
        return True, f"✅ تم بنجاح تعيين المستخدم <code>{tgt_id}</code> برتبة: <b>{role_display}</b>."

    async def demote_user(
        self,
        operator_id: int,
        target_id: Optional[int] = None,
        assigned_by: Optional[int] = None,
    ) -> Tuple[bool, str]:
        """
        Revokes privileges and resets user role to MEMBER.
        Supports both (operator_id, target_id) and (target_id, assigned_by=...) signatures.
        """
        if assigned_by is not None:
            return await self.promote_user(operator_id=operator_id, role="MEMBER", assigned_by=assigned_by)
        return await self.promote_user(operator_id=operator_id, target_id=target_id, role="MEMBER")

    async def list_admins(self) -> List[Dict[str, Any]]:
        """
        Returns a list of all configured Super Admins and active appointed Admins.
        """
        admins: List[Dict[str, Any]] = []

        # 1. Super Admins
        for sa_id in settings.super_admin_ids_list:
            admins.append({
                "telegram_id": sa_id,
                "role": "SUPER_ADMIN",
                "role_name": RoleLevel.ROLE_NAMES["SUPER_ADMIN"],
                "first_name": "المالك الأساسي",
                "is_super": True,
            })

        # 2. Appointed Admins & Moderators from DB
        async with db_manager.session() as session:
            stmt = select(UserModel).where(UserModel.role.in_(["ADMIN", "MODERATOR", "VIP"]))
            results = (await session.execute(stmt)).scalars().all()
            for u in results:
                if u.telegram_id not in settings.super_admin_ids_list:
                    admins.append({
                        "telegram_id": u.telegram_id,
                        "role": u.role,
                        "role_name": RoleLevel.ROLE_NAMES.get(u.role, u.role),
                        "first_name": u.first_name,
                        "custom_title": u.custom_title,
                        "is_super": False,
                    })

        return admins

    async def add_dynamic_rule(
        self,
        operator_id: int,
        instruction_text: str,
        rule_type: str = "DIRECTIVE",
        target_gender: Optional[str] = None,
        target_user_id: Optional[int] = None,
    ) -> Tuple[bool, str]:
        """
        Adds a new behavioral rule or prohibition dynamically during chat.
        """
        if not await self.can_manage_rules(operator_id):
            return False, "⚠️ عذراً يا غالي، إضافة وتعديل الأوامر والممنوعات مقتصرة فقط على إدارة البوت المعتمدة."

        async with db_manager.session() as session:
            rule = BehavioralRuleModel(
                user_id=operator_id,
                rule_type=rule_type,
                instruction_text=instruction_text.strip(),
                target_gender=target_gender,
                target_user_id=target_user_id,
                is_active=True,
                created_at=datetime.utcnow(),
            )
            session.add(rule)
            await session.commit()
            rule_id = rule.id

        logger.info(f"Operator [{operator_id}] created dynamic rule #{rule_id}: '{instruction_text}'")
        return True, f"✅ تم تفعيل القاعدة / الأمر بنجاح (رقم: <code>#{rule_id}</code>):\n<blockquote>{instruction_text}</blockquote>"

    async def delete_dynamic_rule(self, operator_id: int, rule_id: int) -> Tuple[bool, str]:
        """
        Deactivates or deletes an existing behavioral rule.
        """
        if not await self.can_manage_rules(operator_id):
            return False, "⚠️ عذراً، لا تملك صلاحية حذف وتعديل القواعد."

        async with db_manager.session() as session:
            stmt = select(BehavioralRuleModel).where(BehavioralRuleModel.id == rule_id)
            rule = (await session.execute(stmt)).scalars().first()
            if not rule:
                return False, f"⚠️ لم يتم العثور على قاعدة برقم <code>#{rule_id}</code>."

            rule.is_active = False
            await session.commit()

        logger.info(f"Operator [{operator_id}] deactivated rule #{rule_id}.")
        return True, f"✅ تم إلغاء وتجميد القاعدة <code>#{rule_id}</code> بنجاح."

    async def list_active_rules(self) -> List[Dict[str, Any]]:
        """
        Lists all currently enforced behavioral rules and prohibitions.
        """
        async with db_manager.session() as session:
            stmt = select(BehavioralRuleModel).where(BehavioralRuleModel.is_active == True)
            rules = (await session.execute(stmt)).scalars().all()
            return [
                {
                    "id": r.id,
                    "rule_type": r.rule_type,
                    "instruction_text": r.instruction_text,
                    "target_gender": r.target_gender,
                    "target_user_id": r.target_user_id,
                    "created_at": r.created_at.strftime("%Y-%m-%d %H:%M") if r.created_at else "",
                }
                for r in rules
            ]


# Global instance
admin_manager = AdminManagerService()
