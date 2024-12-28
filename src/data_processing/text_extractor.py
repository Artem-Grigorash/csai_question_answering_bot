import fitz
from PIL import Image
import easyocr
import os
import aiofiles
from phi.document import Document
from googletrans import Translator
from phi.document.reader.pdf import PDFReader

translator = Translator()

reader = easyocr.Reader(['ru', 'en'])


async def process_pdf(pdf_path, chunk=True):
    print(pdf_path)
    doc = fitz.open(pdf_path)
    documents = []

    for page_number in range(len(doc)):
        page = doc[page_number]
        text = page.get_text()
        images = page.get_images(full=True)
        for img_index, img in enumerate(images):
            xref = img[0]
            base_image = doc.extract_image(xref)
            image_bytes = base_image["image"]
            image_ext = base_image["ext"]
            image_path = f"page{page_number + 1}_img{img_index + 1}.{image_ext}"
            async with aiofiles.open(image_path, "wb") as img_file:
                await img_file.write(image_bytes)

            with Image.open(image_path) as image:
                image = image.convert("L")
                image.save(image_path)
                ocr_result = reader.readtext(image_path, detail=0)
                ocr_text = "\n".join(ocr_result)
                text += ocr_text

            os.remove(image_path)

        translated_text = translator.translate(text, dest='en').text
        doc_name = pdf_path.split("/")[-1].split(".")[0].replace(" ", "_")
        documents.append(Document(
            name=doc_name,
            id=f"{doc_name}_{page_number}",
            meta_data={"page": page_number},
            content=translated_text,
        ))

    if chunk:
        chunked_documents = []
        pdf_reader = PDFReader()
        for document in documents:
            chunked_documents.extend(pdf_reader.chunk_document(document))
        return chunked_documents

    return documents
