"""
Script to clear all commands (global and guild-specific)
Run this to remove duplicate commands
"""
import discord
from discord.ext import commands
import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv('DISCORD_TOKEN', '').strip()

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'{bot.user} connected!')
    print(f'Servers: {len(bot.guilds)}')
    
    try:
        # Clear all global commands
        print('\n🔄 Clearing all global commands...')
        bot.tree.clear_commands(guild=None)
        synced = await bot.tree.sync()
        print(f'✅ Cleared global commands (synced {len(synced)} commands)')
        
        # Clear all guild-specific commands
        print('\n🔄 Clearing all guild-specific commands...')
        for guild in bot.guilds:
            try:
                bot.tree.clear_commands(guild=guild)
                synced_guild = await bot.tree.sync(guild=guild)
                print(f'✅ Cleared commands for {guild.name} (synced {len(synced_guild)} commands)')
            except Exception as e:
                print(f'⚠️  Error clearing commands for {guild.name}: {e}')
        
        print('\n✅ All commands cleared!')
        print('⚠️  Wait 1-2 minutes, then restart the bot to sync new commands')
    except Exception as e:
        print(f'❌ Error: {e}')
        import traceback
        traceback.print_exc()
    
    await bot.close()

if __name__ == "__main__":
    if not TOKEN:
        print("❌ Error: DISCORD_TOKEN not found in .env file")
        exit(1)
    bot.run(TOKEN)
