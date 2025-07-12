import discord
from discord.ext import tasks
import openai
import json
import random
import os
import aiohttp
from keep_alive import keep_alive

# Load API keys from environment variables
openai.api_key = os.getenv("OPENAI_API_KEY")
DISCORD_TOKEN = os.getenv("DISCORD_BOT_TOKEN")

intents = discord.Intents.default()
intents.message_content = True
intents.messages = True
intents.guilds = True
intents.members = True

class AIClient(discord.Client):
    def __init__(self):
        super().__init__(intents=intents)
        self.tree = discord.app_commands.CommandTree(self)

    async def setup_hook(self):
        # Sync commands globally (or per guild for testing)
        await self.tree.sync()

bot = AIClient()

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
    print(f"✅ {bot.user} is online!")
    auto_responder.start()

@bot.tree.command(name="enable-ai", description="Enable AI features in this server")
@discord.app_commands.checks.has_permissions(manage_guild=True)
async def enable_ai(interaction: discord.Interaction):
    enabled = load_enabled_servers()
    guild_id = str(interaction.guild.id)
    if guild_id not in enabled:
        enabled.append(guild_id)
        save_enabled_servers(enabled)
        await interaction.response.send_message("✅ AI features enabled!", ephemeral=True)
    else:
        await interaction.response.send_message("⚠️ AI is already enabled.", ephemeral=True)

@bot.tree.command(name="disable-ai", description="Disable AI features in this server")
@discord.app_commands.checks.has_permissions(manage_guild=True)
async def disable_ai(interaction: discord.Interaction):
    enabled = load_enabled_servers()
    guild_id = str(interaction.guild.id)
    if guild_id in enabled:
        enabled.remove(guild_id)
        save_enabled_servers(enabled)
        await interaction.response.send_message("❌ AI features disabled.", ephemeral=True)
    else:
        await interaction.response.send_message("⚠️ AI is already disabled.", ephemeral=True)

@bot.tree.command(name="meme", description="Generate a meme image from recent messages")
async def meme(interaction: discord.Interaction):
    guild_id = str(interaction.guild.id)
    if guild_id not in load_enabled_servers():
        return await interaction.response.send_message("⚠️ AI is disabled in this server.", ephemeral=True)

    messages = [m async for m in interaction.channel.history(limit=10)]
    recent = [m.content for m in messages if not m.author.bot]
    if not recent:
        return await interaction.response.send_message("No usable messages found.", ephemeral=True)

    prompt = "Create a funny meme image idea based on this chat:\n" + "\n".join(recent)

    await interaction.response.defer()  # Acknowledge and thinking...

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
                    await interaction.followup.send(file=discord.File("meme.png"))
                else:
                    await interaction.followup.send("❌ Failed to download meme image.")
    except Exception as e:
        await interaction.followup.send(f"⚠️ Error: {str(e)}")

@tasks.loop(seconds=60)
async def auto_responder():
    await bot.wait_until_ready()
    for guild in bot.guilds:
        guild_id = str(guild.id)
        if guild_id not in load_enabled_servers():
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
            except Exception:
                continue

keep_alive()
bot.run(DISCORD_TOKEN)