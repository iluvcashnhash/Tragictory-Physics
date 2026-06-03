from ..registry import register_content

THEORY = "<h2>Броуновское движение</h2><p>Контент в разработке...</p>"

FORMULAS = []

QUESTIONS = []

register_content(
    grade=7,
    grade_desc="Введение в физику",
    title="Броуновское движение",
    has_simulation=False,
    theory_html=THEORY,
    formulas=FORMULAS,
    questions=QUESTIONS,
)
