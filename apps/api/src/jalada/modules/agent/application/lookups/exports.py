from typing import Any

from pydantic import BaseModel, Field

from jalada.modules.agent.application.tools import Tool, ToolContext


class WorkbookArguments(BaseModel):
    year: int | None = Field(None, ge=2000, le=2100, description="Default: last year.")


class TaxYearWorkbook(Tool[WorkbookArguments]):
    """Only a link: the workbook is built when the person opens it, signed in."""

    name = "tax_year_workbook"
    label = "Finding your workbook"
    description = "A link to download the Excel workbook of a year's confirmed records."
    arguments = WorkbookArguments

    def __init__(self, public_url: str) -> None:
        self._public_url = public_url.rstrip("/")

    def run(self, context: ToolContext, arguments: WorkbookArguments) -> dict[str, Any]:
        year = arguments.year or context.today.year - 1
        return {
            "year": year,
            "link": f"{self._public_url}/v1/exports/{year}.xlsx",
            "holds": "Confirmed payments only. Anything still on To check is left out.",
        }
