"""
Theory widget module for Tragictory Physics.

This module contains the TheoryWidget class that displays theory content
and formulas using QWebEngineView with MathJax for professional LaTeX rendering.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton
)
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEngineSettings
from PyQt6.QtCore import QUrl
from typing import List, Dict


class TheoryWidget(QWidget):
    """Widget for displaying theory content and formulas.

    Uses QWebEngineView with MathJax for professional LaTeX rendering.
    """

    def __init__(self) -> None:
        """Initialize the theory widget with UI components."""
        super().__init__()

        # Internal data storage
        self.current_theory: str = ""
        self.current_formulas: List[Dict] = []
        self.current_title: str = ""

        # Main layout
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(20, 20, 20, 20)
        self.layout.setSpacing(15)

        self._setup_web_view()
        self._setup_simulation_button()

    def _setup_web_view(self) -> None:
        """Setup the web engine view with permissions for remote/local content."""
        self.web_view = QWebEngineView()

        # Allow local HTML to access remote (CDN) and local file resources
        settings = self.web_view.settings()
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessFileUrls, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled, True)

        self.layout.addWidget(self.web_view)

    def _setup_simulation_button(self) -> None:
        """Setup the simulation launch button (hidden by default)."""
        self.simulation_button = QPushButton("Запустить симуляцию")
        self.simulation_button.setMinimumWidth(200)
        self.simulation_button.hide()

        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(self.simulation_button)
        self.layout.addLayout(button_layout)

    def _render_content(self) -> None:
        """Render the complete HTML content with MathJax support."""
        formulas_html = self._generate_formulas_html()

        html_content = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>
    window.MathJax = {
        tex: {
            inlineMath: [['$', '$'], ['\\\\(', '\\\\)']],
            displayMath: [['$$', '$$'], ['\\\\[', '\\\\]']],
            processEscapes: true
        },
        svg: { fontCache: 'global' },
        startup: {
            typeset: true
        }
    };
    </script>
    <script async src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"></script>
    <style>
        body {
            margin: 0;
            padding: 0;
            background-color: #1e1e1e;
            color: #d4d4d4;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            line-height: 1.6;
        }
        .container {
            max-width: 800px;
            margin: 0 auto;
            padding: 40px 20px;
        }
        h1 {
            color: #ffffff;
            border-bottom: 1px solid #333;
            padding-bottom: 10px;
            margin-top: 0;
            margin-bottom: 20px;
        }
        h2, h3, h4, h5, h6 {
            color: #ffffff;
            margin-top: 24px;
            margin-bottom: 16px;
        }
        h2 { font-size: 24px; }
        h3 { font-size: 20px; }
        p { margin-bottom: 16px; }
        strong, b { color: #ffffff; }
        ul, ol { margin-bottom: 16px; padding-left: 20px; }
        li { margin-bottom: 8px; }
        table {
            border-collapse: collapse;
            width: 100%;
            margin-top: 30px;
            background-color: #252526;
            border-radius: 8px;
            overflow: hidden;
        }
        th, td {
            border: 1px solid #333;
            padding: 16px;
            text-align: left;
            vertical-align: middle;
        }
        th {
            background-color: #2d2d30;
            font-weight: 600;
            color: #ffffff;
        }
        .formula-cell {
            text-align: center;
            min-width: 220px;
        }
        .formula-description {
            color: #d4d4d4;
        }
        mjx-container {
            color: #ffffff !important;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>__TITLE__</h1>
        __THEORY__
        __FORMULAS__
    </div>
</body>
</html>
"""

        # Inject content via placeholders to avoid f-string brace conflicts
        html_content = (
            html_content
            .replace("__TITLE__", self.current_title)
            .replace("__THEORY__", self.current_theory)
            .replace("__FORMULAS__", formulas_html)
        )

        # Use a baseUrl so MathJax CDN and local resources can load
        base_url = QUrl("https://local.tragictory/")
        self.web_view.setHtml(html_content, base_url)

    def _generate_formulas_html(self) -> str:
        """Generate HTML table with LaTeX formulas wrapped for MathJax."""
        if not self.current_formulas:
            return ""

        rows = ""
        for formula in self.current_formulas:
            formula_latex = (formula.get('formula_latex') or '').strip()
            description = formula.get('description', '')

            # Strip surrounding $$ if already present, then wrap in display math
            cleaned = formula_latex
            if cleaned.startswith("$$") and cleaned.endswith("$$"):
                cleaned = cleaned[2:-2].strip()
            wrapped = f"\\[{cleaned}\\]"

            rows += f"""
                <tr>
                    <td class="formula-cell">{wrapped}</td>
                    <td class="formula-description">{description}</td>
                </tr>
            """

        return f"""
        <h2>Формулы</h2>
        <table>
            <thead>
                <tr>
                    <th>Формула</th>
                    <th>Описание</th>
                </tr>
            </thead>
            <tbody>
                {rows}
            </tbody>
        </table>
        """

    def set_title(self, text: str) -> None:
        """Set the topic title."""
        self.current_title = text
        self._render_content()

    def set_theory(self, html: str) -> None:
        """Set the theory content in HTML format."""
        self.current_theory = html
        self._render_content()

    def set_formulas(self, data_list: List[Dict]) -> None:
        """Set the formulas data and re-render."""
        self.current_formulas = data_list or []
        self._render_content()

    def show_simulation_button(self) -> None:
        """Show the simulation launch button."""
        self.simulation_button.show()

    def hide_simulation_button(self) -> None:
        """Hide the simulation launch button."""
        self.simulation_button.hide()

    def get_simulation_button(self) -> QPushButton:
        """Return the simulation launch button."""
        return self.simulation_button
