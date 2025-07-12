import discord from discord.ext import tasks from discord.commands import SlashCommandGroup import openai import random import os import asyncio from dotenv import load_dotenv

Load environment variables

load_dotenv() TOKEN = os.getenv("DISCORD_TOKEN") OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

openai.api_key = OPENAI_API_KEY

intents = discord.Intents.default() intents.messages = True intents.guilds = True intents.message_content = True intents.members = True

bot = discord.Bot(intents=intents)

enabled_servers = set()

Slash command group

ai_group = SlashCommandGroup("ai", "AI-related commands")

@ai_group.command(name="enable", description="Enable AI features in this server") async def enable_ai(ctx): enabled_servers.add(ctx.guild.id) await ctx.respond("✅ AI features enabled in this server.")

@ai_group.command(name="disable", description="Disable AI features in this server") async def disable_ai(ctx): enabled_servers.discard(ctx.guild.id) await ctx.respond("🛑 AI features disabled in this server.")

@ai_group.command(name="status", description="Check if AI is enabled") async def status_ai(ctx): if ctx.guild.id in enabled_servers: await ctx.respond("✅ AI is currently enabled in this server.") else: await ctx.respond("❌ AI is currently disabled in this server.")

@ai_group.command(name="meme", description="Generate an AI meme based on recent messages") async def meme(ctx): await ctx.defer()

if ctx.guild.id not in enabled_servers:
    await ctx.respond("⚠️ AI is disabled in this server. Use /ai enable to activate it.")
    return

# Fetch recent messages
messages = [message async for message in ctx.channel.history(limit=15) if not message.author.bot]
recent_text = "\n".join(m.content for m in reversed(messages))

# Ask OpenAI to generate a meme caption
prompt = f"Create a short, funny meme caption based on this conversation:\n{recent_text}"
print(f"Sending prompt to OpenAI: {prompt}")

try:
    completion = await openai.ChatCompletion.acreate(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You're a witty meme expert."},
            {"role": "user", "content": prompt},
        ]
    )
    caption = completion.choices[0].message.content.strip()
except Exception as e:
    await ctx.respond(f"❌ Error generating caption: {e}")
    return

# Generate meme image using DALL-E
try:
    image_response = await asyncio.wait_for(
        openai.Image.acreate(
            prompt=caption,
            n=1,
            size="512x512"
        ),
        timeout=30
    )
    image_url = image_response["data"][0]["url"]
except asyncio.TimeoutError:
    await ctx.respond("⏱️ Image generation took too long. Try again later.")
    return
except Exception as e:
    await ctx.respond(f"❌ Error generating image: {e}")
    return

embed = discord.Embed(title="🖼️ AI Meme", description=caption)
embed.set_image(url=image_url)
await ctx.respond(embed=embed)

Register group

bot.add_application_command(ai_group)

Background replies (optional feature)

@tasks.loop(minutes=2) async def auto_reply_loop(): for guild in bot.guilds: if guild.id not in enabled_servers: continue

for channel in guild.text_channels:
        try:
            messages = [msg async for msg in channel.history(limit=10) if not msg.author.bot]
            if not messages:
                continue

            convo = "\n".join(m.content for m in reversed(messages))

            completion = await openai.ChatCompletion.acreate(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "Be casual and funny, and reply to a chat message."},
                    {"role": "user", "content": convo},
                ]
            )
            reply = completion.choices[0].message.content.strip()
            await channel.send(reply)
            break  # reply in only 1 channel per server

        except Exception as e:
            print(f"[AutoReply] Error: {e}")

@bot.event async def on_ready(): print(f"✅ Logged in as {bot.user}") auto_reply_loop.start()

bot.run(TOKEN)

