from dataclasses import dataclass
from pathlib import Path

import pymupdf


class PdfConversionError(RuntimeError):
    pass


@dataclass(frozen=True)
class RenderedPage:
    page_number: int
    image_path: Path
    width: int
    height: int


def render_pdf_pages(
    pdf_path: Path,
    output_directory: Path,
    dpi: int = 150,
) -> list[RenderedPage]:
    if dpi < 72 or dpi > 600:
        raise PdfConversionError("PDF render DPI must be between 72 and 600.")
    if not pdf_path.is_file():
        raise PdfConversionError("The uploaded PDF is missing from local storage.")

    output_directory.mkdir(parents=True, exist_ok=True)
    rendered_pages: list[RenderedPage] = []

    try:
        with pymupdf.open(pdf_path) as pdf:
            if not pdf.is_pdf or pdf.page_count < 1:
                raise PdfConversionError("The uploaded file is not a readable PDF.")

            scale = dpi / 72
            matrix = pymupdf.Matrix(scale, scale)
            for page_index in range(pdf.page_count):
                page_number = page_index + 1
                pixmap = pdf.load_page(page_index).get_pixmap(matrix=matrix, alpha=False)
                image_path = output_directory / f"page_{page_number:04d}.png"
                pixmap.save(image_path)
                rendered_pages.append(
                    RenderedPage(
                        page_number=page_number,
                        image_path=image_path.resolve(),
                        width=pixmap.width,
                        height=pixmap.height,
                    )
                )
    except PdfConversionError:
        _remove_rendered_pages(rendered_pages, output_directory)
        raise
    except (pymupdf.FileDataError, RuntimeError, OSError) as exc:
        _remove_rendered_pages(rendered_pages, output_directory)
        raise PdfConversionError("PyMuPDF could not convert the uploaded PDF.") from exc

    return rendered_pages


def _remove_rendered_pages(
    rendered_pages: list[RenderedPage], output_directory: Path
) -> None:
    for rendered_page in rendered_pages:
        rendered_page.image_path.unlink(missing_ok=True)
    try:
        output_directory.rmdir()
    except OSError:
        pass
