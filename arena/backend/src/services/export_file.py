import re
from datetime import date, timedelta
from io import BytesIO
from pathlib import Path
from typing import Literal
from xml.sax.saxutils import escape

import cairosvg
from pypdf import PdfReader, PdfWriter

from src.models import Athlete, Bracket, BracketMatch, BracketType
from src.utils import sanitize_filename

SVG_TEMPLATE_PATH = "assets/template.svg"
SVG_ROUND_TEMPLATE_PATH = "assets/round_template.svg"

ExportMode = Literal["filled", "manual"]
ROUND_ROBIN_MAX_ATHLETES = 6
ROUND_ROBIN_NAME_MAX_CHARS = 22
ROUND_ROBIN_LINE_HEIGHT = 13
FIGHTS_LINE_HEIGHT = 17
PLACEHOLDER_PATTERN = re.compile(r"\[\[\s*(\w+)\s*\]\]")


def build_entry(
    matches: list[BracketMatch],
    bracket: Bracket,
    offset: int,
    position_offset: int,
    start_time_tatami: str,
    tournament_title: str,
    mode: ExportMode,
) -> dict[str, str]:
    entry = {
        "tournament_name": tournament_title,
        "category": (bracket.get_display_name() if hasattr(bracket, "get_display_name") else bracket.category.name),
        "start_time_tatami": start_time_tatami,
    }

    for match in matches:
        if mode == "manual" and match.round_number != 1:
            continue

        rnd = match.round_number + offset

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
    matches: list[BracketMatch],
    category: str,
    start_time_tatami: str,
    tournament_title: str,
    mode: ExportMode,
) -> dict[str, str]:
    def _format_athlete_for_round_template(last_name: str, first_name: str, coach_names: list[str]) -> str:
        coach_str = ", ".join(coach_names)
        if not coach_str:
            return f"{last_name} {first_name}"
        return f"{last_name} {first_name}\n({coach_str})"

    def _format_athlete_for_fights(athlete: Athlete | None) -> str:
        if athlete is None:
            return "?"
        coach_names = [link.coach.last_name for link in athlete.coach_links if link.coach is not None]
        name = f"{athlete.last_name} {athlete.first_name}"
        return f"{name} ({', '.join(coach_names)})" if coach_names else name

    athletes_map = {}
    for match in matches:
        a1 = match.match.athlete1
        a2 = match.match.athlete2
        if a1:
            # Get coach names from the many-to-many relationship
            coach_names = [link.coach.last_name for link in a1.coach_links if link.coach is not None]
            athletes_map[a1.id] = _format_athlete_for_round_template(a1.last_name, a1.first_name, coach_names)
        if a2:
            # Get coach names from the many-to-many relationship
            coach_names = [link.coach.last_name for link in a2.coach_links if link.coach is not None]
            athletes_map[a2.id] = _format_athlete_for_round_template(a2.last_name, a2.first_name, coach_names)

    athlete_ids = list(athletes_map)
    athletes = list(athletes_map.values())

    entry = {
        "tournament_name": tournament_title,
        "category": category,
        "start_time_tatami": start_time_tatami,
    }

    for idx, athlete in enumerate(athletes, start=1):
        entry[f"athlete{idx}"] = athlete

    # Same wording as the "fights by bracket" report in the admin UI.
    ordered = sorted(matches, key=lambda m: (m.round_number, m.position))
    entry["fights"] = "\n".join(
        f"{index}) {_format_athlete_for_fights(m.match.athlete1)} vs {_format_athlete_for_fights(m.match.athlete2)}"
        for index, m in enumerate(ordered, start=1)
    )

    if mode == "filled":
        athlete_positions = {athlete_id: idx for idx, athlete_id in enumerate(athlete_ids, start=1)}
        for match in matches:
            a1 = match.match.athlete1
            a2 = match.match.athlete2
            score1 = match.match.score_athlete1
            score2 = match.match.score_athlete2
            if not a1 or not a2 or score1 is None or score2 is None:
                continue

            pos1 = athlete_positions[a1.id]
            pos2 = athlete_positions[a2.id]
            entry[f"score_{pos1}_{pos2}"] = f"{score1} : {score2}"
            entry[f"score_{pos2}_{pos1}"] = f"{score2} : {score1}"

    return entry


