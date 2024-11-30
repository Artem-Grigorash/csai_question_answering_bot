import fitz
from PIL import Image
import easyocr
import os

reader = easyocr.Reader(['ru', 'en'])


def get_text(pdf_path) -> str:
    """
    Extract text from pdf file
    :param pdf_path: path to pdf file
    :return: extracted text
    """
    doc = fitz.open(pdf_path)
    res = ""
    for page_number in range(len(doc)):
        page = doc[page_number]
        text = page.get_text()
        res += text
        images = page.get_images(full=True)
        for img_index, img in enumerate(images):
            xref = img[0]
            base_image = doc.extract_image(xref)
            image_bytes = base_image["image"]
            image_ext = base_image["ext"]
            image_path = f"page{page_number + 1}_img{img_index + 1}.{image_ext}"
            with open(image_path, "wb") as img_file:
                img_file.write(image_bytes)

            with Image.open(image_path) as image:
                image = image.convert("L")
                image.save(image_path)
                ocr_result = reader.readtext(image_path, detail=0)
                ocr_text = "\n".join(ocr_result)
                print(ocr_text)
                res += ocr_text

            os.remove(image_path)
    return res
