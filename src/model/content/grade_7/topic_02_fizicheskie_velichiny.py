from ..registry import register_content

THEORY = "<h2>Физические величины</h2><p>Контент в разработке...</p>"

FORMULAS = []

QUESTIONS = []

register_content(
    grade=7,
    grade_desc="Введение в физику",
    title="Физические величины",
    has_simulation=False,
    theory_html=THEORY,
    formulas=FORMULAS,
    questions=QUESTIONS,
)
