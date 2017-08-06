import pytz
import discord
import sqlite3
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
	
	@commands.command()
	async def whois(self, name):
		trn = c.execute('SELECT pogo_name, total_xp, last_updated, team, discord_id, real_name FROM trainers WHERE pogo_name=?', (name,)).fetchone()
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

	@commands.command(pass_context=True)
	async def newprofile(self, ctx, mention, name, team, level, xp):
		lvl = c.execute('SELECT level, min_xp FROM levels WHERE level=?', (level,)).fetchone()
		teami = c.execute('SELECT id FROM teams WHERE name=?', (team,)).fetchone()
		c.execute("INSERT INTO trainers (pogo_name, discord_id, total_xp, last_updated, team) VALUES ('{pgnm}','{did}','{txp}','{t}','{tm}')".\
				  format(pgnm=name, did=ctx.message.mentions[0].id, txp=lvl[1]+int(xp), t=int(time.time()), tm=teami[0]))
		trnr.commit()
		await ctx.invoke(self.whois, name=name)
		
#	@commands.command(pass_context=True)
#	async def approve(self, ctx, mention, name, team, level, xp):
#		mbr = ctx.message.mentions[0]
#		await self.bot.change_nickname(mbr, name)
#		trnrrole = discord.utils.get(message.server.roles, name='Trainer')
#		tmrole = discord.utils.get(message.server.roles, name=team)
#		await self.bot.add_roles(mbr, trnrrole, tmrole)
#		await ctx.invoke(self.newprofile, mention=mention, name=name, team=team, level=level, xp=xp)
		
def setup(bot):
    bot.add_cog(Profiles(bot))