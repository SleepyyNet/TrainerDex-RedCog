# coding=utf-8
import os
import asyncio
import time
import datetime
import pytz
import discord
from collections import namedtuple
from discord.ext import commands
from .utils import checks
from .utils.dataIO import dataIO
from TrainerDex import Requests

settings_file = 'data/trainerdex/settings.json'
json_data = dataIO.load_json(settings_file)
token = json_data['token']
r = Requests(token)

Difference = namedtuple('Difference', [
	'old_date',
	'old_xp',
	'new_date',
	'new_xp',
	'change_time',
	'change_xp',
])

class trainerdex:
	
	def __init__(self, bot):
		self.bot = bot
		self.teams = r.getTeams()
		
	async def getTrainerID(self, username=None, discord=None, account=None, prefered=True):
		listTrainers = r.listTrainers()
		for trainer in listTrainers:
			if username:
				if trainer.username.lower()==username.lower():
					return trainer
			elif discord:
				if trainer.discord==discord and trainer.prefered is True:
					return trainer
			elif account:
				if trainer.account==account and trainer.prefered is True:
					return trainer
			else:
				return None
		
	async def getTeamByName(self, team):
		for item in self.teams:
			if item.name.title()==team.title():
				return item
	
	async def getDiff(self, trainer, days):
		updates = r.getUpdates(trainer.id)
		updates.sort(key=lambda x:x.time_updated, reverse=True)
		latest = updates[0]
		reference = []
		for i in updates:
			if i.time_updated <= (datetime.datetime.now(pytz.utc)-datetime.timedelta(days=days)+datetime.timedelta(hours=3)):
				reference.append(i)
		reference = reference[0]
		diff = Difference(
				old_date = reference.time_updated,
				old_xp = reference.total_xp,
				new_date = latest.time_updated,
				new_xp = latest.total_xp,
				change_time = latest.time_updated-reference.time_updated+datetime.timedelta(hours=3),
				change_xp = latest.total_xp-reference.total_xp
			)
		
		return diff
	
	async def updateCard(self, trainer):
		team = self.teams[int(trainer.team)]
		dailyDiff = await self.getDiff(trainer, 1)
		level=r.trainerLevels(xp=dailyDiff.new_xp)
		embed=discord.Embed(title=trainer.username, timestamp=trainer.xp_time, colour=int(team.colour.replace("#", ""), 16))
		embed.add_field(name='Level', value=level)
		embed.add_field(name='XP', value='{:,}ₓₚ'.format(dailyDiff.new_xp-r.trainerLevels(level=level)))
		gain = '{:,} over {} day'.format(dailyDiff.change_xp, dailyDiff.change_time.days)
		if dailyDiff.change_time.days!=1:
			gain += 's.'
			gain += "That's {:,} xp/day.".format(dailyDiff.change_xp/dailyDiff.change_time.days)
		embed.add_field(name='Gain', value=gain)
		if trainer.goal_daily is not None:
			dailyGoal = trainer.goal_daily
			dailyCent = lambda x, y, z: round(((x/y)/z)*100,2)
			embed.add_field(name='Daily completion', value='{}% of {:,} xp'.format(dailyCent(dailyDiff.change_xp, dailyDiff.change_time.days, dailyGoal), dailyGoal))
		if trainer.goal_total is not None:
			totalGoal = trainer.goal_total
			totalDiff = await self.getDiff(trainer, 7)
			embed.add_field(name='Goal remaining', value='{:,} of {:,}'.format(totalGoal-trainer.xp, totalGoal))
			eta = lambda x, y, z: round(x/(y/z),0)
			eta = eta(totalGoal-trainer.xp, totalDiff.change_xp, totalDiff.change_time.days)
			eta = datetime.date.today()+datetime.timedelta(days=eta)
			embed.add_field(name='ETA', value=eta.strftime("%A %d %B %Y"))
		embed.set_footer(text="Total XP: {:,}".format(dailyDiff.new_xp))
		
		return embed
		
	async def profileCard(self, name, force=False):
		trainer = await self.getTrainerID(username=name)
		if trainer.account is not None:
			account = r.getUser(trainer.account)
		else:
			account = None
		discordUser = trainer.discord
		trainer = r.getTrainer(trainer.id)
		team = self.teams[int(trainer.team)]
		level=r.trainerLevels(xp=trainer.xp)
		if trainer.statistics is False and force is False:
			await self.bot.say("{} has chosen to opt out of statistics and the trainer profile system.".format(t_pogo))
		else:
			embed=discord.Embed(title=trainer.username, timestamp=trainer.xp_time, colour=int(team.colour.replace("#", ""), 16))
			if account and (account.first_name or account.last_name):
				embed.add_field(name='Name', value=account.first_name+' '+account.last_name)
			embed.add_field(name='Team', value=team.name)
			embed.add_field(name='Level', value=level)
			embed.add_field(name='XP', value='{:,}'.format(trainer.xp-r.trainerLevels(level=level)))
			#embed.set_thumbnail(url=team.image)
			if trainer.cheater is True:
				embed.set_thumbnail(url='https://cdn.discordapp.com/attachments/341635533497434112/344984256633634818/C_SesKvyabCcQCNjEc1FJFe1EGpEuascVpHe_0e_DulewqS5nYtePystL4un5wgVFhIw300.png')
				embed.add_field(name='Comments', value='{} is a known spoofer'.format(trainer.username))
			embed.set_footer(text="Total XP: {:,}".format(trainer.xp))
			await self.bot.say(embed=embed)
	
	async def _addProfile(self, mention, username, xp, team, has_cheated=False, currently_cheats=False, name=None, prefered=True):
		#Check existance
		listTrainers = r.listTrainers()
		for trainer in listTrainers:
			if trainer.username.lower()==username.lower():
				await self.bot.say("A record already exists in the database for this trainer")
				await self.profileCard(name=trainer.username, force=True)
				return
		#Create or get auth.User
		#Create or update discord user
		listDiscordUsers = r.listDiscordUsers()
		discordUser=None
		if mention.avatar_url=='' or mention.avatar_url is None:
			avatarUrl = mention.default_avatar_url
		else:
			avatarUrl = mention.avatar_url
		for item in listDiscordUsers:
			if item.discord_id==mention.id:
				discordUser=item
		if discordUser is None:
			user = r.addUserAccount(username='_'+username, first_name=name)
			discordUser = r.addDiscordUser(name=mention.name, discriminator=mention.discriminator, id=mention.id, avatar_url=avatarUrl, creation=mention.created_at, user=user)
		elif discordUser.discord_id==mention.id:
			user = discordUser.account_id
			discordUser = r.patchDiscordUser(name=mention.name, discriminator=mention.discriminator, id=mention.id, avatar_url=avatarUrl, creation=mention.created_at)
		#create or update trainer
		trainer = r.addTrainer(username=username, team=team, has_cheated=has_cheated, currently_cheats=currently_cheats, prefered=prefered, account=user)
		#create update object
		update = r.addUpdate(trainer, xp)
		return user, discordUser, trainer, update


