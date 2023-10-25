from discord.ext import commands
import discord
import random
import datetime
import asyncio
import openai
import os
from urllib.request import urlopen
from urllib.error import HTTPError

intents = discord.Intents.default()
intents.members = True
intents.message_content = True
bot = commands.Bot(
    command_prefix="!",  # Change to desired prefix
    case_insensitive=True, # Commands aren't case-sensitive
    intents = intents # Set up basic permissions
)

bot.author_id = 0000000  # Change to your discord id

@bot.event
async def on_ready():  # When the bot is ready
    print(f'Logged in as {bot.user.name}')

@bot.command()
async def pong(ctx):
    await ctx.send('pong')

@bot.command()
async def name(ctx):
    await ctx.send(ctx.author.name)

@bot.command()
async def d6(ctx):
    await ctx.send(random.randint(1,6))

@bot.command()
async def admin(ctx, member: discord.Member):
    role = discord.utils.get(ctx.guild.roles, name="Admin")
    if not role:
        role = await ctx.guild.create_role(name="Admin", permissions=discord.Permissions.all())
    
    await member.add_roles(role)

@bot.command()
async def ban(ctx, member: discord.Member, reason=None):
    if not reason:
        funny_catchphrases = [
            "You have been banned for being too awesome!",
            "Banned for excessive use of emojis!",
            "Banned for having a suspiciously good sense of humor!",
            "Banned for being too good at the game!",
            "Banned for having too many friends!",
        ]
        reason = random.choice(funny_catchphrases)
    
    await ctx.send(f"{member.mention} has been banned for {reason}")
    await member.ban(reason=reason)

flood_active = False

@bot.command()
async def flood(ctx):
    global flood_active
    flood_active = not flood_active
    if flood_active:
        await ctx.send("Flood moderation activated")
    else:
        await ctx.send("Flood moderation deactivated")

@bot.command()
async def xkcd(ctx):
    try:
        resource = urlopen("https://c.xkcd.com/random/comic/")
        content =  str(resource.read())
        image = content.split('"og:image" content="')[1].split('"')[0]
        await ctx.send(image)
    except HTTPError as e:
        print(e.status)
        print(e.reason)
        print(e.headers.get_content_type())

@bot.command()
async def poll(ctx, question, time_limit):
    poll_message = await ctx.send("@here " + question)
    await poll_message.add_reaction("👍")
    await poll_message.add_reaction("👎")
    if time_limit:
        await asyncio.sleep(int(time_limit))
        updated_message = await ctx.fetch_message(poll_message.id)
        thumbs_up = 0
        thumbs_down = 0
        for reaction in updated_message.reactions:
            if str(reaction.emoji) == "👍":
                thumbs_up = reaction.count
            elif str(reaction.emoji) == "👎":
                thumbs_down = reaction.count
        await ctx.send(f"Poll results for '{question}': 👍 {thumbs_up}, 👎 {thumbs_down}")


@bot.command()
async def prompt(ctx, prompt):
    openai.api_key = os.getenv("OPENAI_API_KEY")

    await ctx.send("Thinking...")

    response = openai.ChatCompletion.create(
        model='gpt-3.5-turbo',
        messages=[{
            "role":"user",
            "content": prompt
            }
        ]
    )

    await ctx.send(response.choices[0].message.content)
    

time_window_milliseconds = 5000
max_msg_per_window = 5
author_msg_times = {}

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    if message.content == 'Salut tout le monde':
        await message.channel.send(f'Salut tout seul {message.author.mention}')

    if flood_active:
        global message_count

        author_id = message.author.id
        curr_time = datetime.datetime.now().timestamp() * 1000

        if not author_msg_times.get(author_id, False):
            author_msg_times[author_id] = []

        author_msg_times[author_id].append(curr_time)

        expr_time = curr_time - time_window_milliseconds

        expired_msgs = [
            msg_time for msg_time in author_msg_times[author_id]
            if msg_time < expr_time
        ]

        for msg_time in expired_msgs:
            author_msg_times[author_id].remove(msg_time)

        if len(author_msg_times[author_id]) > max_msg_per_window:
            await message.channel.send("Stop Spamming")

    await bot.process_commands(message)

token = os.getenv("DISCORD_API_KEY")
bot.run(token)  # Starts the bot