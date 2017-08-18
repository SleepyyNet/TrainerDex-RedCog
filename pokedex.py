import discord
from discord.ext import commands
from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search, DocType, Date, Integer, Keyword, Text, Float, Boolean
from elasticsearch_dsl.connections import connections

connections.create_connection(hosts=['localhost'])

class Pokemon(DocType):
    name = Text(analyzer='snowball', fields={'raw': Keyword()})
    hp_ratio = Integer()
    attack_ratio = Integer()
    defense_ratio = Integer()
    min_cp_cap = Integer()
    max_cp_cap = Integer()
    legendary = Boolean()
    basic_attack = Text()
    quick_dps = Float()
    charge_attack = Text()
    charge_dps = Float()
    offensive_percent = Float()
    duel_percent = Float()
    defensive_percent = Float()
    full_cycle_dps = Float()

    class Meta:
        index = 'pokemon'

class Pokedex:
    """My custom cog that does stuff!"""

    def __init__(self, bot):
        self.bot = bot
        self.client = Elasticsearch()

    @commands.command()
    async def pokedex(self, pokemon):
        s = Search(using=self.client, index="pokemon").query("match", name={'query': pokemon, 'fuzziness': 2})
        response = s.execute()
        if response.hits.total == 0:
            await self.bot.say("I couldn't find that pokemon")
            return
        hit = response[0]
        embed=discord.Embed(title=hit.name, url="http://bulbapedia.bulbagarden.net/wiki/{}".format(hit.name))
        embed.set_thumbnail(url="http://serebii.net/pokemongo/pokemon/{:03d}.png".format(int(hit.meta.id)))
        embed.add_field(name='Base Attack Stat', value=hit.attack_ratio)
        embed.add_field(name='Base Defence Stat', value=hit.defense_ratio)
        embed.add_field(name='Base HP Stat', value=hit.hp_ratio)
        embed.add_field(name='Min CP', value=hit.min_cp_cap)
        embed.add_field(name='Max CP', value=hit.max_cp_cap)
        embed.add_field(name='Best Offensive Moveset', value=hit.basic_attack+' / '+hit.charge_attack)
        #embed.add_field(name='Basic Atk', value=hit.basic_attack)
        #embed.add_field(name='Quick DPS', value=hit.quick_dps)
        #embed.add_field(name='Charge Atk', value=hit.charge_attack)
        #embed.add_field(name='Charge DPS', value=hit.charge_dps)
        #embed.add_field(name='Offensive %', value=hit.offensive_percent)
        #embed.add_field(name='Duel %', value=hit.duel_percent)
        #embed.add_field(name='Defensive %', value=hit.defensive_percent)
        #embed.add_field(name='Full Cycle DPS', value=hit.full_cycle_dps)
        embed.set_footer(text='Min and Max CP are for level 40. Best Offensive Moveset may be incorrect.')
        await self.bot.say(embed=embed)

def setup(bot):
    bot.add_cog(Pokedex(bot))

