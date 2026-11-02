# AI assisted development
import os
import subprocess
import uuid

from pdf2image import convert_from_path
from PIL import Image
from pypdf import PdfReader, PdfWriter
import re


UPLOAD_DIR = "static/uploads"
OUTPUT_DIR = "static/converted"
def save_uploaded_file(upload_file):
    filename = f"{uuid.uuid4()}_{upload_file.filename}"
    file_path = os.path.join("static/uploads", filename)
    with open(file_path, "wb") as buffer:
        buffer.write(upload_file.file.read())
    return file_path.replace("\\", "/")

def convert_word_to_pdf(word_path):
    import os
    import subprocess

    # Possible LibreOffice locations
    possible_paths = [
        r"C:\Program Files\LibreOffice\program\soffice.exe",
        r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
        "soffice",
    ]

    soffice_path = None

    # Detect LibreOffice
    for path in possible_paths:
        if path == "soffice":
            try:
                result = subprocess.run(
                    ["where", "soffice"],
                    capture_output=True,
                    text=True,
                    shell=True,
                )
                if result.returncode == 0:
                    soffice_path = "soffice"
                    break
            except Exception:
                pass
        elif os.path.exists(path):
            soffice_path = path
            break

    if not soffice_path:
        raise Exception(
            "LibreOffice not found. Install LibreOffice or add it to PATH.\n"
            "Download: https://www.libreoffice.org/download/"
        )

    # Ensure output folder exists
    output_dir = os.path.abspath("static/converted")
    os.makedirs(output_dir, exist_ok=True)

    # Absolute path of input file and expected output PDF path
    abs_word_path = os.path.abspath(word_path)
    filename_base = os.path.splitext(os.path.basename(abs_word_path))[0]
    expected_pdf_path = os.path.join(output_dir, f"{filename_base}.pdf")

    # Run LibreOffice conversion
    result = subprocess.run(
        [
            soffice_path,
            "--headless",
            "--convert-to",
            "pdf",
            "--outdir",
            output_dir,
            abs_word_path,
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=120,
    )

    # If LibreOffice fails
    if result.returncode != 0:
        error = result.stderr.decode() if result.stderr else result.stdout.decode()
        raise Exception(f"LibreOffice conversion failed: {error}")

    # Ensure the expected PDF was actually generated for this specific input
    if not os.path.exists(expected_pdf_path):
        raise Exception(
            f"LibreOffice conversion finished but no PDF was generated at "
            f"{expected_pdf_path}"
        )

    return expected_pdf_path.replace("\\", "/")

def convert_html_to_pdf(html_path):
    import subprocess
    import os

    OUTPUT_DIR = "static/converted"
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    filename_base = os.path.splitext(os.path.basename(html_path))[0]
    output_pdf_path = os.path.join(OUTPUT_DIR, f"{filename_base}.pdf")

    result = subprocess.run([
        "wkhtmltopdf",
        "--enable-local-file-access",
        "--load-error-handling", "ignore",          # ✅ suppress errors
        "--load-media-error-handling", "ignore",    # ✅ ignore CSS/JS/image load failures
        html_path,
        output_pdf_path
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    if result.returncode not in [0, 1]:  # 1 = handled warnings
        raise Exception(f"wkhtmltopdf failed: {result.stderr.decode()}")

    return output_pdf_path.replace("\\", "/")



def convert_pdf_to_image_pdf(pdf_path: str) -> str:
    OUTPUT_DIR = "static/converted"
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Convert PDF to list of PIL images
    images = convert_from_path(pdf_path)

    # Output PDF path
    filename_base = os.path.splitext(os.path.basename(pdf_path))[0]
    output_pdf_path = os.path.join(OUTPUT_DIR, f"{filename_base}_image_converted.pdf")

    # Save all images into a single PDF
    images[0].save(
        output_pdf_path,
        "PDF",
        save_all=True,
        append_images=images[1:]
    )

    return output_pdf_path.replace("\\", "/")


def convert_excel_to_pdf(excel_path: str) -> str:
    OUTPUT_DIR = "static/converted"
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Build PDF output path
    filename_base = os.path.splitext(os.path.basename(excel_path))[0]
    output_pdf_path = os.path.join(OUTPUT_DIR, f"{filename_base}.pdf")

    # Try multiple possible LibreOffice paths
    possible_paths = [
        r"C:\Program Files\LibreOffice\program\soffice.exe",
        r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
        "soffice",  # If in PATH
    ]
    
    soffice_path = None
    for path in possible_paths:
        if path == "soffice":
            result = subprocess.run(["where", "soffice"], capture_output=True, text=True, shell=True)
            if result.returncode == 0:
                soffice_path = "soffice"
                break
        elif os.path.exists(path):
            soffice_path = path
            break
    
    if not soffice_path:
        raise Exception(
            "LibreOffice not found. Please install LibreOffice or add it to PATH.\n"
            "Download from: https://www.libreoffice.org/download/"
        )

    # Get absolute paths
    abs_excel_path = os.path.abspath(excel_path)
    abs_output_dir = os.path.abspath(OUTPUT_DIR)

    result = subprocess.run([
        soffice_path,
        "--headless",
        "--convert-to", "pdf",
        "--outdir", abs_output_dir,
        abs_excel_path
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=60)

    if result.returncode != 0:
        error_msg = result.stderr.decode() if result.stderr else result.stdout.decode()
        raise Exception(f"LibreOffice conversion failed: {error_msg}")

    # Check if PDF was actually created
    if not os.path.exists(output_pdf_path):
        raise Exception(f"PDF file was not created at {output_pdf_path}")

    return output_pdf_path.replace("\\", "/")


def merge_pdfs(pdf_paths: list) -> str:
    OUTPUT_DIR = "static/converted"
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    writer = PdfWriter()

    for pdf_path in pdf_paths:
        reader = PdfReader(pdf_path)
        for page in reader.pages:
            writer.add_page(page)

    merged_filename = f"merged_{uuid.uuid4()}.pdf"
    merged_path = os.path.join(OUTPUT_DIR, merged_filename)

    with open(merged_path, "wb") as f:
        writer.write(f)

    return merged_path.replace("\\", "/")


def compress_pdf(pdf_path: str, level: str = "extreme") -> str:
    OUTPUT_DIR = "static/converted"
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    filename_base = os.path.splitext(os.path.basename(pdf_path))[0]
    output_pdf = os.path.join(
        OUTPUT_DIR,
        f"{filename_base}_compressed_{uuid.uuid4()}.pdf"
    )

    # Compression profiles
    quality_map = {
        "extreme": "/screen",     # MAX compression (lowest quality)
        "high": "/ebook",         # strong compression
        "medium": "/printer",     # balanced
        "low": "/prepress"        # best quality
    }

    profile = quality_map.get(level, "/screen")

    command = [
        "gswin64c" if os.name == "nt" else "gs",
        "-sDEVICE=pdfwrite",
        "-dCompatibilityLevel=1.4",
        f"-dPDFSETTINGS={profile}",
        "-dNOPAUSE",
        "-dQUIET",
        "-dBATCH",
        f"-sOutputFile={output_pdf}",
        pdf_path
    ]

    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    if result.returncode != 0:
        raise Exception(result.stderr.decode())

    return output_pdf.replace("\\", "/")


# PDF to Word conversion
def convert_pdf_to_word(pdf_path: str) -> str:
    OUTPUT_DIR = "static/converted"
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    filename_base = os.path.splitext(os.path.basename(pdf_path))[0]
    output_docx = os.path.join(OUTPUT_DIR, f"{filename_base}.docx")
    
    # Try multiple possible LibreOffice paths
    possible_paths = [
        r"C:\Program Files\LibreOffice\program\soffice.exe",
        r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
        "soffice",
    ]
    
    soffice_path = None
    for path in possible_paths:
        if path == "soffice":
            try:
                result = subprocess.run(["where", "soffice"], capture_output=True, text=True, shell=True, timeout=5)
                if result.returncode == 0:
                    soffice_path = "soffice"
                    break
            except:
                continue
        elif os.path.exists(path):
            soffice_path = path
            break
    
    if not soffice_path:
        raise Exception("LibreOffice not found. Please install LibreOffice.")
    
    abs_pdf_path = os.path.abspath(pdf_path)
    abs_output_dir = os.path.abspath(OUTPUT_DIR)
    
    result = subprocess.run([
        soffice_path,
        "--headless",
        "--convert-to", "docx",
        "--outdir", abs_output_dir,
        abs_pdf_path
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=60)
    
    if result.returncode != 0:
        raise Exception(f"Conversion failed: {result.stderr.decode()}")
    
    if not os.path.exists(output_docx):
        raise Exception(f"DOCX file was not created")
    
    return output_docx.replace("\\", "/")


# PDF to Image (extract pages as images)
def convert_pdf_to_image(pdf_path: str, format: str = "png") -> str:
    OUTPUT_DIR = "static/converted"
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    images = convert_from_path(pdf_path)
    filename_base = os.path.splitext(os.path.basename(pdf_path))[0]
    
    # Save first page as image
    output_image = os.path.join(OUTPUT_DIR, f"{filename_base}_page1.{format}")
    images[0].save(output_image, format.upper())
    
    # If multiple pages, create a zip or return first page
    return output_image.replace("\\", "/")


# Image to PDF
def convert_image_to_pdf(image_path: str) -> str:
    OUTPUT_DIR = "static/converted"
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    filename_base = os.path.splitext(os.path.basename(image_path))[0]
    output_pdf = os.path.join(OUTPUT_DIR, f"{filename_base}.pdf")
    
    image = Image.open(image_path)
    # Convert to RGB if necessary
    if image.mode != 'RGB':
        image = image.convert('RGB')
    
    image.save(output_pdf, "PDF")
    return output_pdf.replace("\\", "/")


# Split PDF
def split_pdf(pdf_path: str, start_page: int, end_page: int) -> str:
    OUTPUT_DIR = "static/converted"
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    reader = PdfReader(pdf_path)
    writer = PdfWriter()
    
    # Validate page numbers
    total_pages = len(reader.pages)
    if start_page < 1 or end_page > total_pages or start_page > end_page:
        raise Exception(f"Invalid page range. PDF has {total_pages} pages.")
    
    # Extract pages (0-indexed)
    for i in range(start_page - 1, end_page):
        writer.add_page(reader.pages[i])
    
    filename_base = os.path.splitext(os.path.basename(pdf_path))[0]
    output_pdf = os.path.join(OUTPUT_DIR, f"{filename_base}_pages_{start_page}-{end_page}.pdf")
    
    with open(output_pdf, "wb") as f:
        writer.write(f)
    
    return output_pdf.replace("\\", "/")


# Rotate PDF
def rotate_pdf(pdf_path: str, angle: int) -> str:
    OUTPUT_DIR = "static/converted"
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    if angle not in [90, 180, 270]:
        raise Exception("Angle must be 90, 180, or 270 degrees")
    
    reader = PdfReader(pdf_path)
    writer = PdfWriter()
    
    for page in reader.pages:
        page.rotate(angle)
        writer.add_page(page)
    
    filename_base = os.path.splitext(os.path.basename(pdf_path))[0]
    output_pdf = os.path.join(OUTPUT_DIR, f"{filename_base}_rotated_{angle}.pdf")
    
    with open(output_pdf, "wb") as f:
        writer.write(f)
    
    return output_pdf.replace("\\", "/")


# Protect PDF with password
def protect_pdf(pdf_path: str, password: str) -> str:
    OUTPUT_DIR = "static/converted"
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    reader = PdfReader(pdf_path)
    writer = PdfWriter()
    
    # Copy all pages
    for page in reader.pages:
        writer.add_page(page)
    
    # Encrypt with password
    writer.encrypt(password)
    
    filename_base = os.path.splitext(os.path.basename(pdf_path))[0]
    output_pdf = os.path.join(OUTPUT_DIR, f"{filename_base}_protected.pdf")
    
    with open(output_pdf, "wb") as f:
        writer.write(f)
    
    return output_pdf.replace("\\", "/")


# PDF to Text
def extract_text_from_pdf(pdf_path: str) -> str:
    OUTPUT_DIR = "static/converted"
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    reader = PdfReader(pdf_path)
    text_content = []
    
    for page in reader.pages:
        text_content.append(page.extract_text())
    
    full_text = "\n\n".join(text_content)
    
    filename_base = os.path.splitext(os.path.basename(pdf_path))[0]
    output_txt = os.path.join(OUTPUT_DIR, f"{filename_base}.txt")
    
    with open(output_txt, "w", encoding="utf-8") as f:
        f.write(full_text)
    
    return output_txt.replace("\\", "/")


# Add watermark to PDF
def add_watermark_to_pdf(pdf_path: str, watermark_text: str) -> str:
    OUTPUT_DIR = "static/converted"
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter
    from io import BytesIO
    
    reader = PdfReader(pdf_path)
    writer = PdfWriter()
    
    # Create watermark PDF
    packet = BytesIO()
    can = canvas.Canvas(packet, pagesize=letter)
    can.setFont("Helvetica", 50)
    can.setFillColorRGB(0.7, 0.7, 0.7)
    can.setFillAlpha(0.3)
    can.rotate(45)
    can.drawString(200, 100, watermark_text)
    can.save()
    
    packet.seek(0)
    watermark_pdf = PdfReader(packet)
    watermark_page = watermark_pdf.pages[0]
    
    # Apply watermark to each page
    for page in reader.pages:
        page.merge_page(watermark_page)
        writer.add_page(page)
    
    filename_base = os.path.splitext(os.path.basename(pdf_path))[0]
    output_pdf = os.path.join(OUTPUT_DIR, f"{filename_base}_watermarked.pdf")
    
    with open(output_pdf, "wb") as f:
        writer.write(f)
    
    return output_pdf.replace("\\", "/")



#----------------- AI SUMMARIZER ---------------------------------#
GEMINI_ENDPOINT = (
    "https://generativelanguage.googleapis.com/v1beta/"
    "models/gemini-2.5-flash:generateContent"
)


def _extract_gemini_text(data: dict) -> str:
    try:
        return data["candidates"][0]["content"]["parts"][0]["text"].strip()
    except Exception:
        raise Exception(f"Gemini API error: {data}")


def summarize_pdf(pdf_path: str) -> str:
    import requests
    from langchain_text_splitters import RecursiveCharacterTextSplitter

    gemini_api_key = os.getenv("GEMINI_API_KEY")
    if not gemini_api_key:
        raise Exception("GEMINI_API_KEY is not configured")

    reader = PdfReader(pdf_path)
    text = ""

    for page in reader.pages:
        if page.extract_text():
            text += page.extract_text() + "\n"

    if not text.strip():
        raise Exception("No readable text found in PDF")
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=6000,
        chunk_overlap=300
    )
    chunks = splitter.split_text(text)

    summaries = []

    headers = {
        "Content-Type": "application/json",
        "x-goog-api-key": gemini_api_key
    }

    for chunk in chunks:
        prompt = f"""
You are an expert document analyst.

Summarize the following content clearly and concisely.
Explain what the document is about.

CONTENT:
{chunk}

SUMMARY:
"""

        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": prompt}
                    ]
                }
            ]
        }

        response = requests.post(
            GEMINI_ENDPOINT,
            headers=headers,
            json=payload,
            timeout=60
        )
        response.raise_for_status()

        data = response.json()
        summaries.append(_extract_gemini_text(data))

    final_prompt = f"""
Combine the following summaries into ONE final summary
that clearly explains what the PDF document is about:

{summaries}

FINAL SUMMARY:
"""

    payload = {
        "contents": [
            {
                "parts": [
                    {"text": final_prompt}
                ]
            }
        ]
    }

    final_response = requests.post(
        GEMINI_ENDPOINT,
        headers=headers,
        json=payload,
        timeout=60
    )
    final_response.raise_for_status()

    final_data = final_response.json()
    return _extract_gemini_text(final_data)



