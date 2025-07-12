import discord from discord.ext import tasks from discord.commands import slash_command, Option import openai import os import random import json import asyncio

intents = discord.Intents.default() intents.messages = True intents.guilds = True intents.message_content = True

bot = discord.Bot(intents=intents)

Environment Variables

TOKEN = os.getenv("DISCORD_TOKEN") OPENAI_API_KEY = os.getenv("OPENAI_API_KEY") openai.api_key = OPENAI_API_KEY

File to store enabled server IDs

ENABLED_SERVERS_FILE = "enabled_servers.json"

def load_enabled_servers(): if os.path.exists(ENABLED_SERVERS_FILE): with open(ENABLED_SERVERS_FILE, "r") as f: return json.load(f) return []

def save_enabled_servers(server_ids): with open(ENABLED_SERVERS_FILE, "w") as f: json.dump(server_ids, f)

enabled_servers = load_enabled_servers()

Enable AI

@slash_command(name="enable-ai", description="Enable AI features in this server") async def enable_ai(ctx): if ctx.guild.id not in enabled_servers: enabled_servers.append(ctx.guild.id) save_enabled_servers(enabled_servers) await ctx.respond("✅ AI features enabled in this server.") else: await ctx.respond("ℹ️ AI features are already enabled.")

Disable AI

@slash_command(name="disable-ai", description="Disable AI features in this server") async def disable_ai(ctx): if ctx.guild.id in enabled_servers: enabled_servers.remove(ctx.guild.id) save_enabled_servers(enabled_servers) await ctx.respond("🛑 AI features disabled in this server.") else: await ctx.respond("ℹ️ AI features were not enabled.")

AI Status

@slash_command(name="ai-status", description="Check if AI is enabled in this server") async def ai_status(ctx): if ctx.guild.id in enabled_servers: await ctx.respond("✅ AI is enabled in this server.") else: await ctx.respond("❌ AI is not enabled in this server.")

Meme command

@slash_command(name="meme", description="Generate a meme based on recent messages") async def meme(ctx): if ctx.guild.id not in enabled_servers: await ctx.respond("⚠️ AI is not enabled in this server.") return await ctx.defer() channel = ctx.channel messages = [msg async for msg in channel.history(limit=10)] context_text = "\n".join([msg.content for msg in messages if msg.content]) prompt = f"Generate a funny meme idea based on this conversation:\n{context_text}"

try:
    response = openai.Image.create(
        prompt=prompt,
        n=1,
        size="512x512"
    )
    image_url = response['data'][0]['url']
    await ctx.respond(f"🖼️ Meme based on chat: {image_url}")
except Exception as e:
    await ctx.respond(f"❌ Failed to generate meme: {e}")

Ask command

@slash_command(name="ask", description="Ask AI a question") async def ask(ctx, question: Option(str, "What do you want to ask?")): await ctx.defer() try: completion = openai.ChatCompletion.create( model="gpt-3.5-turbo", messages=[{"role": "user", "content": question}] ) reply = completion.choices[0].message.content await ctx.respond(reply) except Exception as e: await ctx.respond(f"❌ Failed to get response: {e}")

Generate command

@slash_command(name="generate", description="Generate creative content (story, idea, etc.)") async def generate(ctx, idea: Option(str, "Describe what to generate")): await ctx.defer() prompt = f"Create something fun or creative based on this: {idea}" try: completion = openai.ChatCompletion.create( model="gpt-3.5-turbo", messages=[{"role": "user", "content": prompt}] ) result = completion.choices[0].message.content await ctx.respond(result) except Exception as e: await ctx.respond(f"❌ Failed to generate: {e}")

Background Task for smart replies

@tasks.loop(minutes=2) async def auto_reply(): for guild in bot.guilds: if guild.id not in enabled_servers: continue for channel in guild.text_channels: try: messages = [msg async for msg in channel.history(limit=5)] context = "\n".join([msg.content for msg in messages if msg.content]) if context: prompt = f"Respond cleverly to this conversation:\n{context}" completion = openai.ChatCompletion.create( model="gpt-3.5-turbo", messages=[{"role": "user", "content": prompt}] ) response = completion.choices[0].message.content await channel.send(response) break except: continue

@bot.event async def on_ready(): print(f"✅ Logged in as {bot.user}") auto_reply.start()

bot.run(TOKEN)

