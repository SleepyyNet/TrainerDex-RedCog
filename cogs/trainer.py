# coding=utf-8
import os
import asyncio
import time
import datetime
import pytz
import discord
import random
from collections import namedtuple
from discord.ext import commands
from .utils import checks
from .utils.dataIO import dataIO
import TrainerDex

settings_file = 'data/trainerdex/settings.json'
json_data = dataIO.load_json(settings_file)
token = json_data['token']

Difference = namedtuple('Difference', [
	'old_date',
	'old_xp',
	'new_date',
	'new_xp',
	'change_time',
	'change_xp',
])

levelup = ["You reached your goal, well done. Now if only applied that much effort at buying {member} pizza, I might be happy!", "Well done on reaching {goal:,}", "much xp, very goal", "Great, you got to {goal:,} XP, now what?"]

class trainerdex:
	
	def __init__(self, bot):
		self.bot = bot
		self.client = TrainerDex.Client(token)
		self.teams = self.client.get_teams
		
	async def get_trainer(self, username=None, discord=None, account=None, prefered=True):
		"""Returns a Trainer object for a given discord, trainer username or account id"""
		
		if username:
			return self.client.get_user_from_username(username)
		elif discord:
			return TrainerDex.DiscordUser(discord).owner().trainer()
		elif account:
			return TrainerDex.User(account).trainer()
		else:
			return None
		
	async def getTeamByName(self, team: str):
		for item in self.teams:
			if item.name.title()==team.title():
				return item
	
	async def getDiff(self, trainer, days: int):
		updates = trainer.all_updates()
		latest = updates[0]
		first = updates[-1]
		reference = []
		for i in updates:
			if i.time_updated <= (datetime.datetime.now(pytz.utc)-datetime.timedelta(days=days)+datetime.timedelta(hours=3)):
				reference.append(i)
		if reference==[]:
			if latest==first:
				diff = Difference(
					old_date = None,
					old_xp = None,
					new_date = latest.time_updated,
					new_xp = latest.xp,
					change_time = None,
					change_xp = None
				)
				return diff
			elif first.time_updated > (datetime.datetime.now(pytz.utc)-datetime.timedelta(days=days)+datetime.timedelta(hours=3)):
				reference=first
		else:
			reference = reference[0]
		print(reference)
		diff = Difference(
				old_date = reference.time_updated,
				old_xp = reference.xp,
				new_date = latest.time_updated,
				new_xp = latest.xp,
				change_time = latest.time_updated-reference.time_updated+datetime.timedelta(hours=3),
				change_xp = latest.xp-reference.xp
			)
		
		return diff
	
	async def updateCard(self, trainer):
		dailyDiff = await self.getDiff(trainer, 1)
		level=trainer.level()
		embed=discord.Embed(title=trainer.username, timestamp=dailyDiff.new_date, colour=int(trainer.team.colour.replace("#", ""), 16))
		embed.add_field(name='Level', value=level.level)
		embed.add_field(name='XP', value='{:,}'.format(dailyDiff.new_xp-level.xp_required))
		if dailyDiff.change_xp and dailyDiff.change_time:
			gain = '{:,} over {} day'.format(dailyDiff.change_xp, dailyDiff.change_time.days)
			if dailyDiff.change_time.days!=1:
				gain += 's. '
			if dailyDiff.change_time.days>1:
				gain += "That's {:,} xp/day.".format(round(dailyDiff.change_xp/dailyDiff.change_time.days))
			embed.add_field(name='Gain', value=gain)
			if (trainer.goal_daily!=None) and (dailyDiff.change_time.days>0):
				dailyGoal = trainer.goal_daily
				dailyCent = lambda x, y, z: round(((x/y)/z)*100,2)
				embed.add_field(name='Daily completion', value='{}% of {:,}'.format(dailyCent(dailyDiff.change_xp, dailyDiff.change_time.days, dailyGoal), dailyGoal))
		if (trainer.goal_total!=None):
			totalGoal = trainer.goal_total
			totalDiff = await self.getDiff(trainer, 7)
			embed.add_field(name='Goal remaining', value='{:,} of {:,}'.format(totalGoal-totalDiff.new_xp, totalGoal))
			if totalDiff.change_time.days>0:
				eta = lambda x, y, z: round(x/(y/z))
				eta = eta(totalGoal-totalDiff.new_xp, totalDiff.change_xp, totalDiff.change_time.days)
				eta = datetime.date.today()+datetime.timedelta(days=eta)
				embed.add_field(name='ETA', value=eta.strftime("%A %d %B %Y"))
		embed.set_footer(text="Total XP: {:,}".format(dailyDiff.new_xp))
		
		return embed
		
	async def profileCard(self, name: str, force=False):
		trainer = await self.get_trainer(username=name)
		account = trainer.account
		level=trainer.level()
		if trainer.statistics is False and force is False:
			await self.bot.say("{} has chosen to opt out of statistics and the trainer profile system.".format(t_pogo))
		else:
			embed=discord.Embed(title=trainer.username, timestamp=trainer.update.xp_time, colour=int(trainer.team.colour.replace("#", ""), 16))
			if account and (account.first_name or account.last_name):
				embed.add_field(name='Name', value=account.first_name+' '+account.last_name)
			embed.add_field(name='Team', value=trainer.team.name)
			embed.add_field(name='Level', value=level.level)
			embed.add_field(name='XP', value='{:,}'.format(trainer.update.xp-level.total_xp))
			#embed.set_thumbnail(url=trainer.team.image)
			if trainer.cheater is True:
				embed.set_thumbnail(url='https://cdn.discordapp.com/attachments/341635533497434112/344984256633634818/C_SesKvyabCcQCNjEc1FJFe1EGpEuascVpHe_0e_DulewqS5nYtePystL4un5wgVFhIw300.png')
				embed.add_field(name='Comments', value='{} is a known spoofer'.format(trainer.username))
			embed.set_footer(text="Total XP: {:,}".format(trainer.update.xp))
			await self.bot.say(embed=embed)
	
	async def _addProfile(self, mention, username: str, xp: int, team, has_cheated=False, currently_cheats=False, name: str=None, prefered=True):
		#Check existance
		if self.get_trainer(username=username):
			await self.bot.say("A record already exists in the database for this trainer. Aborted.")
			return
		#Create or get auth.User and discord user
		discordUser=None
		if mention.avatar_url=='' or mention.avatar_url is None:
			avatarUrl = mention.default_avatar_url
		else:
			avatarUrl = mention.avatar_url
		if TrainerDex.DiscordUser(mention.id):
			discordUser=TrainerDex.DiscordUser(mention.id)
			user = discordUser.owner
		elif discordUser==None:
			user = self.client.create_user(username='_'+username, first_name=name)
			discordUser = self.client.import_discord_user(name=mention.name, discriminator=mention.discriminator, id=mention.id, avatar_url=avatarUrl, creation=mention.created_at, user=user.id)
		#create or update trainer
		trainer = self.client.create_trainer(username=username, team=team.id, has_cheated=has_cheated, currently_cheats=currently_cheats, prefered=prefered, account=user.id)
		#create update object
		update = self.client.create_update(trainer.id, xp)
		return trainer


