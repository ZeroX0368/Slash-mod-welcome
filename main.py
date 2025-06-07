
import discord
from discord.ext import commands
from discord import app_commands
import asyncio
from datetime import datetime, timedelta
import os

# Bot setup
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix='!', intents=intents)

# Global variables to store data
mute_role_id = None
welcome_data = {}  # Format: {guild_id: {'channel_id': int, 'message': str, 'enabled': bool}}
giveaway_data = {}  # Format: {message_id: {'host': user_id, 'prize': str, 'end_time': datetime, 'channel_id': int, 'guild_id': int, 'winners': int, 'participants': set()}}

@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} command(s)")
    except Exception as e:
        print(f"Failed to sync commands: {e}")

@bot.tree.command(name="ban", description="Ban a user from the server")
@app_commands.describe(user="The user to ban", reason="Reason for the ban")
async def ban(interaction: discord.Interaction, user: discord.Member, reason: str = "No reason provided"):
    if not interaction.user.guild_permissions.ban_members:
        await interaction.response.send_message("❌ You don't have permission to ban members!", ephemeral=True)
        return
    
    try:
        await user.ban(reason=reason)
        await interaction.response.send_message(f"✅ **{user}** has been banned.\n**Reason:** {reason}")
    except discord.Forbidden:
        await interaction.response.send_message("❌ I don't have permission to ban this user!", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"❌ An error occurred: {str(e)}", ephemeral=True)

@bot.tree.command(name="kick", description="Kick a user from the server")
@app_commands.describe(user="The user to kick", reason="Reason for the kick")
async def kick(interaction: discord.Interaction, user: discord.Member, reason: str = "No reason provided"):
    if not interaction.user.guild_permissions.kick_members:
        await interaction.response.send_message("❌ You don't have permission to kick members!", ephemeral=True)
        return
    
    try:
        await user.kick(reason=reason)
        await interaction.response.send_message(f"✅ **{user}** has been kicked.\n**Reason:** {reason}")
    except discord.Forbidden:
        await interaction.response.send_message("❌ I don't have permission to kick this user!", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"❌ An error occurred: {str(e)}", ephemeral=True)

@bot.tree.command(name="unban", description="Unban a user from the server")
@app_commands.describe(user_id="The ID of the user to unban", reason="Reason for the unban")
async def unban(interaction: discord.Interaction, user_id: str, reason: str = "No reason provided"):
    if not interaction.user.guild_permissions.ban_members:
        await interaction.response.send_message("❌ You don't have permission to unban members!", ephemeral=True)
        return
    
    try:
        user_id = int(user_id)
        user = await bot.fetch_user(user_id)
        await interaction.guild.unban(user, reason=reason)
        await interaction.response.send_message(f"✅ **{user}** has been unbanned.\n**Reason:** {reason}")
    except discord.NotFound:
        await interaction.response.send_message("❌ User not found or not banned!", ephemeral=True)
    except ValueError:
        await interaction.response.send_message("❌ Invalid user ID!", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"❌ An error occurred: {str(e)}", ephemeral=True)

@bot.tree.command(name="softban", description="Softban a user (ban then immediately unban to delete messages)")
@app_commands.describe(user="The user to softban", reason="Reason for the softban")
async def softban(interaction: discord.Interaction, user: discord.Member, reason: str = "No reason provided"):
    if not interaction.user.guild_permissions.ban_members:
        await interaction.response.send_message("❌ You don't have permission to ban members!", ephemeral=True)
        return
    
    try:
        await user.ban(reason=f"Softban: {reason}", delete_message_days=7)
        await interaction.guild.unban(user, reason=f"Softban completion: {reason}")
        await interaction.response.send_message(f"✅ **{user}** has been softbanned (messages deleted).\n**Reason:** {reason}")
    except discord.Forbidden:
        await interaction.response.send_message("❌ I don't have permission to ban this user!", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"❌ An error occurred: {str(e)}", ephemeral=True)

@bot.tree.command(name="mute", description="Mute a user")
@app_commands.describe(user="The user to mute", duration="Duration in minutes", reason="Reason for the mute")
async def mute(interaction: discord.Interaction, user: discord.Member, duration: int = None, reason: str = "No reason provided"):
    if not interaction.user.guild_permissions.moderate_members:
        await interaction.response.send_message("❌ You don't have permission to mute members!", ephemeral=True)
        return
    
    global mute_role_id
    mute_role = None
    
    if mute_role_id:
        mute_role = interaction.guild.get_role(mute_role_id)
    
    if not mute_role:
        await interaction.response.send_message("❌ Mute role not set! Use `/setmuterole` first.", ephemeral=True)
        return
    
    try:
        await user.add_roles(mute_role, reason=reason)
        
        if duration:
            await interaction.response.send_message(f"✅ **{user}** has been muted for {duration} minutes.\n**Reason:** {reason}")
            await asyncio.sleep(duration * 60)
            await user.remove_roles(mute_role, reason="Mute duration expired")
        else:
            await interaction.response.send_message(f"✅ **{user}** has been muted indefinitely.\n**Reason:** {reason}")
            
    except discord.Forbidden:
        await interaction.response.send_message("❌ I don't have permission to mute this user!", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"❌ An error occurred: {str(e)}", ephemeral=True)

