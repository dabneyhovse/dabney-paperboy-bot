import logging
import os

import cups
from dotenv import load_dotenv
from telegram.ext import (
    Application,
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
    MessageHandler,
    filters,
)

from paperboy.handlers.print import handle_job_request, handle_job_request_callback
from paperboy.handlers.start import handle_start

load_dotenv()

BOT_TOKEN = os.getenv("TG_TOKEN", "")
CUPS_SERVER = os.getenv("CUPS_SERVER", "")

logging.getLogger("httpx").setLevel(logging.WARNING)
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)


cups.setServer(CUPS_SERVER)


async def post_init(app: Application) -> None:
    me = await app.bot.get_me()
    app.add_handler(CommandHandler("start", handle_start))
    app.add_handler(
        MessageHandler(
            (filters.ChatType.PRIVATE | filters.Mention(me)),
            handle_job_request,
        )
    )
    app.add_handler(CallbackQueryHandler(handle_job_request_callback))


def main() -> None:

    app = (
        ApplicationBuilder()
        .token(BOT_TOKEN)
        .arbitrary_callback_data(True)
        .post_init(post_init)
        .build()
    )
    app.run_polling()


if __name__ == "__main__":
    main()
