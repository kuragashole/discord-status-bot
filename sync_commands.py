"""
Скрипт для принудительной синхронизации команд бота
Запустите этот файл, если команды не работают
"""
import discord
from discord.ext import commands
from discord import app_commands
import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv('DISCORD_TOKEN', '').strip()

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# Register commands from main bot file
@bot.tree.command(name="setup_status", description="Create status message in this channel")
@app_commands.default_permissions(administrator=True)
async def setup_status(interaction: discord.Interaction):
    """Command to create status message"""
    await interaction.response.send_message("Command registered!", ephemeral=True)

@bot.tree.command(name="start", description="Change status")
@app_commands.describe(mode="Mode: work or sleep")
@app_commands.default_permissions(administrator=True)
@app_commands.choices(mode=[
    app_commands.Choice(name="work", value="work"),
    app_commands.Choice(name="sleep", value="sleep")
])
async def start_status(interaction: discord.Interaction, mode: str):
    """Command to change status"""
    await interaction.response.send_message("Command registered!", ephemeral=True)

@bot.event
async def on_ready():
    print(f'{bot.user} connected!')
    print(f'Servers: {len(bot.guilds)}')
    for guild in bot.guilds:
        print(f'  - {guild.name} (ID: {guild.id})')
    
    try:
        # Show registered commands
        print('\n📋 Registered commands:')
        commands_list = bot.tree.get_commands()
        print(f'   Total commands: {len(commands_list)}')
        for cmd in commands_list:
            print(f'   - /{cmd.name}: {cmd.description}')
        
        # Sync global commands only (removes duplicates)
        print('\n🔄 Syncing global commands...')
        synced = await bot.tree.sync()
        print(f'✅ Synced {len(synced)} global commands')
        for cmd in synced:
            print(f'   - /{cmd.name} (ID: {cmd.id})')
        
        # Clear guild-specific commands to avoid duplicates
        print('\n🔄 Clearing guild-specific commands to avoid duplicates...')
        for guild in bot.guilds:
            try:
                # Clear all guild commands
                bot.tree.clear_commands(guild=guild)
                await bot.tree.sync(guild=guild)
                print(f'✅ Cleared commands for {guild.name}')
            except Exception as e:
                print(f'⚠️  Error clearing commands for {guild.name}: {e}')
        
        print('\n✅ Sync completed!')
        print('⚠️  Wait 1-2 minutes for commands to appear in Discord')
        print('⚠️  Old commands with Russian descriptions will be removed automatically')
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