# ----------------- AI PDF TRANSLATOR -----------------

from groq import Groq
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics


SUPPORTED_LANGUAGES = {
    "english": "English",
    "hindi": "Hindi",
    "spanish": "Spanish",
    "french": "French",
    "german": "German",
    "italian": "Italian",
    "portuguese": "Portuguese",
    "russian": "Russian",
    "japanese": "Japanese",
    "korean": "Korean",
    "chinese": "Chinese",
    "arabic": "Arabic",
    "bengali": "Bengali",
    "marathi": "Marathi",
    "tamil": "Tamil",
    "telugu": "Telugu",
    "gujarati": "Gujarati",
    "punjabi": "Punjabi",
    "urdu": "Urdu",
}


def _get_groq_client():
    """
    Create and return Groq client using GROQ_API_KEY.
    """
    groq_api_key = os.getenv("GROQ_API_KEY")

    if not groq_api_key:
        raise Exception("GROQ_API_KEY is not configured")

    return Groq(api_key=groq_api_key)


def _extract_pdf_text(pdf_path: str) -> list[str]:
    """
    Extract text page-by-page from a PDF.

    Returns:
        List of page text strings.
    """
    reader = PdfReader(pdf_path)

    pages = []

    for page in reader.pages:
        text = page.extract_text() or ""
        pages.append(text.strip())

    return pages


