from telethon import TelegramClient, events
from telethon.tl.types import InputChannel, Photo
from telethon.tl.custom.file import File
import yaml
import discord
import asyncio
import queue

q = queue.Queue()
iq = queue.Queue() #image queue

with open('config.yml', 'rb') as f:
    config = yaml.safe_load(f)


"""
TELEGRAM CLIENT STUFF
"""
client = TelegramClient("forwardgram", config["api_id"], config["api_hash"])
client.start()


input_channels = []


#Find input telegram channels
for d in client.iter_dialogs():
    if (
        d.name in config["input_channel_names"]
        or d.entity.id in config["input_channel_ids"]
    ):
        try:
            input_channels.append(
                InputChannel(d.entity.id, d.entity.access_hash)
            )
        except:
            input_channels.append(d.entity)


for i in input_channels:
    print(i)


#TELEGRAM NEW CHANNEL MESSAGE
@client.on(events.NewMessage(chats=input_channels))
async def handler(event):

    sender = await event.get_sender()
    parsed_response = prefix(sender)
    
    # debugging -- some messages don't have prefixes
    if not parsed_response:
        print(sender)

    if event.message.message:
        parsed_response = parsed_response + event.message.message

        # idk if this is actually doing anything, was in the original so i kept it
        try:
            parsed_response = parsed_response + "\n" + event.message.entities[0].url
            parsed_response = "".join(parsed_response)
        except:
            pass

        q.put(parsed_response)

    if event.message.photo:
        f = event.message.photo
        q.put(f)



def prefix(sender):
    prefix = ""
    try:

        if sender.first_name is not None:
            prefix = sender.first_name
            if sender.last_name is not None:
                prefix = prefix + sender.last_name


    # Or else we only send Message
    except:
        if sender.username is None:
            prefix = "Channel " + sender.title

    if prefix:
        return "`" + prefix + ":` "
    else: 
        return prefix


"""
DISCORD CLIENT STUFF
"""
discord_client = discord.Client()

async def background_task():
    global q
    await discord_client.wait_until_ready()
    discord_channel = discord_client.get_channel(config["discord_channel"])
    while True:
        if not q.empty():
            msg = q.get()
            if type(msg) == str :
                await discord_channel.send(msg)
            elif type(msg)  == Photo:
                pass

        await asyncio.sleep(0.1)

discord_client.loop.create_task(background_task())



"""
RUN EVERYTHING ASYNCHRONOUSLY
"""

print("Listening now")
asyncio.run( discord_client.run(config["discord_bot_token"]) )
asyncio.run( client.run_until_disconnected() )