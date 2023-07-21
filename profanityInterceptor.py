import discord
from discord.ext import tasks
import re
import string
import json
from datetime import timedelta


separators = string.punctuation + string.digits + string.whitespace
excluded = string.ascii_letters

pIModeEnabled = True

activeServers = [
  {
    "serverID": 756680992256819251,
    "spamChannelIDs": [756680992772849757]
  },
  {
    "serverID": 915844175428218910,
    "spamChannelIDs": [915844175428218913]
  }
]

#Detect if the user is currently on the watchlist
#If their message contains certain keywords, warn the user.
#Up to three warnings. After the third warning, timeout the user for 10 minutes.
async def blockProfaneMessages(message):
  if isinstance(message.channel, discord.channel.DMChannel):
    return
  if pIModeEnabled:
    with open("profanitylist.json", "r") as f:
      data = f.readlines()
      for num, line in enumerate(data):
        entry = json.loads(line)
        if message.author.id == entry["userID"]:
          if re.search(r"https://media.discordapp.net/attachments", message.content) != None:
            wordsInMessage = re.split("/", message.content)
          elif re.search(r"http.*://", message.content) != None:
            wordsInMessage = re.split("/|-|_", message.content)
          else:
            wordsInMessage = message.content.lower().split()
          profane = await checkForProfanity(wordsInMessage)
          if profane:
            await message.delete()
            entry["totalWarns"] += 1
            await timeoutUser(message = message, reason = "the use of profanity")
            data[num] = json.dumps(entry)
      with open("profanitylist.json", "w") as file:
        for i in range(len(data)):
          file.write(data[i])


@tasks.loop(seconds = 3)
async def checkProfaneNicknames(bot):
  with open("profanitylist.json", "r") as f:
    data = f.readlines()
    for num, line in enumerate(data):
      entry = json.loads(line)
      for s in activeServers:
        server = bot.get_guild(s["serverID"])
        member = server.get_member(entry['userID'])
        if member != None:
          nickname = member.nick
          if nickname != None:
            wordsInNickname = nickname.lower().split()
            profane = await checkForProfanity(wordsInNickname)
            if profane:
              await member.edit(nick = None)
              entry["totalWarns"] += 1
              await timeoutUser(member = member, server = server, nicknames = True)
              data[num] = json.dumps(entry)
      with open("profanitylist.json", "w") as file:
        for i in range(len(data)):
          file.write(data[i])         
        

async def checkForProfanity(wordsInMessage):
  profane = False
  for i in range(len(wordsInMessage)):
    hasPing = re.search(r"<.+>\s*", wordsInMessage[i], re.IGNORECASE)
    if hasPing != None:
      wordsInMessage[i] = wordsInMessage[i][hasPing.end():]
  with open("noNoWords.json", "r") as fi:
    d = fi.readline()
    noNoWords = json.loads(d)["noNoWords"]
    for w in wordsInMessage:
      formatted_word = f"[{separators}]*".join(list(w))
      regex_true = re.compile(fr"{formatted_word}", re.IGNORECASE)
      regex_false = re.compile(fr"([{excluded}]+{w})|({w}[{excluded}]+)", re.IGNORECASE)
      if (regex_true.search(w) is not None and regex_false.search(w) is None) and (re.findall(formatted_word, w, re.IGNORECASE)[0] in noNoWords):
        profane = True
    return profane


@tasks.loop(seconds = 3)
async def checkForSpam(bot):
  with open("profanitylist.json", "r") as f:
    data = f.readlines()
    for num, line in enumerate(data):
      entry = json.loads(line)
      for s in activeServers:
        server = bot.get_guild(s["serverID"])
        for c in s['spamChannelIDs']:
          numSuccessiveMessages = 0
          channel = server.get_channel(c)
          messages = [message async for message in channel.history(limit=5)]
          for m in messages:
            if m.author.id == entry["userID"]:
              numSuccessiveMessages += 1
            else:
              numSuccessiveMessages = 0
            if numSuccessiveMessages >= 5:
              await timeoutUser(message = m, reason = "spam")
              rMessages = [message async for message in channel.history(limit=10)]
              for message in rMessages:
                if message.author.id != entry['userID']:
                  return
                else:
                  await message.delete()


async def timeoutUser(message = None, member = None, server = None, reason = "", nicknames = False):
  duration = timedelta(minutes = 5)
  if nicknames:
    await member.timeout(duration)
    await member.send(f"You have been timed out of **{server}** for **five minutes** for **using a profane nickname**.")
    if server.id == 756680992256819251:
      await server.get_channel(756680992772849757).send(f"<@{member.id}> has been timed out for **five minutes** for **using a profane nickname**.")
    else:
      await server.system_channel.send(f"<@{member.id}> has been timed out for **five minutes** for **using a profane nickname**.")
  else:
    await message.author.timeout(duration)
    await message.author.send(f"You have been timed out of **{message.guild}** for **five minutes** for **{reason}**.")
    await message.channel.send(f"<@{message.author.id}> has been timed out for **five minutes** for **{reason}**.")