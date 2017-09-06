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
parentLogsChannel = '355112430713438209'

NOT_IN_SYSTEM = "Uh-oh! Looks like you're not registered into the system. Please ask an admin to handle this for you!"

def roundDays(x):
	return int(86500 * round(float(x)/86400))

class Calls:

	def getName(discord):
		t = c.execute('SELECT pogo_name FROM trainers WHERE discord_id=? AND primaryac=1', (discord.id,)).fetchone()
		if t:
			return t[0]
		else:
			return discord.nick if discord.nick else str(discord.name)
	
	def getMember(pogo):
		try:
			t_discord, = c.execute('SELECT discord_id FROM trainers WHERE pogo_name=?', (pogo,)).fetchone()
		except:
			return None
		else:
			return t_discord

class Profiles:
	"""Trainer profile system"""
	
	def __init__(self, bot):
		self.bot = bot
	
	async def updateDiff(self, discord, num_days):
		t_pogo, t_xp, t_time= c.execute('SELECT pogo_name, total_xp, last_updated FROM trainers WHERE discord_id=?', (discord,)).fetchone()
		seconds = t_time-(num_days*86400)-21600
		h_pogo, h_xp, h_time = c.execute('SELECT trainer, xp, time FROM xp_history WHERE trainer=? AND time<? ORDER BY time DESC', (t_pogo, seconds)).fetchone()
		diff = int(t_xp)-int(h_xp)
		pure_time = t_time-h_time
		days = int(roundDays(pure_time)/86400)
		return diff, days, pure_time
		
	async def goalDaily(self, discord):
		t_goal, = c.execute('SELECT goalDaily FROM trainers WHERE discord_id=?', (discord,)).fetchone()
		diff, days, pureTime = await self.updateDiff(discord=discord, num_days=1)
		goal_cent = round(((diff/days)/t_goal)*100,2)
		return goal_cent
	
	async def goalTotal(self, discord):
		t_xp, t_time, t_goal, = c.execute('SELECT total_xp, last_updated, goalTotal FROM trainers WHERE discord_id=?', (discord,)).fetchone()
		diff, days, pureTime = await self.updateDiff(discord=discord, num_days=7)
		goal_remaining = t_goal-t_xp
		g_eta = ((goal_remaining)/(diff/days))*86400
		return g_eta, diff, goal_remaining, t_goal
		
	async def profileCard(self, name, channel, goal_daily=False, goal_total=False):
		try:
			t_pogo, t_xp, t_time, t_team, t_discord, t_name, t_cheat, t_opt_out = c.execute('SELECT pogo_name, total_xp, last_updated, team, discord_id, real_name, spoofer, no_stats FROM trainers WHERE pogo_name=?', (name,)).fetchone()
			if t_opt_out:
				await self.bot.say("{} has chosen to opt out of statistics and the trainer profile system.".format(t_pogo))
			else:
				l_level, l_min = c.execute('SELECT level, min_xp FROM levels WHERE min_xp<=?', (t_xp,)).fetchall()[-1]
				f_name, f_leader, f_mentionable, f_colour, f_logo = c.execute('SELECT name, leader, role, colour, logo FROM teams WHERE id=?', (t_team,)).fetchone()
				embed=discord.Embed(description="**"+t_pogo+"** | <@"+str(t_discord)+">", timestamp=(datetime.datetime.fromtimestamp(t_time, tz)), color=f_colour)
				embed.add_field(name='Name', value=t_name or 'Undisclosed')
				embed.add_field(name='Team', value=f_name)
				embed.add_field(name='Level', value=l_level)
				if l_level == 40:
					embed.add_field(name='XP', value=t_xp-l_min)
				else:
					embed.add_field(name='XP', value='{}/{}'.format(t_xp-l_min, (c.execute('SELECT min_xp FROM levels WHERE level=?', (l_level+1,)).fetchone()[0]-l_min)))
				embed.set_thumbnail(url=f_logo)
				if t_cheat == 1:
					embed.set_thumbnail(url='https://cdn.discordapp.com/attachments/341635533497434112/344984256633634818/C_SesKvyabCcQCNjEc1FJFe1EGpEuascVpHe_0e_DulewqS5nYtePystL4un5wgVFhIw300.png')
					embed.add_field(name='Comments', value='{} is a known spoofer'.format(t_pogo))
				if goal_daily==True:
					embed.add_field(name='Daily goal completion', value='{}%'.format(await self.goalDaily(discord=t_discord)))
				if goal_total==True:
					g_eta, g_diff, g_remaining, g_goal = await self.goalTotal(discord=t_discord)
					g_completetime = datetime.datetime.fromtimestamp(time.time()+g_eta).strftime("%a %d %b '%y around %-I %p")
					embed.add_field(name='Goal Completion', value='{}/{}'.format(t_xp, g_goal))
					embed.add_field(name='Goal ETA', value=g_completetime)
				embed.set_footer(text="Total XP: "+str(t_xp))
				await self.bot.say(embed=embed)
		except TypeError:
			await self.bot.say("Unfortunately, I couldn't find {} in the database. Are you sure you spelt their name right?".format(name))
	
	async def addProfile(self, mention, name, team, level, xp, primary=True, cheat=None):
		if not (team in ['Valor','Mystic','Instinct', 'Teamless']):
			await self.bot.say("{} isn't a valid team. Please ensure that you have used the command correctly.".format(tteam))
			return
		l_level, l_min = c.execute('SELECT level, min_xp FROM levels WHERE level=?', (level,)).fetchone()
		f_id, = c.execute('SELECT id FROM teams WHERE name=?', (team,)).fetchone()
		if primary==True:
			primary=1
		elif primary==False:
			primary=0
		else:
			await self.bot.say("`TypeError: primary value is a boolean yet somehow it's erroring.`")
			await self.bot.say("It's officially the end of the world.")
		try:
			c.execute("INSERT INTO trainers (pogo_name, discord_id, total_xp, last_updated, team, spoofed, spoofer, primaryac) VALUES (?,?,?,?,?,?,?,?)",(name, mention, l_min+int(xp), int(time.time()), f_id, cheat, cheat, primary))
		except sqlite3.IntegrityError:
			await self.bot.say("`HappyError: Profile already exists.` :slightsmile:")
		else:
			await self.bot.say("Successfully added {} to the database.".format(name))
			await self.bot.send_message(discord.Object(parentLogsChannel), "Added {} to the database.".format(name))
			trnr.commit()

