import discord
from discord import app_commands
from discord.ext import tasks, commands
from writeToJSON import appendToDatabase
from helpInterceptor import helpInterceptor
from profanityInterceptor import blockProfaneMessages, checkProfaneNicknames, checkForSpam 
from spiteInterceptor import spiteInterceptor
from decouple import config
import json
import random
import os
import re


USER_ID = int(config('USER_ID'))

#List of servers to run message checks
#1: Server
#2: The CYBRverse (testing purposes)
activeServerIDs = [756680992256819251, 915844175428218910]

#Used to give the bot privileges to perform its functions.
intents = discord.Intents.default()
intents.members = True
intents.presences = True
intents.message_content = True
intents.guilds = True

#Creates the bot object, with command prefix "/", gives the bot full intents, that were defined previously.
bot = commands.Bot(command_prefix="/", intents = intents)


#Initial bot startup, syncs commands to Discord's API, and lets the user know the the bot is running in the console.
@bot.event
async def on_ready():
  try:
    synced = await bot.tree.sync()
    print(f"Synced {len(synced)} command(s).")
  except Exception as e:
    print(f"Error syncing command(s): {e}")
  print(f"{bot.user} is running!")
  checkProfaneNicknames.start(bot)
  cycleStatus.start(bot)
  checkForSpam.start(bot)


@tasks.loop(seconds = 180)
# #Used to change the bot's status every few minutes
async def cycleStatus(bot):
  statusArr = [
    discord.Activity(type = 1, name = "with fire"),
    discord.Activity(type = discord.ActivityType.watching, name = "you. All the time."),
    discord.Activity(type = discord.ActivityType.listening, name = "messages. 100% of them."),
    discord.Activity(type = discord.ActivityType.watching, name = "the world burn")
  ]
  index = random.randint(0, len(statusArr) - 1)
  await bot.change_presence(activity = statusArr[index])
  

@bot.event
async def on_message(message):
  await helpInterceptor(bot, message)
  if isinstance(message.channel, discord.channel.DMChannel):
    return
  elif message.guild.id in activeServerIDs:
    await blockProfaneMessages(message)
    await spiteInterceptor(message)


async def commandApprovalCheck(interaction: discord.Interaction):
  verify = ("moderate_members", True)
  if verify in interaction.user.guild_permissions:
    return
  else:
    await interaction.response.send_message("You do not have the permissions required to use this command.", ephemeral = True)
    return


def isModerator(member):
  verify = ("moderate_members", True)
  if verify in member.guild_permissions:
    return True
  return False
  

@bot.tree.command(name = "delete", description = "Remove a certain number of the most recent messages in the chat.")
@app_commands.describe(number = "Enter the number of messages to be deleted.")
async def delete(interaction: discord.Interaction, number: int):
  await commandApprovalCheck(interaction)
  if isinstance(interaction.channel, discord.channel.DMChannel):
    await interaction.response.send_message("Cannot use this command in a DM channel.", ephemeral = True)
    return
  if number <= 0:
    await interaction.response.send_message("No messages deleted.", ephemeral = True)
    return
  else:
    await interaction.response.defer(ephemeral = True)
    messages = [message async for message in interaction.channel.history(limit=123)]
    if number > len(messages):
      number = len(messages)
    for i in range(number):
      await interaction.channel.purge(limit = 1)
    await interaction.followup.send(f"Deleted {number} message(s).", ephemeral = True)
    appendToDatabase(user = interaction.user, type = "deleteMessage", numDeleted = number, server = interaction.guild, channel = interaction.channel)

    
@bot.tree.command(name = "ping", description = "Pings a user of your choice a certain number of times.")
@app_commands.describe(user = "Who would you like to ping?", number = "How many times would you like to ping them?")
async def ping(interaction: discord.Interaction, user: str, number: int):
  await commandApprovalCheck(interaction)
  channel = bot.get_channel(interaction.channel_id)
  if user == f"<@{USER_ID}>":
    await interaction.response.send_message("You cannot ping this user.", ephemeral = True)
    return
  else:
    await interaction.response.defer(ephemeral = True)
    for i in range(number):
      message = await channel.send(f"{user}")
      await message.delete()
    await interaction.followup.send(f"Pinged {user} {number} times.", ephemeral = True)
  strippedUserID = re.findall(r"\d+", user)
  appendToDatabase(user = interaction.user, type = "pingMessage", pingedUser = interaction.guild.get_member(int(strippedUserID[0])), numPings = number, server = interaction.guild, channel = interaction.channel)
  return