def _split_text_for_translation(
    text: str,
    max_chars: int = 10000
) -> list[str]:
    """
    Split text into chunks without unnecessarily breaking paragraphs.
    """

    if not text.strip():
        return []

    paragraphs = text.split("\n")

    chunks = []
    current_chunk = ""

    for paragraph in paragraphs:

        paragraph = paragraph.strip()

        if not paragraph:
            continue

        # If adding this paragraph exceeds the limit,
        # save the current chunk.
        if (
            current_chunk
            and len(current_chunk) + len(paragraph) + 1 > max_chars
        ):
            chunks.append(current_chunk.strip())
            current_chunk = ""

        current_chunk += paragraph + "\n"

    if current_chunk.strip():
        chunks.append(current_chunk.strip())

    return chunks


def _translate_text_with_groq(
    text: str,
    source_language: str,
    target_language: str,
) -> str:

    client = _get_groq_client()

    model = os.getenv(
        "GROQ_TRANSLATION_MODEL",
        "openai/gpt-oss-120b"
    )

    prompt = f"""
Translate the following document content from {source_language}
to {target_language}.

IMPORTANT RULES:

1. Translate accurately and naturally.
2. Do not summarize.
3. Do not add explanations.
4. Return ONLY the translated document content.
5. Preserve paragraph structure.
6. Preserve numbers, dates, names, URLs and identifiers.
7. Preserve headings and list structure.

SOURCE LANGUAGE:
{source_language}

TARGET LANGUAGE:
{target_language}

DOCUMENT CONTENT:
{text}
"""

    completion = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a professional document translator. "
                    "Translate accurately while preserving "
                    "the meaning and structure of the source."
                ),
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        temperature=0.1,
        max_completion_tokens=12000,
    )

    translated_text = completion.choices[0].message.content

    if not translated_text:
        raise Exception("Groq returned an empty translation")

    return translated_text.strip()

