from pathlib import Path

KNOWLEDGE_BASE_UNAVAILABLE_MESSAGE = (
    "База знаний пока не заполнена. Лучше уточнить вопрос у менеджера."
)


class KnowledgeService:
    def __init__(self, knowledge_base_path: str = "data/knowledge_base.md") -> None:
        self.knowledge_base_path = Path(knowledge_base_path)

    def read_knowledge_base(self) -> str:
        if not self.knowledge_base_path.exists():
            return KNOWLEDGE_BASE_UNAVAILABLE_MESSAGE

        try:
            content = self.knowledge_base_path.read_text(encoding="utf-8").strip()
        except OSError:
            return KNOWLEDGE_BASE_UNAVAILABLE_MESSAGE

        if not content:
            return KNOWLEDGE_BASE_UNAVAILABLE_MESSAGE

        return content

    def get_contacts(self) -> str:
        knowledge_base = self.read_knowledge_base()
        contacts_section = self._extract_section(knowledge_base, "Контакты")

        if contacts_section:
            return contacts_section

        return "Контакты не указаны в базе знаний. Лучше уточнить их у менеджера."

    @staticmethod
    def _extract_section(markdown: str, title: str) -> str | None:
        lines = markdown.splitlines()
        section_lines: list[str] = []
        in_section = False

        for line in lines:
            stripped = line.strip()

            if stripped.startswith("#"):
                heading = stripped.lstrip("#").strip()
                normalized_heading = KnowledgeService._normalize_heading(heading)
                normalized_title = title.lower()

                if in_section and normalized_heading != normalized_title:
                    break
                in_section = normalized_heading == normalized_title
                if in_section:
                    section_lines.append(stripped)
                continue

            if in_section:
                section_lines.append(line)

        section = "\n".join(section_lines).strip()
        return section or None

    @staticmethod
    def _normalize_heading(heading: str) -> str:
        parts = heading.split(maxsplit=1)
        if len(parts) == 2 and parts[0].rstrip(".").isdigit():
            return parts[1].strip().lower()
        return heading.strip().lower()
