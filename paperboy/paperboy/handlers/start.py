from telegram import Update
from telegram.ext import ContextTypes


async def handle_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not (msg := update.message):
        return
    await msg.reply_text(
        "Welcome! Please send me a document, photo, or sticker to print."
    )
