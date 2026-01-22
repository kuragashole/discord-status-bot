# Discord Status Bot

## Overview
A Discord bot for managing server status messages with keep-alive functionality for Replit deployment.

## Project Structure
- `bot_replit.py` - Main bot file for Replit (uses keep-alive)
- `bot.py` - Alternative bot file (without keep-alive)
- `keep_alive.py` - Flask server to prevent bot from sleeping
- `sync_commands.py` - Utility to sync Discord slash commands
- `clear_commands.py` - Utility to clear Discord commands
- `requirements.txt` - Python dependencies

## Commands
- `/setup_status` - Create a status message in the current channel
- `/start work|sleep` - Change the status mode

## Environment Variables Required
- `DISCORD_TOKEN` - Your Discord bot token
- `OWNER_ID` - Your Discord user ID
- `IMAGE_URL` - Image URL for work mode (optional)
- `IMAGE_URL_SLEEP` - Image URL for sleep mode (optional)
- `TICKET_CHANNEL_ID` - Channel ID for tickets (optional, set to 0)
- `STATUS_LOG_CHANNEL_ID` - Channel ID for status logs (optional, set to 0)

## Running
The bot runs on port 5000 with a Flask keep-alive server. Use `python bot_replit.py` to start.

## Dependencies
- discord.py>=2.3.2
- python-dotenv>=1.0.0
- flask>=2.3.0
