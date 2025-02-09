import io
from dataclasses import dataclass
from io import BytesIO

from PIL import Image
from telegram import Message
from telegram._files._basemedium import _BaseMedium


@dataclass
class Media:
    data: bytes
    name: str
    mime_type: str


def convert_img_to_png(file_io):
    with Image.open(file_io) as image:
        output = BytesIO()
        image.save(output, format="PNG")
        return output


async def create_media(attachment: _BaseMedium, name: str, mime_type: str) -> Media:
    file = await attachment.get_file()
    file_bytes = io.BytesIO()
    await file.download_to_memory(file_bytes)
    if mime_type == "image/webp":
        file_bytes.seek(0)
        file_bytes = convert_img_to_png(file_bytes)
        mime_type = "image/png"
    data = file_bytes.getvalue()
    return Media(data, name, mime_type)


async def extract_media(msg: Message) -> Media | None:
    if (document := msg.document) and document.mime_type:
        return await create_media(
            document, document.file_name or "document", document.mime_type
        )
    elif photo := msg.photo:
        return await create_media(photo[-1], "photo.jpg", "image/jpeg")
    elif (sticker := msg.sticker) and not msg.sticker.is_animated:  # not comprehensive?
        return await create_media(sticker, "sticker.webp", "image/webp")
    if msg.reply_to_message:
        return await extract_media(msg.reply_to_message)
    return None