@bot.tree.command(name="unmute", description="Unmute a user")
@app_commands.describe(user="The user to unmute", reason="Reason for the unmute")
async def unmute(interaction: discord.Interaction, user: discord.Member, reason: str = "No reason provided"):
    if not interaction.user.guild_permissions.moderate_members:
        await interaction.response.send_message("❌ You don't have permission to unmute members!", ephemeral=True)
        return
    
    global mute_role_id
    mute_role = None
    
    if mute_role_id:
        mute_role = interaction.guild.get_role(mute_role_id)
    
    if not mute_role:
        await interaction.response.send_message("❌ Mute role not set! Use `/setmuterole` first.", ephemeral=True)
        return
    
    try:
        await user.remove_roles(mute_role, reason=reason)
        await interaction.response.send_message(f"✅ **{user}** has been unmuted.\n**Reason:** {reason}")
    except discord.Forbidden:
        await interaction.response.send_message("❌ I don't have permission to unmute this user!", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"❌ An error occurred: {str(e)}", ephemeral=True)

@bot.tree.command(name="lock", description="Lock a channel")
@app_commands.describe(channel="The channel to lock", reason="Reason for locking")
async def lock(interaction: discord.Interaction, channel: discord.TextChannel = None, reason: str = "No reason provided"):
    if not interaction.user.guild_permissions.manage_channels:
        await interaction.response.send_message("❌ You don't have permission to manage channels!", ephemeral=True)
        return
    
    channel = channel or interaction.channel
    
    try:
        await channel.set_permissions(interaction.guild.default_role, send_messages=False, reason=reason)
        await interaction.response.send_message(f"🔒 **{channel.mention}** has been locked.\n**Reason:** {reason}")
    except discord.Forbidden:
        await interaction.response.send_message("❌ I don't have permission to lock this channel!", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"❌ An error occurred: {str(e)}", ephemeral=True)

@bot.tree.command(name="unlock", description="Unlock a channel")
@app_commands.describe(channel="The channel to unlock", reason="Reason for unlocking")
async def unlock(interaction: discord.Interaction, channel: discord.TextChannel = None, reason: str = "No reason provided"):
    if not interaction.user.guild_permissions.manage_channels:
        await interaction.response.send_message("❌ You don't have permission to manage channels!", ephemeral=True)
        return
    
    channel = channel or interaction.channel
    
    try:
        await channel.set_permissions(interaction.guild.default_role, send_messages=None, reason=reason)
        await interaction.response.send_message(f"🔓 **{channel.mention}** has been unlocked.\n**Reason:** {reason}")
    except discord.Forbidden:
        await interaction.response.send_message("❌ I don't have permission to unlock this channel!", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"❌ An error occurred: {str(e)}", ephemeral=True)

@bot.tree.command(name="lockall", description="Lock all channels in the server")
@app_commands.describe(reason="Reason for locking all channels")
async def lockall(interaction: discord.Interaction, reason: str = "No reason provided"):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("❌ You need administrator permission to lock all channels!", ephemeral=True)
        return
    
    await interaction.response.defer()
    
    locked_channels = []
    failed_channels = []
    
    for channel in interaction.guild.text_channels:
        try:
            await channel.set_permissions(interaction.guild.default_role, send_messages=False, reason=reason)
            locked_channels.append(channel.name)
        except:
            failed_channels.append(channel.name)
    
    response = f"🔒 **Locked {len(locked_channels)} channels**\n**Reason:** {reason}"
    if failed_channels:
        response += f"\n❌ **Failed to lock:** {', '.join(failed_channels[:5])}"
        if len(failed_channels) > 5:
            response += f" and {len(failed_channels) - 5} more..."
    
    await interaction.followup.send(response)

@bot.tree.command(name="unlockall", description="Unlock all channels in the server")
@app_commands.describe(reason="Reason for unlocking all channels")
async def unlockall(interaction: discord.Interaction, reason: str = "No reason provided"):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("❌ You need administrator permission to unlock all channels!", ephemeral=True)
        return
    
    await interaction.response.defer()
    
    unlocked_channels = []
    failed_channels = []
    
    for channel in interaction.guild.text_channels:
        try:
            await channel.set_permissions(interaction.guild.default_role, send_messages=None, reason=reason)
            unlocked_channels.append(channel.name)
        except:
            failed_channels.append(channel.name)
    
    response = f"🔓 **Unlocked {len(unlocked_channels)} channels**\n**Reason:** {reason}"
    if failed_channels:
        response += f"\n❌ **Failed to unlock:** {', '.join(failed_channels[:5])}"
        if len(failed_channels) > 5:
            response += f" and {len(failed_channels) - 5} more..."
    
    await interaction.followup.send(response)

@bot.tree.command(name="clear", description="Clear messages from a channel")
@app_commands.describe(amount="Number of messages to delete (1-100)", channel="Channel to clear messages from")
async def clear(interaction: discord.Interaction, amount: int, channel: discord.TextChannel = None):
    if not interaction.user.guild_permissions.manage_messages:
        await interaction.response.send_message("❌ You don't have permission to manage messages!", ephemeral=True)
        return
    
    if amount < 1 or amount > 100:
        await interaction.response.send_message("❌ Amount must be between 1 and 100!", ephemeral=True)
        return
    
    channel = channel or interaction.channel
    
    try:
        deleted = await channel.purge(limit=amount)
        await interaction.response.send_message(f"✅ Deleted {len(deleted)} messages from {channel.mention}!", ephemeral=True)
    except discord.Forbidden:
        await interaction.response.send_message("❌ I don't have permission to delete messages in this channel!", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"❌ An error occurred: {str(e)}", ephemeral=True)

@bot.tree.command(name="setmuterole", description="Set the mute role for the server")
@app_commands.describe(role="The role to use for muting users")
async def setmuterole(interaction: discord.Interaction, role: discord.Role):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("❌ You need administrator permission to set the mute role!", ephemeral=True)
        return
    
    global mute_role_id
    mute_role_id = role.id
    
    await interaction.response.send_message(f"✅ Mute role set to **{role.name}**!")

