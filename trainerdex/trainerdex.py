# coding=utf-8
import os
import asyncio
import time
import datetime
import pytz
import discord
import random
import requests
from collections import namedtuple
from discord.ext import commands
from .utils import checks
from .utils.dataIO import dataIO
import trainerdex

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

class TrainerDex:
	
	def __init__(self, bot):
		self.bot = bot
		self.client = trainerdex.Client(token)
		self.teams = self.client.get_teams()
		
	async def get_trainer(self, username=None, discord=None, account=None, prefered=True):
		"""Returns a Trainer object for a given discord, trainer username or account id
		
		Search is done in the order of username > discord > account, if you specify more than one, it will ONLY search the first one.
		"""
		
		if username:
			try:
				return self.client.get_trainer_from_username(username)
			except LookupError:
				raise
		elif discord and prefered==True:
			return trainerdex.DiscordUser(discord).owner.trainer(all_=False)
		elif discord and prefered==False:
			return trainerdex.DiscordUser(discord).owner.trainer(all_=True)
		elif account and prefered==True:
			return trainerdex.User(account).trainer(all_=False)
		elif account and prefered==False:
			return trainerdex.User(account).trainer(all_=True)
		
	async def getTeamByName(self, team: str):
		for item in self.teams:
			if item.name.title()==team.title():
				return item
	
	async def getDiff(self, trainer, days: int):
		updates = trainer.updates()
		latest = trainer.update
		oldest = updates[-1]
		reference = []
		for i in updates:
			if i.time_updated <= (datetime.datetime.now(pytz.utc)-datetime.timedelta(days=days)+datetime.timedelta(hours=3)):
				reference.append(i)
		if reference==[]:
			if latest==oldest:
				diff = Difference(
					old_date = None,
					old_xp = None,
					new_date = latest.time_updated,
					new_xp = latest.xp,
					change_time = None,
					change_xp = None
				)
				return diff
			elif oldest.time_updated > (datetime.datetime.now(pytz.utc)-datetime.timedelta(days=days)+datetime.timedelta(hours=3)):
				reference=oldest
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
		level=trainer.level
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
		try:
			trainer = await self.get_trainer(username=name)
		except LookupError:
			raise
		account = trainer.account
		discordUser = account.discord()
		level=trainer.level
		if trainer.statistics is False and force is False:
			await self.bot.say("{} has chosen to opt out of statistics and the trainer profile system.".format(t_pogo))
		else:
			embed=discord.Embed(title=trainer.username, timestamp=trainer.update.time_updated, colour=int(trainer.team.colour.replace("#", ""), 16))
			if account and (account.first_name or account.last_name):
				embed.add_field(name='Name', value=account.first_name+' '+account.last_name)
			if discordUser:
				embed.add_field(name='Discord', value='<@{}>'.format(discordUser.id))
			embed.add_field(name='Team', value=trainer.team.name)
			embed.add_field(name='Level', value=level.level)
			embed.add_field(name='XP', value='{:,}'.format(trainer.update.xp-level.total_xp))
			#embed.set_thumbnail(url=trainer.team.image)
			if trainer.cheater is True:
				embed.set_thumbnail(url='https://cdn.discordapp.com/attachments/341635533497434112/344984256633634818/C_SesKvyabCcQCNjEc1FJFe1EGpEuascVpHe_0e_DulewqS5nYtePystL4un5wgVFhIw300.png')
				embed.add_field(name='Comments', value='{} is a known spoofer'.format(trainer.username))
			embed.set_footer(text="Total XP: {:,}".format(trainer.update.xp))
			return embed
	
	async def _addProfile(self, message, mention, username: str, xp: int, team, has_cheated=False, currently_cheats=False, name: str=None, prefered=True):
		#Check existance
		try:
			print('Attempting to add {} to database, checking if they already exist'.format(username))
			await self.get_trainer(username=username, prefered=prefered)
		except LookupError:
			pass
		else:
			print('Found {}, aborting...'.format(username))
			await self.bot.edit_message(message, "A record already exists in the database for this trainer. Aborted.")
			return
		#Create or get auth.User and discord user
		discordUser=None
		if mention.avatar_url=='' or mention.avatar_url is None:
			avatarUrl = mention.default_avatar_url
		else:
			avatarUrl = mention.avatar_url
		try:
			print('Checking if existing Discord User {} exists in our database...'.format(mention.id))
			discordUser=trainerdex.DiscordUser(mention.id)
		except requests.exceptions.HTTPError as e:
			print(e)
			user = self.client.create_user(username='_'+username, first_name=name)
			discordUser = self.client.import_discord_user(name=mention.name, discriminator=mention.discriminator, id_=mention.id, avatar_url=avatarUrl, creation=mention.created_at, user=user.id)
		else:
			print('Found... Using that.')
			user = discordUser.owner
		finally:
			#create or update trainer
			print('Creating trainer...')
			trainer = self.client.create_trainer(username=username, team=team.id, has_cheated=has_cheated, currently_cheats=currently_cheats, prefered=prefered, account=user.id)
			print('Trainer created. Creating update object...')
			#create update object
			update = self.client.create_update(trainer.id, xp)
			print('Update object created')
			return trainer


