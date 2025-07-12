import discord
from discord.ext import commands, tasks
import json
import random
import asyncio
from keep_alive import keep_alive

# Replace with your OpenAI logic if desired
AI_RESPONSES = [
    "That's an interesting point.",
    "Can you explain more?",
    "🤣 That made my circuits laugh!",
    "🤖 Beep boop, I'm smarter now.",
    "Sounds like a skill issue 😎",
]

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

def load_enabled_servers():
    try:
        with open("enabled_servers.json", "r") as f:
            return json.load(f).get("enabled", [])
    except FileNotFoundError:
        return []

def save_enabled_servers(server_ids):
    with open("enabled_servers.json", "w") as f:
        json.dump({"enabled": server_ids}, f, indent=4)

@bot.event
async def on_ready():
    print(f"Bot is online as {bot.user}")
    auto_responder.start()

@bot.slash_command(name="enable-ai", description="Enable AI chat and memes in this server")
@commands.has_permissions(manage_guild=True)
async def enable_ai(ctx):
    enabled = load_enabled_servers()
    if str(ctx.guild.id) not in enabled:
        enabled.append(str(ctx.guild.id))
        save_enabled_servers(enabled)
        await ctx.respond("✅ AI features enabled in this server!")
    else:
        await ctx.respond("⚠️ AI is already enabled here.")

@bot.slash_command(name="disable-ai", description="Disable AI chat and memes in this server")
@commands.has_permissions(manage_guild=True)
async def disable_ai(ctx):
    enabled = load_enabled_servers()
    if str(ctx.guild.id) in enabled:
        enabled.remove(str(ctx.guild.id))
        save_enabled_servers(enabled)
        await ctx.respond("❌ AI features disabled in this server.")
    else:
        await ctx.respond("⚠️ AI is already disabled here.")

@bot.slash_command(name="meme", description="Generate a random meme response")
async def meme(ctx):
    if str(ctx.guild.id) not in load_enabled_servers():
        return await ctx.respond("AI is disabled in this server.")
    
    meme_text = random.choice([
        "When the group chat gets spicy 🔥",
        "This server in one picture 🤡",
        "Monday energy be like... 😴",
        "Server drama starter pack 💥",
    ])
    await ctx.respond(f"🖼️ Meme: {meme_text}")

@tasks.loop(seconds=60)
async def auto_responder():
    await bot.wait_until_ready()
    for guild in bot.guilds:
        if str(guild.id) not in load_enabled_servers():
            continue
        for channel in guild.text_channels:
            try:
                async for message in channel.history(limit=10):
                    if message.author.bot:
                        continue
                    if random.random() < 0.05:  # 5% chance to respond
                        response = random.choice(AI_RESPONSES)
                        await channel.send(response)
                        break
            except:
                continue

# Run web server to keep bot alive on Render
keep_alive()

# Run bot
bot.run("YOUR_DISCORD_BOT_TOKEN")