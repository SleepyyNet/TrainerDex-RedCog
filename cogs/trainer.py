import pytz
import discord
import sqlite3
from cogs.utils import checks
from discord.ext import commands
import time
import datetime

tz = pytz.timezone('Europe/London')
trnr = sqlite3.connect('trainers.db')
c = trnr.cursor()

class Profiles:
	"""Trainer profile system"""
	
	def __init__(self, bot):
		self.bot = bot
	
	@commands.command(pass_context=True)
	async def whois(self, ctx, name):
		self.bot.send_typing(ctx.message.channel)
		trn = c.execute('SELECT pogo_name, total_xp, last_updated, team, discord_id, real_name FROM trainers WHERE pogo_name=?', (name,)).fetchone()
		if trn:
			trnrlvl = c.execute('SELECT level, min_xp FROM levels WHERE min_xp<?', (trn[1],)).fetchall()[-1]
			team = c.execute('SELECT name, leader, role, colour, logo FROM teams WHERE id=?', (trn[3],)).fetchone()
			embed=discord.Embed(title=trn[0], timestamp=(datetime.datetime.fromtimestamp(trn[2], tz)), color=team[3])
	#		user = discord.utils.get(server.members, id=trn[4]) # <<<<< Lines causing issue
			if trn[5]:
				embed.add_field(name='Name', value=trn[5])
			else:
				embed.add_field(name='Name', value='Undisclosed')
			embed.add_field(name='Team', value=team[0])
			embed.add_field(name='Level', value=trnrlvl[0])
			embed.add_field(name='XP', value=trn[1]-trnrlvl[1])
			embed.set_footer(text="Total XP: "+str(trn[1]))
	#		embed.set_thumbnail(url=user.avatar_url) # <<<<< Lines causing issue
			embed.set_thumbnail(url=team[4])
			await self.bot.say(embed=embed)
		else:
			await self.bot.send_message(ctx.message.channel, "Unfortunatly, I couldn't find {} in the database. Are you sure you spelt their name right?".format(name))

	@commands.command(pass_context=True)
	@checks.mod_or_permissions(assign_roles=True)
	async def newprofile(self, ctx, mention, name, team, level, xp):
		self.bot.send_typing(ctx.message.channel)
		tteam = team.title()
		if not (tteam in ['Valor','Mystic','Instinct', 'Teamless']):
			await self.bot.send_message(ctx.message.channel, "This isn't a valid team. Please ensure that you have used the command correctly.")
			return
		lvl = c.execute('SELECT level, min_xp FROM levels WHERE level=?', (level,)).fetchone()
		teami = c.execute('SELECT id FROM teams WHERE name=?', (tteam,)).fetchone()
		try:
			c.execute("INSERT INTO trainers (pogo_name, discord_id, total_xp, last_updated, team) VALUES (?,?,?,?,?)",(name, ctx.message.mentions[0].id, lvl[1]+int(xp), int(time.time()), teami[0]))
		except sqlite3.IntegrityError:
			await self.bot.send_message(ctx.message.channel, "Happy Error: Profile already exists. Just use the `updatexp`command :slightsmile:")
		else:
			trnr.commit()
			await ctx.invoke(self.whois, name=name)
		
	@commands.command(pass_context=True)
	@checks.mod_or_permissions(assign_roles=True)
	async def approve(self, ctx, mention, name, team, level, xp):
		self.bot.send_typing(ctx.message.channel)
		tteam = team.title()
		if not (tteam in ['Valor','Mystic','Instinct', 'Teamless']):
			await self.bot.send_message(ctx.message.channel, "This isn't a valid team. Please ensure that you have used the command correctly.")
			return
		mbr = ctx.message.mentions[0]
		try:
			await self.bot.change_nickname(mbr, name)
		except discord.errors.Forbidden:
			await self.bot.send_message(ctx.message.channel, "Error: I don't have permission to change nicknames. Aborted!")
		else:
			trnrrole = discord.utils.get(ctx.message.server.roles, name='Trainer')
			tmrole = discord.utils.get(ctx.message.server.roles, name=tteam)
			try:
				await self.bot.add_roles(mbr, trnrrole)
				if (tteam in ['Valor','Mystic','Instinct']):
					await self.bot.add_roles(mbr, tmrole)
			except discord.errors.Forbidden:
				await self.bot.send_message(ctx.message.channel, "Error: I don't have permission to set roles. Aborted!")
			else:
				await self.bot.send_message(ctx.message.channel, "{} has been approved.".format(name))
				await ctx.invoke(self.newprofile, mention=mention, name=name, team=team, level=level, xp=xp)
	
	@commands.command(pass_context=True)
	async def updatexp(self, ctx, xp):
		self.bot.send_typing(ctx.message.channel)
		oldxp = c.execute('SELECT pogo_name, total_xp, last_updated FROM trainers WHERE discord_id=?', (ctx.message.author.id,)).fetchone()
		if oldxp:
			if int(oldxp[1]) > int(xp):
				await self.bot.send_message(ctx.message.channel, "Error: Specified XP higher than currently set XP. Please use the total xp at the bottom of your profile.")
				return
			c.execute("INSERT INTO xp_history (trainer, xp, time) VALUES (?,?,?)", (oldxp[0], oldxp[1], oldxp[2]))
			c.execute("UPDATE trainers SET total_xp=?, last_updated=? WHERE discord_id=?", (int(xp), int(time.time()), ctx.message.author.id))
			trnr.commit()
			await ctx.invoke(self.whois, name=oldxp[0])
		else:
			await self.bot.send_message(ctx.message.channel, "Please ask a member of staff to add your profile to the system.")
			return
		
def setup(bot):
    bot.add_cog(Profiles(bot))