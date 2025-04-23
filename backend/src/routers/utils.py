from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse
from docxtpl import DocxTemplate
from docxcompose.composer import Composer
from docx import Document
import json
import os
from uuid import uuid4

from src.dependencies.auth import get_current_user

router = APIRouter(
    prefix="/utils", tags=["Utils"], dependencies=[Depends(get_current_user)]
)


def build_entries():
    with open("pdf_storage/matches.json", encoding="utf-8") as f:
        data = json.load(f)

    entries = []
    for bracket in data:
        entry = {"category": bracket["category"]}
        max_round = max(m["round_number"] for m in bracket["matches"])

        if max_round > 4:
            print(bracket["category"])

        for match in bracket["matches"]:
            rnd = 4 - max_round + match["round_number"]
            pos = match["position"]
            m = match["match"]

            # athlete1
            athlete1 = m.get("athlete1")
            if athlete1:
                key1 = f"round{rnd}_position{pos}_athlete1"
                entry[key1] = f"{athlete1['first_name']} {athlete1['last_name']}"

            # athlete2
            athlete2 = m.get("athlete2")
            if athlete2:
                key2 = f"round{rnd}_position{pos}_athlete2"
                entry[key2] = f"{athlete2['first_name']} {athlete2['last_name']}"

        entries.append(entry)
    return entries


@router.get("/generate-docx")
def generate_docx():
    entries = build_entries()
    template_path = "pdf_storage/tmp.docx"
    temp_files = []

    # создаём временные docx
    for i, entry in enumerate(entries):
        tpl = DocxTemplate(template_path)
        tpl.render(entry)
        temp_path = f"pdf_storage/temp_page_{uuid4()}.docx"
        tpl.save(temp_path)
        temp_files.append(temp_path)

    # склеиваем их
    final_doc = f"pdf_storage/final_result_{uuid4()}.docx"
    composer = Composer(Document(temp_files[0]))
    for temp_path in temp_files[1:]:
        composer.append(Document(temp_path))
    composer.save(final_doc)

    # удаляем временные
    for temp_path in temp_files:
        os.remove(temp_path)

    return FileResponse(
        final_doc,
        filename="pdf_storage/final_result.docx",
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )
