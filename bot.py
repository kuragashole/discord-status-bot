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
                # Clear all guild commands by syncing empty tree
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
    except Exception as e:
        print(f'❌ Error syncing commands: {e}')
        import traceback
        traceback.print_exc()

@bot.event
async def on_interaction(interaction: discord.Interaction):
    """Handler for all interactions for logging"""
    print("=" * 60)
    print("🔔 INTERACTION RECEIVED!")
    print(f"   Type: {interaction.type}")
    print(f"   User: {interaction.user.name} (ID: {interaction.user.id})")
    if interaction.channel:
        print(f"   Channel: {interaction.channel.name} (ID: {interaction.channel.id})")
    if interaction.type == discord.InteractionType.application_command:
        print(f"   Command: {interaction.command.name if interaction.command else 'unknown'}")
        if interaction.command:
            print(f"   Full command name: /{interaction.command.name}")
    print("=" * 60)

# Add command error handler
@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    print(f"❌ Command error: {error}")
    print(f"   Error type: {type(error).__name__}")
    import traceback
    traceback.print_exc()
    try:
        if interaction.response.is_done():
            await interaction.followup.send(f"❌ An error occurred: {str(error)}", ephemeral=True)
        else:
            await interaction.response.send_message(f"❌ An error occurred: {str(error)}", ephemeral=True)
    except Exception as e:
        print(f"❌ Failed to send error message: {e}")

def is_owner(interaction: discord.Interaction) -> bool:
    """Check if user is bot owner"""
    user_id = interaction.user.id
    if OWNER_ID == 0:
        # If OWNER_ID not set, allow everyone (for testing)
        print("⚠️  OWNER_ID not set, allowing access to everyone")
        return True
    is_owner_result = user_id == OWNER_ID
    print(f"🔐 Owner check: user {user_id} == {OWNER_ID}? {is_owner_result}")
    return is_owner_result

