import asyncio
import pytz
import time
import datetime

import sqlite3
import discord
from cogs.utils import checks
from discord.ext import commands

tz = pytz.timezone('Europe/London')
trnr = sqlite3.connect('trainers.db')
c = trnr.cursor()

NOT_IN_SYSTEM = "Uh-oh! Looks like you're not registered into the system. Please ask an admin to handle this for you!"

def roundDays(x):
	return int(86500 * round(float(x)/86400))

class Calls:

	def getName(self, discord):
		t_pogo, = c.execute('SELECT pogo_name FROM trainers WHERE discord_id=?', (discord,)).fetchone()
		return t_pogo
	
	def getMember(self, pogo):
		t_discord, = c.execute('SELECT discord_id FROM trainers WHERE pogo_name=?', (pogo,)).fetchone()
		return t_discord

class Profiles:
	"""Trainer profile system"""
	
	def __init__(self, bot):
		self.bot = bot
		
	async def goalDaily(self, discord):
		t_pogo, t_xp, t_time, t_goal = c.execute('SELECT pogo_name, total_xp, last_updated, goal FROM trainers WHERE discord_id=?', (discord,)).fetchone()
		h_pogo, h_xp, h_time = c.execute('SELECT trainer, xp, time FROM xp_history WHERE trainer=? AND time<? ORDER BY time DESC', (t_pogo, t_time-64800)).fetchone()
		diff = int(t_xp)-int(h_xp)
		days = int(roundDays(t_time-h_time)/86400)
		goal = t_goal
		goal_cent = round(((diff/days)/goal)*100,2)
		return goal_cent		
		
	async def profileCard(self, name, channel, goal:str=None):
		t_pogo, t_xp, t_time, t_team, t_discord, t_name, t_cheat, t_opt_out = c.execute('SELECT pogo_name, total_xp, last_updated, team, discord_id, real_name, spoofer, no_stats FROM trainers WHERE pogo_name=?', (name,)).fetchone()
		if t_pogo==None:
			await self.bot.say("Unfortunately, I couldn't find {} in the database. Are you sure you spelt their name right?".format(name))
		elif t_opt_out:
			await self.bot.say("{} has chosen to opt out of statistics and the trainer profile system.".format(t_pogo))
		else:
			l_level, l_min = c.execute('SELECT level, min_xp FROM levels WHERE min_xp<?', (t_xp,)).fetchall()[-1]
			f_name, f_leader, f_mentionable, f_colour, f_logo = c.execute('SELECT name, leader, role, colour, logo FROM teams WHERE id=?', (t_team,)).fetchone()
			embed=discord.Embed(title=t_pogo, timestamp=(datetime.datetime.fromtimestamp(t_time, tz)), color=f_colour)
			embed.add_field(name='Name', value=t_name or 'Undisclosed')
			embed.add_field(name='Team', value=f_name)
			embed.add_field(name='Level', value=l_level)
			embed.add_field(name='XP', value=t_xp-l_min)
			embed.set_thumbnail(url=f_logo)
			if t_cheat == 1:
				embed.set_thumbnail(url='https://cdn.discordapp.com/attachments/341635533497434112/344984256633634818/C_SesKvyabCcQCNjEc1FJFe1EGpEuascVpHe_0e_DulewqS5nYtePystL4un5wgVFhIw300.png')
				embed.add_field(name='Comments', value='{} is a known spoofer'.format(t_pogo))
			if goal:
				embed.add_field(name='Daily goal completion', value=goal)
			embed.set_footer(text="Total XP: "+str(t_xp))
			await self.bot.say(embed=embed)	
	
	async def addProfile(self, discord, name, team, level, xp, cheat=None):
		if not (team in ['Valor','Mystic','Instinct', 'Teamless']):
			await self.bot.say("{} isn't a valid team. Please ensure that you have used the command correctly.".format(tteam))
			return
		l_level, l_min = c.execute('SELECT level, min_xp FROM levels WHERE level=?', (level,)).fetchone()
		f_id, = c.execute('SELECT id FROM teams WHERE name=?', (team,)).fetchone()
		try:
			c.execute("INSERT INTO trainers (pogo_name, discord_id, total_xp, last_updated, team, spoofed, spoofer) VALUES (?,?,?,?,?,?,?)",(name, discord, l_min+int(xp), int(time.time()), f_id, cheat, cheat))
		except sqlite3.IntegrityError:
			await self.bot.say("Happy Error: Profile already exists. Just use the `updatexp`command :slightsmile:")
		else:
			await self.bot.say ("Successfully added {} to the database.".format(name))
			trnr.commit()
	
