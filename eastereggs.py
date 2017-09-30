import random
import discord
from discord.ext import commands


class EasterEggs:
	"""Easter Eggs"""
	
	def __init__(self, bot):
		self.bot = bot
	
	@commands.command(pass_context=True)
	async def excuse(self, ctx):
		excuses = [
			'{} is finding socks.', 
			'{} is only '+str(random.randint(1,120))+' minutes away.', 
			'{}’s cat got stuck in the toilet.', 
			'Pizzzaaaaaaa 🍕🍍', 
			'{} just put a casserole in the oven.', 
			'{} accidentally got on a plane. ✈️', 
		]
		await self.bot.send_typing(ctx.message.channel)
		await self.bot.say(random.choice(excuses).format(ctx.message.author.display_name))
		
def setup(bot):
    bot.add_cog(EasterEggs(bot))