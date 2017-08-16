import asyncio
import pytz
import time
import datetime
import discord
from cogs.utils import checks
from discord.ext import commands
import sqlite3

tz = pytz.timezone('Europe/London')
trnr = sqlite3.connect('trainers.db')
c = trnr.cursor()

def rounddays(x):
	return int(86500 * round(float(x)/86400))

class Profiles:
	"""Trainer profile system"""
	
	def __init__(self, bot):
		self.bot = bot
		
	async def goal_daily(self, discord):
		profile = c.execute('SELECT pogo_name, total_xp, last_updated, goal FROM trainers WHERE discord_id=?', (discord,)).fetchone()
		history = c.execute('SELECT trainer, xp, time FROM xp_history WHERE trainer=? AND time<? ORDER BY time DESC', (profile[0], profile[2]-64800)).fetchone()
		diff = int(profile[1])-int(history[1])
		days = int(rounddays(profile[2]-history[2])/86400)
		goal = profile[3]
		goal_cent = ((diff/days)/goal)*100
		return goal_cent		
		
	async def profile_card(self, name, channel, goal:str=None):
		trn = c.execute('SELECT pogo_name, total_xp, last_updated, team, discord_id, real_name, spoofer, no_stats FROM trainers WHERE pogo_name=?', (name,)).fetchone()
		if trn==None:
			await self.bot.say("Unfortunately, I couldn't find {} in the database. Are you sure you spelt their name right?".format(name))
		elif trn[7]:
			await self.bot.say("{} has chosen to opt out of statistics and the trainer profile system.".format(trn[0]))
		else:
			trnrlvl = c.execute('SELECT level, min_xp FROM levels WHERE min_xp<?', (trn[1],)).fetchall()[-1]
			team = c.execute('SELECT name, leader, role, colour, logo FROM teams WHERE id=?', (trn[3],)).fetchone()
			embed=discord.Embed(title=trn[0], timestamp=(datetime.datetime.fromtimestamp(trn[2], tz)), color=team[3])
			embed.add_field(name='Name', value=trn[5] or 'Undisclosed')
			embed.add_field(name='Team', value=team[0])
			embed.add_field(name='Level', value=trnrlvl[0])
			embed.add_field(name='XP', value=trn[1]-trnrlvl[1])
			embed.set_thumbnail(url=team[4])
			if trn[6] == 1:
				embed.set_thumbnail(url='https://cdn.discordapp.com/attachments/341635533497434112/344984256633634818/C_SesKvyabCcQCNjEc1FJFe1EGpEuascVpHe_0e_DulewqS5nYtePystL4un5wgVFhIw300.png')
				embed.add_field(name='Comments', value='{} is a known spoofer'.format(trn[0]))
			if goal:
				embed.add_field(name='Daily goal completion', value=goal)
			embed.set_footer(text="Total XP: "+str(trn[1]))
			await self.bot.say(embed=embed)	
	
	async def add_profile(self, discord, name, team, level, xp):
		tteam = team.title()
		if not (tteam in ['Valor','Mystic','Instinct', 'Teamless']):
			await self.bot.say("{} isn't a valid team. Please ensure that you have used the command correctly.".format(tteam))
			return
		lvl = c.execute('SELECT level, min_xp FROM levels WHERE level=?', (level,)).fetchone()
		teami = c.execute('SELECT id FROM teams WHERE name=?', (tteam,)).fetchone()
		try:
			c.execute("INSERT INTO trainers (pogo_name, discord_id, total_xp, last_updated, team) VALUES (?,?,?,?,?)",(name, discord, lvl[1]+int(xp), int(time.time()), teami[0]))
		except sqlite3.IntegrityError:
			await self.bot.say("Happy Error: Profile already exists. Just use the `updatexp`command :slightsmile:")
		else:
			await self.bot.say ("Successfully added {} to the database.".format(name))
			trnr.commit()
	