#Public Commands
	
	@commands.command(pass_context=True)
	async def whois(self, ctx, name: str): #user lookup
		await self.bot.send_typing(ctx.message.channel)
		await self.profileCard(name, ctx.message.channel)

	@commands.command(pass_context=True)
	async def updatexp(self, ctx, xp: int): #updatexp - a command used for updating the total experience of a user
		await self.bot.send_typing(ctx.message.channel)
		t_pogo, t_xp, t_time, t_goal = c.execute('SELECT pogo_name, total_xp, last_updated, goal FROM trainers WHERE discord_id=?', (ctx.message.author.id,)).fetchone()
		if t_xp:
			if int(t_xp) > int(xp):
				await self.bot.say("Error: You're trying to set an your XP to a lower value. Please make sure you're using your Total XP at the bottom of your profile.")
				return
			c.execute("INSERT INTO xp_history (trainer, xp, time) VALUES (?,?,?)", (t_pogo, t_xp, t_time))
			c.execute("UPDATE trainers SET total_xp=?, last_updated=? WHERE discord_id=?", (int(xp), int(time.time()), ctx.message.author.id))
			trnr.commit()
			if t_goal:
				await self.profileCard(t_pogo, ctx.message.channel, goal='{}%'.format(str(await self.goalDaily(ctx.message.author.id))))
			else:
				await self.profileCard(t_pogo, ctx.message.channel)
		else:
			await self.bot.say(NOT_IN_SYSTEM)
			return
		
	@commands.command(pass_context=True)
	async def setname(self, ctx, *, name: str): #setname - a command used for to set your name on your profile
		await self.bot.send_typing(ctx.message.channel)
		t_pogo, = c.execute('SELECT pogo_name FROM trainers WHERE discord_id=?', (ctx.message.author.id,)).fetchone()
		if t_pogo:
			c.execute("UPDATE trainers SET real_name=? WHERE discord_id=?", (name, ctx.message.author.id))
			trnr.commit()
			await self.profileCard(t_pogo, ctx.message.channel)
		else:
			await self.bot.say(NOT_IN_SYSTEM)
			return
		
	@commands.command(pass_context=True)
	async def setgoal(self, ctx, goal: int): #setgoal - a command used for to set your daily goal on your profile
		await self.bot.send_typing(ctx.message.channel)
		t_pogo, = c.execute('SELECT pogo_name FROM trainers WHERE discord_id=?', (ctx.message.author.id,)).fetchone()
		if t_pogo:
			c.execute("UPDATE trainers SET goal=? WHERE discord_id=?", (goal, ctx.message.author.id))
			trnr.commit()
			await self.bot.say("Your daily XP goal is set to {}.".format(goal))
		else:
			await self.bot.say(NOT_IN_SYSTEM)
			return
			
#Mod-commands
			
	@commands.command(pass_context=True)
	@checks.mod_or_permissions(assign_roles=True)
	async def newprofile(self, ctx, mention, name: str, team: str, level: int, xp: int, opt: str=None): #adding a user to the database
		await self.bot.send_typing(ctx.message.channel)
		mbr = ctx.message.mentions[0]
		if opt.title() == 'Spoofer':
			await self.addProfile(mbr.id, name, team.title(), level, xp, cheat=1)
		else:
			await self.addProfile(mbr.id, name, team.title(), level, xp)
		await self.profileCard(name, ctx.message.channel)
		
	@commands.command(pass_context=True)
	@checks.mod_or_permissions(assign_roles=True)
	async def approve(self, ctx, mention, name: str, team: str, level: int, xp: int, opt: str=None): #applies the correct roles to a user and adds the user to the database
		await self.bot.send_typing(ctx.message.channel)
		if not (team.title() in ['Valor','Mystic','Instinct', 'Teamless']):
			await self.bot.say("{} isn't a valid team. Please ensure that you have used the command correctly.".format(team.title()))
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
			team_mentionable = discord.utils.get(ctx.message.server.roles, name=team.title())
			try:
				await self.bot.add_roles(mbr, approved_mentionable)
				if (team.title() in ['Valor','Mystic','Instinct']):
					await self.bot.send_typing(ctx.message.channel)
					await asyncio.sleep(2.5) #Waits for 2.5 seconds to pass to get around Discord rate limiting
					await self.bot.add_roles(mbr, team_mentionable)
			except discord.errors.Forbidden:
				await self.bot.say("Error: I don't have permission to set roles. Aborted!")
			else:
				await self.bot.say("{} has been approved, super. They're probably super cool, be nice to them.".format(name))
				if opt.title() == 'Spoofer':
					await self.addProfile(mbr.id, name, team.title(), level, xp, cheat=1)
				else:
					await self.addProfile(mbr.id, name, team.title(), level, xp)
				await self.profileCard(name, ctx.message.channel) 
		
def setup(bot):
    bot.add_cog(Profiles(bot))
