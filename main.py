import discord
from discord import app_commands
from discord.ext import commands
from openai import OpenAI
import os
import json
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Initialize OpenAI
client = OpenAI(api_key=OPENAI_API_KEY)

# Intents and Bot
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

# File to track which servers have AI enabled
AI_ENABLED_FILE = "enabled_servers.json"

# Load enabled servers
if os.path.exists(AI_ENABLED_FILE):
    with open(AI_ENABLED_FILE, "r") as f:
        enabled_servers = json.load(f)
else:
    enabled_servers = []

# Save enabled servers
def save_enabled_servers():
    with open(AI_ENABLED_FILE, "w") as f:
        json.dump(enabled_servers, f)

# Sync commands
@bot.event
async def on_ready():
    try:
        synced = await tree.sync()
        print(f"✅ Synced {len(synced)} command(s)")
    except Exception as e:
        print(f"❌ Failed to sync commands: {e}")
    print(f"🤖 Bot is ready as {bot.user}!")

# Command: Enable AI
@tree.command(name="enable-ai", description="Enable AI features in this server.")
async def enable_ai(interaction: discord.Interaction):
    if str(interaction.guild_id) not in enabled_servers:
        enabled_servers.append(str(interaction.guild_id))
        save_enabled_servers()
    await interaction.response.send_message("✅ AI features enabled in this server.")

# Command: Disable AI
@tree.command(name="disable-ai", description="Disable AI features in this server.")
async def disable_ai(interaction: discord.Interaction):
    if str(interaction.guild_id) in enabled_servers:
        enabled_servers.remove(str(interaction.guild_id))
        save_enabled_servers()
    await interaction.response.send_message("🚫 AI features disabled in this server.")

# Command: Ask AI
@tree.command(name="ask", description="Ask the AI a question.")
@app_commands.describe(question="Your question for the AI")
async def ask_ai(interaction: discord.Interaction, question: str):
    if str(interaction.guild_id) not in enabled_servers:
        await interaction.response.send_message("❌ AI is disabled in this server. Use /enable-ai to activate it.")
        return

    try:
        await interaction.response.defer(thinking=True)

        # OpenAI call
        response = await client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": question}]
        )

        ai_reply = response.choices[0].message.content
        await interaction.followup.send(ai_reply)

    except Exception as e:
        await interaction.followup.send(f"❌ AI error: {e}")

# Run the bot
bot.run(DISCORD_TOKEN)