#Public Commands
	
	@commands.command(pass_context=True, name="trainer")
	async def trainer(self, ctx, trainer: str): 
		"""Look up a Pokemon Go Trainer
		
		Usage: trainer <username>
		"""
		
		await self.bot.send_typing(ctx.message.channel)
		await self.profileCard(trainer)

	@commands.group(pass_context=True)
	async def update(self, ctx):
		"""Update information about your TrainerDex profile"""
			
		if ctx.invoked_subcommand is None:
			await self.bot.send_cmd_help(ctx)
		
	@update.command(name="xp", pass_context=True)
	async def xp(self, ctx, xp: int): 
		"""Update your xp
		
		Usage: update xp <number>
		"""
		
		await self.bot.send_typing(ctx.message.channel)
		trainer = await self.get_trainer(discord=ctx.message.author.id)
		if trainer is not None:
			if int(trainer.update.xp) >= int(xp):
				await self.bot.say("Error: You last set your XP to {xp:,}, please try a higher number. `ValidationError: {usr}, {xp}`".format(usr= trainer.username, xp=trainer.update.xp))
				return
			if trainer.goal_total:
				if trainer.goal_total<=xp and trainer.goal_total != 0:
					await self.bot.say(random.choice(levelup).format(goal=trainer.goal_total, member=random.choice(list(ctx.message.server.members)).mention))
					self.client.update_trainer(trainer, total_goal=0)
			update = self.client.create_update(trainer.id, xp)
			await asyncio.sleep(1)
			embed = await self.updateCard(trainer)
			await self.bot.say(embed=embed)
		
	@update.command(name="name", pass_context=True)
	async def name(self, ctx, first_name: str, last_name: str=None): 
		"""Update your name on your profile - entirely optional
		
		Set your name in form of <first_name> <last_name>
		If you want to blank your last name set it to two dots '..'
		
		Usage: update xp Bob ..
		or
		Usage: update xp Jay Turner
		"""
		
		await self.bot.send_typing(ctx.message.channel)
		account = TrainerDex.DiscordUser(ctx.message.author.id).user
		if last_name=='..':
			last_name=' '
		if account:
			self.client.update_user(account, first_name=first_name, last_name=last_name)
			await self.profileCard(account.trainer.username)
		else:
			await self.bot.say("Not found!")
			return

	@update.command(name="goal", pass_context=True)
	async def goal(self, ctx, which: str, goal: int):
		"""Update your goals
		
		Usage: update goal <daily/update> <number>
		"""
		
		await self.bot.send_typing(ctx.message.channel)
		trainer = TrainerDex.DiscordUser(ctx.message.author.id).owner.trainer
		if which.title()=='Daily':
			self.client.update_trainer(trainer, daily_goal=goal)
			await self.bot.say("Daily goal set to {:,}".format(goal))
		elif which.title()=='Total':
			if goal>trainer.update.xp:
				self.client.update_trainer(trainer, total_goal=goal)
				await self.bot.say("Total goal set to {:,}".format(goal))
			else:
				await self.bot.say("Try something higher than your current XP of {:,}.".format(trainer.update.xp))
		else:
			await self.bot.say("`Please choose 'Daily' or 'Total' for after goal.")
	
	@commands.command(pass_context=True)
	async def leaderboard(self, ctx, entries=9):
		Message = await self.bot.say("Thinking...")
		await self.bot.send_typing(ctx.message.channel)
		trainers = []
		for user in ctx.message.server.members:
			try:
				trainers.append(TrainerDex.DiscordUser(user.id).owner.trainer)
			except:
				pass
		trainers.sort(key=lambda x:x.update.xp, reverse=True)
		embed=discord.Embed(title="Leaderboard")
		for i in range(min(entries, 25, len(trainers))):
			embed.add_field(name='{}. {}'.format(i+1, trainers[i].username), value="{:,}".format(trainers[i].xp))
		await self.bot.edit_message(Message, new_content=str(datetime.date.today()), embed=embed)