@bot.tree.command(name="schedule_message", description = "Schedule a message to be sent to a user at a time of your choice.")
@app_commands.describe(user = "Who would you like to send a message to?", time = "When would you like the message to be sent?", message = "Type the message that you would like to send.")
async def schedule_message(interaction: discord.Interaction, user: str, time: str, message: str):
  await interaction.response.send_message("Work in progress, check back soon!", ephemeral = True)
  return


# @bot.tree.command(name = "activity_log", description = "Displays recent actions taken by the bot.")
# async def activity_log(interaction: discord.Interaction):
#   await commandApprovalCheck(interaction.user)
#   with open("database.json", "r") as f:
#     # embed = discord.Embed(title = "Activity Log", color = discord.Color.red(), description = "These are the most recent actions taken by the bot.")
#     # await interaction.response.send_message(embed=embed)
#     await interaction.response.send_message("Work in progress, check back soon!", ephemeral = True)


# @bot.tree.command(name = "vc_log", description = "Displays recent activity in voice channels.")
# async def vc_log(interaction: discord.Interaction):
#   await commandApprovalCheck(interaction.user)
#   with open("database.json", "r") as f:
#     # embed = discord.Embed(title = "Activity Log", color = discord.Color.red(), description = "These are the most recent actions taken by the bot.")
#     # await interaction.response.send_message(embed=embed)
#     await interaction.response.send_message("Work in progress, check back soon!", ephemeral = True)


# @bot.tree.command(name="rat_interception", description = "Enables/disables rat interception.")
# async def rat_interception(interaction: discord.Interaction):
#   await specialCommandApprovalCheck(interaction)
#   global riModeEnabled
#   if riModeEnabled:
#     riModeEnabled = False
#     await interaction.response.send_message("Rat interception mode enabled.")
#   else:
#     riModeEnabled = True
#     await interaction.response.send_message("Rat interception mode disabled.")
  

@bot.tree.command(name = "add_to_watchlist", description = "Adds a user to the watchlist.")
@app_commands.describe(user = "Who would you like to add to the watchlist?")
async def add_to_watchlist(interaction: discord.Interaction, user: str):
  await commandApprovalCheck(interaction)
  strippedPing = re.findall(r"\d+", user, re.IGNORECASE)
  if strippedPing == None:
    await interaction.response.send_message("Invalid user entered.", ephemeral = True)
    return
  userID = strippedPing[0]
  if userID == interaction.user.id:
    await interaction.response.send_message("You cannot add yourself to the watchlist.")
    return
  member = bot.get_guild(interaction.guild.id).get_member(userID)
  if isModerator(member):
    await interaction.response.send_message("You cannot add this user to the watchlist.")
    return
  with open("profanitylist.json", "a+") as f:
    data = f.readlines()
    for num, line in enumerate(data):
      entry = json.loads(line)
      if entry['userID'] == userID:
        await interaction.response.send_message(f"<@{userID}> is already on the watchlist.", ephemeral = True)
        return
    f.write({"userID": userID, 'totalWarns': 0} + "\n")
    await interaction.response.send_message(f"Successfully added <@{userID}> to the watchlist.")
    return


@bot.tree.command(name = "remove_from_watchlist", description = "Removes a user from the watchlist.")
@app_commands.describe(user = "Who would you like to remove from the watchlist?")
async def remove_from_watchlist(interaction: discord.Interaction, user: str):
  await commandApprovalCheck(interaction)
  strippedPing = re.findall(r"\d+", user, re.IGNORECASE)
  if strippedPing == None:
    await interaction.response.send_message("Invalid user entered.", ephemeral = True)
    return
  userID = strippedPing[0]
  if userID == interaction.user.id:
    await interaction.response.send_message("You cannot add yourself to the watchlist.")
    return
  member = bot.get_guild(interaction.guild.id).get_member(userID)
  if isModerator(member):
    await interaction.response.send_message("You cannot add this user to the watchlist.")
    return
  with open("profanitylist.json", "a+") as f:
    data = f.readlines()
    for num, line in enumerate(data):
      entry = json.loads(line)
      if entry['userID'] == userID:
        data.pop(num)
        with open("profanitylist.json", "w") as file:
          for i in range(len(data)):
            file.write(data[i])
          await interaction.response.send_message(f"Removed <@{userID}> from the watchlist.")
          return
    await interaction.response.send_message(f"Removal failed. <@{userID} is not on the watchlist.>")
    return       


TOKEN = config("DISCORD_BOT_SECRET")
bot.run(TOKEN)

keep_alive()