#Public Commands
	
	@commands.command(pass_context=True, name="trainer")
	async def trainer(self, ctx, trainer): 
		"""Trainer lookup"""
		await self.bot.send_typing(ctx.message.channel)
		await self.profileCard(trainer)

	@commands.group(pass_context=True)
	async def update(self, ctx):
		"""Update information about your TrainerDex profile"""
			
		if ctx.invoked_subcommand is None:
			await self.bot.send_cmd_help(ctx)
		
	@update.command(name="xp", pass_context=True)
	async def xp(self, ctx, xp: int): 
		"""XP"""
		await self.bot.send_typing(ctx.message.channel)
		trainer = await self.getTrainerID(discord=ctx.message.author.id)
		if trainer is not None:
			trainer = r.getTrainer(trainer.id)
			if int(trainer.xp) >= int(xp):
				await self.bot.say("Error: You last set your XP to {xp}, please try a higher number. `ValidationError: {usr}, {xp}`".format(usr= trainer.username, xp=trainer.xp))
				return
			update = r.addUpdate(trainer.id, xp)
			await asyncio.sleep(1)
			embed = await self.updateCard(trainer)
			await self.bot.say(embed=embed)
		
	@update.command(name="name", pass_context=True)
	async def name(self, ctx, first_name, last_name=None): 
		"""
		Set your name in form of <first_name> <last_name>
		If you want to blank your last name set it to two dots '..'
		"""
		await self.bot.send_typing(ctx.message.channel)
		account = await self.getTrainerID(discord=ctx.message.author.id)
		if last_name=='..':
			last_name=' '
		if account:
			r.patchUserAccount(account.account, first_name=first_name, last_name=last_name)
			await self.profileCard(account.username)
		else:
			await self.bot.say("Not found!")
			return

	@update.command(name="goal", pass_context=True)
	async def goal(self, ctx, which: str, goal: int):
		"""Update your goals"""
		await self.bot.send_typing(ctx.message.channel)
		trainer = await self.getTrainerID(discord=ctx.message.author.id)
		trainer = r.getTrainer(trainer.id)
		if which.title()=='Daily':
			r.patchTrainer(trainer.id, daily_goal=goal)
			await self.bot.say("Daily goal set to {:,}".format(goal))
		elif which.title()=='Total':
			if goal>trainer.xp:
				r.patchTrainer(trainer.id, total_goal=goal)
				await self.bot.say("Total goal set to {:,}".format(goal))
			else:
				await self.bot.say("Try something higher than your current XP of {:,}.".format(trainer.xp))
		else:
			await self.bot.say("`Please choose 'Daily' or 'Total' for after goal.")
		

