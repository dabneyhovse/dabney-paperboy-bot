from dataclasses import dataclass
from http import HTTPStatus

import cups

from paperboy.media import Media


@dataclass
class Printer:
    name: str
    location: str

    def get_id(self) -> str:
        return f"{self.name} ({self.location})"


class JobRequest:
    printer: Printer
    media: Media

    def __init__(self, printer: Printer, file: Media, name: str) -> None:
        self.printer = printer
        self.media = file
        self.name = name

    async def create_job(self) -> int:
        conn = cups.Connection()
        job_id = conn.createJob(self.printer.name, self.name, {})
        if not job_id:
            raise Exception(f"Failed to create job: {cups.lastErrorString()}")

        if (
            conn.startDocument(
                self.printer.name, job_id, self.name, "mime type here", True
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