def _inject_round_template_multiline_athletes(svg_template: str, entry: dict[str, str]) -> str:
    for idx in range(1, ROUND_ROBIN_MAX_ATHLETES + 1):
        key = f"athlete{idx}"
        raw_value = entry.get(key, "")
        name_line, _, coach_line = raw_value.partition("\n")
        # Long names do not fit the 6-column table: put last and first name on separate lines.
        if len(name_line) > ROUND_ROBIN_NAME_MAX_CHARS and " " in name_line:
            lines = name_line.split(" ", 1)
        else:
            lines = [name_line]
        if coach_line:
            lines.append(coach_line)
        lines = [escape(line) for line in lines]

        pattern = rf"<text(?P<attrs>[^>]*)>\[\[\s*{key}\s*\]\]</text>"

        def replace_text(match: re.Match[str]) -> str:
            attrs = match.group("attrs")
            if len(lines) == 1:
                return f"<text{attrs}>{lines[0]}</text>"

            x_match = re.search(r'\bx="([^"]+)"', attrs)
            x_attr = f' x="{x_match.group(1)}"' if x_match else ""
            # Lift the first line so the whole block stays centred in the cell.
            lift = (len(lines) - 1) * ROUND_ROBIN_LINE_HEIGHT / 2
            attrs = re.sub(r'\by="([^"]+)"', lambda m: f'y="{float(m.group(1)) - lift:g}"', attrs, count=1)
            tail = "".join(f'<tspan{x_attr} dy="{ROUND_ROBIN_LINE_HEIGHT}">{line}</tspan>' for line in lines[1:])
            return f"<text{attrs}>{lines[0]}{tail}</text>"

        svg_template = re.sub(pattern, replace_text, svg_template)

    return _inject_multiline_text(svg_template, "fights", entry.get("fights", ""), FIGHTS_LINE_HEIGHT)


def _inject_multiline_text(svg_template: str, key: str, value: str, line_height: int) -> str:
    """Render a newline-separated value into the template's [[key]] <text> as stacked tspans."""
    pattern = rf"<text(?P<attrs>[^>]*)>\[\[\s*{key}\s*\]\]</text>"

    def replace_text(match: re.Match[str]) -> str:
        attrs = match.group("attrs")
        x_match = re.search(r'\bx="([^"]+)"', attrs)
        x_attr = f' x="{x_match.group(1)}"' if x_match else ""
        lines = [escape(line) for line in value.split("\n")] if value else [""]
        tail = "".join(f'<tspan{x_attr} dy="{line_height}">{line}</tspan>' for line in lines[1:])
        return f"<text{attrs}>{lines[0]}{tail}</text>"

    return re.sub(pattern, replace_text, svg_template)


def _replace_placeholders(svg_template: str, entry: dict[str, str]) -> str:
    return PLACEHOLDER_PATTERN.sub(lambda match: escape(entry.get(match.group(1), "")), svg_template)


def build_entries(
    data: list[Bracket],
    tournament_title: str,
    start_date: date | None = None,
    mode: ExportMode = "filled",
) -> list[dict[str, str]]:
    all_entries = []

    for bracket in data:
        timetable_entry = getattr(bracket, "timetable_entry", None)
        if timetable_entry:
            start_time_value = timetable_entry.start_time.strftime("%H:%M")
            if start_date is not None:
                event_date = start_date + timedelta(days=max(0, timetable_entry.day - 1))
                event_date_value = event_date.strftime("%d.%m.%Y")
            else:
                event_date_value = "-"
            start_time_tatami = (
                f"{event_date_value} | Day: {timetable_entry.day} | Start time: {start_time_value} | "
                f"Tatami: {timetable_entry.tatami}"
            )
        else:
            fallback_date = start_date.strftime("%d.%m.%Y") if start_date is not None else "-"
            start_time_tatami = f"{fallback_date} | Day: - | Start time: - | Tatami: -"
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
                mode=mode,
            )
            entry["_template"] = BracketType.ROUND_ROBIN.value
            all_entries.append(entry)
            continue

        max_round = min(4, max(m.round_number for m in matches))

        round1_matches = sorted([m for m in matches if m.round_number == 1], key=lambda m: m.position)

        chunk_size = 8
        for i in range(0, len(round1_matches), chunk_size):
            position_offset = i
            entry = build_entry(
                bracket=bracket,
                matches=matches,
                offset=4 - max_round,
                position_offset=position_offset,
                start_time_tatami=start_time_tatami,
                tournament_title=tournament_title,
                mode=mode,
            )
            if len(entry) > 1:
                entry["_template"] = "elimination"
                all_entries.append(entry)

    return all_entries


def generate_pdf(
    data: list[Bracket],
    tournament_title: str,
    start_date: date | None = None,
    mode: ExportMode = "filled",
) -> bytes | None:
    """Render all brackets into one PDF in memory. Returns None when there is nothing to export."""
    entries = build_entries(data, tournament_title, start_date=start_date, mode=mode)
    if not entries:
        return None

    writer = PdfWriter()
    elimination_template = Path(SVG_TEMPLATE_PATH).read_text(encoding="utf-8")
    round_template = Path(SVG_ROUND_TEMPLATE_PATH).read_text(encoding="utf-8")

    for entry in entries:
        template_type = entry.get("_template", "elimination")
        if template_type == BracketType.ROUND_ROBIN.value:
            svg_template = _inject_round_template_multiline_athletes(round_template, entry)
        else:
            svg_template = elimination_template

        svg_template = _replace_placeholders(svg_template, entry)
        page = BytesIO()
        cairosvg.svg2pdf(bytestring=svg_template.encode("utf-8"), write_to=page)
        page.seek(0)
        writer.append_pages_from_reader(PdfReader(page))

    output = BytesIO()
    writer.write(output)
    return output.getvalue()


def export_filename(tournament_title: str, mode: ExportMode) -> str:
    return f"{sanitize_filename(tournament_title or 'tournament')}_{mode}.pdf"
