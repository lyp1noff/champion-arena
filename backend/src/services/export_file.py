from fastapi.responses import FileResponse
from tempfile import NamedTemporaryFile
from pathlib import Path
import cairosvg
import re
from PyPDF2 import PdfMerger
import os
import uuid

SVG_TEMPLATE_PATH = "assets/template.svg"

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


def generate_pdf(data):
    entries = build_entries(data)
    if not entries:
        return {"detail": "Нет данных для генерации."}

    merger = PdfMerger()
    temp_paths = []

    original_template = Path(SVG_TEMPLATE_PATH).read_text(encoding="utf-8")

    for entry in entries:
        svg_template = original_template

        placeholders = set(re.findall(r"{{\s*(\w+)\s*}}", svg_template))
        for key in placeholders:
            value = entry.get(key, "")
            svg_template = svg_template.replace(f"{{{{ {key} }}}}", value)

        with NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            cairosvg.svg2pdf(bytestring=svg_template.encode("utf-8"), write_to=tmp.name)
            temp_paths.append(tmp.name)
            merger.append(tmp.name)

    final_path = f"pdf_storage/{uuid.uuid4()}.pdf"
    with open(final_path, "wb") as final_file:
        merger.write(final_file)
    merger.close()

    for path in temp_paths:
        os.remove(path)

    return FileResponse(
        final_path, media_type="application/pdf", filename="brackets.pdf"
    )
