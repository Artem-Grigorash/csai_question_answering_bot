import json
import os

import aiofiles
import easyocr
import fitz
from PIL import Image
from phi.document import Document

from src.utils.chunker import split_text
from src.utils.translator import translate_text_with_openai

reader = easyocr.Reader(['ru', 'en'])


async def process_pdf(pdf_path, chunk=True):
    print(pdf_path)
    doc = fitz.open(pdf_path)
    documents = []
    all_text = ""
    pages = []
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

        translated_text = await translate_text_with_openai(text)
        pages.append(translated_text)
        all_text += translated_text

    if chunk:
        if len(all_text) <= 10000:
            print(all_text)
            chunks = await split_text(all_text)
        else:
            chunks = pages
        doc_name = pdf_path.split("/")[-1].split(".")[0].replace(" ", "_")
        for i, chunk in enumerate(chunks):
            documents.append(Document(
                name=doc_name,
                id=f"{doc_name}_{i}",
                meta_data={"chunk": i},
                content=chunk))
        print(documents)
    else:
        doc_name = pdf_path.split("/")[-1].split(".")[0].replace(" ", "_")
        documents.append(Document(
            name=doc_name,
            id=f"doc_name_{1}",
            content=all_text,
            meta_data={"chunk": 1}
        ))
    return documents


async def process_json(json_path):
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    documents = []
    id = 0
    json_name = json_path.split("/")[-1].split(".")[0].replace(" ", "_")
    for message in data['messages']:
        text = f'DATE: {message['date']}\n{message['text']}'
        print(text)
        translated_text = translate_text_with_openai(text)
        documents.append(Document(
            name=json_name,
            id=f"{json_name}_{id}",
            meta_data={"id": id},
            content=translated_text,
        ))
        id += 1
    return documents
