# AI assisted development
import os
import uuid
import subprocess
from pdf2image import convert_from_path
from PIL import Image
from pypdf import PdfMerger
from pypdf import PdfMerger
from pypdf import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
import google.generativeai as genai
import os
import requests
from pypdf import PdfReader


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


from pypdf import PdfReader, PdfWriter
import os
import uuid

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


import subprocess
import os
import uuid

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
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_ENDPOINT = (
    "https://generativelanguage.googleapis.com/v1beta/"
    "models/gemini-2.5-flash:generateContent"
)

def summarize_pdf(pdf_path: str) -> str:
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
        "x-goog-api-key": GEMINI_API_KEY
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

        data = response.json()

        try:
            chunk_summary = (
                data["candidates"][0]
                ["content"]["parts"][0]["text"]
            )
            summaries.append(chunk_summary)
        except Exception:
            raise Exception(f"Gemini API error: {data}")

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

    final_data = final_response.json()

    try:
        return (
            final_data["candidates"][0]
            ["content"]["parts"][0]["text"]
            .strip()
        )
    except Exception:
        raise Exception(f"Final Gemini error: {final_data}")
