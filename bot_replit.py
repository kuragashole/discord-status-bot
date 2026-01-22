"""
Версия бота для Replit с поддержкой keep-alive
Используйте этот файл вместо bot.py на Replit!
"""
from keep_alive import keep_alive
keep_alive()

# Импортируем основной код бота
import discord
from discord.ext import commands
from discord import app_commands
import os
import json
from dotenv import load_dotenv

load_dotenv()

# Bot settings
TOKEN = os.getenv('DISCORD_TOKEN', '').strip()  # Automatically remove spaces
OWNER_ID = int(os.getenv('OWNER_ID', '0'))  # Your Discord ID
IMAGE_URL = os.getenv('IMAGE_URL', 'https://i.imgur.com/example.png')  # Image URL for work mode or file path
IMAGE_URL_SLEEP = os.getenv('IMAGE_URL_SLEEP', 'https://i.imgur.com/example.png')  # Image URL for sleep mode or file path
TICKET_CHANNEL_ID = os.getenv('TICKET_CHANNEL_ID', '0')  # Ticket channel ID (optional)
STATUS_LOG_CHANNEL_ID = os.getenv('STATUS_LOG_CHANNEL_ID', '0')  # Status log channel ID (optional)

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# File for saving status messages
STATUS_FILE = 'status_messages.json'