#Public Commands
	
	@commands.command(pass_context=True)
	async def whois(self, ctx, mention, extra=''): #user lookup
		await self.bot.send_typing(ctx.message.channel)
		try:
			mbr = ctx.message.mentions[0].id
		except:
			mbr = None
		try:
			t_pogo, t_goal = c.execute('SELECT pogo_name, goalTotal FROM trainers WHERE (discord_id=? AND primaryac=1) OR (pogo_name=?)', (mbr,mention)).fetchone()
		except TypeError:
			await self.bot.say("TypeError: Likely user not found!")
		else:
			if extra.title()=="Extra" and t_goal:
				await self.profileCard(t_pogo, ctx.message.channel, goal_total=True)
			else:
				await self.profileCard(t_pogo, ctx.message.channel)

	@commands.command(pass_context=True)
	async def updatexp(self, ctx, xp: int, profile=None): #updatexp - a command used for updating the total experience of a user
		await self.bot.send_typing(ctx.message.channel)
		if profile==None:
			t_pogo, t_xp, t_time, t_goalD, t_goalT = c.execute('SELECT pogo_name, total_xp, last_updated, goalDaily, goalTotal FROM trainers WHERE discord_id=? AND primaryac=1', (ctx.message.author.id,)).fetchone()
		else:
			try:
				t_pogo, t_xp, t_time, t_goalD, t_goalT = c.execute('SELECT pogo_name, total_xp, last_updated, goalDaily, goalTotal FROM trainers WHERE discord_id=? AND primaryac=0 AND pogo_name=?', (ctx.message.author.id,profile)).fetchone()
			except TypeError:
				return await self.bot.say("`TypeError` - No secondary account called {} belonging to <@{}> found.".format(profile,ctx.message.author.id))
		if t_xp:
			if int(t_xp) > int(xp):
				await self.bot.say("Error: You're trying to set an your XP to a lower value. Please make sure you're using your Total XP at the bottom of your profile.")
				return
			c.execute("INSERT INTO xp_history (trainer, xp, time) VALUES (?,?,?)", (t_pogo, t_xp, t_time))
			c.execute("UPDATE trainers SET total_xp=?, last_updated=? WHERE pogo_name=?", (int(xp), int(time.time()), t_pogo))
			trnr.commit()
			await self.bot.send_message(discord.Object(parentLogsChannel), "Updated {}'s XP to {}".format(t_pogo, xp))
			await asyncio.sleep(1)
			if t_goalD and t_goalT:
				await self.profileCard(t_pogo, ctx.message.channel, goal_daily=True, goal_total=True)
				if t_goalT<xp:
					c.execute("UPDATE trainers SET goalTotal=? WHERE discord_id=?", (None, ctx.message.author.id,))
					await self.bot.say("Congratulations, you've reached your goal.")
			elif t_goalD:
				await self.profileCard(t_pogo, ctx.message.channel, goal_daily=True)
			elif t_goalT:
				await self.profileCard(t_pogo, ctx.message.channel, goal_total=True)
				if t_goalT<=xp:
					c.execute("UPDATE trainers SET goalTotal=None WHERE discord_id=?", (ctx.message.author.id,))
					await self.bot.say("🎉 Congratulations, you've reached your goal. 🎉")
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
			await self.bot.send_message(discord.Object(parentLogsChannel), "Set {}'s name to {}".format(t_pogo, xp))
			await self.profileCard(t_pogo, ctx.message.channel)
		else:
			await self.bot.say(NOT_IN_SYSTEM)
			return

	@commands.command(pass_context=True)
	async def setgoaldaily(self, ctx, goal: int): #setgoal - a command used for to set your daily goal on your profile
		await self.bot.send_typing(ctx.message.channel)
		t_pogo, = c.execute('SELECT pogo_name FROM trainers WHERE discord_id=?', (ctx.message.author.id,)).fetchone()
		if t_pogo:
			c.execute("UPDATE trainers SET goalDaily=? WHERE discord_id=?", (goal, ctx.message.author.id))
			trnr.commit()
			await self.bot.say("Your daily XP goal is set to {}.".format(goal))
			await self.bot.send_message(discord.Object(parentLogsChannel), "Set {}'s daily goal to {}".format(t_pogo, goal))
		else:
			await self.bot.say(NOT_IN_SYSTEM)
			return

	@commands.command(pass_context=True)
	async def setgoaltotal(self, ctx, goal: int): #setgoal - a command used for to set your daily goal on your profile
		await self.bot.send_typing(ctx.message.channel)
		t_pogo, t_xp = c.execute('SELECT pogo_name, total_xp FROM trainers WHERE discord_id=?', (ctx.message.author.id,)).fetchone()
		if t_pogo:
			if goal>t_xp:
				c.execute("UPDATE trainers SET goalTotal=? WHERE discord_id=?", (goal, ctx.message.author.id))
				trnr.commit()
				await self.bot.say("Your total XP goal is set to {}.".format(goal))
				await self.bot.send_message(discord.Object(parentLogsChannel), "Set {}'s total goal to {}".format(t_pogo, goal))
			else:
				await self.bot.say("Your goal is lower than your current XP.")
		else:
			await self.bot.say(NOT_IN_SYSTEM)
			return

