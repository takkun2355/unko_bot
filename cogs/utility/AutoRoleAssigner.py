import logging

logger = logging.getLogger(__name__)
import discord
from discord.ext import commands


class AutoRoleAssigner(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # 自動で付与したいユーザーIDとロール名
        self.target_users = {
            885841692832464907: "メンバー",
            968755981326639104: "管理者",
            1295371078704824351: "メンバー",
        }

    @commands.Cog.listener()
    async def on_ready(self):
        """Bot起動時に対象ユーザーへロールを自動付与"""
        logger.info(" AutoRoleAssigner 起動チェック開始")
        for guild in self.bot.guilds:
            for user_id, role_name in self.target_users.items():
                member = guild.get_member(user_id)
                if not member:
                    continue

                role = discord.utils.get(guild.roles, name=role_name)
                if not role:
                    logger.info(f" ロール '{role_name}' が {guild.name} に見つかりません。")
                    continue

                if role not in member.roles:
                    try:
                        await member.add_roles(role)
                        logger.info(f" {member.name} にロール '{role_name}' を付与しました。")
                    except discord.Forbidden:
                        logger.info(f" 権限不足で {member.name} にロールを付与できません。")
                    except Exception as e:
                        logger.info(f" エラー: {e}")
                else:
                    logger.info(f" {member.name} はすでに '{role_name}' を持っています。")

    @commands.Cog.listener()
    async def on_member_join(self, member):
        """サーバーに新しく入った時もチェック"""
        role_name = self.target_users.get(member.id)
        if role_name:
            role = discord.utils.get(member.guild.roles, name=role_name)
            if role and role not in member.roles:
                await member.add_roles(role)
                logger.info(f" {member.name} が参加時に '{role_name}' を付与しました。")


async def setup(bot):
    await bot.add_cog(AutoRoleAssigner(bot))
