import discord
import json
import os
import re
from writeToJSON import appendToDatabase
from datetime import timedelta
from decouple import config


USER_ID = int(config('USER_ID'))
USER_ID_2 = int(config('USER_ID_2'))

#List of people to be exempted from the help blockade
exemptionIDs = [USER_ID, USER_ID_2]

#List of servers to run message checks
#1: Server
#2: The CYBRverse (testing purposes)
activeServerIDs = [756680992256819251, 915844175428218910]

#List of servers where I have admin powers
moderatedServers = [756680992256819251, 915844175428218910]

sentAwayMessage = False
pingWNoHelp = False

async def helpInterceptor(bot, message):
  global pingWNoHelp
  #Message that tells people to solve their own problems.
  if message.author == bot.user or message.author.id in exemptionIDs:
    return
  if re.findall(r".*help (geoffrey|geo|jeffrey|jeff)+.*", message.content, re.IGNORECASE):
    return

  member = await bot.get_guild(756680992256819251).get_member(USER_ID)
  if member.status != discord.Status.online:
    #For cases where I'm pinged and people want help
    global sentAwayMessage
    if sentAwayMessage == True and re.findall(r".*why.*", message.content, re.IGNORECASE) and isinstance(message.channel, discord.channel.DMChannel):
      await message.author.send(f"<@{USER_ID}> has **unilaterally** decided that they do not wish to continue assisting the people in this server.\n***This decision is final and can't be appealed***.\n__***Solve your own problem and DO NOT CONTACT <@{USER_ID}> for assistance***__.")
      sentAwayMessage = False
      appendToDatabase(user = message.author, type = "whyMessage")
      return
    
    for ping in message.mentions:
      if ping.id == USER_ID and re.findall(r"help|how do|not working|isn't working|what is|how is|what are|do you|can you|would this|is this|how much|is it|where is|how did|how many", message.content, re.IGNORECASE):
        isOffender = userOnWatchlist(message.author.id)
        if not isOffender or isAdminOfProblematicServer(message):
          await message.author.send(await buildAwayMessage(bot, message))
          sentAwayMessage = True
        await processHelpRequest(bot, message, isOffender, isAdminOfProblematicServer(message))
        appendToDatabase(user = message.author, type = "awayMessage", server = message.guild, channel = message.channel)
        return
      else:
        pingWNoHelp = True
        return
        
    #For cases where I'm not pinged, but mentioned by name and people want help
    if re.findall(r"(geoffrey|geo|jeffrey|jeff)+ help.*", message.content, re.IGNORECASE):
      isOffender = userOnWatchlist(message.author.id)
      if not isOffender or isAdminOfProblematicServer(message):
        await message.author.send(await buildAwayMessage(bot, message))
        sentAwayMessage = True
      await processHelpRequest(bot, message, isOffender, isAdminOfProblematicServer(message))
      appendToDatabase(user = message.author, type = "awayMessage", server = message.guild, channel = message.channel)
      return
    elif pingWNoHelp:
      if re.findall(r"help|how do|not working|isn't working|what is|how is|what are|do you|can you|would this|is this|how much|is it|where is|how did|how many", message.content, re.IGNORECASE):
        isOffender = userOnWatchlist(message.author.id)
        if not isOffender or isAdminOfProblematicServer(message):
          await message.author.send(await buildAwayMessage(bot, message))
          sentAwayMessage = True
        await processHelpRequest(bot, message, isOffender, isAdminOfProblematicServer(message))
        appendToDatabase(user = message.author, type = "awayMessage", server = message.guild, channel = message.channel)
      pingWNoHelp = False
      return


async def buildAwayMessage(bot, message):
  mutualServers = []
  for server in activeServerIDs:
    if await bot.get_guild(server).get_member(message.author.id) != None:
      mutualServers.append(await bot.get_guild(server))
  outputOne = f"<@{USER_ID}> is not accepting requests for help from any members of "
  outputTwo = f".\n<@{USER_ID}> has been notified of your attempt to contact them, and they **WILL NOT RESPOND** to any direct messages or calls related to your help request.\n***Solve the problem yourself and __DO NOT CONTACT__ <@{USER_ID}> for assistance***."
  for i in range(len(mutualServers)):
    if mutualServers[i].id in activeServerIDs:
      if i == len(mutualServers) - 1 and len(mutualServers) != 1:
        outputOne += "and "
      outputOne += "**" + str(mutualServers[i]) + "**"
      if i == len(mutualServers) - 2:
        outputOne += " "
      elif i != len(mutualServers) - 1:
        outputOne += ", "
  return outputOne + outputTwo
  

def userOnWatchlist(userID):
  with open("watchlist.json", "r") as f:
    for line in f:
      entry = json.loads(line)
      if entry["userID"] == userID:
        return True
  return False


def isAdminOfProblematicServer(message):
  if message.guild.id == 756680992256819251:
    adminRole = discord.utils.get(message.guild.roles, name = "god")
    if adminRole in message.author.roles:
      return True
  return False
  

