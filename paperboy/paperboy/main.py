import os
from dotenv import load_dotenv
from telegram import (
    Update,
    Document,
    User,
    Message,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
    PicklePersistence,
)
from telegram.helpers import escape_markdown
from telegram.constants import ParseMode, MessageEntityType

import io
import cups
from http import HTTPStatus

load_dotenv()

BOT_TOKEN = os.getenv("TG_TOKEN") or ""
CUPS_SERVER = os.getenv("CUPS_SERVER")

cups.setServer(CUPS_SERVER)


async def download_document(document: Document) -> bytes:
    file = await document.get_file()
    file_bytes = io.BytesIO()
    await file.download_to_memory(file_bytes)
    file_bytes.seek(0)
    return file_bytes.getvalue()


def format_job_name(document: Document, user: User) -> str:
    return f"{document.file_name}_{user.username}_{user.id}"


async def create_job(printer: str, data: bytes, mime_type: str, job_title: str) -> int:
    conn = cups.Connection()

    job_id = conn.createJob(printer, job_title, {})
    if not job_id:
        raise Exception(f"Failed to create job: {cups.lastErrorString()}")

    if (
        conn.startDocument(printer, job_id, job_title, mime_type, True)
        != HTTPStatus.CONTINUE
    ):
        raise Exception(f"Failed to start document: {cups.lastErrorString()}")

    if conn.writeRequestData(data, len(data)) != HTTPStatus.CONTINUE:
        raise Exception(f"Failed to write request data: {cups.lastErrorString()}")

    ipp_status = conn.finishDocument(printer)
    if ipp_status != cups.IPP_STATUS_OK:
        raise Exception(f"Failed to finish document: {cups.ippErrorString(ipp_status)}")

    return job_id


async def handle_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not (msg := update.message):
        return
    await msg.reply_text("Welcome! Please send me a document to print.")


async def handle_print(msg: Message, document: Document, author: User) -> None:
    conn = cups.Connection()
    document_data = await download_document(document)
    mime_type = document.mime_type

    keyboard = [
        [
            InlineKeyboardButton(
                f"{name}, {data["printer-location"]}",
                callback_data={
                    "printer": {
                        "name": name,
                        "data": data,
                    },
                    "document_data": document_data,
                    "mime_type": mime_type,
                    "job_title": format_job_name(document, author),
                },
            )
        ]
        for name, data in conn.getPrinters().items()
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await msg.reply_text(
        f"You're printing {document.file_name}. Choose the printer you'd like to use:",
        reply_markup=reply_markup,
    )


async def handle_dm_print(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if (
        not (msg := update.message)
        or not (document := msg.document)
        or not (author := msg.from_user)
    ):
        return
    await handle_print(msg, document, author)


async def handle_reply_print(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    if (
        not (msg := update.message)
        or not (document_msg := msg.reply_to_message)
        or not (document := document_msg.document)
        or not (author := msg.from_user)
    ):
        return
    await handle_print(msg, document, author)


async def handle_printer_selection(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    if not (query := update.callback_query) or not (data := query.data):
        return

    await query.answer()

        printer = data["printer"]  # type: ignore
    try:
        job_id = await create_job(
            printer["name"], data["document_data"], data["mime_type"], data["job_title"]  # type: ignore
        )
    except Exception as e:
        await query.edit_message_text(text=f"Failed to print document: {e}")
        return
    await query.edit_message_text(
        text=f"Document sent to {printer['name']}, {printer['data']['printer-location']} successfully. Job ID: {job_id}"  # type: ignore
    )



def main() -> None:
    persistence = PicklePersistence("data")
    app = ApplicationBuilder().token(BOT_TOKEN).arbitrary_callback_data(True).build()

    app.add_handler(CommandHandler("start", handle_start))
    app.add_handler(
        MessageHandler(
            filters.Document.ALL & filters.ChatType.PRIVATE,
            handle_dm_print,
        )
    )
    app.add_handler(
        MessageHandler(
            filters.REPLY & filters.Entity(MessageEntityType.MENTION),
            handle_reply_print,
        )
    )
    app.add_handler(CallbackQueryHandler(handle_printer_selection))

    app.run_polling()


if __name__ == "__main__":
    main()
