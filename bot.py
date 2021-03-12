import os
import discord
from discord.ext import commands
import dotenv
import json
import random
import requests
from bs4 import BeautifulSoup

dotenv.load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD = os.getenv('DISCORD_GUILD')
LIST_PATH = os.getenv('LIST_PATH')
THUMBS_UP = '\U0001F44D'
URL = 'https://www.liquipedia.net/starcraft2/'
UNDESIRED_TAGS = ['Type', 'Description', 'Hotkey']


def error_msg(cmd, descr):
    msg = 'Error: `' + cmd + '`\n' \
          '```' + descr + '```'
    return msg


if os.path.exists(LIST_PATH):
    with open(LIST_PATH) as f:
        style_list = json.load(f)
else:
    style_list = {}

bot = commands.Bot(command_prefix='!')


@bot.event
async def on_ready():
    guild = discord.utils.get(bot.guilds, name=GUILD)
    print(
        f'{bot.user} is connected to the following guild: {guild.name}'
    )


@bot.command(name='about', help='Provides info on what the bot does')
async def about(ctx):
    await ctx.send('This bot provides a way to randomize Starcraft 2 play styles, according to a user-defined list of '
                   'styles and weights (probabilities). Type \'!help\' for a list of commands.')


@bot.command(name='add', help='Adds a new play style along with its weight to the list')
async def add(ctx, style, weight: int):
    # Handle the case where the weight is not a natural number
    if weight <= 0:
        await ctx.send(error_msg('!add <style> <weight>',
                                 'style: name of play style\n'
                                 'weight: positive integer specifying weight of the style'))
        return

    # Update style list and .json file
    style_list[style] = weight
    with open(LIST_PATH, 'w') as f:
        json.dump(style_list, f)
    await ctx.message.add_reaction(THUMBS_UP)


@bot.command(name='delete', help='Deletes a play style from the list')
async def delete(ctx, style):
    # Handle the case where the style is not in the dictionary
    if style not in style_list.keys():
        await ctx.send(error_msg('!delete <style>',
                                 'style: name of play style in !list\n'))
        return

    # Update style list and .json file
    weight = style_list[style]
    del style_list[style]
    with open(LIST_PATH, 'w') as f:
        json.dump(style_list, f)
    await ctx.message.add_reaction(THUMBS_UP)


@bot.command(name='edit', help='Edits a current play style\'s weight')
async def edit(ctx, style, weight: int):
    # Handle argument errors
    if style not in style_list.keys():  # Style not in list
        await ctx.send(error_msg('!edit <style> <weight>',
                                 '\'style\' needs to be an existing entry in !list'))
        return
    elif int(weight) <= 0:  # Weight not a natural number
        await ctx.send(error_msg('!edit <style> <weight>',
                                 'style: name of existing play style\n'
                                 'weight: positive integer specifying weight of the style'))
        return

    # Update style list and .json file
    old_weight = style_list[style]
    style_list[style] = weight
    with open(LIST_PATH, 'w') as f:
        json.dump(style_list, f)
    await ctx.message.add_reaction(THUMBS_UP)


@bot.command(name='list', help='Lists all play styles, their respective weights, and probabilities')
async def list_styles(ctx):
    tot_weight = sum(style_list.values())
    print_str = '**style, weight, probability**\n'
    for key in style_list.keys():
        print_str += '{0}, {1}, {2:.2f}\n'.format(key, style_list[key], style_list[key]/tot_weight)
    await ctx.send(print_str[:-1])
    await ctx.message.add_reaction(THUMBS_UP)


@bot.command(name='roll', help='Rolls a new play style')
async def roll(ctx):
    rand_roll = random.randrange(sum(style_list.values()))
    weight_sum = 0
    for key in style_list.keys():
        weight_sum += style_list[key]
        if rand_roll < weight_sum:
            break
    await ctx.send(key)
    await ctx.message.add_reaction(THUMBS_UP)


@bot.command(name='scale', help='Scales the weights of the styles in the list')
async def scale(ctx, factor: float):
    # Handle the case where the weight is not above 0
    if factor <= 0:
        await ctx.send(error_msg('!scale <style> <weight>',
                                 'factor: name of play style'))
        return

    # Scale all weights in the list
    for key in style_list.keys():
        style_list[key] = int(round((style_list[key] * factor)))

    # Update .json file
    with open(LIST_PATH, 'w') as f:
        json.dump(style_list, f)
    await ctx.message.add_reaction(THUMBS_UP)


@bot.command(name='stop', help='Stops the bot')
async def stop(ctx):
    await ctx.send('Bot logging off...')
    await ctx.message.add_reaction(THUMBS_UP)
    await bot.logout()


@bot.command(name='info', help='Searches Liquipedia for info on the search term')
async def info(ctx, search):
    page = requests.get(URL + search)
    soup = BeautifulSoup(page.content, 'html.parser')
    infobox_tags = soup.find_all('div', class_='infobox-cell-2 infobox-description')

    if page.status_code == 404:
        await ctx.send('No article found.')
        return

    info_str = 'Accessed: ' + '<' + URL + search + '>\n-----\n'
    for tag in infobox_tags:
        if tag.text[:-1] not in UNDESIRED_TAGS:
            info_str += '**' + tag.text.replace(':', ' ') + '**\n'
            info_str += tag.next_sibling.next_sibling.get_text(separator=' ') + '\n'
    await ctx.send(info_str)


@bot.event
async def on_command_error(ctx, error):
    if ctx.command.name == 'add':
        await ctx.send(error_msg('!add <style> <weight>',
                                 'style: name of play style\n'
                                 'weight: positive integer specifying weight of the style'))
    elif ctx.command.name == 'edit':
        await ctx.send(error_msg('!edit <style> <weight>',
                                 'style: name of existing play style\n'
                                 'weight: positive integer specifying weight of the style'))

bot.run(TOKEN)
