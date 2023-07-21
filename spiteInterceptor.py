import os
from decouple import config


SPITE_ID = int(config('SPITE_ID'))

#Deletes all messages from spited users in a channel.
async def spiteInterceptor(message):
  if message.author.id == SPITE_ID:
    await message.delete()
