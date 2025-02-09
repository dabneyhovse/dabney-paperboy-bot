import logging

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, User
from telegram.ext import ContextTypes

from ..media import Media, extract_media
from ..printer import JobRequest, get_printers


def format_job_name(media: Media, user: User) -> str:
    return f"{media.name}_{user.username}_{user.id}"


async def handle_print_request(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    if not (
        (msg := update.message)
        and (author := msg.from_user)
        and (media := await extract_media(msg))
    ):
        return
    logging.info("Received print request from %s for %s", author, media.name)
    job_name = format_job_name(media, author)

    keyboard = [
        [
            InlineKeyboardButton(
                printer.get_id(),
                callback_data=JobRequest(printer, media, job_name),
            )
        ]
        for printer in get_printers()
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await msg.reply_text(
        f"You're printing a file. Choose the printer you'd like to use:",
        reply_markup=reply_markup,
    )


async def handle_printer_selection(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    req: JobRequest

    if not ((query := update.callback_query) and (req := query.data)):  # type: ignore since we're using arbitrary_callback_data
        return

    await query.answer()
    try:
        job_id = await req.create_job()
    except Exception as e:
        await query.edit_message_text(text=f"Failed to print document: {e}")
        return
    await query.edit_message_text(
        text=(
            f"Document sent to {req.printer.get_id()} successfully. The job ID is {job_id}."
        )
    )
