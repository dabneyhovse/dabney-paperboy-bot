import os
from dotenv import load_dotenv
from telegram import Update, MessageEntity, Document, File, User
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
import io
import cups

load_dotenv()

BOT_TOKEN = str(os.getenv("TG_TOKEN"))
CUPS_SERVER = str(os.getenv("CUPS_SERVER"))


cups.setServer(CUPS_SERVER)


async def download_document(document: Document) -> io.BytesIO:
    file = await document.get_file()
    file_bytes = io.BytesIO()
    await file.download_to_memory(file_bytes)
    file_bytes.seek(0)
    return file_bytes


def format_job_name(document: Document, user: User) -> str:
    return f"{document.file_name}_{user.username}_{user.id}"


async def create_job(printer: str, document: Document, user: User) -> None:
    conn = cups.Connection()
    data = await download_document(document)

    job_title = format_job_name(document, user)
    job_id = conn.createJob(printer, job_title, {})
    if not job_id:
        print("Failed to create job:", cups.lastErrorString())
        return

    print("Job created with ID:", job_id)
    http_status = conn.startDocument(
        printer, job_id, job_title, document.mime_type, True
    )
    print(http_status)
    # if http_status != cups.HTTP_STATUS_OK:
    #     print("Failed to start document (HTTP status: {})".format(http_status))
    #     return

    http_status = conn.writeRequestData(data, document.file_size)

    print(http_status)

    ipp_status = conn.finishDocument(printer)
    if ipp_status != cups.IPP_STATUS_OK:
        print("Failed to finish document:", cups.ippErrorString(ipp_status))
        return

    print("Print job submitted successfully!")


async def handle_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not (msg := update.message):
        return


async def handle_print(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if (
        not (msg := update.message)
        or not (document := msg.document)
        or not (author := msg.from_user)
    ):
        return
    await create_job("Apathy", document, author)


def main() -> None:
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", handle_start))
    app.add_handler(
        MessageHandler(
            (filters.ChatType.PRIVATE | filters.Entity(MessageEntity.MENTION))
            & (filters.PHOTO | filters.Document.ALL)
            & (~filters.Command()),
            handle_print,
        )
    )
    app.run_polling()


if __name__ == "__main__":
    main()
