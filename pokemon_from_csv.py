import csv
from elasticsearch_dsl.connections import connections
from elasticsearch_dsl import DocType, Date, Integer, Keyword, Text, Float, Boolean
# Define a default Elasticsearch client
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

# https://docs.google.com/spreadsheets/d/1vv5XXzdepc-xq1FK-q3YtYWneYAUgw8w5yNt_gf8sNw/edit#gid=1638340170

with open('Pokemon DPS Rankings w_ TM Movesets - Species Data.csv', 'r') as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        Pokemon(
            meta={'id': row['#']},
            name=row['Name'],
            hp_ratio=row['HP Ratio'],
            attack_ratio=row['Attack Ratio'],
            defense_ratio=row['Defense Ratio'],
            min_cp_cap=row['Min CP Cap'],
            max_cp_cap=row['Max CP Cap']
        ).save()

with open('Pokemon DPS Rankings w_ TM Movesets - Rankings.csv', 'r') as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        pokemon = Pokemon.get(id=row['PKMN #'])
        pokemon.legendary = True if row['Legend?'] == 'y' else False
        pokemon.basic_attack = row['Basic Atk']
        pokemon.quick_dps = row['Quick DPS']
        pokemon.charge_attack = row['Charge Atk']
        pokemon.charge_dps = row['Charge DPS']
        pokemon.offensive_percent = row['Offensive %']
        pokemon.duel_percent = row['Duel %']
        pokemon.defensive_percent = row['Defensive %']
        pokemon.full_cycle_dps = row['Full Cycle DPS']
        pokemon.save()
