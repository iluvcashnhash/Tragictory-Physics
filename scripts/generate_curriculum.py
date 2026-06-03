"""
Curriculum generator for Tragictory Physics.

Generates the folder structure and stub content files for every grade/topic
defined in CURRICULUM. Re-running the script is safe — existing files are
never overwritten.

Usage
-----
From the project root (with the virtual environment active):

    python scripts/generate_curriculum.py
"""

import re
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Transliteration table (Russian → Latin)
# ---------------------------------------------------------------------------
_TRANSLIT: dict[str, str] = {
    "а": "a",  "б": "b",  "в": "v",  "г": "g",  "д": "d",
    "е": "e",  "ё": "yo", "ж": "zh", "з": "z",  "и": "i",
    "й": "y",  "к": "k",  "л": "l",  "м": "m",  "н": "n",
    "о": "o",  "п": "p",  "р": "r",  "с": "s",  "т": "t",
    "у": "u",  "ф": "f",  "х": "kh", "ц": "ts", "ч": "ch",
    "ш": "sh", "щ": "sch","ъ": "",   "ы": "y",  "ь": "",
    "э": "e",  "ю": "yu", "я": "ya",
}


def transliterate(text: str) -> str:
    """Convert a Russian string to a lowercase Latin identifier fragment.

    Args:
        text: Russian (or mixed) input string.

    Returns:
        str: Lowercase Latin string with spaces replaced by underscores,
             suitable for use in a Python module name.
    """
    result = []
    for char in text.lower():
        result.append(_TRANSLIT.get(char, char))
    joined = "".join(result)
    # Replace any non-alphanumeric characters with underscores
    joined = re.sub(r"[^a-z0-9]+", "_", joined)
    # Strip leading/trailing underscores
    return joined.strip("_")


# ---------------------------------------------------------------------------
# Curriculum definition
# ---------------------------------------------------------------------------
CURRICULUM: dict[int, list[str]] = {
    7: [
        "Физика как наука",
        "Физические величины",
        "Броуновское движение",
    ],
    8: [
        "Тепловое движение",
        "Внутренняя энергия",
    ],
    9: [],
    10: [],
    11: [],
}

GRADE_DESCRIPTIONS: dict[int, str] = {
    7:  "Введение в физику",
    8:  "Тепловые явления и электричество",
    9:  "Динамика и законы сохранения",
    10: "Кинематика",
    11: "Квантовая физика и астрофизика",
}

# ---------------------------------------------------------------------------
# File template
# ---------------------------------------------------------------------------
_STUB_TEMPLATE = '''\
from ..registry import register_content

THEORY = "<h2>{title}</h2><p>Контент в разработке...</p>"

FORMULAS = []

QUESTIONS = []

register_content(
    grade={grade},
    grade_desc="{grade_desc}",
    title="{title}",
    has_simulation=False,
    theory_html=THEORY,
    formulas=FORMULAS,
    questions=QUESTIONS,
)
'''


# ---------------------------------------------------------------------------
# Generator
# ---------------------------------------------------------------------------

def generate(content_root: Path) -> None:
    """Generate grade folders and topic stub files under *content_root*.

    Args:
        content_root: Absolute path to ``src/model/content/``.
    """
    for grade, topics in CURRICULUM.items():
        if not topics:
            continue  # Skip grades with no topics defined yet

        grade_dir = content_root / f"grade_{grade}"
        grade_dir.mkdir(parents=True, exist_ok=True)

        init_file = grade_dir / "__init__.py"
        if not init_file.exists():
            init_file.write_text("", encoding="utf-8")
            print(f"  Created {init_file.relative_to(content_root.parent.parent.parent)}")

        grade_desc = GRADE_DESCRIPTIONS.get(grade, f"{grade} класс")

        for idx, title in enumerate(topics, start=1):
            slug = transliterate(title)
            filename = f"topic_{idx:02d}_{slug}.py"
            topic_file = grade_dir / filename

            if topic_file.exists():
                print(f"  Skipped (exists): {topic_file.relative_to(content_root.parent.parent.parent)}")
                continue

            stub = _STUB_TEMPLATE.format(
                title=title,
                grade=grade,
                grade_desc=grade_desc,
            )
            topic_file.write_text(stub, encoding="utf-8")
            print(f"  Created {topic_file.relative_to(content_root.parent.parent.parent)}")

    print("\nCurriculum generation complete.")


if __name__ == "__main__":
    # Resolve the content directory relative to this script's location
    project_root = Path(__file__).resolve().parent.parent
    content_root = project_root / "src" / "model" / "content"

    if not content_root.exists():
        print(f"ERROR: content directory not found: {content_root}", file=sys.stderr)
        sys.exit(1)

    print(f"Generating curriculum stubs in: {content_root}\n")
    generate(content_root)