#Public Commands
	
	@commands.command(pass_context=True, name="trainer")
	async def trainer(self, ctx, trainer: str): 
		"""Look up a Pokemon Go Trainer
		
		Example: trainer JayTurnr
		"""
		
		message = await self.bot.say('Searching...')
		await self.bot.send_typing(ctx.message.channel)
		try:
			embed = await self.profileCard(trainer)
			await self.bot.edit_message(message, new_content='I found this one...', embed=embed)
		except LookupError as e:
			await self.bot.say('`Error: '+str(e)+'`')

	@commands.group(pass_context=True)
	async def update(self, ctx):
		"""Update information about your TrainerDex profile"""
			
		if ctx.invoked_subcommand is None:
			await self.bot.send_cmd_help(ctx)
		
	@update.command(name="xp", pass_context=True)
	async def xp(self, ctx, xp: int): 
		"""Update your xp
		
		Example: update xp 6000000
		"""
		
		message = await self.bot.say('Processing...')
		await self.bot.send_typing(ctx.message.channel)
		trainer = await self.get_trainer(discord=ctx.message.author.id)
		if trainer is not None:
			if int(trainer.update.xp) >= int(xp):
				await self.bot.edit_message(message, "Error: You last set your XP to {xp:,}, please try a higher number. `ValidationError: {usr}, {xp}`".format(usr= trainer.username, xp=trainer.update.xp))
				return
			if trainer.goal_total:
				if trainer.goal_total<=xp and trainer.goal_total != 0:
					await self.bot.say(random.choice(levelup).format(goal=trainer.goal_total, member=random.choice(list(ctx.message.server.members)).mention))
					self.client.update_trainer(trainer, total_goal=0)
			update = self.client.create_update(trainer.id, xp)
			await asyncio.sleep(1)
			embed = await self.updateCard(trainer)
			await self.bot.edit_message(message, new_content='Success 👍', embed=embed)
		
	@update.command(name="name", pass_context=True)
	async def name(self, ctx, first_name: str, last_name: str=None): 
		"""Update your name on your profile
		
		Set your name in form of <first_name> <last_name>
		If you want to blank your last name set it to two dots '..'
		
		Example: update xp Bob ..
		Example: update xp Jay Turner
		"""
		
		message = await self.bot.say('Processing...')
		await self.bot.send_typing(ctx.message.channel)
		trainer = await self.get_trainer(discord=ctx.message.author.id)
		account = trainer.account
		if last_name=='..':
			last_name=' '
		if account:
			self.client.update_user(account, first_name=first_name, last_name=last_name)
			try:
				embed = await self.profileCard(trainer.username)
				await self.bot.edit_message(message, new_content='Success 👍', embed=embed)
			except LookupError as e:
				await self.bot.edit_message(message, new_content='`Error: '+str(e)+'`')
		else:
			await self.bot.edit_message(message, new_content="Not found!")

	@update.command(name="goal", pass_context=True)
	async def goal(self, ctx, which: str, goal: int):
		"""Update your goals
		
		Example: update goal daily 2000
		"""
		
		message = await self.bot.say('Processing...')
		await self.bot.send_typing(ctx.message.channel)
		trainer = await self.get_trainer(discord=ctx.message.author.id)
		if which.title()=='Daily':
			self.client.update_trainer(trainer, daily_goal=goal)
			await self.bot.edit_message(message, "{}, your daily goal has been set to {:,}".format(ctx.message.author.mention, goal))
		elif which.title()=='Total':
			if goal>trainer.update.xp:
				self.client.update_trainer(trainer, total_goal=goal)
				await self.bot.edit_message(message, "{}, your total goal has been set to {:,}".format(ctx.message.author.mention, goal))
			else:
				await self.bot.edit_message(message, "{}, try something higher than your current XP of {:,}.".format(ctx.message.author.mention, trainer.update.xp))
		else:
			await self.bot.edit_message(message, "{}, please choose 'Daily' or 'Total' for after goal.".format(ctx.message.author.mention))
	
	@commands.command(pass_context=True)
	async def leaderboard(self, ctx, entries=9):
		"""View the leaderboard for your server
		
		Optional argument: entries - default, 9
		
		Example: leaderboard 25
		Example: leaderboard
		"""
		
		message = await self.bot.say("Thinking...")
		await self.bot.send_typing(ctx.message.channel)
		trainer_list = trainerdex.DiscordServer(ctx.message.server.id).get_trainers(ctx.message.server)
		trainers = []
		for trainer in trainer_list:
			if trainer.statistics==True:
				trainers.append(trainer)
		trainers.sort(key=lambda x:x.update.xp, reverse=True)
		embed=discord.Embed(title="Leaderboard")
		for i in range(min(entries, 25, len(trainers))):
			embed.add_field(name='{}. {}'.format(i+1, trainers[i].username), value="{:,}".format(trainers[i].update.xp))
		await self.bot.edit_message(message, new_content=str(datetime.date.today()), embed=embed)