def _register_unicode_font():
    """
    Try to register a Unicode font for multilingual PDF output.

    Returns the font name to use.
    """

    possible_fonts = [
        r"C:\Windows\Fonts\arial.ttf",
        r"C:\Windows\Fonts\segoeui.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
    ]

    for font_path in possible_fonts:

        if os.path.exists(font_path):

            try:
                font_name = "OneClickDocUnicode"

                pdfmetrics.registerFont(
                    TTFont(font_name, font_path)
                )

                return font_name

            except Exception:
                continue

    return "Helvetica"


def _create_translated_pdf(
    translated_pages: list[str],
    output_path: str,
):
    """
    Generate a new PDF containing translated text.
    """

    font_name = _register_unicode_font()

    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        rightMargin=45,
        leftMargin=45,
        topMargin=45,
        bottomMargin=45,
        title="Translated Document",
    )

    styles = getSampleStyleSheet()

    body_style = ParagraphStyle(
        "TranslatedBody",
        parent=styles["BodyText"],
        fontName=font_name,
        fontSize=10,
        leading=15,
        alignment=TA_LEFT,
        spaceAfter=8,
    )

    heading_style = ParagraphStyle(
        "TranslatedHeading",
        parent=styles["Heading2"],
        fontName=font_name,
        fontSize=14,
        leading=18,
        spaceAfter=12,
    )

    story = []

    for page_index, page_text in enumerate(translated_pages):

        if not page_text.strip():
            continue

        paragraphs = page_text.split("\n")

        for paragraph in paragraphs:

            paragraph = paragraph.strip()

            if not paragraph:
                story.append(Spacer(1, 6))
                continue

            # Escape ReportLab-sensitive characters
            paragraph = (
                paragraph
                .replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
            )

            # Simple heading detection
            if len(paragraph) < 100 and (
                paragraph.isupper()
                or paragraph.endswith(":")
            ):
                story.append(
                    Paragraph(paragraph, heading_style)
                )
            else:
                story.append(
                    Paragraph(paragraph, body_style)
                )

        # Preserve page separation
        if page_index < len(translated_pages) - 1:
            story.append(PageBreak())

    doc.build(story)


