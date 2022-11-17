import asyncio
import discord

from discord.ext import commands

# Fill out all the necessary information

server_id: int = 0  # The server id to whitelist for ban battle
channel_id: int = 0  # The channel id to whitelist for banning
allowed_role: int = 0  # Role required to ban people. Leave it to 0 if none

moderator_role: int = 0


# People with this role in the bb server are treated as admins and are immune
# and can control the game. Leave it to 0 if there is none. Made to allow
# giveaway managers to host this event on their own.

# Do not touch any thing beyond this line if
# you don't know what you are doing


class BanBattle(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
		self.players = []
		self.game_in_progress = False

	@commands.group(name='bb')
	async def ban_battle(self, ctx):
		if ctx.invoked_subcommand:
			return

	@ban_battle.command(name='start')
	@commands.max_concurrency(1, commands.BucketType.guild)
	async def start(self, ctx, max_allowed_persons: int = 25):
		if moderator_role != 0 and moderator_role not in [role.id for role in ctx.author.roles]:
			return  # Silently fail as they don't have enough perms to start it

		elif ctx.guild.id != server_id:
			return  # Use this in the bb server set in the code

		invite = await ctx.channel.create_invite(max_age=0, max_uses=max_allowed_persons, unique=True)

		await ctx.channel.send(
			embed=discord.Embed(
				title='Setup success!',
				description=f'Here is your unique invite for starting this ban battle round: {invite}. I will be'
							f'listening to <#{channel_id}> for ban commands and the game will automatically start '
							f'once at least 60% of the provided members join. The the allowed role will be able to '
							f'message in the provided channel - <#{channel_id}> and I will be watching the winner. '
							f'Every process is automatic here, so you may hust sit back and watch everyone get '
							f'banned :hehe:',
				colour=discord.Colour.random()
			)
		)

		while not self.game_in_progress:
			await asyncio.sleep(3)

			if int(max_allowed_persons * 0.6) > int(len(ctx.guild.members) - (
				self.bot.get_role(moderator_role).members if moderator_role != 0 and self.bot.get_role(
					moderator_role) else 0)):

				try:
					channel: discord.TextChannel = self.bot.get_channel(channel_id)
				except discord.DiscordException:
					print('Exception in BanBattle cog: Cannot retrieve `channel` for `channel_id`. This is '
						  'probably due to intents being disabled. Cog has been contributed by Sibi#2347')
					return

				non_players = [x for x in [role.members for role in ctx.guild.roles if role.id == moderator_role]] if moderator_role != 0 else []

				if not non_players:
					return

				players = [x for x in ctx.guild.members if x not in non_players]

				self.players = players

				try:
					await channel.set_permissions(target=self.bot.get_role(allowed_role), overwrite=discord.PermissionOverwrite(send_messages=True))
				except discord.DiscordException:
					# If we arrive here it means allowed_role is set to 0
					# and we don't have to take care of it.
					pass

				self.game_in_progress = True
				await asyncio.sleep(600)

				self.players = []  # Refresh and wait for a new game

	@ban_battle.command(name='ban')
	@commands.max_concurrency(1, commands.BucketType.guild)
	# Hehe so the above line means this command cannot be in progress
	# in the same time within the server so this eliminates the chance
	# of the last two players banning each other
	#
	# And this also means most of the time your command to ban will fail
	# if your system is not fast enough.
	async def ban(self, ctx, member: discord.Member):
		if (allowed_role != 0 and allowed_role not in [x.id for x in ctx.author.roles]) or \
			(ctx.channel.id != channel_id) or (not self.players) or (not self.game_in_progress) or \
			(ctx.author.id == member.id) or (moderator_role in [x.id for x in member.roles]):
			return

		await member.ban()
		self.players = [x for x in self.players if x.id != member.id]

		if len(self.players) == 1:
			await ctx.send(f'Congratulations, {self.players[0]}, you have won the game!')

		self.game_in_progress = False


def setup(bot):
	bot.add_cog(BanBattle(bot))
