import re

from pypdf import PdfReader


class PlanogramError(ValueError):
    pass


def parse_planogram(upload):
    """Extract structured planogram rows from the supplier PDF table pages."""
    try:
        reader = PdfReader(upload)
    except Exception as exc:
        raise PlanogramError("The uploaded file is not a readable PDF.") from exc

    result = []
    for page_number, page in enumerate(reader.pages, 1):
        fragments = []

        def collect(text, _cm, tm, _font, _size):
            value = " ".join(text.split())
            if value:
                fragments.append((float(tm[4]), float(tm[5]), value))

        page.extract_text(visitor_text=collect)
        markers = sorted(
            [(y, int(match.group(1)), int(match.group(2))) for x, y, value in fragments if 30 <= x <= 90 and (match := re.fullmatch(r"(\d+)/(\d+)", value))],
            reverse=True,
        )
        for marker_index, (marker_y, fixture, shelf) in enumerate(markers):
            lower_y = markers[marker_index + 1][0] if marker_index + 1 < len(markers) else 55
            starts = sorted(
                [(y, int(value)) for x, y, value in fragments if 8 <= x <= 35 and lower_y < y < marker_y and value.isdigit() and 1 <= int(value) <= 100],
                reverse=True,
            )
            for row_index, (row_y, position) in enumerate(starts):
                next_y = starts[row_index + 1][0] if row_index + 1 < len(starts) else lower_y
                band = [(x, y, value) for x, y, value in fragments if next_y < y <= row_y + 1]

                def column(left, right):
                    values = [value for x, _y, value in sorted(band, key=lambda item: (-item[1], item[0])) if left <= x < right]
                    return "".join(values).strip()

                londis_code = column(45, 96)
                m_code = column(96, 139)
                name = column(139, 272)
                pack_size = column(272, 327).replace(" ", "")
                units = column(327, 336)
                barcode = re.sub(r"\D", "", column(336, 431))
                facings = column(431, 480)
                if name and (barcode or londis_code):
                    result.append({
                        "page": page_number,
                        "fixture_number": fixture,
                        "shelf_number": shelf,
                        "position": position,
                        "londis_code": londis_code,
                        "m_code": m_code,
                        "name": name,
                        "pack_size": pack_size,
                        "units_per_case": int(units) if units.isdigit() else None,
                        "barcode": barcode,
                        "facings": int(facings) if facings.isdigit() else 1,
                    })

    unique = {(row["fixture_number"], row["shelf_number"], row["position"]): row for row in result}
    rows = sorted(unique.values(), key=lambda row: (row["fixture_number"], row["shelf_number"], row["position"]))
    if not rows:
        raise PlanogramError("No structured product table was found in this PDF.")
    return rows
