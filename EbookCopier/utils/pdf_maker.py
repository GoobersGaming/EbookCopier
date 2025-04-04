import os
import fitz
from io import BytesIO
from utils import logs

"""Create and Save Your PDF"""

def add_image_to_pdf(images : list, pdf_path : str):
    if len(images) == 0:
        return True
    """
    :param list images: Batch Of Screenshots To Be Added To PDF
    :param str pdf_path: File Location Of Where To Save/Append PDF"""

    if os.path.exists(pdf_path):
        logs.LOGGER.info(f"PDF path exists: {pdf_path}")
        doc = fitz.open(pdf_path)
    else:
        logs.LOGGER.info(f"PDF path created: {pdf_path}")
        doc = fitz.open()

    for img in images:
        img_width, img_height = img.size
        page = doc.new_page(width=img_width, height=img_height)
        img_bytes = BytesIO()
        img.save(img_bytes, format="PNG", quality=100)
        img_bytes.seek(0)
        rect = fitz.Rect(0, 0, img_width, img_height)
        page.insert_image(rect, stream=img_bytes.getvalue())
    
    # Save Arguments
    save_kwargs = {
        "garbage": 0,       # Compact file
        "deflate": True,    # Compress
        "encryption": 0      # Explicitly disable encryption (0 = none)
    }
    try:
        doc.save(pdf_path, **save_kwargs)
        doc.close()
        logs.LOGGER.info(f"Batch Saved To PDF: {pdf_path}")
        return True
    except ValueError:
        doc.save(pdf_path, incremental=True , **save_kwargs)
        doc.close()
        logs.LOGGER.info(f"Batch appended to existing PDF file: {pdf_path}")
        return True