#Mod-commands

	@commands.command(pass_context=True)
	@checks.mod_or_permissions(assign_roles=True)
	async def spoofer(self, ctx):
		"""Set a user as a spoofer
		
		WIP
		"""
		await self.bot.say("This command is currently a work in progress.")

	@commands.command(name="addprofile", no_pm=True, pass_context=True, alias="newprofile")
	@checks.mod_or_permissions(assign_roles=True)
	async def addprofile(self, ctx, mention, name: str, team: str, level: int, xp: int, opt: str=''): 
		"""Add a user to the Trainer Dex database
		
		Optional arguments:
		spoofer - sets the user as a spoofer
		
		Example: approve @JayTurnr#1234 JayTurnr Valor 34 1234567
		"""
		
		message = await self.bot.say('Processing...')
		await self.bot.send_typing(ctx.message.channel)
		mbr = ctx.message.mentions[0]
		xp = trainerdex.Level.from_level(level).total_xp + xp
		team = await self.getTeamByName(team)
		if team is None:
			await self.bot.edit_message(message, "That isn't a valid team. Please ensure that you have used the command correctly.")
			return
		if opt.title() == 'Spoofer':
			await self._addProfile(message, mbr, name, xp, team, has_cheated=True, currently_cheats=True)
		else:
			await self._addProfile(message, mbr, name, xp, team)
		try:
			embed = await self.profileCard(name)
			await self.bot.edit_message(message, new_content='Success 👍', embed=embed)
		except LookupError as e:
			await self.bot.edit_message(message, '`Error: '+str(e)+'`')
		
	@commands.command(pass_context=True, no_pm=True)
	@checks.mod_or_permissions(assign_roles=True)
	async def addsecondary(self, ctx, mention, name: str, team: str, level: int, xp: int, opt: str=''):
		"""Add a user to the Trainer Dex database as a secondary profile
		
		Optional arguments:
		spoofer - sets the user as a spoofer
		
		Example: approve @JayTurnr#1234 JayTurnr Valor 34 1234567 spoofer
		"""
		
		message = await self.bot.say('Processing...')
		await self.bot.send_typing(ctx.message.channel)
		mbr = ctx.message.mentions[0]
		xp = trainerdex.Level.from_level(level).total_xp + xp
		team = await self.getTeamByName(team)
		if team is None:
			await self.bot.edit_message(message, "That isn't a valid team. Please ensure that you have used the command correctly.")
			return
		if opt.title() == 'Spoofer':
			await self._addProfile(message, mbr, name, xp, team, has_cheated=True, currently_cheats=True, prefered=False)
		else:
			await self._addProfile(message, mbr, name, xp, team, prefered=False)
		try:
			embed = await self.profileCard(name)
			await self.bot.edit_message(message, new_content='Success 👍', embed=embed)
		except LookupError as e:
			await self.bot.edit_message(message, '`Error: '+str(e)+'`')
		
	@commands.command(pass_context=True, no_pm=True)
	@checks.mod_or_permissions(assign_roles=True)
	async def approve(self, ctx, mention, name: str, team: str, level: int, xp: int, opt: str=''): 
		"""Add a user to the Trainer Dex database and set the correct role on Discord
		
		Roles and renaming based on the ekpogo.uk discord - options coming soon.
		
		Optional arguments:
		spoofer - sets the user as a spoofer (db only)
		minor/child - sets the 'Minor' role instead of the 'Trainer' role (discord only)
		
		Example: approve @JayTurnr#1234 JayTurnr Valor 34 1234567 minor
		"""
		
		message = await self.bot.say('Processing step 1 of 2...')
		await self.bot.send_typing(ctx.message.channel)
		xp = trainerdex.Level.from_level(level).total_xp + xp
		team = await self.getTeamByName(team)
		if team is None:
			await self.bot.edit_message(message, "That isn't a valid team. Please ensure that you have used the command correctly.")
			return
		mbr = ctx.message.mentions[0]
		try:
			await self.bot.change_nickname(mbr, name)
		except discord.errors.Forbidden:
			await self.bot.edit_message(message, "Error: I don't have permission to change nicknames. Aborted!")
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
				await self.bot.edit_message(message, "Error: I don't have permission to set roles. Aborted!")
			else:
				await self.bot.edit_message(message, "{} has been approved! 👍".format(name))
				message = await self.bot.say('Processing step 2 of 2...')
				await self.bot.send_typing(ctx.message.channel)
				if opt.title() == 'Spoofer':
					await self._addProfile(message, mbr, name, xp, team, has_cheated=True, currently_cheats=True)
				else:
					await self._addProfile(message, mbr, name, xp, team)
				try:
					embed = await self.profileCard(name)
					await self.bot.edit_message(message, new_content='Success 👍', embed=embed)
				except LookupError as e:
					await self.bot.edit_message(message, '`Error: '+str(e)+'`')
	
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
		
		message = await self.bot.say('Processing...')
		await self.bot.send_typing(ctx.message.channel)
		settings = dataIO.load_json(settings_file)
		if token:
			settings['token'] = token
			dataIO.save_json(settings_file, settings)
			await self.bot.edit_message(message, '```API token set - please restart cog```')
	
	@tdset.command(pass_context=True)
	@checks.is_owner()
	async def register_server(self, ctx, cheaters, minors):
		"""Register Server to database, required before leaderboards can work
		
		arguments:
		cheaters - allowed, ban, segregate
		minors - allowed, ban, segregate
		"""
		
		message = await self.bot.say('Processing...')
		await self.bot.send_typing(ctx.message.channel)
		if cheaters == 'allowed':
			c1=False
			c2=False
		elif cheaters == 'ban':
			c1=True
			c2=False
		elif cheaters in ('segregate','seg'):
			c1=False
			c2=True
		if minors == 'allowed':
			m1=False
			m2=False
		elif minors == 'ban':
			m1=True
			m2=False
		elif minors in ('segregate','seg'):
			m1=False
			m2=True
		print('{}{}{}{}'.format(c1,c2,m1,m2))
		svr = ctx.message.server
		server = self.client.import_discord_server(svr.name, str(svr.region), svr.id, owner=svr.owner.id, bans_cheaters=c1, seg_cheaters=c2, bans_minors=m1, seg_minors=m2)
		await self.bot.edit_message(message, 'Server #{s.id} {s.name} succesfully added.'.format(server))
	
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
	bot.add_cog(TrainerDex(bot))