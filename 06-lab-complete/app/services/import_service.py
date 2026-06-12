import csv
import io

from sqlalchemy.orm import Session

from app.models.card import Card


REQUIRED_COLUMNS = {"front", "back"}
OPTIONAL_COLUMNS = {"phonetic", "part_of_speech", "example", "example_translation", "tags"}
ALL_COLUMNS = REQUIRED_COLUMNS | OPTIONAL_COLUMNS
MAX_ROWS = 1000


def parse_csv_content(content: str) -> tuple[list[str] | None, list[dict], str | None]:
    reader = csv.DictReader(io.StringIO(content))
    if not reader.fieldnames:
        return None, [], "File CSV trống hoặc không có header"

    headers = {h.strip().lower() for h in reader.fieldnames}
    missing = REQUIRED_COLUMNS - headers
    if missing:
        return None, [], f"Thiếu cột bắt buộc: {', '.join(sorted(missing))}"

    rows = []
    for i, row in enumerate(reader, start=2):
        if i - 1 > MAX_ROWS:
            break
        normalized = {k.strip().lower(): (v.strip() if v else "") for k, v in row.items()}
        rows.append({"row_number": i, **normalized})
    return list(headers), rows, None


def validate_import_rows(db: Session, deck_id: int, rows: list[dict]) -> list[dict]:
    existing_fronts = {
        c.front.lower()
        for c in db.query(Card).filter(Card.deck_id == deck_id, Card.is_deleted == False).all()
    }
    results = []
    seen_fronts: set[str] = set()

    for row in rows:
        front = row.get("front", "").strip()
        back = row.get("back", "").strip()
        row_num = row.get("row_number", 0)
        error = None
        is_valid = True

        if not front:
            error = "Từ tiếng Anh (front) không được để trống"
            is_valid = False
        elif len(front) > 255:
            error = "Từ tiếng Anh quá dài (tối đa 255 ký tự)"
            is_valid = False
        elif not back:
            error = "Nghĩa tiếng Việt (back) không được để trống"
            is_valid = False

        is_duplicate = front.lower() in existing_fronts or front.lower() in seen_fronts
        if is_valid:
            seen_fronts.add(front.lower())

        results.append({
            "row_number": row_num,
            "front": front,
            "back": back,
            "phonetic": row.get("phonetic") or None,
            "part_of_speech": row.get("part_of_speech") or None,
            "example": row.get("example") or None,
            "example_translation": row.get("example_translation") or None,
            "tags": row.get("tags") or None,
            "is_valid": is_valid,
            "is_duplicate": is_duplicate,
            "error": error,
        })
    return results


def import_cards(db: Session, deck_id: int, rows: list[dict], skip_duplicates: bool = True) -> int:
    count = 0
    existing_fronts = {
        c.front.lower()
        for c in db.query(Card).filter(Card.deck_id == deck_id, Card.is_deleted == False).all()
    }
    for row in rows:
        if not row.get("is_valid"):
            continue
        if skip_duplicates and row.get("is_duplicate"):
            continue
        front = row["front"]
        if front.lower() in existing_fronts:
            continue
        card = Card(
            deck_id=deck_id,
            front=front,
            back=row["back"],
            phonetic=row.get("phonetic"),
            part_of_speech=row.get("part_of_speech"),
            example=row.get("example"),
            example_translation=row.get("example_translation"),
            tags=row.get("tags"),
        )
        db.add(card)
        existing_fronts.add(front.lower())
        count += 1
    db.commit()
    return count
