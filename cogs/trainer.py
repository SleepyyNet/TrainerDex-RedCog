import os
import asyncio
import time
import datetime
import discord
from discord.ext import commands
from .utils import checks
from .utils.dataIO import dataIO
try:
	from TrainerDex import Requests
	importedTrainerDex = True
except:
	importedTrainerDex = False



class Calls:

	def getName(discord):
		return Profiles.getTrainerID(discord=discord.id).username if Profiles.getTrainerID(discord=discord.id).username else discord.display_name
	
	def getMember(ussername):
		return Profiles.getTrainerID(username=username).discord_ID

class Profiles:
	"""Trainer profile system"""
	
	def __init__(self, bot):
		self.bot = bot
		self.config_path = "data/trainerdex/config.json"
		self.json_data = dataIO.load_json(self.file_path)
		r = Requests(token=self.json_data['token']ter)
		self.teams = r.getTeams()
		self.trainers = r.listTrainers() #Works like a cache
		
	async def getTrainerID(self, username=None, discord=None, account=None, prefered=True):
		for trainer in self.trainers:
			if username:
				if trainer.username=username:
					return trainer
			elif discord:
				if trainer.discord_ID=discord and trainer.prefered=True:
					return trainer
			elif account:
				if trainer.account_ID=account and trainer.prefered=True:
					return trainer
			else:
				return None
		
	async def getTeamByName(self, team):
		for team in self.teams:
			return team if team.name.title()=team.title():
		
	async def profileCard(self, name, force=False):
		trainerIDs = getTrainerID(username=name)
		trainer= r.getTrainer(trainerIDs.trainer_ID)
		team = self.teams[int(trainer.team)]
		level=r.trainerLevels(xp=trainer.xp)
		if trainer.statistics is False and force is False:
			await self.bot.say("{} has chosen to opt out of statistics and the trainer profile system.".format(t_pogo))
		else:
			embed=discord.Embed(description="**"+trainer.username+"**", timestamp=trainer.xp_time)
			embed.add_field(name='Team', value=team.name)
			embed.add_field(name='Level', value=level)
			embed.add_field(name='XP', value=int(trainer.xp) - int(r.trainerLevels(level=level)))
			embed.set_thumbnail(url=team.image)
			if trainer.cheater is True:
				embed.set_thumbnail(url='https://cdn.discordapp.com/attachments/341635533497434112/344984256633634818/C_SesKvyabCcQCNjEc1FJFe1EGpEuascVpHe_0e_DulewqS5nYtePystL4un5wgVFhIw300.png')
				embed.add_field(name='Comments', value='{} is a known spoofer'.format(t_pogo))
			embed.set_footer(text="Total XP: "+str(trainer.xp))
			await self.bot.say(embed=embed)
	
	async def addProfile(self, ctx, mention, username, xp, team, start_date=None, has_cheated=None, currently_cheats=None, name=None, prefered=True):
		#Check existance
		for trainer in r.listTrainers():
			if trainer.username=username:
				await self.bot.say("A record already exists in the database for this trainer")
				await self.profileCard(name=trainer.username, force=True)
				return
		#Create or get auth.User
		#Create or update discord user
		for item in r.listDiscordUsers():
			if item.discord_id=mention.id:
				discordUser=item
		if discordUser is None:
			user = r.addUserAccount(username=username, first_name=name)
			discordUser = r.addDiscordUser(name=mention.name, discriminator=mention.discriminator, id=mention.id, avatar_url=mention.avatar_url, creation=mention.created_at, user=user)
		elif discordUser.discord_id=mention.id:
			user = discordUser.account_id
			discordUser = r.putDiscordUser(name=mention.name, discriminator=mention.discriminator, id=mention.id, avatar_url=mention.avatar_url)
		#create or update trainer
		trainer = r.addTrainer(username=username, team=self.getTeamByName(team).id, start_date=start_date, has_cheated=has_cheated, currently_cheats=currently_cheats, prefered=prefered)
		#create update object
		update = r.addUpdate(trainer, xp)
		return user, discordUser, trainer, update