def load_status_messages():
    """Load status messages from file"""
    if os.path.exists(STATUS_FILE):
        try:
            with open(STATUS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_status_messages():
    """Save status messages to file"""
    try:
        with open(STATUS_FILE, 'w', encoding='utf-8') as f:
            json.dump(status_messages, f, indent=2)
    except Exception as e:
        print(f"Error saving status messages: {e}")

# Storage for status messages
# Format: {channel_id: {"status_message_id": id, "image_message_id": id}}
status_messages = load_status_messages()

# Storage for messages in status log channel
# Format: {channel_id: log_message_id}
status_log_messages = {}

@bot.event
async def on_ready():
    print(f'{bot.user} connected to Discord!')
    print(f'Bot ID: {bot.user.id}')
    print(f'OWNER_ID from .env: {OWNER_ID}')
    print(f'Bot on {len(bot.guilds)} servers')
    for guild in bot.guilds:
        print(f'   - {guild.name} (ID: {guild.id})')
    try:
        # Sync only global commands to avoid duplicates
        synced = await bot.tree.sync()
        print(f'✅ Synced {len(synced)} global commands')
        for cmd in synced:
            print(f'   - /{cmd.name} (ID: {cmd.id})')
        
        # Clear guild-specific commands to avoid duplicates
        for guild in bot.guilds:
            try:
                bot.tree.clear_commands(guild=guild)
                synced_guild = await bot.tree.sync(guild=guild)
                if len(synced_guild) == 0:
                    print(f'✅ Cleared guild commands for {guild.name}')
                else:
                    print(f'⚠️  Still {len(synced_guild)} commands for {guild.name}')
            except Exception as e:
                print(f'⚠️  Error clearing guild commands for {guild.name}: {e}')
        
        print('\n⚠️  IMPORTANT: If commands don\'t work, wait 1-2 minutes for synchronization!')
        print('⚠️  Old commands with Russian descriptions will be removed automatically')
        print('✅ Keep-alive server is running on port 5000')
    except Exception as e:
        print(f'❌ Error syncing commands: {e}')
        import traceback
        traceback.print_exc()

@bot.event
async def on_interaction(interaction: discord.Interaction):
    """Handler for all interactions for logging"""
    if interaction.type == discord.InteractionType.application_command:
        print(f"📝 Command used: /{interaction.command.name} by {interaction.user} in {interaction.channel}")

@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    """Handler for command errors"""
    print(f"❌ Command error: {error}")
    if isinstance(error, app_commands.MissingPermissions):
        await interaction.response.send_message("❌ You don't have permission to use this command!", ephemeral=True)
    else:
        await interaction.response.send_message(f"❌ Error: {str(error)}", ephemeral=True)

def is_owner(interaction: discord.Interaction) -> bool:
    """Check if user is the bot owner"""
    return interaction.user.id == OWNER_ID

class StatusView(discord.ui.View):
    def __init__(self, status_type: str = "work"):
        super().__init__(timeout=None)
        try:
            if TICKET_CHANNEL_ID and TICKET_CHANNEL_ID != '0':
                ticket_channel = bot.get_channel(int(TICKET_CHANNEL_ID))
                if ticket_channel:
                    ticket_button = discord.ui.Button(
                        label="Create Ticket",
                        style=discord.ButtonStyle.link,
                        url=f"https://discord.com/channels/{ticket_channel.guild.id}/{TICKET_CHANNEL_ID}"
                    )
                    self.add_item(ticket_button)
        except:
            pass

@bot.tree.command(name="setup_status", description="Create status message in this channel")
@app_commands.default_permissions(administrator=True)
async def setup_status(interaction: discord.Interaction):
    """Command to create status message"""
    # Logging for debugging
    print(f"📝 /setup_status called by {interaction.user} in {interaction.channel}")
    
    if not is_owner(interaction):
        await interaction.response.send_message("❌ Only the bot owner can use this command!", ephemeral=True)
        return
    
    await interaction.response.defer(ephemeral=True)
    
    try:
        welcome_text = "Yo, this is Sauce. Below you can see the server status. If it's in sleep mode you can still open a ticket and I'll take a look as soon as it switches back to work mode."

        embed = discord.Embed(
            title="📊 Status",
            description=f"{welcome_text}\n\n🟢 Active",
            color=discord.Color.green()
        )

        current_image_url = IMAGE_URL
        file = None
        if os.path.exists(current_image_url):
            file_ext = os.path.splitext(current_image_url)[1].lower() or '.png'
            filename = f"status_image_work{file_ext}"
            file = discord.File(current_image_url, filename=filename)
            embed.set_image(url=f"attachment://{filename}")
        else:
            embed.set_image(url=current_image_url)

        view = StatusView(status_type="work")

        if file:
            message = await interaction.channel.send(embed=embed, view=view, file=file)
        else:
            message = await interaction.channel.send(embed=embed, view=view)

        status_messages[str(interaction.channel.id)] = {"status_message_id": str(message.id)}
        save_status_messages()
        
        await interaction.followup.send("✅ Status message created!", ephemeral=True)
        print(f"✅ Status message created in channel {interaction.channel.id}")
    except Exception as e:
        print(f"❌ Error creating status message: {e}")
        error_msg = f"❌ Error: {str(e)}"
        try:
            await interaction.followup.send(error_msg, ephemeral=True)
        except:
            await interaction.response.send_message(error_msg, ephemeral=True)


@bot.tree.command(name="start", description="Change status")
@app_commands.describe(mode="Mode: work or sleep")
@app_commands.default_permissions(administrator=True)
@app_commands.choices(mode=[
    app_commands.Choice(name="work", value="work"),
    app_commands.Choice(name="sleep", value="sleep")
])
async def start_status(interaction: discord.Interaction, mode: str):
    """Command to change status"""
    print(f"📝 /start {mode} called by {interaction.user} in {interaction.channel}")
    
    if not is_owner(interaction):
        await interaction.response.send_message("❌ Only the bot owner can use this command!", ephemeral=True)
        return
    
    await interaction.response.defer(ephemeral=True)
    
    try:
        channel_id_str = str(interaction.channel.id)
        if channel_id_str not in status_messages:
            await interaction.followup.send("❌ Status message not found in this channel! Use `/setup_status` first.", ephemeral=True)
            return
        
        message_id = status_messages[channel_id_str].get("status_message_id")
        if not message_id:
            await interaction.followup.send("❌ Status message ID not found! Use `/setup_status` again.", ephemeral=True)
            return
        
        try:
            message = await interaction.channel.fetch_message(int(message_id))
        except discord.NotFound:
            await interaction.followup.send("❌ Status message not found! Use `/setup_status` again.", ephemeral=True)
            return
        
        # Create new embed depending on mode
        welcome_text = "Yo, this is Sauce. Below you can see the server status. If it's in sleep mode you can still open a ticket and I'll take a look as soon as it switches back to work mode."
        
        if mode == "work":
            embed = discord.Embed(
                title="📊 Status",
                description=f"{welcome_text}\n\n🟢 Active",
                color=discord.Color.green()
            )
            view = StatusView(status_type="work")
            current_image_url = IMAGE_URL
            if os.path.exists(current_image_url):
                file_ext = os.path.splitext(current_image_url)[1].lower() or '.png'
                filename = f"status_image_work{file_ext}"
                file = discord.File(current_image_url, filename=filename)
                embed.set_image(url=f"attachment://{filename}")
                await message.edit(embed=embed, view=view, attachments=[file])
            else:
                embed.set_image(url=current_image_url)
                await message.edit(embed=embed, view=view, attachments=[])
        else:  # sleep
            embed = discord.Embed(
                title="📊 Status",
                description=f"{welcome_text}\n\n🔴 Sleep",
                color=discord.Color.red()
            )
            view = StatusView(status_type="sleep")
            current_image_url = IMAGE_URL_SLEEP
            if os.path.exists(current_image_url):
                file_ext = os.path.splitext(current_image_url)[1].lower() or '.png'
                filename = f"status_image_sleep{file_ext}"
                file = discord.File(current_image_url, filename=filename)
                embed.set_image(url=f"attachment://{filename}")
                await message.edit(embed=embed, view=view, attachments=[file])
            else:
                embed.set_image(url=current_image_url)
                await message.edit(embed=embed, view=view, attachments=[])
        
        await interaction.followup.send(
            f"✅ Status changed to: **{mode}**",
            ephemeral=True
        )

        # Send full status panel to log channel and delete old one
        if STATUS_LOG_CHANNEL_ID and STATUS_LOG_CHANNEL_ID != '0':
            try:
                log_channel = bot.get_channel(int(STATUS_LOG_CHANNEL_ID))
                if log_channel:
                    log_channel_id_str = str(log_channel.id)
                    if log_channel_id_str in status_log_messages:
                        try:
                            old_log_message_id = status_log_messages[log_channel_id_str]
                            old_log_message = await log_channel.fetch_message(old_log_message_id)
                            await old_log_message.delete()
                            print(f"✅ Deleted old log message: {old_log_message_id}")
                        except discord.NotFound:
                            pass
                        except Exception as e:
                            print(f"⚠️  Error deleting old log message: {e}")

                    # Create the full status panel for the log channel
                    log_embed = discord.Embed(
                        title="📊 Status",
                        description=f"{welcome_text}\n\n{('🟢 Active' if mode == 'work' else '🔴 Sleep')}",
                        color=discord.Color.green() if mode == "work" else discord.Color.red()
                    )
                    
                    log_file_to_send = None
                    if os.path.exists(current_image_url):
                        log_file_ext = os.path.splitext(current_image_url)[1].lower() or '.png'
                        log_filename = f"status_image_{mode}{log_file_ext}"
                        log_file_to_send = discord.File(current_image_url, filename=log_filename)
                        log_embed.set_image(url=f"attachment://{log_filename}")
                    else:
                        log_embed.set_image(url=current_image_url)

                    log_view = StatusView(status_type=mode)

                    # Send the new status panel with @everyone tag only for work mode
                    content = "@everyone" if mode == "work" else None
                    log_message = await log_channel.send(content=content, embed=log_embed, view=log_view, file=log_file_to_send)
                    status_log_messages[log_channel_id_str] = log_message.id
                    print(f"✅ Full status panel sent to log channel: {log_channel.name}")
            except Exception as e:
                print(f"⚠️  Error sending full status panel to log channel: {e}")
        
    except Exception as e:
        print(f"❌ Error changing status: {e}")
        import traceback
        traceback.print_exc()
        error_msg = f"❌ Error: {str(e)}"
        try:
            await interaction.followup.send(error_msg, ephemeral=True)
        except:
            await interaction.response.send_message(error_msg, ephemeral=True)

# Error handling for token
if not TOKEN:
    print("=" * 60)
    print("❌ ERROR: DISCORD_TOKEN not found in .env file!")
    print("=" * 60)
    print("\nPlease:")
    print("1. Create a .env file in the project directory")
    print("2. Add: DISCORD_TOKEN=your_token_here")
    print("3. Restart the bot")
    print("=" * 60)
    exit(1)

if len(TOKEN) < 50:
    print("=" * 60)
    print("⚠️  WARNING: Token looks incorrect!")
    print("=" * 60)
    print("Token should be long (usually 59+ characters)")
    print("And contain dots, for example: MTIzNDU2...AbC.DeF...")
    print("Check that the token is copied completely")
    print("=" * 60)
    print("\nAttempting connection... (may not work)")

try:
    bot.run(TOKEN)
except discord.errors.LoginFailure:
    print("=" * 60)
    print("❌ CONNECTION ERROR: Invalid token!")
    print("=" * 60)
    print("\nPossible causes:")
    print("1. Token is incorrect or was reset")
    print("2. Token has extra spaces or characters")
    print("3. Token was not copied completely")
    print("\nSolution:")
    print("1. Go to https://discord.com/developers/applications")
    print("2. Select your application → Bot")
    print("3. Click 'Reset Token' → 'Yes, do it!'")
    print("4. Copy the NEW token completely")
    print("5. Paste into .env file (make sure there are no spaces)")
    print("6. Restart the bot")
    print("=" * 60)
except Exception as e:
    print(f"❌ Unexpected error: {e}")
    import traceback
    traceback.print_exc()