#Public Commands
	
	@commands.command(pass_context=True)
	async def whois(self, ctx, name): #user lookup
		await self.bot.send_typing(ctx.message.channel)
		await self.profile_card(name, ctx.message.channel)

	@commands.command(pass_context=True)
	async def updatexp(self, ctx, xp): #updatexp - a command used for updating the total experience of a user
		await self.bot.send_typing(ctx.message.channel)
		oldxp = c.execute('SELECT pogo_name, total_xp, last_updated, goal FROM trainers WHERE discord_id=?', (ctx.message.author.id,)).fetchone()
		if oldxp:
			if int(oldxp[1]) > int(xp):
				await self.bot.say("Error: Specified XP higher than currently set XP. Please use the Total XP at the bottom of your profile.")
				return
			c.execute("INSERT INTO xp_history (trainer, xp, time) VALUES (?,?,?)", (oldxp[0], oldxp[1], oldxp[2]))
			c.execute("UPDATE trainers SET total_xp=?, last_updated=? WHERE discord_id=?", (int(xp), int(time.time()), ctx.message.author.id))
			trnr.commit()
			if oldxp[3]:
				await self.profile_card(oldxp[0], ctx.message.channel, goal='{}%'.format(str(await self.goal_daily(ctx.message.author.id))))
			else:
				await self.profile_card(oldxp[0], ctx.message.channel)
		else:
			await self.bot.say("Please ask a member of staff to add your profile to the system.")
			return
		
	@commands.command(pass_context=True)
	async def setname(self, ctx, *, name: str): #setname - a command used for to set your name on your profile
		await self.bot.send_typing(ctx.message.channel)
		profile = c.execute('SELECT pogo_name FROM trainers WHERE discord_id=?', (ctx.message.author.id,)).fetchone()
		if profile:
			c.execute("UPDATE trainers SET real_name=? WHERE discord_id=?", (name, ctx.message.author.id))
			trnr.commit()
			await self.profile_card(profile[0], ctx.message.channel)
		else:
			await self.bot.say("Please ask a member of staff to add your profile to the system.")
			return
		
	@commands.command(pass_context=True)
	async def setgoal(self, ctx, goal: int): #setgoal - a command used for to set your daily goal on your profile
		await self.bot.send_typing(ctx.message.channel)
		profile = c.execute('SELECT pogo_name FROM trainers WHERE discord_id=?', (ctx.message.author.id,)).fetchone()
		if profile:
			c.execute("UPDATE trainers SET goal=? WHERE discord_id=?", (goal, ctx.message.author.id))
			trnr.commit()
			await self.bot.say("Your daily XP goal is set to {}.".format(goal))
		else:
			await self.bot.say("Please ask a member of staff to add your profile to the system.")
			return
			
#Mod-commands
			
	@commands.command(pass_context=True)
	@checks.mod_or_permissions(assign_roles=True)
	async def newprofile(self, ctx, mention, name, team, level, xp): #adding a user to the database
		await self.bot.send_typing(ctx.message.channel)
		mbr = ctx.message.mentions[0]
		await self.add_profile(mbr.id, name, team, level, xp)
		await self.profile_card(name, ctx.message.channel)
		
	@commands.command(pass_context=True)
	@checks.mod_or_permissions(assign_roles=True)
	async def approve(self, ctx, mention, name, team, level, xp): #applies the correct roles to a user and adds the user to the database
		await self.bot.send_typing(ctx.message.channel)
		tteam = team.title()
		if not (tteam in ['Valor','Mystic','Instinct', 'Teamless']):
			await self.bot.say("{} isn't a valid team. Please ensure that you have used the command correctly.".format(tteam))
			return
		mbr = ctx.message.mentions[0]
		try:
			await self.bot.change_nickname(mbr, name)
		except discord.errors.Forbidden:
			await self.bot.say("Error: I don't have permission to change nicknames. Aborted!")
		else:
			trnrrole = discord.utils.get(ctx.message.server.roles, name='Trainer')
			tmrole = discord.utils.get(ctx.message.server.roles, name=tteam)
			try:
				await self.bot.add_roles(mbr, trnrrole)
				if (tteam in ['Valor','Mystic','Instinct']):
					await self.bot.send_typing(ctx.message.channel)
					await asyncio.sleep(2.5)
					await self.bot.add_roles(mbr, tmrole)
			except discord.errors.Forbidden:
				await self.bot.say("Error: I don't have permission to set roles. Aborted!")
			else:
				await self.bot.say("{} has been approved, super. They're probably super cool, be nice to them.".format(name))
				await self.add_profile(mbr.id, name, team, level, xp)
				await self.profile_card(name, ctx.message.channel) 
		
def setup(bot):
    bot.add_cog(Profiles(bot))
