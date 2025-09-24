from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse
from io import BytesIO
from PIL import Image
from rembg import remove
import logging
from starlette.concurrency import run_in_threadpool

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("bg-remover")

# Max allowed file size in bytes (e.g., 5 MB)
MAX_FILE_SIZE = 5_000_000

app = FastAPI()

@app.post("/remove-bg/")
async def remove_background(file: UploadFile = File(...)):
    try:
        # Read uploaded file
        image_bytes = await file.read()
        file_size = len(image_bytes)
        logger.info(f"Received file: {file.filename}, size: {file_size} bytes")

        # Check file size
        if file_size > MAX_FILE_SIZE:
            logger.warning(f"File {file.filename} is too large: {file_size} bytes")
            raise HTTPException(status_code=413, detail="File too large. Max 5 MB allowed.")

        # Remove background (run in thread to avoid blocking)
        result_bytes = await run_in_threadpool(remove, image_bytes)

        # Convert to PNG
        result_image = Image.open(BytesIO(result_bytes)).convert("RGBA")
        img_io = BytesIO()
        result_image.save(img_io, format="PNG")
        img_io.seek(0)

        # Add Content-Length header for progress tracking
        headers = {"Content-Length": str(len(img_io.getvalue()))}
        logger.info(f"Background removed successfully for file: {file.filename}")

        return StreamingResponse(
            img_io,
            media_type="image/png",
            headers=headers
        )

    except Exception as e:
        logger.exception(f"Error processing file {file.filename if 'file' in locals() else 'unknown'}: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")
