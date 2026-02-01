import os
import re
from pathlib import Path
from tempfile import NamedTemporaryFile

import cairosvg
from pypdf import PdfReader, PdfWriter

from src.models import Bracket, BracketMatch, BracketType, MatchStatus
from src.utils import sanitize_filename

SVG_TEMPLATE_PATH = "assets/template.svg"
SVG_ROUND_TEMPLATE_PATH = "assets/round_template.svg"

HIDE_FINISHED_MATCHES = True


def build_entry(
    matches: list[BracketMatch],
    bracket: Bracket,
    offset: int,
    position_offset: int,
    start_time_tatami: str,
    tournament_title: str,
) -> dict[str, str]:
    entry = {
        "tournament_name": tournament_title,
        "category": (bracket.get_display_name() if hasattr(bracket, "get_display_name") else bracket.category.name),
        "start_time_tatami": start_time_tatami,
    }

    for match in matches:
        rnd = match.round_number + offset

        if HIDE_FINISHED_MATCHES and getattr(match.match, "status", "finished") == MatchStatus.FINISHED.value:
            continue

        round_key = f"type_round{rnd}"
        round_type = (match.match.round_type or f"round {rnd}").strip()
        if round_type and round_key not in entry:
            entry[round_key] = round_type

        divisor = 2 ** (match.round_number - 1)
        norm_pos = match.position - (position_offset // divisor)

        if not (1 <= norm_pos <= 8):
            continue

        a1 = match.match.athlete1
        a2 = match.match.athlete2

        if a1:
            # Get coach names from the many-to-many relationship
            coach_names = [link.coach.last_name for link in a1.coach_links if link.coach is not None]
            coach_str = ", ".join(coach_names) if coach_names else ""
            entry[f"round{rnd}_position{norm_pos}_athlete1"] = f"{a1.last_name} {a1.first_name} ({coach_str})"

        if a2:
            # Get coach names from the many-to-many relationship
            coach_names = [link.coach.last_name for link in a2.coach_links if link.coach is not None]
            coach_str = ", ".join(coach_names) if coach_names else ""
            entry[f"round{rnd}_position{norm_pos}_athlete2"] = f"{a2.last_name} {a2.first_name} ({coach_str})"

    return entry


def build_round_robin_entry(
    matches: list[BracketMatch], category: str, start_time_tatami: str, tournament_title: str
) -> dict[str, str]:
    athletes_map = {}
    for match in matches:
        a1 = match.match.athlete1
        a2 = match.match.athlete2
        if a1:
            # Get coach names from the many-to-many relationship
            coach_names = [link.coach.last_name for link in a1.coach_links if link.coach is not None]
            coach_str = ", ".join(coach_names) if coach_names else ""
            athletes_map[a1.id] = f"{a1.last_name} {a1.first_name} ({coach_str})"
        if a2:
            # Get coach names from the many-to-many relationship
            coach_names = [link.coach.last_name for link in a2.coach_links if link.coach is not None]
            coach_str = ", ".join(coach_names) if coach_names else ""
            athletes_map[a2.id] = f"{a2.last_name} {a2.first_name} ({coach_str})"

    athletes = list(athletes_map.values())

    entry = {
        "tournament_name": tournament_title,
        "category": category,
        "start_time_tatami": start_time_tatami,
    }

    for idx, athlete in enumerate(athletes, start=1):
        entry[f"athlete{idx}"] = athlete

    return entry


def build_entries(data: list[Bracket], tournament_title: str) -> list[dict[str, str]]:
    all_entries = []

    for bracket in data:
        timetable_entry = getattr(bracket, "timetable_entry", None)
        if timetable_entry:
            start_time_value = timetable_entry.start_time.strftime("%H:%M")
            start_time_tatami = (
                f"Day: {timetable_entry.day} | Start time: {start_time_value} | Tatami: {timetable_entry.tatami}"
            )
        else:
            start_time_tatami = "Day: - | Start time: - | Tatami: -"
        matches = bracket.matches
        if not matches:
            continue

        if bracket.type == BracketType.ROUND_ROBIN.value:
            entry = build_round_robin_entry(
                matches=matches,
                category=(
                    bracket.get_display_name() if hasattr(bracket, "get_display_name") else bracket.category.name
                ),
                start_time_tatami=start_time_tatami,
                tournament_title=tournament_title,
            )
            entry["_template"] = BracketType.ROUND_ROBIN.value
            all_entries.append(entry)
            continue

        max_round = min(4, max(m.round_number for m in matches))

        round1_matches = sorted([m for m in matches if m.round_number == 1], key=lambda m: m.position)

        chunk_size = 8
        for i in range(0, len(round1_matches), chunk_size):
            position_offset = i * chunk_size
            entry = build_entry(
                bracket=bracket,
                matches=matches,
                offset=4 - max_round,
                position_offset=position_offset,
                start_time_tatami=start_time_tatami,
                tournament_title=tournament_title,
            )
            if len(entry) > 1:
                entry["_template"] = "elimination"
                all_entries.append(entry)

    return all_entries


def generate_pdf(data: list[Bracket], tournament_title: str) -> str | dict[str, str]:
    entries = build_entries(data, tournament_title)
    if not entries:
        return {"detail": "Нет данных для генерации."}

    writer = PdfWriter()
    temp_paths = []

    elimination_template = Path(SVG_TEMPLATE_PATH).read_text(encoding="utf-8")
    round_template = Path(SVG_ROUND_TEMPLATE_PATH).read_text(encoding="utf-8")

    for entry in entries:
        template_type = entry.get("_template", "elimination")
        if template_type == BracketType.ROUND_ROBIN.value:
            svg_template = round_template
        else:
            svg_template = elimination_template

        placeholders = set(re.findall(r"{{\s*(\w+)\s*}}", svg_template))

        for key in placeholders:
            value = entry.get(key, "")
            svg_template = svg_template.replace(f"{{{{ {key} }}}}", value)

        with NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            cairosvg.svg2pdf(bytestring=svg_template.encode("utf-8"), write_to=tmp.name)
            temp_paths.append(tmp.name)
            reader = PdfReader(tmp.name)
            writer.append_pages_from_reader(reader)

    sanitized_title = sanitize_filename(tournament_title or "tournament")

    pdf_storage_path = os.path.join(os.getcwd(), "pdf_storage")
    final_path = os.path.join(pdf_storage_path, f"{sanitized_title}.pdf")

    with open(final_path, "wb") as f_out:
        writer.write(f_out)

    for path in temp_paths:
        os.remove(path)

    return final_path
