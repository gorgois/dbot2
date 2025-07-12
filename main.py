import discord
from discord.ext import commands, tasks
from discord.commands import SlashCommandGroup
import openai
import random
import json
import os
import asyncio
from keep_alive import keep_alive

# Load environment variables
TOKEN = os.getenv("DISCORD_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai.api_key = OPENAI_API_KEY

# Set up intents
intents = discord.Intents.default()
intents.message_content = True
intents.messages = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# AI Settings File
AI_SETTINGS_FILE = "ai_settings.json"

def load_ai_settings():
    try:
        with open(AI_SETTINGS_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_ai_settings(data):
    with open(AI_SETTINGS_FILE, "w") as f:
        json.dump(data, f, indent=4)

ai_enabled = load_ai_settings()

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user.name}")
    auto_ai_loop.start()

# AI Slash Commands Group
ai = SlashCommandGroup("ai", "AI control commands")

@ai.command(name="enable")
async def enable_ai(ctx):
    ai_enabled[str(ctx.guild.id)] = True
    save_ai_settings(ai_enabled)
    await ctx.respond("✅ AI features have been enabled in this server.")

@ai.command(name="disable")
async def disable_ai(ctx):
    ai_enabled[str(ctx.guild.id)] = False
    save_ai_settings(ai_enabled)
    await ctx.respond("❌ AI features have been disabled in this server.")

@ai.command(name="status")
async def status_ai(ctx):
    status = ai_enabled.get(str(ctx.guild.id), False)
    await ctx.respond(f"🔍 AI is {'enabled' if status else 'disabled'} in this server.")

@ai.command(name="meme")
async def meme_ai(ctx):
    await ctx.defer()

    if not ai_enabled.get(str(ctx.guild.id), False):
        await ctx.respond("❌ AI is not enabled in this server.")
        return

    messages = []
    async for msg in ctx.channel.history(limit=20):
        if msg.author != bot.user:
            messages.append(f"{msg.author.display_name}: {msg.content}")

    prompt = "Create a funny Discord meme idea based on this chat:\n" + "\n".join(messages[-10:])

    try:
        dalle_response = openai.Image.create(prompt=prompt, n=1, size="512x512")
        image_url = dalle_response['data'][0]['url']
        embed = discord.Embed(title="🤣 Meme Generated", color=discord.Color.green())
        embed.set_image(url=image_url)
        await ctx.respond(embed=embed)
    except Exception as e:
        await ctx.respond(f"⚠️ Failed to generate meme: {e}")

@ai.command(name="ask")
async def ask_ai(ctx, question: str):
    await ctx.defer()

    if not ai_enabled.get(str(ctx.guild.id), False):
        await ctx.respond("❌ AI is not enabled in this server.")
        return

    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": question}]
        )
        await ctx.respond(response.choices[0].message.content)
    except Exception as e:
        await ctx.respond(f"⚠️ Failed to get a reply: {e}")

@ai.command(name="generate")
async def generate_ai(ctx, idea: str):
    await ctx.defer()

    if not ai_enabled.get(str(ctx.guild.id), False):
        await ctx.respond("❌ AI is not enabled in this server.")
        return

    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": f"Write something creative: {idea}"}]
        )
        await ctx.respond(response.choices[0].message.content)
    except Exception as e:
        await ctx.respond(f"⚠️ Failed to generate content: {e}")

bot.add_application_command(ai)

# Periodic AI auto-reply
@tasks.loop(minutes=2)
async def auto_ai_loop():
    for guild in bot.guilds:
        if not ai_enabled.get(str(guild.id), False):
            continue

        for channel in guild.text_channels:
            try:
                messages = []
                async for msg in channel.history(limit=20):
                    if msg.author != bot.user:
                        messages.append(f"{msg.author.display_name}: {msg.content}")

                if not messages:
                    continue

                prompt = "Reply humorously to this recent Discord chat:\n" + "\n".join(messages[-5:])
                response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": prompt}]
                )
                reply = response.choices[0].message.content
                await channel.send(reply)
                await asyncio.sleep(2)

            except Exception:
                continue

# Start server and bot
keep_alive()
bot.run(TOKEN)