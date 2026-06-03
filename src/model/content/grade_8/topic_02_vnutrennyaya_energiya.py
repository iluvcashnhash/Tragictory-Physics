from ..registry import register_content

THEORY = "<h2>Внутренняя энергия</h2><p>Контент в разработке...</p>"

FORMULAS = []

QUESTIONS = []

register_content(
    grade=8,
    grade_desc="Тепловые явления и электричество",
    title="Внутренняя энергия",
    has_simulation=False,
    theory_html=THEORY,
    formulas=FORMULAS,
    questions=QUESTIONS,
)