# Welcome System Commands
@bot.tree.command(name="welcome", description="Main welcome system command")
async def welcome_main(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.manage_guild:
        await interaction.response.send_message("❌ You don't have permission to manage welcome settings!", ephemeral=True)
        return
    
    guild_id = interaction.guild.id
    welcome_config = welcome_data.get(guild_id, {})
    
    embed = discord.Embed(title="🎉 Welcome System", color=0x00ff00)
    
    if welcome_config:
        channel = interaction.guild.get_channel(welcome_config.get('channel_id'))
        channel_name = channel.mention if channel else "❌ Channel not found"
        status = "✅ Enabled" if welcome_config.get('enabled', False) else "❌ Disabled"
        
        embed.add_field(name="Status", value=status, inline=True)
        embed.add_field(name="Channel", value=channel_name, inline=True)
        embed.add_field(name="Message Preview", value=welcome_config.get('message', 'No message set')[:100] + "..." if len(welcome_config.get('message', '')) > 100 else welcome_config.get('message', 'No message set'), inline=False)
    else:
        embed.add_field(name="Status", value="❌ Not configured", inline=False)
        embed.description = "Use `/welcome create` to set up the welcome system."
    
    embed.set_footer(text="Use /welcome <subcommand> to manage settings")
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="welcome-info", description="Show detailed welcome system information")
async def welcome_info(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.manage_guild:
        await interaction.response.send_message("❌ You don't have permission to view welcome settings!", ephemeral=True)
        return
    
    guild_id = interaction.guild.id
    welcome_config = welcome_data.get(guild_id, {})
    
    embed = discord.Embed(title="🎉 Welcome System Information", color=0x0099ff)
    
    if welcome_config:
        channel = interaction.guild.get_channel(welcome_config.get('channel_id'))
        channel_name = channel.mention if channel else "❌ Channel not found"
        status = "✅ Enabled" if welcome_config.get('enabled', False) else "❌ Disabled"
        
        embed.add_field(name="Status", value=status, inline=True)
        embed.add_field(name="Welcome Channel", value=channel_name, inline=True)
        embed.add_field(name="Full Message", value=welcome_config.get('message', 'No message set'), inline=False)
        
        embed.add_field(name="Available Variables", value="`{user}` - User mention\n`{username}` - Username\n`{server}` - Server name\n`{membercount}` - Member count", inline=False)
    else:
        embed.description = "❌ Welcome system is not configured for this server.\nUse `/welcome-create` to set it up."
    
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="welcome-preview", description="Preview how the welcome message will look")
async def welcome_preview(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.manage_guild:
        await interaction.response.send_message("❌ You don't have permission to preview welcome messages!", ephemeral=True)
        return
    
    guild_id = interaction.guild.id
    welcome_config = welcome_data.get(guild_id, {})
    
    if not welcome_config or not welcome_config.get('message'):
        await interaction.response.send_message("❌ No welcome message configured! Use `/welcome-create` first.", ephemeral=True)
        return
    
    # Format the message with sample data
    message = welcome_config['message']
    formatted_message = message.replace('{user}', interaction.user.mention)
    formatted_message = formatted_message.replace('{username}', interaction.user.display_name)
    formatted_message = formatted_message.replace('{server}', interaction.guild.name)
    formatted_message = formatted_message.replace('{membercount}', str(interaction.guild.member_count))
    
    embed = discord.Embed(title="🎉 Welcome Message Preview", description=formatted_message, color=0x00ff00)
    embed.set_footer(text="This is how the welcome message will appear for new members")
    
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="welcome-create", description="Create/setup the welcome system")
@app_commands.describe(channel="The channel where welcome messages will be sent", message="The welcome message (use {user}, {username}, {server}, {membercount})")
async def welcome_create(interaction: discord.Interaction, channel: discord.TextChannel, message: str):
    if not interaction.user.guild_permissions.manage_guild:
        await interaction.response.send_message("❌ You don't have permission to manage welcome settings!", ephemeral=True)
        return
    
    guild_id = interaction.guild.id
    
    # Check if bot can send messages in the channel
    if not channel.permissions_for(interaction.guild.me).send_messages:
        await interaction.response.send_message(f"❌ I don't have permission to send messages in {channel.mention}!", ephemeral=True)
        return
    
    welcome_data[guild_id] = {
        'channel_id': channel.id,
        'message': message,
        'enabled': True
    }
    
    embed = discord.Embed(title="✅ Welcome System Created", color=0x00ff00)
    embed.add_field(name="Channel", value=channel.mention, inline=True)
    embed.add_field(name="Status", value="✅ Enabled", inline=True)
    embed.add_field(name="Message", value=message, inline=False)
    embed.set_footer(text="Welcome system is now active!")
    
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="welcome-change", description="Change welcome message or channel")
@app_commands.describe(channel="New welcome channel (optional)", message="New welcome message (optional)")
async def welcome_change(interaction: discord.Interaction, channel: discord.TextChannel = None, message: str = None):
    if not interaction.user.guild_permissions.manage_guild:
        await interaction.response.send_message("❌ You don't have permission to manage welcome settings!", ephemeral=True)
        return
    
    guild_id = interaction.guild.id
    
    if guild_id not in welcome_data:
        await interaction.response.send_message("❌ Welcome system not configured! Use `/welcome-create` first.", ephemeral=True)
        return
    
    if not channel and not message:
        await interaction.response.send_message("❌ You must specify either a new channel or a new message!", ephemeral=True)
        return
    
    changes = []
    
    if channel:
        if not channel.permissions_for(interaction.guild.me).send_messages:
            await interaction.response.send_message(f"❌ I don't have permission to send messages in {channel.mention}!", ephemeral=True)
            return
        welcome_data[guild_id]['channel_id'] = channel.id
        changes.append(f"Channel updated to {channel.mention}")
    
    if message:
        welcome_data[guild_id]['message'] = message
        changes.append("Welcome message updated")
    
    embed = discord.Embed(title="✅ Welcome System Updated", color=0x00ff00)
    embed.description = "\n".join(changes)
    
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="welcome-delete", description="Delete/disable the welcome system")
async def welcome_delete(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.manage_guild:
        await interaction.response.send_message("❌ You don't have permission to manage welcome settings!", ephemeral=True)
        return
    
    guild_id = interaction.guild.id
    
    if guild_id not in welcome_data:
        await interaction.response.send_message("❌ Welcome system is not configured!", ephemeral=True)
        return
    
    del welcome_data[guild_id]
    
    embed = discord.Embed(title="✅ Welcome System Deleted", description="Welcome system has been completely removed from this server.", color=0xff0000)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="welcome-text", description="Update only the welcome message text")
