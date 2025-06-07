
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

bot.run('bottoken')
