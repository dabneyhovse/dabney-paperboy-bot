from dataclasses import dataclass
from http import HTTPStatus

import cups

from paperboy.media import Media


@dataclass
class Printer:
    name: str
    location: str

    PRINTER_ALIAS = {
        "Love": "❤️ @ Library",
        "Hope": "😊 @ A7",
        "Joy": "😄 @ CS Lab",
        "Peace": "☮️ @ CS Lab",
        "Apathy": "😶 @ Lounge",
    }

    def get_short_id(self) -> str:
        if self.name in self.PRINTER_ALIAS:
            return self.PRINTER_ALIAS[self.name]
        return self.get_id()

    def get_id(self) -> str:
        return f"{self.name} @ {self.location}"


class JobRequest:
    printer: Printer | None
    media: Media
    copies: int = 1
    name: str

    def __init__(self, printer: Printer | None, file: Media, name: str) -> None:
        self.printer = printer
        self.media = file
        self.name = name

    def get_status(self) -> str:
        printer_status = (
            self.printer.get_id() if self.printer else "an unselected printer"
        )
        return f"You're printing {self.copies} copy(s) to {printer_status}. Modify your options below:"

    async def create_job(self) -> int:
        if not self.printer:
            raise Exception("no printer selected!")

        conn = cups.Connection()
        job_id = conn.createJob(
            self.printer.name,
            self.name,
            {
                "copies": str(self.copies),
            },
        )
        if not job_id:
            raise Exception(f"Failed to create job: {cups.lastErrorString()}")

        if (
            conn.startDocument(
                self.printer.name, job_id, self.name, self.media.mime_type, True
            )
            != HTTPStatus.CONTINUE
        ):
            raise Exception(f"Failed to start document: {cups.lastErrorString()}")

        if (
            conn.writeRequestData(self.media.data, len(self.media.data))
            != HTTPStatus.CONTINUE
        ):
            raise Exception(f"Failed to write request data: {cups.lastErrorString()}")

        ipp_status = conn.finishDocument(self.printer.name)
        if ipp_status != cups.IPP_STATUS_OK:
            raise Exception(
                f"Failed to finish document: {cups.ippErrorString(ipp_status)}"
            )

        return job_id


# we really don't need all the info about a printer
def get_printers() -> list[Printer]:
    conn = cups.Connection()
    return [
        Printer(name, data["printer-location"])
        for name, data in conn.getPrinters().items()
    ]
