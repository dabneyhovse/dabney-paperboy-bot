import logging
from enum import Enum

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, User
from telegram.ext import ContextTypes

from paperboy.media import Media, extract_media
from paperboy.printer import JobRequest, get_printers


class JobRequestCallbackType(Enum):
    CANCEL = 0
    SET_PRINTER = 1
    SET_COPIES = 2
    PRINT = 3


def format_job_name(media: Media, user: User) -> str:
    return f"{media.name}_{user.username}_{user.id}"


def generate_keyboard(job: JobRequest) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    printer.get_short_id(),
                    callback_data=(JobRequestCallbackType.SET_PRINTER, printer),
                )
                for printer in get_printers()
            ],
            [
                InlineKeyboardButton(
                    "-1 Copy",
                    callback_data=(
                        JobRequestCallbackType.SET_COPIES,
                        max(job.copies - 1, 0),
                    ),
                ),
                InlineKeyboardButton(
                    "+1 Copy",
                    callback_data=(JobRequestCallbackType.SET_COPIES, job.copies + 1),
                ),
            ],
            [
                InlineKeyboardButton(
                    "❌", callback_data=(JobRequestCallbackType.CANCEL,)
                ),
                InlineKeyboardButton(
                    "🖨️", callback_data=(JobRequestCallbackType.PRINT,)
                ),
            ],
        ]
    )


async def handle_job_request(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    if not (
        (msg := update.message)
        and (author := msg.from_user)
        and (media := await extract_media(msg))
    ):
        return
    logging.info("Received job request from %s for %s", author, media.name)

    job = JobRequest(None, media, format_job_name(media, author))
    reply_markup = generate_keyboard(job)

    new_msg = await msg.reply_text(
        job.get_status(),
        reply_markup=reply_markup,
    )
    context.bot_data[new_msg.id] = job


async def handle_job_request_callback(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    callback_data: tuple[JobRequestCallbackType]
    if not (
        (query := update.callback_query)
        and (callback_data := query.data)  # type: ignore since we're using arbitrary_callback_data
        and (msg := query.message)
    ):
        return
    callback_type, *args = callback_data

    await query.answer()

    req: JobRequest = context.bot_data.get(msg.message_id)  # type: ignore

    match callback_type:
        case JobRequestCallbackType.CANCEL:
            await query.delete_message()
            context.bot_data.pop(msg.message_id, None)
            return
        case JobRequestCallbackType.SET_PRINTER:
            req.printer = args[0]
        case JobRequestCallbackType.SET_COPIES:
            req.copies = args[0]
        case JobRequestCallbackType.PRINT:
            context.bot_data.pop(msg.message_id, None)
            try:
                job_id = await req.create_job()  # throws if no printer
            except Exception as e:
                await query.edit_message_text(text=f"Failed to print document: {e}")
                return
            await query.edit_message_text(
                text=(
                    f"Document sent to {req.printer.get_id()} successfully. The job ID is {job_id}."  # type: ignore
                )
            )
            return
    await query.edit_message_text(req.get_status(), reply_markup=generate_keyboard(req))
