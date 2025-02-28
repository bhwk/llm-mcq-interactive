from pypdf import PdfReader


def extract_pdf_text(file: str) -> str:
    text = []
    reader = PdfReader(file)

    for page in reader.pages:
        text.append(page.extract_text())

    return "\n".join(text)
