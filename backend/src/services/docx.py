from io import BytesIO
from docxtpl import DocxTemplate
from docxcompose.composer import Composer
from docx import Document
import os
from uuid import uuid4

from fastapi.responses import StreamingResponse

TEMPLATE_PATH = "pdf_storage/tmp.docx"

HIDE_FINISHED_MATCHES = True


def build_entry(bracket, matches, offset, position_offset):
    entry = {"category": bracket.category}

    for match in matches:
        rnd = match.round_number + offset

        if HIDE_FINISHED_MATCHES and getattr(match.match, "is_finished", True):
            continue

        divisor = 2 ** (match.round_number - 1)
        norm_pos = match.position - (position_offset // divisor)

        if not (1 <= norm_pos <= 8):
            continue

        a1 = match.match.athlete1
        a2 = match.match.athlete2

        if a1:
            entry[f"round{rnd}_position{norm_pos}_athlete1"] = (
                f"{a1.last_name} {a1.first_name}"
            )

        if a2:
            entry[f"round{rnd}_position{norm_pos}_athlete2"] = (
                f"{a2.last_name} {a2.first_name}"
            )

    return entry


def build_entries(data):
    all_entries = []

    for bracket in data:
        matches = bracket.matches
        if not matches:
            continue

        max_round = min(4, max(m.round_number for m in matches))

        round1_matches = sorted(
            [m for m in matches if m.round_number == 1], key=lambda m: m.position
        )

        chunk_size = 8
        position_chunks = [
            [m.position for m in round1_matches[i : i + chunk_size]]
            for i in range(0, len(round1_matches), chunk_size)
        ]

        for i, pos_set in enumerate(position_chunks):
            position_offset = i * chunk_size
            entry = build_entry(
                bracket=bracket,
                matches=matches,
                offset=4 - max_round,
                position_offset=position_offset,
            )
            if len(entry) > 1:
                all_entries.append(entry)

    return all_entries


def generate_docx_stream(data):
    entries = build_entries(data)
    docs = []

    for entry in entries:
        tpl = DocxTemplate(TEMPLATE_PATH)
        tpl.render(entry)

        stream = BytesIO()
        tpl.save(stream)
        stream.seek(0)
        docs.append(stream)

    if not docs:
        return {"detail": "Нет данных для генерации."}

    final_stream = BytesIO()
    first_doc = Document(docs[0])
    composer = Composer(first_doc)

    for stream in docs[1:]:
        composer.append(Document(stream))

    composer.save(final_stream)
    final_stream.seek(0)

    for doc in docs:
        doc.close()

    return StreamingResponse(
        final_stream,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": "attachment; filename=final_result.docx"},
    )
