import asyncio
import pytz
import time
import datetime
import discord
from cogs.utils import checks
from discord.ext import commands
from TrainerDex import Requests
from data.TrainerDex.config import Config

tz = pytz.timezone('Europe/London')
r = Requests(token=Config.token)

class Calls: #Commented out functions not used by other cogs currently, left enough uncommented to not cause an error but to similate this not existing

	def getName(discord):
#		t = c.execute('SELECT pogo_name FROM trainers WHERE discord_id=? AND primaryac=1', (discord.id,)).fetchone()
#		if t:
#			return t[0]
#		else:
		return discord.nick if discord.nick else str(discord.name)
#	
#	def getMember(pogo):
#		try:
#			t_discord, = c.execute('SELECT discord_id FROM trainers WHERE pogo_name=?', (pogo,)).fetchone()
#		except:
#			return None
#		else:
#			return t_discord

class Profiles:
	"""Trainer profile system"""
	
	def __init__(self, bot):
		self.bot = bot
		self.teams = r.getTeams()
		
		
	async def profileCard(self, name, force=False):
		trainer, statistics = r.getTrainer(name)
		team = self.teams[int(trainer.team)]
		level=r.trainerLevels(xp=trainer.xp)
		if statistics is False and force is False:
			await self.bot.say("{} has chosen to opt out of statistics and the trainer profile system.".format(t_pogo))
		else:
			embed=discord.Embed(description="**"+trainer.username+"**", timestamp=datetime.datetime.strptime(trainer.xp_time, "%Y-%m-%dT%H:%M:%S.%fZ"))
			embed.add_field(name='Team', value=team.name)
			embed.add_field(name='Level', value=level)
			embed.add_field(name='XP', value=int(trainer.xp) - int(r.trainerLevels(level=level)))
#			embed.set_thumbnail(url=f_logo)
			if trainer.cheater is True:
				embed.set_thumbnail(url='https://cdn.discordapp.com/attachments/341635533497434112/344984256633634818/C_SesKvyabCcQCNjEc1FJFe1EGpEuascVpHe_0e_DulewqS5nYtePystL4un5wgVFhIw300.png')
				embed.add_field(name='Comments', value='{} is a known spoofer'.format(t_pogo))
			embed.set_footer(text="Total XP: "+str(trainer.xp))
			await self.bot.say(embed=embed)
	
#	async def addProfile(self, discord, name, team, level, xp, primary=True, cheat=None):
#		if not (team in ['Valor','Mystic','Instinct', 'Teamless']):
#			await self.bot.say("{} isn't a valid team. Please ensure that you have used the command correctly.".format(tteam))
#			return
#		l_level, l_min = c.execute('SELECT level, min_xp FROM levels WHERE level=?', (level,)).fetchone()
#		f_id, = c.execute('SELECT id FROM teams WHERE name=?', (team,)).fetchone()
#		if primary==True:
#			primary=1
#		elif primary==False:
#			primary=0
#		else:
#			await self.bot.say("`TypeError: primary value is a boolean yet somehow it's erroring.`")
#			await self.bot.say("It's officially the end of the world.")
#		try:
#			c.execute("INSERT INTO trainers (pogo_name, discord_id, total_xp, last_updated, team, spoofed, spoofer, primaryac) VALUES (?,?,?,?,?,?,?,?)",(name, discord, l_min+int(xp), int(time.time()), f_id, cheat, cheat, primary))
#		except sqlite3.IntegrityError:
#			await self.bot.say("`HappyError: Profile already exists.` :slightsmile:")
#		else:
#			await self.bot.say ("Successfully added {} to the database.".format(name))
#			trnr.commit()

#Public Commands
	
#	@commands.command()
#	async def dbcheck(self, username):
#		try:
#			trainer = r.getTrainer(username)[0]
#		except KeyError:
#			state=False
#		else:
#			state=True
#		await self.bot.say(str(state))
#	
	@commands.command(pass_context=True)
	async def whois(self, ctx, trainer): 
		await self.bot.send_typing(ctx.message.channel)
		await self.profileCard(trainer)
#
#	@commands.command(pass_context=True)
#	async def updatexp(self, ctx, xp: int, profile=None): #updatexp - a command used for updating the total experience of a user
#		await self.bot.send_typing(ctx.message.channel)
#		if profile==None:
#			t_pogo, t_xp, t_time, t_goalD, t_goalT = c.execute('SELECT pogo_name, total_xp, last_updated, goalDaily, goalTotal FROM trainers WHERE discord_id=? AND primaryac=1', (ctx.message.author.id,)).fetchone()
#		else:
#			try:
#				t_pogo, t_xp, t_time, t_goalD, t_goalT = c.execute('SELECT pogo_name, total_xp, last_updated, goalDaily, goalTotal FROM trainers WHERE discord_id=? AND primaryac=0 AND pogo_name=?', (ctx.message.author.id,profile)).fetchone()
#			except TypeError:
#				return await self.bot.say("`TypeError` - No secondary account called {} belonging to <@{}> found.".format(profile,ctx.message.author.id))
#		if t_xp:
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
#		else:
#			await self.bot.say(NOT_IN_SYSTEM)
#			return

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

#
#Mod-commands
#
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
#
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
#		
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
#		
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
				

def setup(bot):
    bot.add_cog(Profiles(bot))
	