class StatusView(discord.ui.View):
    """View with buttons for status message"""
    
    def __init__(self, status_type: str = "work"):
        super().__init__(timeout=None)
        self.status_type = status_type
        
        # Add ticket button for both modes (work and sleep)
        if TICKET_CHANNEL_ID and TICKET_CHANNEL_ID != '0':
            try:
                ticket_channel = bot.get_channel(int(TICKET_CHANNEL_ID))
                if ticket_channel:
                    # Create link button to ticket channel
                    ticket_button = discord.ui.Button(
                        label="Create Ticket",
                        style=discord.ButtonStyle.link,
                        emoji="🎫",
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
    print("=" * 60)
    print("🚀 FUNCTION setup_status CALLED!")
    print(f"   User: {interaction.user.name} (ID: {interaction.user.id})")
    print(f"   OWNER_ID: {OWNER_ID}")
    print("=" * 60)
    
    if not is_owner(interaction):
        print(f"❌ Access denied: {interaction.user.id} != {OWNER_ID}")
        await interaction.response.send_message(
            "❌ You don't have permission to use this command.",
            ephemeral=True
        )
        return
    
    try:
        # First respond to interaction
        await interaction.response.defer(ephemeral=True)
        
        # Create embed with image and status
        # Add welcome text and status
        welcome_text = "Yo, this is Sauce. Below you can see the server status. If it's in sleep mode you can still open a ticket and I'll take a look as soon as it switches back to work mode."
        embed = discord.Embed(
            title="📊 Status",
            description=f"{welcome_text}\n\n🟢 Active",
            color=discord.Color.green()
        )
        
        # Add image (GIF) - will be shown at bottom of embed
        if os.path.exists(IMAGE_URL):
            file_ext = os.path.splitext(IMAGE_URL)[1].lower() or '.png'
            filename = f"status_image{file_ext}"
            file = discord.File(IMAGE_URL, filename=filename)
            embed.set_image(url=f"attachment://{filename}")
        else:
            embed.set_image(url=IMAGE_URL)
            file = None
        
        view = StatusView(status_type="work")
        
        # Send one message with embed (GIF and status together)
        if file:
            message = await interaction.channel.send(embed=embed, view=view, file=file)
        else:
            message = await interaction.channel.send(embed=embed, view=view)
        
        # Save message ID
        status_messages[str(interaction.channel.id)] = str(message.id)
        save_status_messages()
        
        print(f"✅ Status message created in channel {interaction.channel.id}, message ID: {message.id}")
        
        await interaction.followup.send(
            "✅ Status message created!",
            ephemeral=True
        )
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
    print(f"🔍 Command /start {mode} called by user: {interaction.user.id}")
    
    if not is_owner(interaction):
        print(f"❌ Access denied: {interaction.user.id} != {OWNER_ID}")
        await interaction.response.send_message(
            "❌ You don't have permission to use this command.",
            ephemeral=True
        )
        return
    
    channel_id = str(interaction.channel.id)
    
    if channel_id not in status_messages:
        await interaction.response.send_message(
            "❌ Status message not found in this channel. Use /setup_status first.",
            ephemeral=True
        )
        return
    
    try:
        # Get message ID (support old and new format)
        status_data = status_messages[channel_id]
        if isinstance(status_data, dict):
            message_id = int(status_data.get("status_message_id", status_data.get("image_message_id", 0)))
        else:
            message_id = int(status_data)
        
        message = await interaction.channel.fetch_message(message_id)
        
        # Get image URL from original message
        image_url = None
        if message.embeds and len(message.embeds) > 0 and message.embeds[0].image:
            image_url = message.embeds[0].image.url
        # Also check attachments (if image was sent as file)
        elif message.attachments:
            for attachment in message.attachments:
                if attachment.content_type and attachment.content_type.startswith('image/'):
                    image_url = attachment.url
                    break
        
        # Create new embed depending on mode
        # Add welcome text and status
        welcome_text = "Yo, this is Sauce. Below you can see the server status. If it's in sleep mode you can still open a ticket and I'll take a look as soon as it switches back to work mode."
        
        if mode == "work":
            embed = discord.Embed(
                title="📊 Status",
                description=f"{welcome_text}\n\n🟢 Active",
                color=discord.Color.green()
            )
            view = StatusView(status_type="work")
            # Use image for work mode
            if os.path.exists(IMAGE_URL):
                file_ext = os.path.splitext(IMAGE_URL)[1].lower() or '.png'
                filename = f"status_image_work{file_ext}"
                file = discord.File(IMAGE_URL, filename=filename)
                embed.set_image(url=f"attachment://{filename}")
                await message.edit(embed=embed, view=view, attachments=[file])
            else:
                embed.set_image(url=IMAGE_URL)
                await message.edit(embed=embed, view=view, attachments=[])
        else:  # sleep
            embed = discord.Embed(
                title="📊 Status",
                description=f"{welcome_text}\n\n🔴 Sleep",
                color=discord.Color.red()
            )
            view = StatusView(status_type="sleep")
            # Use different image for sleep mode
            if os.path.exists(IMAGE_URL_SLEEP):
                file_ext = os.path.splitext(IMAGE_URL_SLEEP)[1].lower() or '.png'
                filename = f"status_image_sleep{file_ext}"
                file = discord.File(IMAGE_URL_SLEEP, filename=filename)
                embed.set_image(url=f"attachment://{filename}")
                await message.edit(embed=embed, view=view, attachments=[file])
            else:
                embed.set_image(url=IMAGE_URL_SLEEP)
                await message.edit(embed=embed, view=view, attachments=[])
        
        # Send full status panel to log channel only for work mode (if specified)
        if mode == "work" and STATUS_LOG_CHANNEL_ID and STATUS_LOG_CHANNEL_ID != '0':
            try:
                log_channel = bot.get_channel(int(STATUS_LOG_CHANNEL_ID))
                if log_channel:
                    # Delete old message if it exists
                    log_channel_id_str = str(log_channel.id)
                    if log_channel_id_str in status_log_messages:
                        try:
                            old_log_message_id = status_log_messages[log_channel_id_str]
                            old_log_message = await log_channel.fetch_message(old_log_message_id)
                            await old_log_message.delete()
                            print(f"✅ Deleted old log message: {old_log_message_id}")
                        except discord.NotFound:
                            # Message already deleted or not found
                            pass
                        except Exception as e:
                            print(f"⚠️  Error deleting old log message: {e}")
                    
                    # Create full status panel for log channel (only for work mode)
                    welcome_text = "Yo, this is Sauce. Below you can see the server status. If it's in sleep mode you can still open a ticket and I'll take a look as soon as it switches back to work mode."
                    
                    log_embed = discord.Embed(
                        title="📊 Status",
                        description=f"{welcome_text}\n\n🟢 Active",
                        color=discord.Color.green()
                    )
                    log_view = StatusView(status_type="work")
                    # Use image for work mode
                    if os.path.exists(IMAGE_URL):
                        file_ext = os.path.splitext(IMAGE_URL)[1].lower() or '.png'
                        filename = f"status_image_work_log{file_ext}"
                        log_file = discord.File(IMAGE_URL, filename=filename)
                        log_embed.set_image(url=f"attachment://{filename}")
                        log_message = await log_channel.send("@everyone", embed=log_embed, view=log_view, file=log_file)
                    else:
                        log_embed.set_image(url=IMAGE_URL)
                        log_message = await log_channel.send("@everyone", embed=log_embed, view=log_view)
                    
                    status_log_messages[log_channel_id_str] = log_message.id
                    print(f"✅ Status panel sent to log channel: {log_channel.name}")
            except Exception as e:
                print(f"⚠️  Error sending status panel to log channel: {e}")
                import traceback
                traceback.print_exc()
        
        await interaction.response.send_message(
            f"✅ Status changed to: **{mode}**",
            ephemeral=True
        )
        
    except discord.NotFound:
        await interaction.response.send_message(
            "❌ Status message not found. Create a new one using /setup_status.",
            ephemeral=True
        )
        if channel_id in status_messages:
            del status_messages[channel_id]
            save_status_messages()
    except Exception as e:
        await interaction.response.send_message(
            f"❌ Error updating status: {e}",
            ephemeral=True
        )

# Bot startup
if __name__ == "__main__":
    if not TOKEN or TOKEN == "your_bot_token_here" or TOKEN.strip() == "":
        print("=" * 60)
        print("❌ ERROR: DISCORD_TOKEN not found or not set!")
        print("=" * 60)
        print("\nCheck .env file:")
        print("1. Make sure file is named exactly .env (not .env.txt)")
        print("2. Check that token is specified correctly:")
        print("   DISCORD_TOKEN=your_token_here")
        print("3. Make sure token is copied completely (no spaces)")
        print("4. Token should start with letters and numbers, e.g.: MTIzNDU2...")
        print("\nHow to get token:")
        print("1. Go to https://discord.com/developers/applications")
        print("2. Select your application → Bot → Reset Token")
        print("3. Copy token and paste into .env file")
        print("=" * 60)
        exit(1)
    
    if OWNER_ID == 0:
        print("=" * 60)
        print("⚠️  WARNING: OWNER_ID not set!")
        print("=" * 60)
        print("Bot commands will only be available to you if you specify your Discord ID")
        print("In .env file add: OWNER_ID=your_discord_id")
        print("=" * 60)
        print("\nContinuing startup... (but commands may not work)")
        print()
    
    # Check basic token format (warning, but don't block)
    if len(TOKEN) < 30:
        print("=" * 60)
        print("⚠️  WARNING: Token seems too short!")
        print("=" * 60)
        print("Discord token is usually long (50+ characters)")
        print("Check that token is copied completely")
        print("=" * 60)
        print("\nAttempting connection...")
        print()
    
    # Token diagnostics (safely show start and end)
    print("🔍 Token diagnostics:")
    print(f"   Token length: {len(TOKEN)} characters")
    if len(TOKEN) > 0:
        print(f"   Token start: {TOKEN[:10]}...")
        print(f"   Token end: ...{TOKEN[-10:]}")
    print()
    
    try:
        print("🔄 Connecting to Discord...")
        bot.run(TOKEN)
    except discord.errors.LoginFailure:
        print("=" * 60)
        print("❌ CONNECTION ERROR: Invalid token!")
        print("=" * 60)
        print("\n📋 Check the following:")
        print("1. Token is copied COMPLETELY (usually 59+ characters)")
        print("2. No spaces around = sign in .env file")
        print("3. Token doesn't contain line breaks")
        print("4. Token is current (wasn't reset after copying)")
        print("\n🔧 How to fix:")
        print("1. Open https://discord.com/developers/applications")
        print("2. Select your application → Bot")
        print("3. Click 'Reset Token' → 'Yes, do it!'")
        print("4. Copy NEW token (click 'Copy')")
        print("5. Open .env file in notepad")
        print("6. Make sure line looks like this:")
        print("   DISCORD_TOKEN=your_token_here")
        print("   (NO spaces, NO quotes, NO line breaks)")
        print("7. Save file and restart bot")
        print("\n💡 Example of correct format in .env:")
        print("   DISCORD_TOKEN=MTIzNDU2Nzg5MDEyMzQ1Njc4OQ.GaBcDe.EfGhIjKlMnOpQrStUvWxYz")
        print("=" * 60)
        exit(1)