@app_commands.describe(message="The new welcome message")
async def welcome_text(interaction: discord.Interaction, message: str):
    if not interaction.user.guild_permissions.manage_guild:
        await interaction.response.send_message("❌ You don't have permission to manage welcome settings!", ephemeral=True)
        return
    
    guild_id = interaction.guild.id
    
    if guild_id not in welcome_data:
        await interaction.response.send_message("❌ Welcome system not configured! Use `/welcome-create` first.", ephemeral=True)
        return
    
    welcome_data[guild_id]['message'] = message
    
    embed = discord.Embed(title="✅ Welcome Message Updated", color=0x00ff00)
    embed.add_field(name="New Message", value=message, inline=False)
    
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="welcome-toggle", description="Enable or disable the welcome system")
async def welcome_toggle(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.manage_guild:
        await interaction.response.send_message("❌ You don't have permission to manage welcome settings!", ephemeral=True)
        return
    
    guild_id = interaction.guild.id
    
    if guild_id not in welcome_data:
        await interaction.response.send_message("❌ Welcome system not configured! Use `/welcome-create` first.", ephemeral=True)
        return
    
    current_status = welcome_data[guild_id].get('enabled', True)
    welcome_data[guild_id]['enabled'] = not current_status
    
    new_status = "✅ Enabled" if not current_status else "❌ Disabled"
    color = 0x00ff00 if not current_status else 0xff0000
    
    embed = discord.Embed(title=f"Welcome System {new_status.split()[1]}", color=color)
    embed.add_field(name="Status", value=new_status, inline=False)
    
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="help", description="Display all available bot commands with descriptions")
async def help_command(interaction: discord.Interaction):
    commands_data = [
        ("🔨 **Moderation Commands**", [
            ("`/mute <user> [duration] [reason]`", "Temporarily mute a user"),
            ("`/unmute <user> [reason]`", "Unmute a user"),
            ("`/timeout <user> <duration> [reason]`", "Timeout a user"),
            ("`/kick <user> [reason]`", "Kick a user from the server"),
            ("`/ban <user> [reason]`", "Ban a user from the server"),
            ("`/unban <user_id> [reason]`", "Unban a user by ID"),
            ("`/set-mute-role <role>`", "Set the mute role for the server")
        ]),
        ("🔒 **Channel Management**", [
            ("`/lockall [reason]`", "Lock all channels in the server"),
            ("`/unlockall [reason]`", "Unlock all channels in the server")
        ]),
        ("🎉 **Welcome System**", [
            ("`/welcome`", "View welcome system status"),
            ("`/welcome-create <channel> <message>`", "Set up welcome system"),
            ("`/welcome-change [channel] [message]`", "Update welcome settings"),
            ("`/welcome-text <message>`", "Update welcome message only"),
            ("`/welcome-toggle`", "Enable/disable welcome system"),
            ("`/welcome-delete`", "Delete welcome system"),
            ("`/welcome-info`", "Show detailed welcome information"),
            ("`/welcome-preview`", "Preview welcome message"),
            ("`/welcome-format`", "Show formatting options")
        ]),
        ("📋 **Server Information**", [
            ("`/roles`", "Display server roles with pagination"),
            ("`/help`", "Show this help menu")
        ]),
        ("🎁 **Giveaway Commands**", [
            ("`/giveaway-create <prize> <duration> [winners] [channel]`", "Create a new giveaway"),
            ("`/giveaway-delete <message_id>`", "Delete a giveaway"),
            ("`/giveaway-edit <message_id> [prize] [duration] [winners]`", "Edit a giveaway"),
            ("`/giveaway-end <message_id>`", "End a giveaway early"),
            ("`/giveaway-reroll <message_id> [winners]`", "Reroll giveaway winners")
        ])
    ]
    
    # Pagination setup
    commands_per_page = 2  # Show 2 categories per page
    total_pages = len(commands_data)
    current_page = 0
    
    def create_embed(page):
        embed = discord.Embed(
            title="🤖 Bot Commands Help",
            color=0x0099ff,
            timestamp=datetime.now()
        )
        
        category_name, commands = commands_data[page]
        embed.add_field(name=category_name, value="\n".join([f"{cmd} - {desc}" for cmd, desc in commands]), inline=False)
        
        embed.set_footer(text=f"Page {page + 1}/{total_pages} • Use buttons to navigate")
        return embed
    
    def create_view(page):
        view = discord.ui.View(timeout=300)
        
        # Previous button
        prev_button = discord.ui.Button(
            label="◀ Previous",
            style=discord.ButtonStyle.primary,
            disabled=page == 0
        )
        
        async def prev_callback(button_interaction):
            nonlocal current_page
            current_page = max(0, current_page - 1)
            embed = create_embed(current_page)
            view = create_view(current_page)
            await button_interaction.response.edit_message(embed=embed, view=view)
        
        prev_button.callback = prev_callback
        view.add_item(prev_button)
        
        # Page indicator
        page_button = discord.ui.Button(
            label=f"{page + 1}/{total_pages}",
            style=discord.ButtonStyle.secondary,
            disabled=True
        )
        view.add_item(page_button)
        
        # Next button
        next_button = discord.ui.Button(
            label="Next ▶",
            style=discord.ButtonStyle.primary,
            disabled=page >= total_pages - 1
        )
        
        async def next_callback(button_interaction):
            nonlocal current_page
            current_page = min(total_pages - 1, current_page + 1)
            embed = create_embed(current_page)
            view = create_view(current_page)
            await button_interaction.response.edit_message(embed=embed, view=view)
        
        next_button.callback = next_callback
        view.add_item(next_button)
        
        return view
    
    embed = create_embed(current_page)
    view = create_view(current_page)
    
    await interaction.response.send_message(embed=embed, view=view)

