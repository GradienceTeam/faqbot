import simplematrixbotlib as botlib
import os
import subprocess
import json
import sys

PREFIX = "!"

USERNAME = os.environ.get("MATRIX_USERNAME", "gradiencefaq")
SERVER = os.environ.get("MATRIX_SERVER", "https://matrix.projectsegfau.lt")
PASSWORD = os.environ.get("MATRIX_PASSWORD", None)
ALIASES = os.environ.get("ALIASES", "faq, f").split(", ")
FAQ_CONFIG = os.environ.get("FAQ_CONFIG", "faq.json")
SYSTEMD_SERVICE_NAME = os.environ.get("SYSTEMD_SERVICE_NAME", "gradiencefaqbot")

HELP = f"""
Help Message:
    prefix: {PREFIX}
    commands:
        faq:
            command: {", ".join(ALIASES)}
            description: display faq for an argument
            example: {PREFIX}faq nightly

        help:
            command: {", ".join(ALIASES)} help, {", ".join(ALIASES)} ?, {", ".join(ALIASES)} h
            description: display help command

        faq all:
            command: {", ".join(ALIASES)} all
            description: display all faq
        
"""


def run():
    if not USERNAME or not SERVER or not PASSWORD:
        print(
            "Please set the environment variables MATRIX_USERNAME(optional), MATRIX_SERVER(optional), and MATRIX_PASSWORD(required)"
        )
        return

    creds = botlib.Creds(SERVER, USERNAME, PASSWORD)
    bot = botlib.Bot(creds)

    FAQ = {}

    @bot.listener.on_message_event
    async def faq(room, message):
        match = botlib.MessageMatch(room, message, bot, PREFIX)

        if match.is_not_from_this_bot() and match.prefix() and ALIASES:
            for alias in ALIASES:
                if match.command(alias):
                    break
            else:
                return

            try:
                prompt = " ".join(arg for arg in match.args())

                global FAQ
                if not FAQ:
                    with open(FAQ_CONFIG) as f:
                        FAQ = json.load(f)

                if prompt == "help" or prompt == "h" or prompt == "?":
                    await bot.api.send_markdown_message(room.room_id, HELP)
                    return

                elif prompt == "all":
                    for key, value in FAQ.items():
                        await bot.api.send_markdown_message(
                            room.room_id, f"> {key}\n\n{value}"
                        )
                else:
                    if prompt in FAQ:
                        response = FAQ[prompt]
                    else:
                        response = "I don't know the answer to that question."

                    await bot.api.send_markdown_message(room.room_id, f"{response}")
            except Exception as e:
                print(e)
                await bot.api.send_markdown_message(room.room_id, f"> {prompt}\n\n{e}")

    try:
        bot.run()
    except Exception as e:
        subprocess.run(["systemctl", "restart", "--user", SYSTEMD_SERVICE_NAME])
        print("Restarting bot due to {e}")
        return 1


if __name__ == "__main__":
    sys.exit(run())
