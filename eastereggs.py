import random
import discord
from discord.ext import commands


class EasterEggs:
	"""Easter Eggs"""
	
	def __init__(self, bot):
		self.bot = bot

	def get_display_name(self, member):
		return member.nick if member.nick else str(member.name)

	@commands.command(pass_context=True)
	async def excuse(self, ctx):
		excuses = ['{} is finding socks.', '{} is only '+str(random.randint(1,120))+' minutes away.', 'A zebra is running down the road and this is holding {} up.', '{}’s cat got stuck in the toilet.', "It's raining.", 'Pizzzaaaaaaa 🍕🍍', '{} just put a casserole in the oven.', "{}'s plastic surgery needed some 'tweaking' to get it just right.", '{} accidentally got on a plane. ✈️', '{} laH wej yIv.']
		await self.bot.send_typing(ctx.message.channel)
		await self.bot.say(random.choice(excuses).format(self.get_display_name(ctx.message.author)))
		
def setup(bot):
    bot.add_cog(EasterEggs(bot))