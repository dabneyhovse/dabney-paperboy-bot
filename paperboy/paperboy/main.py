import os
from dotenv import load_dotenv
from sqlitedict import SqliteDict
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

load_dotenv()

BOT_TOKEN = str(os.getenv("TG_TOKEN"))


# logging.basicConfig(
#     format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
# )


async def handle_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not (msg := update.message):
        return


def main() -> None:
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", handle_start))
    # app.add_handler(MessageHandler(filters.Dice.ALL, handle_roll))
    app.run_polling()


if __name__ == "__main__":
    main()
