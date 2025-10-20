from typing import Final
import os
from dotenv import load_dotenv
from discord import Intents, Client, Message
from discord.ext import tasks
from responses import ResponseHandler

load_dotenv()
TOKEN: Final[str] = os.getenv("DISCORD_TOKEN")
DISCORD_GENERAL_ID = int(os.getenv("DISCORD_GENERAL_ID"))
DISCORD_TRANSACTIONS_ID = int(os.getenv("DISCORD_TRANSACTIONS_ID"))
RIGOR = os.getenv("RIGOR")
intents: Intents = Intents.default()
intents.message_content = True  # NOQA
client = Client(intents=intents)
response_handler = ResponseHandler()

async def send_message(message: Message, user_message: str) -> None:
    if not user_message:
        print("(Message was empty because intents were probably not enabled)")
        return

    if is_private := user_message[0] == "?":
        user_message = user_message[1:]

    try:
        response: str = response_handler.handle(user_message)
        if response is not None:
            await message.author.send(response) if is_private else await message.channel.send(response)
    except Exception as e:
        print(e)

@tasks.loop(minutes=3.0)
async def update_rosters() -> None:
    try:
        response: str = response_handler.handle("!rosters")
        if response is not None:
            channel = client.get_channel(DISCORD_GENERAL_ID)
            await channel.send(response)
    except Exception as e:
        print(e)
    
    try:
        response: str = response_handler.handle("!transactions")
        if response is not None:
            channel = client.get_channel(DISCORD_TRANSACTIONS_ID)
            await channel.send(response)
    except Exception as e:
        print(e)

    try:
        live_roster_results = response_handler.db.get_managers_and_rosters()
        for manager, roster in live_roster_results:
            message_id = None
            if RIGOR == "DEV":
                channel = client.get_channel(manager.dev_transaction_channel_id)
                message_id = manager.dev_transaction_message_id
            else:
                channel = client.get_channel(manager.transaction_channel_id)
                message_id = manager.transaction_message_id
            response = response_handler.db.display_roster(roster)

            if message_id is None:
                message = await channel.send(response)
                if RIGOR == "DEV":
                    manager.dev_transaction_message_id = message.id
                else:
                    manager.transaction_message_id = message.id
                response_handler.db.db_session.commit()
            else:
                message = await channel.fetch_message(message_id) 
                await message.edit(content=response)


    except Exception as e:
        print(e)


@client.event
async def on_ready() -> None:
    print(f"{client.user} is now running!")
    update_rosters.start()

@client.event
async def on_message(message: Message) -> None:
    if message.author == client.user:
        return

    username: str = str(message.author)
    user_message: str = message.content
    channel: str = str(message.channel)

    print(f"[{channel}] {username}: {user_message}")
    await send_message(message, user_message)

def main():
    client.run(token=TOKEN)

if __name__ == "__main__":
    main()
