import csv
from datetime import datetime, timezone
from pathlib import Path


LEADS_CSV_HEADERS = (
    "created_at",
    "telegram_id",
    "username",
    "name",
    "phone",
    "task",
)


class LeadService:
    def __init__(self, leads_path: str = "data/leads.csv") -> None:
        self.leads_path = Path(leads_path)

    def save_lead(
        self,
        telegram_id: int,
        username: str,
        name: str,
        phone: str,
        task: str,
    ) -> dict[str, str]:
        self._ensure_csv_exists()

        lead = {
            "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "telegram_id": str(telegram_id),
            "username": username,
            "name": name,
            "phone": phone,
            "task": task,
        }

        with self.leads_path.open("a", encoding="utf-8", newline="") as file:
            writer = csv.DictWriter(file, fieldnames=LEADS_CSV_HEADERS)
            writer.writerow(lead)

        return lead

    def _ensure_csv_exists(self) -> None:
        self.leads_path.parent.mkdir(parents=True, exist_ok=True)

        if self.leads_path.exists() and self.leads_path.stat().st_size > 0:
            return

        with self.leads_path.open("w", encoding="utf-8", newline="") as file:
            writer = csv.DictWriter(file, fieldnames=LEADS_CSV_HEADERS)
            writer.writeheader()