def translate_pdf(
    pdf_path: str,
    source_language: str,
    target_language: str,
) -> str:
    """
    Translate a PDF and create a translated PDF.

    Args:
        pdf_path:
            Input PDF path.

        source_language:
            Language of the input document.

        target_language:
            Desired output language.

    Returns:
        Path to translated PDF.
    """

    source_language = source_language.strip().lower()
    target_language = target_language.strip().lower()

    if source_language not in SUPPORTED_LANGUAGES:
        raise Exception(
            f"Unsupported source language: {source_language}"
        )

    if target_language not in SUPPORTED_LANGUAGES:
        raise Exception(
            f"Unsupported target language: {target_language}"
        )

    if source_language == target_language:
        raise Exception(
            "Source and target languages must be different."
        )

    source_language_name = SUPPORTED_LANGUAGES[source_language]
    target_language_name = SUPPORTED_LANGUAGES[target_language]

    pages = _extract_pdf_text(pdf_path)

    if not pages:
        raise Exception("No pages found in PDF.")

    translated_pages = []

    for page_number, page_text in enumerate(pages, start=1):

        if not page_text.strip():
            translated_pages.append("")
            continue

        chunks = _split_text_for_translation(
            page_text,
            max_chars=10000
        )

        translated_chunks = []

        for chunk in chunks:

            translated_chunk = _translate_text_with_groq(
                text=chunk,
                source_language=source_language_name,
                target_language=target_language_name,
            )

            translated_chunks.append(
                translated_chunk
            )

        translated_page = "\n\n".join(
            translated_chunks
        )

        translated_pages.append(
            translated_page
        )

    OUTPUT_DIR = "static/converted"
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    filename_base = os.path.splitext(
        os.path.basename(pdf_path)
    )[0]

    output_pdf = os.path.join(
        OUTPUT_DIR,
        f"{filename_base}_{target_language}_translated.pdf"
    )

    _create_translated_pdf(
        translated_pages=translated_pages,
        output_path=output_pdf,
    )

    if not os.path.exists(output_pdf):
        raise Exception(
            "Translated PDF was not created."
        )

    return output_pdf.replace("\\", "/")