async def processHelpRequest(bot, message, isOffender, isAdmin = False):
  masterUser = bot.get_guild(756680992256819251).get_member(USER_ID)
  if isOffender:
    with open("watchlist.json", "r") as f:
      data = f.readlines()
      for num, line in enumerate(data):
        entry = json.loads(line)
        if entry['userID'] != message.author.id:
          continue
        if message.guild.id not in entry["servers"]:
          entry["servers"].append(message.guild.id)
        entry["numRequests"] += 1
        member = message.guild.get_member(entry['userID'])
        if not isAdmin:
          await timeoutEscalation(bot, message, member, entry["numRequests"], entry["servers"])
        else:
          await message.author.send(f"Your position on <@{USER_ID}>'s watchlist of problematic users has increased because of contacting <@{USER_ID} for assistance.")
          await masterUser.send(f"<@{message.author.id}> has repeated their violation of the assistance blockade.\n**Escalation level: {entry['numRequests']}**.\nBegin enacting __***total radio silence for twenty-eight days***__.")
      data[num] = json.dumps(entry)
      
      with open("watchlist.json", "w") as file:
        for i in range(len(data)):
          file.write(data[i])
        
  if not isOffender:
    with open("watchlist.json", "a") as f:
      newWatchedUser = {
        "userID": message.author.id,
        "numRequests": 1,
        "servers": [message.guild.id]
      }
      f.write(json.dumps(newWatchedUser) + "\n")
    await message.author.send(f"This is your **first and only warning**.\nAdditionally, you have been added to a ***watchlist of problematic users***.\nAny further attempts to contact <@{USER_ID}> for assistance will result in **escalating punishments**.")
    await masterUser.send(f"<@{message.author.id}> has violated the assistance blockade and has been added to the watchlist.\n**Escalation Level: 1**.\n<@{message.author.id}> has been issued a warning regarding further consequences should they continue to violate the blockade.")


async def timeoutEscalation(bot, message, member, severity, serverList):
  masterUser = bot.get_guild(message.guild.id).get_member(USER_ID)
  match severity:
    case 2:
      duration = timedelta(minutes = 15)
      time = "fifteen minutes"
      await member.send(buildTimeoutMessage(bot, time, serverList))
      await masterUser.send(buildViolationMessage(bot, member, time, severity, serverList))
    case 3:
      duration = timedelta(minutes = 30)
      time = "thirty minutes"
      await member.send(buildTimeoutMessage(bot, time, serverList))
      await masterUser.send(buildViolationMessage(bot, member, time, severity, serverList))
    case 4:
      duration = timedelta(hours = 1)
      time = "one hour"
      await member.send(buildTimeoutMessage(bot, time, serverList))
      await masterUser.send(buildViolationMessage(bot, member, time, severity, serverList))
    case 5:
      duration = timedelta(hours = 2)
      time = "two hours"
      await member.send(buildTimeoutMessage(bot, time, serverList))
      await masterUser.send(buildViolationMessage(bot, member, time, severity, serverList))
    case 6:
      duration = timedelta(hours = 6)
      time = "six hours"
      await member.send(buildTimeoutMessage(bot, time, serverList))
      await masterUser.send(buildViolationMessage(bot, member, time, severity, serverList))
    case 7:
      duration = timedelta(hours = 12)
      time = "twelve hours"
      await member.send(buildTimeoutMessage(bot, time, serverList))
      await masterUser.send(buildViolationMessage(bot, member, time, severity, serverList))
    case 8:
      duration = timedelta(days = 1)
      time = "twenty-four hours"
      await member.send(buildTimeoutMessage(bot, time, serverList))
      await masterUser.send(buildViolationMessage(bot, member, time, severity, serverList))
    case 9:
      duration = timedelta(days = 2)
      time = "forty-eight hours"
      await member.send(buildTimeoutMessage(bot, time, serverList))
      await masterUser.send(buildViolationMessage(bot, member, time, severity, serverList))
    case 10:
      duration = timedelta(days = 4)
      time = "four days"
      await member.send(buildTimeoutMessage(bot, time, serverList))
      await masterUser.send(buildViolationMessage(bot, member, time, severity, serverList))
    case 11:
      duration = timedelta(days = 7)
      time = "seven days"
      await member.send(buildTimeoutMessage(bot, time, serverList))
      await masterUser.send(buildViolationMessage(bot, member, time, severity, serverList))
    case 12:
      duration = timedelta(days = 14)
      time = "fourteen days"
      await member.send(buildTimeoutMessage(bot, time, serverList))
      await masterUser.send(buildViolationMessage(bot, member, time, severity, serverList))
    case severity if severity > 12:
      duration = timedelta(days = 28)
      time = "twenty-eight days"
      await member.send(buildTimeoutMessage(bot, time, serverList))
      await masterUser.send(buildViolationMessage(bot, member, time, severity, serverList))
  
  for serverID in serverList:
    member = bot.get_guild(serverID).get_member(message.author.id)
    await member.timeout(duration)


def buildTimeoutMessage(bot, time, serverList):
  outputOne = "You have been timed out of "
  for i in range(len(serverList)):
    if i == len(serverList) - 1 and len(serverList) != 1:
      outputOne += "and "
    outputOne += "**" + str(bot.get_guild(serverList[i])) + "**"
    if i == len(serverList) - 2:
      outputOne += " "
    elif i != len(serverList) - 1:
      outputOne += ", "

  outputTwo = f" for **{time}**"
  outputThree = f" for contacting <@{USER_ID}> for assistance.\nFurther offences will ***escalate this punishment***."
  return outputOne + outputTwo + outputThree


def buildViolationMessage(bot, member, time, escalationLevel, serverList):
  outputOne = f"<@{member.id}> has repeated their violation of the assistance blockade.\n**Escalation level: " + str(escalationLevel) + f"**.\n<@{member.id}> has been timed out of "
  for i in range(len(serverList)):
    if i == len(serverList) - 1 and len(serverList) != 1:
      outputOne += "and "
    outputOne += "**" + str(bot.get_guild(serverList[i])) + "**"
    if i == len(serverList) - 2:
      outputOne += " "
    elif i != len(serverList) - 1:
      outputOne += ", "
  outputTwo = " for **" + time + "**."
  return outputOne + outputTwo