#Public Commands
	
	@commands.command(pass_context=True)
	async def whois(self, ctx, trainer): 
		await self.bot.send_typing(ctx.message.channel)
		await self.profileCard(trainer)

	@commands.command(pass_context=True, name='updatexp', aliases=['xp'])
	async def updatexp(self, ctx, xp: int, profile=None): #updatexp - a command used for updating the total experience of a user
		await self.bot.send_typing(ctx.message.channel)
		if profile==None:
			trainer = getTrainerID(discord=ctx.message.author.id)
		else:
			trainer = getTrainerID(username=profile)
			if trainer.discord_ID!=ctx.message.author.id:
				trainer = None
				return await self.bot.say("Cannot find an account called {} belonging to <@{}>.".format(profile,ctx.message.author.id))
		if trainer is not None:
#			if int(t_xp) > int(xp):
#				await self.bot.say("Error: You're trying to set an your XP to a lower value. Please make sure you're using your Total XP at the bottom of your profile.")
#				return
#			c.execute("INSERT INTO xp_history (trainer, xp, time) VALUES (?,?,?)", (t_pogo, t_xp, t_time))
#			c.execute("UPDATE trainers SET total_xp=?, last_updated=? WHERE pogo_name=?", (int(xp), int(time.time()), t_pogo))
#			trnr.commit()
#			await asyncio.sleep(1)
#			if t_goalD and t_goalT:
#				await self.profileCard(t_pogo, ctx.message.channel, goal_daily=True, goal_total=True)
#				if t_goalT<xp:
#					c.execute("UPDATE trainers SET goalTotal=? WHERE discord_id=?", (None, ctx.message.author.id,))
#					await self.bot.say("Congratulations, you've reached your goal.")
#			elif t_goalD:
#				await self.profileCard(t_pogo, ctx.message.channel, goal_daily=True)
#			elif t_goalT:
#				await self.profileCard(t_pogo, ctx.message.channel, goal_total=True)
#				if t_goalT<=xp:
#					c.execute("UPDATE trainers SET goalTotal=None WHERE discord_id=?", (ctx.message.author.id,))
#					await self.bot.say("🎉 Congratulations, you've reached your goal. 🎉")
#			else:
#				await self.profileCard(t_pogo, ctx.message.channel)
		elif trainer is None:
			return self.bot.say(NOT_IN_SYSTEM)

	@commands.group(pass_context=True)
	async def set(self, ctx):
		"""Changing information on your profile"""
			
        if ctx.invoked_subcommand is None:
            await send_cmd_help(ctx)
		
#	@set.command(name="name", pass_context=True)
#	async def _name_set(self, ctx, *, name: str): #setname - a command used for to set your name on your profile
#		await self.bot.send_typing(ctx.message.channel)
#		t_pogo, = c.execute('SELECT pogo_name FROM trainers WHERE discord_id=?', (ctx.message.author.id,)).fetchone()
#		if t_pogo:
#			c.execute("UPDATE trainers SET real_name=? WHERE discord_id=?", (name, ctx.message.author.id))
#			trnr.commit()
#			await self.profileCard(t_pogo, ctx.message.channel)
#		else:
#			await self.bot.say(NOT_IN_SYSTEM)
#			return

	@set.command(pass_context=True)
	async def _goal_set(self, ctx, goal: int):
		await self.bot.say("Goals are currently disabled. Sorry.")

	@set.command(pass_context=True)
	async def _goaldaily_set(self, ctx, goal: int): #setgoal - a command used for to set your daily goal on your profile
		await self.bot.say("Goals are currently disabled. Sorry. They will return as `.set goal daily/total`")
	
	@set.command(pass_context=True)
	async def _goaltotal_set(self, ctx, goal: int): #setgoal - a command used for to set your daily goal on your profile
		await self.bot.say("Goals are currently disabled. Sorry. They will return as `.set goal daily/total`")

#Mod-commands

#	@commands.command(pass_context=True)
#	@checks.mod_or_permissions(assign_roles=True)
#	async def spoofer(self, ctx, mention):
#		await self.bot.send_typing(ctx.message.channel)
#		try:
#			mbr = ctx.message.mentions[0].id
#		except:
#			mbr = None
#		try:
#			t_pogo, t_cheat = c.execute('SELECT pogo_name, spoofer FROM trainers WHERE discord_id=? OR pogo_name=?', (mbr,mention)).fetchone()
#		except:
#			await self.bot.say("Error!")
#		else:
#			if t_cheat==1:
#				try:
#					c.execute('UPDATE trainers SET spoofer=? WHERE pogo_name=?', (0, t_pogo))
#				except sqlite3.IntegrityError:
#					await self.bot.say("Error!")
#				else:
#					await self.bot.say("Success! You've unset the `spoofer` flag on {}!".format(t_pogo))
#					trnr.commit()
#			else:
#				try:
#					c.execute('UPDATE trainers SET spoofer=?, spoofed=? WHERE pogo_name=?', (1,1, t_pogo))
#				except sqlite3.IntegrityError:
#					await self.bot.say("Error!")
#				else:
#					await self.bot.say("Success! You've set the `spoofer` flag on {}!".format(t_pogo))
#					trnr.commit()
#			await self.profileCard(t_pogo, ctx.message.channel)