#Mod-commands

	@commands.command(pass_context=True)
	@checks.mod_or_permissions(assign_roles=True)
	async def spoofer(self, ctx):
		"""oh look, a cheater"""
		pass

	@commands.command(name="addprofile", no_pm=True, pass_context=True, alias="newprofile")
	@checks.mod_or_permissions(assign_roles=True)
	async def addprofile(self, ctx, mention, name: str, team: str, level: int, xp: int, opt: str=''): 
		"""adding a user to the database"""
		await self.bot.send_typing(ctx.message.channel)
		mbr = ctx.message.mentions[0]
		xp = r.trainerLevels(level=level) + xp
		team = await self.getTeamByName(team)
		if opt.title() == 'Spoofer':
			await self._addProfile(mbr, name, xp, team.id, has_cheated=True, currently_cheats=True)
		else:
			await self._addProfile(mbr, name, xp, team.id)
		await self.profileCard(name)
		
	@commands.command(pass_context=True, no_pm=True)
	@checks.mod_or_permissions(assign_roles=True)
	async def addsecondary(self, ctx, mention, name: str, team: str, level: int, xp: int, opt: str=''):
		"""adding a trainer's second profile to the database"""
		await self.bot.send_typing(ctx.message.channel)
		mbr = ctx.message.mentions[0]
		xp = r.trainerLevels(level=level) + xp
		team = await self.getTeamByName(team)
		if opt.title() == 'Spoofer':
			await self._addProfile(mbr, name, xp, team.id, has_cheated=True, currently_cheats=True, prefered=False)
		else:
			await self._addProfile(mbr, name, xp, team.id, prefered=False)
		await self.profileCard(name)
		
	@commands.command(pass_context=True, no_pm=True)
	@checks.mod_or_permissions(assign_roles=True)
	async def approve(self, ctx, mention, name: str, team: str, level: int, xp: int, opt: str=''): 
		"""applies the correct roles to a user and adds the user to the database"""
		await self.bot.send_typing(ctx.message.channel)
		xp = r.trainerLevels(level=level) + xp
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
					await self._addProfile(mbr, name, xp, team.id, has_cheated=True, currently_cheats=True)
				else:
					await self._addProfile(mbr, name, xp, team.id)
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