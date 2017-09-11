# Trainer Profile System for Red
[![BCH compliance](https://bettercodehub.com/edge/badge/PokemonGoEastKent/red-trainergo?branch=master)](https://bettercodehub.com/)

A simple profile system for keeping track of Pokemon Go XP and Team. Can easily be repurposed for another game. Doesn't log into the game and depends on user input of honest data.

## Requirements
* pytz
* ratelimit
* discord
* [red - duh](https://github.com/Cog-Creators/Red-DiscordBot)
* TrainerDex.py - it's in `dependencies` - create a symlink from `[red]/lib/TrainerDex.py` to `[repo]/dependencies/trainerdex/TrainerDex.py`

## Setup
* Edit `config.py`, put your token in and move to `[red]/data/TrainerDex/config.py`