#	@commands.command(pass_context=True)
#	@checks.mod_or_permissions(assign_roles=True)
#	async def newprofile(self, ctx, mention, name: str, team: str, level: int, xp: int, opt: str=''): #adding a user to the database
#		await self.bot.send_typing(ctx.message.channel)
#		mbr = ctx.message.mentions[0]
#		if opt.title() == 'Spoofer':
#			await self.addProfile(mbr.id, name, team.title(), level, xp, cheat=1)
#		else:
#			await self.addProfile(mbr.id, name, team.title(), level, xp)
#		await self.profileCard(name, ctx.message.channel)
		
#	@commands.command(pass_context=True)
#	@checks.mod_or_permissions(assign_roles=True)
#	async def addsecondary(self, ctx, mention, name: str, team: str, level: int, xp: int, opt: str=''): #adding a user to the database
#		await self.bot.send_typing(ctx.message.channel)
#		mbr = ctx.message.mentions[0]
#		if opt.title() == 'Spoofer':
#			await self.addProfile(mbr.id, name, team.title(), level, xp, cheat=1, primary=False)
#		else:
#			await self.addProfile(mbr.id, name, team.title(), level, xp, primary=False)
#		await self.profileCard(name, ctx.message.channel)
		
#	@commands.command(pass_context=True)
#	@checks.mod_or_permissions(assign_roles=True)
#	async def approve(self, ctx, mention, name: str, team: str, level: int, xp: int, opt: str=''): #applies the correct roles to a user and adds the user to the database
#		await self.bot.send_typing(ctx.message.channel)
#		if not (team.title() in ['Valor','Mystic','Instinct', 'Teamless']):
#			await self.bot.say("{} isn't a valid team. Please ensure that you have used the command correctly.".format(team.title()))
#			return
#		mbr = ctx.message.mentions[0]
#		try:
#			await self.bot.change_nickname(mbr, name)
#		except discord.errors.Forbidden:
#			await self.bot.say("Error: I don't have permission to change nicknames. Aborted!")
#		else:
#			if (opt.title() in ['Minor', 'Child']) and discord.utils.get(ctx.message.server.roles, name='Minor'):
#				approved_mentionable = discord.utils.get(ctx.message.server.roles, name='Minor')
#			else:
#				approved_mentionable = discord.utils.get(ctx.message.server.roles, name='Trainer')
#			team_mentionable = discord.utils.get(ctx.message.server.roles, name=team.title())
#			try:
#				await self.bot.add_roles(mbr, approved_mentionable)
#				if (team.title() in ['Valor','Mystic','Instinct']):
#					await self.bot.send_typing(ctx.message.channel)
#					await asyncio.sleep(2.5) #Waits for 2.5 seconds to pass to get around Discord rate limiting
#					await self.bot.add_roles(mbr, team_mentionable)
#			except discord.errors.Forbidden:
#				await self.bot.say("Error: I don't have permission to set roles. Aborted!")
#			else:
#				await self.bot.say("{} has been approved, super. They're probably super cool, be nice to them.".format(name))
#				if opt.title() == 'Spoofer':
#					await self.addProfile(mbr.id, name, team.title(), level, xp, cheat=1)
#				else:
#					await self.addProfile(mbr.id, name, team.title(), level, xp)
#				await self.profileCard(name, ctx.message.channel)
				

def check_folders():
	if not os.path.exists("data/trainerdex"):
		print("Creating data/trainerdex folder...")
		os.makedirs("data/cogfolder")
		
def check_files():
	system = {"TrainerDex.py": {"Token": null}}
	f = self.config_path
	if not dataIO.is_valid_json(f):
		print("Creating default token.json...")
		dataIO.save_json(f, system)
	
def setup(bot):
	check_folders()
	check_files()
	if importedTrainerDex is True:
		bot.add_cog(Profiles(bot))
	else:
		raise RuntimeError('You need to install the TrainerDex.py library.')