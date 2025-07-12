import discord
from discord import app_commands
from discord.ext import tasks
import openai
import json
import os
import asyncio
import traceback
from keep_alive import keep_alive  # remove if you don't have this

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True

bot = discord.Client(intents=intents)
tree = app_commands.CommandTree(bot)

TOKEN = os.getenv("DISCORD_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai.api_key = OPENAI_API_KEY

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
    await tree.sync()
    print(f"✅ Logged in as {bot.user} (ID: {bot.user.id})")
    print("Slash commands synced.")
    auto_ai_loop.start()

ai_group = app_commands.Group(name="ai", description="AI related commands")

@ai_group.command(name="enable", description="Enable AI features in this server")
async def enable_ai(interaction: discord.Interaction):
    print(f"[ENABLE] Guild {interaction.guild.id}")
    ai_enabled[str(interaction.guild.id)] = True
    save_ai_settings(ai_enabled)
    await interaction.response.send_message("✅ AI features enabled in this server.")

@ai_group.command(name="disable", description="Disable AI features in this server")
async def disable_ai(interaction: discord.Interaction):
    print(f"[DISABLE] Guild {interaction.guild.id}")
    ai_enabled[str(interaction.guild.id)] = False
    save_ai_settings(ai_enabled)
    await interaction.response.send_message("❌ AI features disabled in this server.")

@ai_group.command(name="status", description="Check if AI is enabled in this server")
async def status_ai(interaction: discord.Interaction):
    status = ai_enabled.get(str(interaction.guild.id), False)
    await interaction.response.send_message(f"🔍 AI is {'enabled' if status else 'disabled'} in this server.")

@ai_group.command(name="meme", description="Generate a meme based on recent messages")
async def meme_ai(interaction: discord.Interaction):
    await interaction.response.defer()
    if not ai_enabled.get(str(interaction.guild.id), False):
        await interaction.followup.send("❌ AI is not enabled in this server.")
        return

    try:
        print(f"[MEME] Generating meme for guild {interaction.guild.id}")
        messages = []
        async for msg in interaction.channel.history(limit=20):
            if msg.author != bot.user:
                messages.append(f"{msg.author.display_name}: {msg.content}")

        prompt = "Create a funny Discord meme idea based on this chat:\n" + "\n".join(messages[-10:])
        print(f"[MEME] Prompt:\n{prompt}")

        dalle_response = openai.image.create(prompt=prompt, n=1, size="512x512")
        image_url = dalle_response.data[0].url
        embed = discord.Embed(title="🤣 Meme Generated", color=discord.Color.green())
        embed.set_image(url=image_url)
        await interaction.followup.send(embed=embed)
        print("[MEME] Meme sent successfully")

    except Exception as e:
        print("[MEME] Error generating meme:", e)
        traceback.print_exc()
        await interaction.followup.send(f"⚠️ Failed to generate meme: {e}")

@ai_group.command(name="ask", description="Ask AI a question")
async def ask_ai(interaction: discord.Interaction, question: str):
    await interaction.response.defer()
    if not ai_enabled.get(str(interaction.guild.id), False):
        await interaction.followup.send("❌ AI is not enabled in this server.")
        return

    try:
        print(f"[ASK] Question from guild {interaction.guild.id}: {question}")
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": question}]
        )
        reply = response.choices[0].message.content
        print(f"[ASK] Response: {reply}")
        await interaction.followup.send(reply)

    except Exception as e:
        print("[ASK] Error getting AI response:", e)
        traceback.print_exc()
        await interaction.followup.send(f"⚠️ Failed to get a reply: {e}")

@ai_group.command(name="generate", description="Generate creative content")
async def generate_ai(interaction: discord.Interaction, idea: str):
    await interaction.response.defer()
    if not ai_enabled.get(str(interaction.guild.id), False):
        await interaction.followup.send("❌ AI is not enabled in this server.")
        return

    try:
        print(f"[GENERATE] Idea from guild {interaction.guild.id}: {idea}")
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": f"Write something creative: {idea}"}]
        )
        reply = response.choices[0].message.content
        print(f"[GENERATE] Response: {reply}")
        await interaction.followup.send(reply)

    except Exception as e:
        print("[GENERATE] Error generating content:", e)
        traceback.print_exc()
        await interaction.followup.send(f"⚠️ Failed to generate content: {e}")

tree.add_command(ai_group)

@tree.command(name="botcommands", description="Show the list of all bot commands")
async def botcommands(interaction: discord.Interaction):
    cmds = []
    for cmd in tree.walk_commands():
        cmds.append(f"/{cmd.qualified_name} - {cmd.description}")
    response = "📜 **Bot Commands:**\n" + "\n".join(cmds)
    await interaction.response.send_message(response, ephemeral=True)

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
                response = openai.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": prompt}]
                )
                reply = response.choices[0].message.content
                await channel.send(reply)
                await asyncio.sleep(2)
            except Exception:
                continue

keep_alive()
bot.run(TOKEN)