#Mod-commands

	@commands.command(pass_context=True)
	@checks.mod_or_permissions(assign_roles=True)
	async def spoofer(self, ctx, mention):
		await self.bot.send_typing(ctx.message.channel)
		try:
			mbr = ctx.message.mentions[0].id
		except:
			mbr = None
		try:
			t_pogo, t_cheat = c.execute('SELECT pogo_name, spoofer FROM trainers WHERE discord_id=? OR pogo_name=?', (mbr,mention)).fetchone()
		except:
			await self.bot.say("Error!")
		else:
			if t_cheat==1:
				try:
					c.execute('UPDATE trainers SET spoofer=? WHERE pogo_name=?', (0, t_pogo))
				except sqlite3.IntegrityError:
					await self.bot.say("Error!")
				else:
					await self.bot.say("Success! You've unset the `spoofer` flag on {}!".format(t_pogo))
					await self.bot.send_message(discord.Object(parentLogsChannel), "Unset `spoofer` flag on {}!".format(t_pogo))
					trnr.commit()
			else:
				try:
					c.execute('UPDATE trainers SET spoofer=?, spoofed=? WHERE pogo_name=?', (1,1, t_pogo))
				except sqlite3.IntegrityError:
					await self.bot.say("Error!")
				else:
					await self.bot.say("Success! You've set the `spoofer` flag on {}!".format(t_pogo))
					await self.bot.send_message(discord.Object(parentLogsChannel), "Set `spoofer` flag on {}!".format(t_pogo))
					trnr.commit()
			await self.profileCard(t_pogo, ctx.message.channel)

	@commands.command(pass_context=True)
	@checks.mod_or_permissions(assign_roles=True)
	async def newprofile(self, ctx, mention, name: str, team: str, level: int, xp: int, opt: str=''): #adding a user to the database
		await self.bot.send_typing(ctx.message.channel)
		mbr = ctx.message.mentions[0]
		if opt.title() == 'Spoofer':
			await self.addProfile(mbr.id, name, team.title(), level, xp, cheat=1)
		else:
			await self.addProfile(mbr.id, name, team.title(), level, xp)
		await self.profileCard(name, ctx.message.channel)
		
	@commands.command(pass_context=True)
	@checks.mod_or_permissions(assign_roles=True)
	async def addsecondary(self, ctx, mention, name: str, team: str, level: int, xp: int, opt: str=''): #adding a user to the database
		await self.bot.send_typing(ctx.message.channel)
		mbr = ctx.message.mentions[0]
		if opt.title() == 'Spoofer':
			await self.addProfile(mbr.id, name, team.title(), level, xp, cheat=1, primary=False)
		else:
			await self.addProfile(mbr.id, name, team.title(), level, xp, primary=False)
		await self.profileCard(name, ctx.message.channel)
		
	@commands.command(pass_context=True)
	@checks.mod_or_permissions(assign_roles=True)
	async def approve(self, ctx, mention, name: str, team: str, level: int, xp: int, opt: str=''): #applies the correct roles to a user and adds the user to the database
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
				await self.bot.send_message(discord.Object(parentLogsChannel), "<@{}> added to {}!".format(mbr.id, ctx.message.server.name))
				if opt.title() == 'Spoofer':
					await self.addProfile(mbr.id, name, team.title(), level, xp, cheat=1)
				else:
					await self.addProfile(mbr.id, name, team.title(), level, xp)
				await self.profileCard(name, ctx.message.channel) 

def setup(bot):
    bot.add_cog(Profiles(bot))
