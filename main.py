import discord
from discord.ext import commands, tasks
import openai
import json
import random
import os
import aiohttp
from keep_alive import keep_alive

# Load API keys from Render environment variables
openai.api_key = os.getenv("OPENAI_API_KEY")
DISCORD_TOKEN = os.getenv("DISCORD_BOT_TOKEN")

intents = discord.Intents.default()
intents.message_content = True
intents.messages = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# === Load/Save server AI toggle ===
def load_enabled_servers():
    try:
        with open("enabled_servers.json", "r") as f:
            return json.load(f).get("enabled", [])
    except FileNotFoundError:
        return []

def save_enabled_servers(server_ids):
    with open("enabled_servers.json", "w") as f:
        json.dump({"enabled": server_ids}, f, indent=4)

# === Bot Ready ===
@bot.event
async def on_ready():
    print(f"✅ {bot.user} is online!")
    auto_responder.start()

# === /enable-ai command ===
@bot.slash_command(name="enable-ai", description="Enable AI features in this server")
@commands.has_permissions(manage_guild=True)
async def enable_ai(ctx):
    enabled = load_enabled_servers()
    if str(ctx.guild.id) not in enabled:
        enabled.append(str(ctx.guild.id))
        save_enabled_servers(enabled)
        await ctx.respond("✅ AI features enabled!")
    else:
        await ctx.respond("⚠️ AI is already enabled.")

# === /disable-ai command ===
@bot.slash_command(name="disable-ai", description="Disable AI features in this server")
@commands.has_permissions(manage_guild=True)
async def disable_ai(ctx):
    enabled = load_enabled_servers()
    if str(ctx.guild.id) in enabled:
        enabled.remove(str(ctx.guild.id))
        save_enabled_servers(enabled)
        await ctx.respond("❌ AI features disabled.")
    else:
        await ctx.respond("⚠️ AI is already disabled.")

# === /meme command (AI-generated image) ===
@bot.slash_command(name="meme", description="Generate a meme image from recent messages")
async def meme(ctx):
    if str(ctx.guild.id) not in load_enabled_servers():
        return await ctx.respond("⚠️ AI is disabled in this server.")

    messages = [m async for m in ctx.channel.history(limit=10)]
    recent = [m.content for m in messages if not m.author.bot]
    if not recent:
        return await ctx.respond("No usable messages found.")

    prompt = "Create a funny meme image idea based on this chat:\n" + "\n".join(recent)

    await ctx.respond("🧠 Generating meme...")

    # Generate meme image with DALL·E
    try:
        response = openai.Image.create(
            model="dall-e-3",
            prompt=prompt,
            n=1,
            size="1024x1024"
        )
        image_url = response['data'][0]['url']

        async with aiohttp.ClientSession() as session:
            async with session.get(image_url) as resp:
                if resp.status == 200:
                    img_data = await resp.read()
                    with open("meme.png", "wb") as f:
                        f.write(img_data)
                    await ctx.send(file=discord.File("meme.png"))
                else:
                    await ctx.send("❌ Failed to download meme image.")
    except Exception as e:
        await ctx.send(f"⚠️ Error: {str(e)}")

# === Auto AI reply every minute (optional) ===
@tasks.loop(seconds=60)
async def auto_responder():
    await bot.wait_until_ready()
    for guild in bot.guilds:
        if str(guild.id) not in load_enabled_servers():
            continue
        for channel in guild.text_channels:
            try:
                messages = [m async for m in channel.history(limit=5)]
                messages = [m.content for m in messages if not m.author.bot]
                if messages and random.random() < 0.15:
                    prompt = "Join this chat naturally:\n" + "\n".join(messages)
                    reply = openai.ChatCompletion.create(
                        model="gpt-3.5-turbo",
                        messages=[{"role": "user", "content": prompt}],
                        max_tokens=100
                    )
                    await channel.send(reply.choices[0].message.content)
                    break
            except:
                continue

# === Start webserver to keep bot alive ===
keep_alive()

# Run bot
bot.run(DISCORD_TOKEN)