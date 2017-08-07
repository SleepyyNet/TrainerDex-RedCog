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
		tteam = team.title()
		if not (tteam in ['Valor','Mystic','Instinct']):
			await self.bot.send_message(ctx.message.channel, "This isn't a valid team. Please ensure that you have used the command correctly.")
			await self.bot.send_message(ctx.message.channel, "Usage: `.newprofile @mention pogoname team levelasdigits xpasdigits")
			return
		lvl = c.execute('SELECT level, min_xp FROM levels WHERE level=?', (level,)).fetchone()
		teami = c.execute('SELECT id FROM teams WHERE name=?', (tteam,)).fetchone()
		c.execute("INSERT INTO trainers (pogo_name, discord_id, total_xp, last_updated, team) VALUES ('{pgnm}','{did}','{txp}','{t}','{tm}')".\
				  format(pgnm=name, did=ctx.message.mentions[0].id, txp=lvl[1]+int(xp), t=int(time.time()), tm=teami[0]))
		trnr.commit()
		await ctx.invoke(self.whois, name=name)
		
	@commands.command(pass_context=True)
	async def approve(self, ctx, mention, name, team, level, xp):
		await self.bot.send_typing(ctx.message.channel)
		tteam = team.title()
		if not (tteam in ['Valor','Mystic','Instinct']):
			await self.bot.send_message(ctx.message.channel, "This isn't a valid team. Please ensure that you have used the command correctly.")
			await self.bot.send_message(ctx.message.channel, "Usage: `.approve @mention pogoname team levelasdigits xpasdigits")
			return
		mbr = ctx.message.mentions[0] # mbr = the mentioned user
		try:
			await self.bot.change_nickname(mbr, name) #change the nickname of the mentioned user
		except discord.errors.Forbidden:
			await self.bot.send_message(ctx.message.channel, "Fuck you, cunt. I can't change nicknames. I'm not the fucking Name Rater")
		else:
			trnrrole = discord.utils.get(ctx.message.server.roles, name='Trainer') #search for a role on the server named Trainer
			tmrole = discord.utils.get(ctx.message.server.roles, name=tteam) #search for a role on the server with a name that matches the team name
			try:
				await self.bot.add_roles(mbr, trnrrole, tmrole) #apply those two roles
			except discord.errors.Forbidden:
				await self.bot.send_message(ctx.message.channel, "Fuck you, cunt. I can't set roles. Go ask a fucking cunt at subway, they're great with roles.")
			else:
				await self.bot.send_message(ctx.message.channel, "Fuck me, I did something right.")
				await ctx.invoke(self.newprofile, mention=mention, name=name, team=team, level=level, xp=xp) #runs newprofile command
		
def setup(bot):
    bot.add_cog(Profiles(bot))