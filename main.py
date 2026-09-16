from fastapi import (FastAPI, UploadFile, File, Depends, HTTPException, BackgroundTasks, Form, )
from fastapi import Query
from sqlalchemy.orm import Session
from fastapi.responses import JSONResponse
from database import Base, engine, SessionLocal
from schemas import ConversionResponse, PdfSummaryResponse
from crud import save_conversion, get_latest_conversion
from utils import (
    save_uploaded_file, convert_word_to_pdf, convert_html_to_pdf, 
    convert_pdf_to_image_pdf, convert_excel_to_pdf, merge_pdfs,
    compress_pdf, convert_pdf_to_word, convert_pdf_to_image, 
    convert_image_to_pdf, split_pdf, rotate_pdf, protect_pdf, 
    extract_text_from_pdf, add_watermark_to_pdf,summarize_pdf,translate_pdf
)
import os
from fastapi.responses import FileResponse
from typing import List
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Allow requests from React (localhost:3000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # You can restrict this to ["http://localhost:3000"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Create tables
Base.metadata.create_all(bind=engine)

# Ensure dirs exist
os.makedirs("static/uploads", exist_ok=True)
os.makedirs("static/converted", exist_ok=True)

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def _schedule_file_cleanup(background_tasks: BackgroundTasks, *paths: str) -> None:
    """
    Schedule deletion of temporary files (original + converted) after the
    response is sent. This keeps conversions effectively cached instead of
    permanently stored on disk.
    """
    import os

    def _remove_files(files: list[str]) -> None:
        for p in files:
            if p and os.path.exists(p):
                try:
                    os.remove(p)
                except Exception:
                    # Best-effort cleanup; ignore failures
                    pass

    background_tasks.add_task(_remove_files, list(paths))


@app.post("/convert/word-to-pdf", response_model=ConversionResponse)
async def convert_word_to_pdf_api(
    *,
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    if not file.filename or not file.filename.endswith(".docx"):
        raise HTTPException(status_code=400, detail="Only .docx files are allowed.")
    
    try:
        original_path = save_uploaded_file(file)
        converted_path = convert_word_to_pdf(original_path)
        
        conversion = save_conversion(
            db,
            original_filename=file.filename,
            original_path=original_path,
            converted_path=converted_path,
            conversion_type="word-to-pdf"
        )
       
        _schedule_file_cleanup(background_tasks, original_path, converted_path)

        return FileResponse(
            path=converted_path,
            media_type="application/pdf",
            filename=os.path.basename(converted_path)
        )
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_detail = str(e)
        traceback.print_exc()  # Print full traceback for debugging
        raise HTTPException(status_code=500, detail=f"Conversion failed: {error_detail}")

from crud import get_conversion_by_id


@app.get("/conversion/{conversion_id}/download")
def download_conversion(
    conversion_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """
    Download a specific converted document by its unique conversion ID.
    This avoids relying on 'latest' conversions and is safe for
    concurrent multi-user usage.
    """
    conversion = get_conversion_by_id(db, conversion_id)
    if not conversion or not conversion.converted_path or conversion.converted_path == "N/A":
        raise HTTPException(status_code=404, detail="Conversion not found or not downloadable.")

    file_path = conversion.converted_path
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Converted file not found on server.")

    # Best‑effort cleanup of original and converted files after response
    _schedule_file_cleanup(background_tasks, conversion.original_path, conversion.converted_path)

    return FileResponse(
        path=file_path,
        media_type="application/octet-stream",
        filename=os.path.basename(file_path),
    )

@app.post("/convert/html-to-pdf", response_model=ConversionResponse)
async def convert_html_to_pdf_api(
    *,
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    if not file.filename.endswith(".html"):
        raise HTTPException(status_code=400, detail="Only .html files are allowed.")
    
    try:
        original_path = save_uploaded_file(file)
        converted_path = convert_html_to_pdf(original_path)

        conversion = save_conversion(
            db,
            original_filename=file.filename,
            original_path=original_path,
            converted_path=converted_path,
            conversion_type="html-to-pdf"
        )

        _schedule_file_cleanup(background_tasks, original_path, converted_path)

        return FileResponse(
            path=converted_path,
            media_type="application/pdf",
            filename=os.path.basename(converted_path)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/convert/pdf-to-image-pdf", response_model=ConversionResponse)
async def convert_pdf_to_image_pdf_api(
    *,
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only .pdf files are allowed.")
    
    try:
        original_path = save_uploaded_file(file)
        converted_path = convert_pdf_to_image_pdf(original_path)

        conversion = save_conversion(
            db,
            original_filename=file.filename,
            original_path=original_path,
            converted_path=converted_path,
            conversion_type="pdf-to-image-pdf"
        )
        _schedule_file_cleanup(background_tasks, original_path, converted_path)

        return FileResponse(
            path=converted_path,
            media_type="application/pdf",
            filename=os.path.basename(converted_path)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



@app.post("/convert/excel-to-pdf", response_model=ConversionResponse)
async def convert_excel_to_pdf_api(
    *,
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    if not (file.filename.endswith(".xlsx") or file.filename.endswith(".xls")):
        raise HTTPException(status_code=400, detail="Only .xlsx or .xls files are allowed.")
    
    try:
        original_path = save_uploaded_file(file)
        converted_path = convert_excel_to_pdf(original_path)

        conversion = save_conversion(
            db,
            original_filename=file.filename,
            original_path=original_path,
            converted_path=converted_path,
            conversion_type="excel-to-pdf"
        )

        _schedule_file_cleanup(background_tasks, original_path, converted_path)

        return FileResponse(
            path=converted_path,
            media_type="application/pdf",
            filename=os.path.basename(converted_path)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



@app.get("/")
def root():
    return {
        "message": "OneClickDoc API is running!",
        "status": "active",
        "endpoints": {
            "word_to_pdf": "/convert/word-to-pdf",
            "html_to_pdf": "/convert/html-to-pdf",
            "excel_to_pdf": "/convert/excel-to-pdf",
            "pdf_to_image_pdf": "/convert/pdf-to-image-pdf",
            "pdf_to_word": "/convert/pdf-to-word",
            "image_to_pdf": "/convert/image-to-pdf",
            "pdf_to_text": "/convert/pdf-to-text",
            "merge_pdf": "/merge-pdf",
            "split_pdf": "/split-pdf",
            "rotate_pdf": "/rotate-pdf",
            "compress_pdf": "/compress-pdf",
            "protect_pdf": "/protect-pdf",
            "watermark_pdf": "/watermark-pdf",
            "summarize_pdf": "/summarize-pdf",
            "latest_conversion": "/conversion/latest",
            "docs": "/docs"
        }
    }

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "OneClickDoc Backend",
        "version": "1.0.0"
    }

@app.get("/conversion/latest", response_model=ConversionResponse)
def get_latest_conversion_api(db: Session = Depends(get_db)):
    from crud import get_latest_conversion

    conversion = get_latest_conversion(db)
    if not conversion:
        raise HTTPException(status_code=404, detail="No recent conversion found.")
    return conversion

@app.post("/merge-pdf")
async def merge_pdf_api(
    *,
    files: List[UploadFile] = File(...),
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    if len(files) < 2:
        raise HTTPException(status_code=400, detail="Upload at least two PDF files.")

    try:
        saved_paths = []

        for file in files:
            if not file.filename.endswith(".pdf"):
                raise HTTPException(status_code=400, detail="Only PDF files are allowed.")
            saved_paths.append(save_uploaded_file(file))

        merged_path = merge_pdfs(saved_paths)

        save_conversion(
            db,
            original_filename=", ".join([f.filename for f in files]),
            original_path=", ".join(saved_paths),
            converted_path=merged_path,
            conversion_type="merge-pdf"
        )

        _schedule_file_cleanup(background_tasks, *saved_paths, merged_path)

        return FileResponse(
            path=merged_path,
            media_type="application/pdf",
            filename=os.path.basename(merged_path)
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    


@app.post("/compress-pdf")
async def compress_pdf_api(
    *,
    file: UploadFile = File(...),
    level: str = Query(
        "extreme",
        enum=["extreme", "high", "medium", "low"],
        description="Compression level"
    ),
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed.")

    try:
        original_path = save_uploaded_file(file)
        compressed_path = compress_pdf(original_path, level=level)

        save_conversion(
            db,
            original_filename=file.filename,
            original_path=original_path,
            converted_path=compressed_path,
            conversion_type=f"compress-pdf-{level}"
        )

        _schedule_file_cleanup(background_tasks, original_path, compressed_path)

        return FileResponse(
            path=compressed_path,
            media_type="application/pdf",
            filename=os.path.basename(compressed_path)
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/convert/pdf-to-word")
async def convert_pdf_to_word_api(
    *,
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only .pdf files are allowed.")
    
    try:
        original_path = save_uploaded_file(file)
        converted_path = convert_pdf_to_word(original_path)
        
        save_conversion(
            db,
            original_filename=file.filename,
            original_path=original_path,
            converted_path=converted_path,
            conversion_type="pdf-to-word"
        )
        
        _schedule_file_cleanup(background_tasks, original_path, converted_path)

        return FileResponse(
            path=converted_path,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            filename=os.path.basename(converted_path)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/convert/pdf-to-image")
async def convert_pdf_to_image_api(
    *,
    file: UploadFile = File(...),
    format: str = Query("png", enum=["png", "jpg", "jpeg"]),
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only .pdf files are allowed.")
    
    try:
        original_path = save_uploaded_file(file)
        converted_path = convert_pdf_to_image(original_path, format)
        
        save_conversion(
            db,
            original_filename=file.filename,
            original_path=original_path,
            converted_path=converted_path,
            conversion_type=f"pdf-to-image-{format}"
        )
        
        _schedule_file_cleanup(background_tasks, original_path, converted_path)

        return FileResponse(
            path=converted_path,
            media_type=f"image/{format}",
            filename=os.path.basename(converted_path)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/convert/image-to-pdf")
async def convert_image_to_pdf_api(
    *,
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    allowed_extensions = [".jpg", ".jpeg", ".png", ".gif", ".bmp"]
    if not any(file.filename.lower().endswith(ext) for ext in allowed_extensions):
        raise HTTPException(status_code=400, detail="Only image files are allowed.")
    
    try:
        original_path = save_uploaded_file(file)
        converted_path = convert_image_to_pdf(original_path)
        
        save_conversion(
            db,
            original_filename=file.filename,
            original_path=original_path,
            converted_path=converted_path,
            conversion_type="image-to-pdf"
        )
        
        _schedule_file_cleanup(background_tasks, original_path, converted_path)

        return FileResponse(
            path=converted_path,
            media_type="application/pdf",
            filename=os.path.basename(converted_path)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/split-pdf")
async def split_pdf_api(
    *,
    file: UploadFile = File(...),
    start_page: int = Query(..., ge=1),
    end_page: int = Query(..., ge=1),
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only .pdf files are allowed.")
    
    try:
        original_path = save_uploaded_file(file)
        converted_path = split_pdf(original_path, start_page, end_page)
        
        save_conversion(
            db,
            original_filename=file.filename,
            original_path=original_path,
            converted_path=converted_path,
            conversion_type="split-pdf"
        )
        
        _schedule_file_cleanup(background_tasks, original_path, converted_path)

        return FileResponse(
            path=converted_path,
            media_type="application/pdf",
            filename=os.path.basename(converted_path)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/rotate-pdf")
async def rotate_pdf_api(
    *,
    file: UploadFile = File(...),
    angle: int = Query(..., enum=[90, 180, 270]),
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only .pdf files are allowed.")
    
    try:
        original_path = save_uploaded_file(file)
        converted_path = rotate_pdf(original_path, angle)
        
        save_conversion(
            db,
            original_filename=file.filename,
            original_path=original_path,
            converted_path=converted_path,
            conversion_type=f"rotate-pdf-{angle}"
        )
        
        _schedule_file_cleanup(background_tasks, original_path, converted_path)

        return FileResponse(
            path=converted_path,
            media_type="application/pdf",
            filename=os.path.basename(converted_path)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/protect-pdf")
async def protect_pdf_api(
    *,
    file: UploadFile = File(...),
    password: str = Query(...),
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only .pdf files are allowed.")
    
    try:
        original_path = save_uploaded_file(file)
        converted_path = protect_pdf(original_path, password)
        
        save_conversion(
            db,
            original_filename=file.filename,
            original_path=original_path,
            converted_path=converted_path,
            conversion_type="protect-pdf"
        )
        
        _schedule_file_cleanup(background_tasks, original_path, converted_path)

        return FileResponse(
            path=converted_path,
            media_type="application/pdf",
            filename=os.path.basename(converted_path)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/convert/pdf-to-text")
async def convert_pdf_to_text_api(
    *,
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only .pdf files are allowed.")
    
    try:
        original_path = save_uploaded_file(file)
        converted_path = extract_text_from_pdf(original_path)
        
        save_conversion(
            db,
            original_filename=file.filename,
            original_path=original_path,
            converted_path=converted_path,
            conversion_type="pdf-to-text"
        )
        
        _schedule_file_cleanup(background_tasks, original_path, converted_path)

        return FileResponse(
            path=converted_path,
            media_type="text/plain",
            filename=os.path.basename(converted_path)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/watermark-pdf")
async def watermark_pdf_api(
    *,
    file: UploadFile = File(...),
    watermark_text: str = Query(...),
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only .pdf files are allowed.")
    
    try:
        original_path = save_uploaded_file(file)
        converted_path = add_watermark_to_pdf(original_path, watermark_text)
        
        save_conversion(
            db,
            original_filename=file.filename,
            original_path=original_path,
            converted_path=converted_path,
            conversion_type="watermark-pdf"
        )
        
        _schedule_file_cleanup(background_tasks, original_path, converted_path)

        return FileResponse(
            path=converted_path,
            media_type="application/pdf",
            filename=os.path.basename(converted_path)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))




@app.post("/summarize-pdf", response_model=PdfSummaryResponse)
async def summarize_pdf_api(
    *,
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files allowed")

    try:
        original_path = save_uploaded_file(file)
        summary = summarize_pdf(original_path)

        save_conversion(
            db,
            original_filename=file.filename,
            original_path=original_path,
            converted_path="N/A",
            conversion_type="summarize-pdf"
        )

        _schedule_file_cleanup(background_tasks, original_path)

        return {
            "filename": file.filename,
            "summary": summary
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/translate-pdf")
async def translate_pdf_api(
    *,
    file: UploadFile = File(...),
    source_language: str = Form(...),
    target_language: str = Form(...),
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """
    Translate a PDF from one language to another using Groq AI.

    Input:
        - PDF file
        - source_language
        - target_language

    Output:
        - translated PDF
    """

    # Validate file
    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="No file provided."
        )

    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are allowed."
        )

    if not source_language.strip():
        raise HTTPException(
            status_code=400,
            detail="Source language is required."
        )

    if not target_language.strip():
        raise HTTPException(
            status_code=400,
            detail="Target language is required."
        )

    if (
        source_language.strip().lower()
        == target_language.strip().lower()
    ):
        raise HTTPException(
            status_code=400,
            detail=(
                "Source and target languages "
                "must be different."
            )
        )

    try:

        # Save original PDF
        original_path = save_uploaded_file(file)

        # Translate PDF
        translated_path = translate_pdf(
            pdf_path=original_path,
            source_language=source_language,
            target_language=target_language,
        )

        # Save conversion record
        save_conversion(
            db,
            original_filename=file.filename,
            original_path=original_path,
            converted_path=translated_path,
            conversion_type=(
                f"translate-pdf-"
                f"{source_language}-"
                f"to-"
                f"{target_language}"
            ),
        )

        # Cleanup after response
        _schedule_file_cleanup(
            background_tasks,
            original_path,
            translated_path,
        )

        return FileResponse(
            path=translated_path,
            media_type="application/pdf",
            filename=os.path.basename(
                translated_path
            ),
        )

    except HTTPException:
        raise

    except Exception as e:

        import traceback

        traceback.print_exc()

        raise HTTPException(
            status_code=500,
            detail=f"PDF translation failed: {str(e)}",
        )