#Mod-commands

	@commands.command(pass_context=True)
	@checks.mod_or_permissions(assign_roles=True)
	async def spoofer(self, ctx):
		"""Set a user as a spoofer. WIP."""
		
		pass

	@commands.command(name="addprofile", no_pm=True, pass_context=True, alias="newprofile")
	@checks.mod_or_permissions(assign_roles=True)
	async def addprofile(self, ctx, mention, name: str, team: str, level: int, xp: int, opt: str=''): 
		"""Add a user to the Trainer Dex database
		
		Optional arguments: spoofer - sets the user as a spoofer (db only)
		
		Usage: addprofile <the tagged mention of a discord user> <pokemon username> <team> <level> <xp through level> <optional tag words suppoted: spoofer>
		
		Example: approve @JayTurnr#1234 JayTurnr Valor 34 1234567
		"""
		
		await self.bot.send_typing(ctx.message.channel)
		mbr = ctx.message.mentions[0]
		xp = TrainerDex.Level.from_level(level).total_xp + xp
		team = await self.getTeamByName(team)
		if team is None:
			await self.bot.say("That isn't a valid team. Please ensure that you have used the command correctly.")
			return
		if opt.title() == 'Spoofer':
			await self._addProfile(mbr, name, xp, team, has_cheated=True, currently_cheats=True)
		else:
			await self._addProfile(mbr, name, xp, team)
		await self.profileCard(name)
		
	@commands.command(pass_context=True, no_pm=True)
	@checks.mod_or_permissions(assign_roles=True)
	async def addsecondary(self, ctx, mention, name: str, team: str, level: int, xp: int, opt: str=''):
		"""Add a user to the Trainer Dex database as a secondary profile
		
		Optional arguments: spoofer - sets the user as a spoofer (db only)
		
		Usage: addprofile <the tagged mention of a discord user> <pokemon username> <team> <level> <xp through level> <optional tag words suppoted: spoofer>
		
		Example: approve @JayTurnr#1234 JayTurnr Valor 34 1234567
		"""
		
		await self.bot.send_typing(ctx.message.channel)
		mbr = ctx.message.mentions[0]
		xp = TrainerDex.Level.from_level(level).total_xp + xp
		team = await self.getTeamByName(team)
		if team is None:
			await self.bot.say("That isn't a valid team. Please ensure that you have used the command correctly.")
			return
		if opt.title() == 'Spoofer':
			await self._addProfile(mbr, name, xp, team, has_cheated=True, currently_cheats=True, prefered=False)
		else:
			await self._addProfile(mbr, name, xp, team, prefered=False)
		await self.profileCard(name)
		
	@commands.command(pass_context=True, no_pm=True)
	@checks.mod_or_permissions(assign_roles=True)
	async def approve(self, ctx, mention, name: str, team: str, level: int, xp: int, opt: str=''): 
		"""Add a user to the Trainer Dex database and set the correct role on Discord
		
		Based on the ekpogo.uk standard network - options coming soon.
		
		Optional arguments: spoofer - sets the user as a spoofer (db only)
							minor/child - sets the 'Minor' role instead of the 'Trainer' role (discord only)
		
		Usage: approve <the tagged mention of a discord user> <pokemon username> <team> <level> <xp through level> <max one tag, optional tag words suppoted: spoofer, minor/child>
		
		Example: approve @JayTurnr#1234 JayTurnr Valor 34 1234567
		"""
		
		await self.bot.send_typing(ctx.message.channel)
		xp = TrainerDex.Level.from_level(level).total_xp + xp
		team = await self.getTeamByName(team)
		if team is None:
			await self.bot.say("That isn't a valid team. Please ensure that you have used the command correctly.")
			return
		mbr = ctx.message.mentions[0]
		try:
			await self.bot.change_nickname(mbr, name)
		except discord.errors.Forbidden:
			await self.bot.say("Error: I don't have permission to change nicknames. Aborted!")
		else:
			if (opt.title() in ['Minor', 'Child']) and discord.utils.get(ctx.message.server.roles, name='Minor'):
				approved_mentionable = discord.utils.get(ctx.message.server.roles, name='Minor')
			else:
				approved_mentionable = discord.utils.get(ctx.message.server.roles, name='Trainer')
			team_mentionable = discord.utils.get(ctx.message.server.roles, name=team.name)
			try:
				await self.bot.add_roles(mbr, approved_mentionable)
				if team_mentionable is not None:
					await asyncio.sleep(2.5) #Waits for 2.5 seconds to pass to get around Discord rate limiting
					await self.bot.add_roles(mbr, team_mentionable)
			except discord.errors.Forbidden:
				await self.bot.say("Error: I don't have permission to set roles. Aborted!")
			else:
				await self.bot.say("{} has been approved, super. They're probably super cool, be nice to them.".format(name))
				if opt.title() == 'Spoofer':
					await self._addProfile(mbr, name, xp, team, has_cheated=True, currently_cheats=True)
				else:
					await self._addProfile(mbr, name, xp, team)
				await self.profileCard(name)

	@commands.group(pass_context=True)
	@checks.is_owner()
	async def tdset(self, ctx):
		"""Settings for TrainerDex cog"""
		
		if ctx.invoked_subcommand is None:
			await self.bot.send_cmd_help(ctx)

	@tdset.command(pass_context=True)
	@checks.is_owner()
	async def api(self, ctx, token: str):
		"""Sets the TrainerDex API token - owner only"""
		
		settings = dataIO.load_json(settings_file)
		if token:
			settings['token'] = token
			dataIO.save_json(settings_file, settings)
			await self.bot.say('```API token set```')
	
def check_folders():
	if not os.path.exists("data/trainerdex"):
		print("Creating data/trainerdex folder...")
		os.makedirs("data/trainerdex")
		
def check_file():
	f = 'data/trainerdex/settings.json'
	data = {}
	data['token'] = ''
	if not dataIO.is_valid_json(f):
		print("Creating default token.json...")
		dataIO.save_json(f, data)
	
def setup(bot):
	check_folders()
	check_file()
	importedTrainerDex = True
	bot.add_cog(trainerdex(bot))