@bot.tree.command(name="welcome-format", description="Show available formatting options for welcome messages")
async def welcome_format(interaction: discord.Interaction):
    embed = discord.Embed(title="🎨 Welcome Message Formatting", color=0x0099ff)
    
    embed.add_field(name="Available Variables", value="`{user}` - Mentions the new user\n`{username}` - User's display name\n`{server}` - Server name\n`{membercount}` - Current member count", inline=False)
    
    embed.add_field(name="Example Message", value="Welcome {user} to **{server}**! 🎉\nYou are our {membercount}th member!", inline=False)
    
    embed.add_field(name="Result", value=f"Welcome {interaction.user.mention} to **{interaction.guild.name}**! 🎉\nYou are our {interaction.guild.member_count}th member!", inline=False)
    
    embed.set_footer(text="Use these variables in your welcome message for dynamic content!")
    
    await interaction.response.send_message(embed=embed, ephemeral=True)

# Role Info Command with Pagination
@bot.tree.command(name="roles", description="Display server roles with pagination")
async def role_info(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.manage_roles:
        await interaction.response.send_message("❌ You don't have permission to view role information!", ephemeral=True)
        return
    
    roles = [role for role in interaction.guild.roles if role != interaction.guild.default_role]
    roles.sort(key=lambda r: r.position, reverse=True)
    
    if not roles:
        await interaction.response.send_message("❌ No roles found in this server!", ephemeral=True)
        return
    
    # Pagination setup
    roles_per_page = 10
    total_pages = (len(roles) + roles_per_page - 1) // roles_per_page
    current_page = 0
    
    def create_embed(page):
        start_idx = page * roles_per_page
        end_idx = min(start_idx + roles_per_page, len(roles))
        page_roles = roles[start_idx:end_idx]
        
        embed = discord.Embed(
            title=f"📋 Server Roles ({len(roles)} total)",
            color=0x0099ff,
            timestamp=datetime.now()
        )
        
        role_list = []
        for role in page_roles:
            role_list.append(f"{role.mention} `({role.id})`")
        
        embed.description = "\n".join(role_list)
        embed.set_footer(text=f"Page {page + 1}/{total_pages} • {interaction.guild.name}")
        
        return embed
    
    def create_view(page):
        view = discord.ui.View(timeout=300)
        
        # Previous button
        prev_button = discord.ui.Button(
            label="◀️ Previous",
            style=discord.ButtonStyle.secondary,
            disabled=(page == 0)
        )
        
        async def prev_callback(button_interaction):
            nonlocal current_page
            current_page = max(0, current_page - 1)
            embed = create_embed(current_page)
            view = create_view(current_page)
            await button_interaction.response.edit_message(embed=embed, view=view)
        
        prev_button.callback = prev_callback
        view.add_item(prev_button)
        
        # Page indicator
        page_button = discord.ui.Button(
            label=f"{page + 1}/{total_pages}",
            style=discord.ButtonStyle.primary,
            disabled=True
        )
        view.add_item(page_button)
        
        # Next button
        next_button = discord.ui.Button(
            label="Next ▶️",
            style=discord.ButtonStyle.secondary,
            disabled=(page >= total_pages - 1)
        )
        
        async def next_callback(button_interaction):
            nonlocal current_page
            current_page = min(total_pages - 1, current_page + 1)
            embed = create_embed(current_page)
            view = create_view(current_page)
            await button_interaction.response.edit_message(embed=embed, view=view)
        
        next_button.callback = next_callback
        view.add_item(next_button)
        
        # Refresh button
        refresh_button = discord.ui.Button(
            label="🔄 Refresh",
            style=discord.ButtonStyle.success
        )
        
        async def refresh_callback(button_interaction):
            # Refresh the roles list
            updated_roles = [role for role in button_interaction.guild.roles if role != button_interaction.guild.default_role]
            updated_roles.sort(key=lambda r: r.position, reverse=True)
            nonlocal roles, total_pages, current_page
            roles = updated_roles
            total_pages = (len(roles) + roles_per_page - 1) // roles_per_page
            current_page = min(current_page, total_pages - 1) if total_pages > 0 else 0
            
            embed = create_embed(current_page)
            view = create_view(current_page)
            await button_interaction.response.edit_message(embed=embed, view=view)
        
        refresh_button.callback = refresh_callback
        view.add_item(refresh_button)
        
        return view
    
    embed = create_embed(current_page)
    view = create_view(current_page)
    
    await interaction.response.send_message(embed=embed, view=view)

# Giveaway Commands
@bot.tree.command(name="giveaway-create", description="Create a new giveaway")
@app_commands.describe(
    prize="What you're giving away",
    duration="Duration (e.g., 1h, 30m, 2d)",
    winners="Number of winners (default: 1)",
    channel="Channel to post giveaway (default: current channel)"
)
async def giveaway_create(interaction: discord.Interaction, prize: str, duration: str, winners: int = 1, channel: discord.TextChannel = None):
    if not interaction.user.guild_permissions.manage_messages:
        await interaction.response.send_message("❌ You don't have permission to create giveaways!", ephemeral=True)
        return
    
    if winners < 1:
        await interaction.response.send_message("❌ Number of winners must be at least 1!", ephemeral=True)
        return
    
    # Parse duration
    try:
        time_units = {'s': 1, 'm': 60, 'h': 3600, 'd': 86400}
        duration_lower = duration.lower()
        
        if duration_lower[-1] in time_units:
            time_value = int(duration_lower[:-1])
            time_unit = duration_lower[-1]
            total_seconds = time_value * time_units[time_unit]
        else:
            raise ValueError("Invalid format")
        
        if total_seconds < 60:  # Minimum 1 minute
            await interaction.response.send_message("❌ Minimum giveaway duration is 1 minute!", ephemeral=True)
            return
        
        if total_seconds > 2592000:  # Maximum 30 days
            await interaction.response.send_message("❌ Maximum giveaway duration is 30 days!", ephemeral=True)
            return
            
    except (ValueError, IndexError):
        await interaction.response.send_message("❌ Invalid duration format! Use format like: 1h, 30m, 2d", ephemeral=True)
        return
    
    channel = channel or interaction.channel
    
    if not channel.permissions_for(interaction.guild.me).send_messages:
        await interaction.response.send_message(f"❌ I don't have permission to send messages in {channel.mention}!", ephemeral=True)
        return
    
    end_time = datetime.now() + timedelta(seconds=total_seconds)
    
    # Create giveaway embed
    embed = discord.Embed(title="🎉 GIVEAWAY 🎉", color=0xff6b6b)
    embed.add_field(name="Prize", value=prize, inline=False)
    embed.add_field(name="Hosted by", value=interaction.user.mention, inline=True)
    embed.add_field(name="Winners", value=str(winners), inline=True)
    embed.add_field(name="Ends", value=f"<t:{int(end_time.timestamp())}:R>", inline=True)
    embed.add_field(name="How to enter", value="React with 🎉 to enter!", inline=False)
    embed.set_footer(text="Good luck!")
    embed.timestamp = end_time
    
    # Create join button
    class GiveawayView(discord.ui.View):
        def __init__(self):
            super().__init__(timeout=None)
        
        @discord.ui.button(label="🎉 Join Giveaway", style=discord.ButtonStyle.green, custom_id="join_giveaway")
        async def join_giveaway(self, button_interaction: discord.Interaction, button: discord.ui.Button):
            message_id = button_interaction.message.id
            giveaway = giveaway_data.get(message_id)
            
            if not giveaway:
                await button_interaction.response.send_message("❌ This giveaway no longer exists!", ephemeral=True)
                return
            
            if datetime.now() >= giveaway['end_time']:
                await button_interaction.response.send_message("❌ This giveaway has already ended!", ephemeral=True)
                return
            
            user_id = button_interaction.user.id
            
            if user_id in giveaway['participants']:
                giveaway['participants'].remove(user_id)
                await button_interaction.response.send_message("✅ You have left the giveaway!", ephemeral=True)
            else:
                giveaway['participants'].add(user_id)
                await button_interaction.response.send_message("✅ You have joined the giveaway! Good luck!", ephemeral=True)
    
    view = GiveawayView()
    
    try:
        message = await channel.send(embed=embed, view=view)
        
        # Store giveaway data
        giveaway_data[message.id] = {
            'host': interaction.user.id,
            'prize': prize,
            'end_time': end_time,
            'channel_id': channel.id,
            'guild_id': interaction.guild.id,
            'winners': winners,
            'participants': set()
        }
        
        # Update embed to include giveaway ID
        embed.add_field(name="Giveaway ID", value=f"`{message.id}`", inline=True)
        await message.edit(embed=embed, view=view)
        
        # Schedule giveaway end
        asyncio.create_task(schedule_giveaway_end(message.id, total_seconds))
        
        await interaction.response.send_message(f"✅ Giveaway created in {channel.mention}!\n**Giveaway ID:** `{message.id}`", ephemeral=True)
        
    except discord.Forbidden:
        await interaction.response.send_message(f"❌ I don't have permission to send messages in {channel.mention}!", ephemeral=True)

@bot.tree.command(name="giveaway-delete", description="Delete a giveaway")
@app_commands.describe(message_id="The message ID of the giveaway to delete")
async def giveaway_delete(interaction: discord.Interaction, message_id: str):
    if not interaction.user.guild_permissions.manage_messages:
        await interaction.response.send_message("❌ You don't have permission to delete giveaways!", ephemeral=True)
        return
    
    try:
        message_id = int(message_id)
    except ValueError:
        await interaction.response.send_message("❌ Invalid message ID!", ephemeral=True)
        return
    
    giveaway = giveaway_data.get(message_id)
    
    if not giveaway:
        await interaction.response.send_message("❌ Giveaway not found!", ephemeral=True)
        return
    
    if giveaway['host'] != interaction.user.id and not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("❌ You can only delete your own giveaways!", ephemeral=True)
        return
    
    # Try to delete the message
    try:
        channel = bot.get_channel(giveaway['channel_id'])
        if channel:
            message = await channel.fetch_message(message_id)
            await message.delete()
    except:
        pass  # Message might already be deleted
    
    # Remove from data
    del giveaway_data[message_id]
    
    await interaction.response.send_message("✅ Giveaway has been deleted!", ephemeral=True)

@bot.tree.command(name="giveaway-edit", description="Edit a giveaway")
@app_commands.describe(
    message_id="The message ID of the giveaway to edit",
    prize="New prize (optional)",
    duration="New duration (optional, e.g., 1h, 30m, 2d)",
    winners="New number of winners (optional)"
)
async def giveaway_edit(interaction: discord.Interaction, message_id: str, prize: str = None, duration: str = None, winners: int = None):
    if not interaction.user.guild_permissions.manage_messages:
        await interaction.response.send_message("❌ You don't have permission to edit giveaways!", ephemeral=True)
        return
    
    try:
        message_id = int(message_id)
    except ValueError:
        await interaction.response.send_message("❌ Invalid message ID!", ephemeral=True)
        return
    
    giveaway = giveaway_data.get(message_id)
    
    if not giveaway:
        await interaction.response.send_message("❌ Giveaway not found!", ephemeral=True)
        return
    
    if giveaway['host'] != interaction.user.id and not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("❌ You can only edit your own giveaways!", ephemeral=True)
        return
    
    if datetime.now() >= giveaway['end_time']:
        await interaction.response.send_message("❌ Cannot edit an ended giveaway!", ephemeral=True)
        return
    
    changes = []
    
    # Update prize
    if prize:
        giveaway['prize'] = prize
        changes.append("prize")
    
    # Update duration
    if duration:
        try:
            time_units = {'s': 1, 'm': 60, 'h': 3600, 'd': 86400}
            duration_lower = duration.lower()
            
            if duration_lower[-1] in time_units:
                time_value = int(duration_lower[:-1])
                time_unit = duration_lower[-1]
                total_seconds = time_value * time_units[time_unit]
            else:
                raise ValueError("Invalid format")
            
            if total_seconds < 60:
                await interaction.response.send_message("❌ Minimum giveaway duration is 1 minute!", ephemeral=True)
                return
            
            if total_seconds > 2592000:
                await interaction.response.send_message("❌ Maximum giveaway duration is 30 days!", ephemeral=True)
                return
            
            giveaway['end_time'] = datetime.now() + timedelta(seconds=total_seconds)
            changes.append("duration")
            
        except (ValueError, IndexError):
            await interaction.response.send_message("❌ Invalid duration format! Use format like: 1h, 30m, 2d", ephemeral=True)
            return
    
    # Update winners
    if winners:
        if winners < 1:
            await interaction.response.send_message("❌ Number of winners must be at least 1!", ephemeral=True)
            return
        giveaway['winners'] = winners
        changes.append("winners")
    
    if not changes:
        await interaction.response.send_message("❌ You must specify at least one thing to change!", ephemeral=True)
        return
    
    # Update the message
    try:
        channel = bot.get_channel(giveaway['channel_id'])
        message = await channel.fetch_message(message_id)
        
        embed = discord.Embed(title="🎉 GIVEAWAY 🎉", color=0xff6b6b)
        embed.add_field(name="Prize", value=giveaway['prize'], inline=False)
        embed.add_field(name="Hosted by", value=f"<@{giveaway['host']}>", inline=True)
        embed.add_field(name="Winners", value=str(giveaway['winners']), inline=True)
        embed.add_field(name="Ends", value=f"<t:{int(giveaway['end_time'].timestamp())}:R>", inline=True)
        embed.add_field(name="How to enter", value="React with 🎉 to enter!", inline=False)
        embed.set_footer(text="Good luck! (Edited)")
        embed.timestamp = giveaway['end_time']
        
        await message.edit(embed=embed)
        
        await interaction.response.send_message(f"✅ Giveaway updated! Changed: {', '.join(changes)}", ephemeral=True)
        
    except discord.NotFound:
        await interaction.response.send_message("❌ Giveaway message not found!", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"❌ An error occurred: {str(e)}", ephemeral=True)

@bot.tree.command(name="giveaway-end", description="End a giveaway early")
@app_commands.describe(message_id="The message ID of the giveaway to end")
async def giveaway_end(interaction: discord.Interaction, message_id: str):
    if not interaction.user.guild_permissions.manage_messages:
        await interaction.response.send_message("❌ You don't have permission to end giveaways!", ephemeral=True)
        return
    
    try:
        message_id = int(message_id)
    except ValueError:
        await interaction.response.send_message("❌ Invalid message ID!", ephemeral=True)
        return
    
    giveaway = giveaway_data.get(message_id)
    
    if not giveaway:
        await interaction.response.send_message("❌ Giveaway not found!", ephemeral=True)
        return
    
    if giveaway['host'] != interaction.user.id and not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("❌ You can only end your own giveaways!", ephemeral=True)
        return
    
    await end_giveaway(message_id, early=True)
    await interaction.response.send_message("✅ Giveaway has been ended early!", ephemeral=True)

@bot.tree.command(name="giveaway-reroll", description="Reroll giveaway winners")
@app_commands.describe(
    message_id="The message ID of the giveaway to reroll",
    winners="Number of new winners to pick (optional, uses original amount)"
)
async def giveaway_reroll(interaction: discord.Interaction, message_id: str, winners: int = None):
    if not interaction.user.guild_permissions.manage_messages:
        await interaction.response.send_message("❌ You don't have permission to reroll giveaways!", ephemeral=True)
        return
    
    try:
        message_id = int(message_id)
    except ValueError:
        await interaction.response.send_message("❌ Invalid message ID!", ephemeral=True)
        return
    
    # Check if this was a giveaway (might be ended and removed from active data)
    giveaway = giveaway_data.get(message_id)
    
    # Try to get the message to check if it was a giveaway
    try:
        for channel in interaction.guild.text_channels:
            try:
                message = await channel.fetch_message(message_id)
                if message.author == bot.user and message.embeds and "GIVEAWAY" in message.embeds[0].title:
                    break
            except:
                continue
        else:
            await interaction.response.send_message("❌ Giveaway message not found!", ephemeral=True)
            return
    except:
        await interaction.response.send_message("❌ Could not find giveaway message!", ephemeral=True)
        return
    
    if giveaway and datetime.now() < giveaway['end_time']:
        await interaction.response.send_message("❌ Cannot reroll an active giveaway! End it first.", ephemeral=True)
        return
    
    # If no giveaway data, try to get participants from button interactions (limited)
    if not giveaway:
        await interaction.response.send_message("❌ Cannot reroll this giveaway - participant data not available!", ephemeral=True)
        return
    
    participants = list(giveaway['participants'])
    
    if not participants:
        await interaction.response.send_message("❌ No participants to reroll!", ephemeral=True)
        return
    
    winner_count = winners or giveaway['winners']
    winner_count = min(winner_count, len(participants))
    
    import random
    new_winners = random.sample(participants, winner_count)
    
    # Create reroll embed
    embed = discord.Embed(title="🎉 GIVEAWAY REROLLED 🎉", color=0x00ff00)
    embed.add_field(name="Prize", value=giveaway['prize'], inline=False)
    
    if len(new_winners) == 1:
        embed.add_field(name="New Winner", value=f"<@{new_winners[0]}>", inline=False)
    else:
        winners_list = "\n".join([f"<@{winner}>" for winner in new_winners])
        embed.add_field(name="New Winners", value=winners_list, inline=False)
    
    embed.set_footer(text="Congratulations!")
    embed.timestamp = datetime.now()
    
    await interaction.response.send_message(embed=embed)

async def schedule_giveaway_end(message_id: int, delay_seconds: int):
    """Schedule a giveaway to end after the specified delay"""
    await asyncio.sleep(delay_seconds)
    await end_giveaway(message_id)

async def end_giveaway(message_id: int, early: bool = False):
    """End a giveaway and pick winners"""
    giveaway = giveaway_data.get(message_id)
    
    if not giveaway:
        return
    
    participants = list(giveaway['participants'])
    
    try:
        channel = bot.get_channel(giveaway['channel_id'])
        message = await channel.fetch_message(message_id)
        
        # Create ended giveaway embed
        embed = discord.Embed(title="🎉 GIVEAWAY ENDED 🎉", color=0x555555)
        embed.add_field(name="Prize", value=giveaway['prize'], inline=False)
        embed.add_field(name="Hosted by", value=f"<@{giveaway['host']}>", inline=True)
        
        if participants:
            import random
            winner_count = min(giveaway['winners'], len(participants))
            winners = random.sample(participants, winner_count)
            
            if len(winners) == 1:
                embed.add_field(name="Winner", value=f"<@{winners[0]}>", inline=False)
                winner_mentions = f"<@{winners[0]}>"
            else:
                winners_list = "\n".join([f"<@{winner}>" for winner in winners])
                embed.add_field(name="Winners", value=winners_list, inline=False)
                winner_mentions = " ".join([f"<@{winner}>" for winner in winners])
            
            embed.set_footer(text="Congratulations to the winner(s)!" + (" (Ended Early)" if early else ""))
            
            # Send winner announcement
            await channel.send(f"🎉 Congratulations {winner_mentions}! You won **{giveaway['prize']}**!")
            
        else:
            embed.add_field(name="Winner", value="No participants", inline=False)
            embed.set_footer(text="No one participated in this giveaway" + (" (Ended Early)" if early else ""))
        
        embed.timestamp = datetime.now()
        
        # Update the original message
        await message.edit(embed=embed, view=None)
        
    except Exception as e:
        print(f"Error ending giveaway {message_id}: {e}")
    
    # Remove from active giveaways
    if message_id in giveaway_data:
        del giveaway_data[message_id]

# Welcome event handler
@bot.event
async def on_member_join(member):
    guild_id = member.guild.id
    welcome_config = welcome_data.get(guild_id)
    
    if not welcome_config or not welcome_config.get('enabled', True):
        return
    
    channel = member.guild.get_channel(welcome_config['channel_id'])
    if not channel:
        return
    
    message = welcome_config['message']
    formatted_message = message.replace('{user}', member.mention)
    formatted_message = formatted_message.replace('{username}', member.display_name)
    formatted_message = formatted_message.replace('{server}', member.guild.name)
    formatted_message = formatted_message.replace('{membercount}', str(member.guild.member_count))
    
    try:
        embed = discord.Embed(description=formatted_message, color=0x00ff00)
        embed.set_author(name=f"Welcome to {member.guild.name}!", icon_url=member.avatar.url if member.avatar else member.default_avatar.url)
        embed.set_thumbnail(url=member.avatar.url if member.avatar else member.default_avatar.url)
        embed.timestamp = datetime.now()
        
        await channel.send(embed=embed)
    except:
        # Fallback to plain text if embed fails
        await channel.send(formatted_message)

bot.run('Bottoken')
