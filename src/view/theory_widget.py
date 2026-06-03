"""
Theory widget module for Tragictory Physics.

This module contains the TheoryWidget class that displays theory content
and formulas using QWebEngineView with MathJax for professional LaTeX rendering.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton
)
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtGui import QFont
from typing import List, Dict


class TheoryWidget(QWidget):
    """Widget for displaying theory content and formulas.
    
    Provides a structured view for educational content including topic title,
    theory text in HTML format, and formulas with professional LaTeX rendering
    using MathJax via QWebEngineView.
    """
    
    def __init__(self) -> None:
        """Initialize the theory widget with UI components."""
        super().__init__()
        
        # Initialize data storage
        self.current_theory: str = ""
        self.current_formulas: List[Dict] = []
        
        # Create main layout
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(20, 20, 20, 20)
        self.layout.setSpacing(15)
        
        # Initialize UI components
        self._setup_title_label()
        self._setup_web_view()
        self._setup_simulation_button()
    
    def _setup_title_label(self) -> None:
        """Setup the topic title label with large bold font."""
        self.title_label = QLabel()
        font = QFont()
        font.setPointSize(16)
        font.setBold(True)
        self.title_label.setFont(font)
        self.title_label.setWordWrap(True)
        self.layout.addWidget(self.title_label)
    
    def _setup_web_view(self) -> None:
        """Setup the web engine view for HTML content with MathJax."""
        self.web_view = QWebEngineView()
        self.layout.addWidget(self.web_view)
    
    def _setup_simulation_button(self) -> None:
        """Setup the simulation launch button (hidden by default)."""
        self.simulation_button = QPushButton("Запустить симуляцию")
        self.simulation_button.hide()  # Hidden initially
        self.layout.addWidget(self.simulation_button)
    
    def _render_content(self) -> None:
        """Render the complete HTML content with MathJax support."""
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <script src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"></script>
            <style>
                body {{
                    background-color: #1e1e1e;
                    color: #d4d4d4;
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
                    font-size: 16px;
                    line-height: 1.6;
                    padding: 20px;
                    margin: 0;
                }}
                
                h1, h2, h3, h4, h5, h6 {{
                    color: #ffffff;
                    margin-top: 24px;
                    margin-bottom: 16px;
                }}
                
                h1 {{ font-size: 28px; }}
                h2 {{ font-size: 24px; }}
                h3 {{ font-size: 20px; }}
                
                p {{
                    margin-bottom: 16px;
                }}
                
                strong {{
                    color: #ffffff;
                }}
                
                ul, ol {{
                    margin-bottom: 16px;
                    padding-left: 20px;
                }}
                
                li {{
                    margin-bottom: 8px;
                }}
                
                blockquote {{
                    background-color: #2a2a2a;
                    border-left: 4px solid #094771;
                    margin: 16px 0;
                    padding: 12px 16px;
                    border-radius: 0 4px 4px 0;
                }}
                
                table {{
                    border-collapse: collapse;
                    width: 100%;
                    margin-top: 20px;
                    background-color: #252526;
                    border-radius: 4px;
                    overflow: hidden;
                }}
                
                th, td {{
                    border: 1px solid #3e3e42;
                    padding: 12px;
                    text-align: left;
                    vertical-align: top;
                }}
                
                th {{
                    background-color: #2a2a2a;
                    font-weight: bold;
                    color: #ffffff;
                }}
                
                tr:nth-child(even) {{
                    background-color: #2a2a2a;
                }}
                
                .formula {{
                    font-family: 'Courier New', monospace;
                    font-size: 14px;
                    background-color: #1a1a1a;
                    padding: 8px;
                    border-radius: 4px;
                    margin: 4px 0;
                    display: inline-block;
                }}
                
                .formula-description {{
                    color: #b3b3b3;
                    font-style: italic;
                }}
            </style>
        </head>
        <body>
            {self.current_theory}
            
            {self._generate_formulas_html()}
        </body>
        </html>
        """
        
        self.web_view.setHtml(html_content)
    
    def _generate_formulas_html(self) -> str:
        """Generate HTML table with LaTeX formulas."""
        if not self.current_formulas:
            return ""
        
        formulas_html = """
        <h2>Формулы</h2>
        <table>
            <thead>
                <tr>
                    <th>Формула</th>
                    <th>Описание</th>
                </tr>
            </thead>
            <tbody>
        """
        
        for formula in self.current_formulas:
            formula_latex = formula.get('formula_latex', '')
            description = formula.get('description', '')
            
            # Wrap LaTeX formula in $$ for MathJax rendering
            rendered_formula = f"$${formula_latex}$$"
            
            formulas_html += f"""
                <tr>
                    <td>
                        <div class="formula">{rendered_formula}</div>
                    </td>
                    <td>
                        <div class="formula-description">{description}</div>
                    </td>
                </tr>
            """
        
        formulas_html += """
            </tbody>
        </table>
        """
        
        return formulas_html
    
    def set_title(self, text: str) -> None:
        """Set the topic title.
        
        Args:
            text: The title text to display.
        """
        self.title_label.setText(text)
    
    def set_theory(self, html: str) -> None:
        """Set the theory content in HTML format.
        
        Args:
            html: The HTML content to display in the theory view.
        """
        self.current_theory = html
        self._render_content()
    
    def set_formulas(self, data_list: List[Dict]) -> None:
        """Set the formulas data for rendering.
        
        Args:
            data_list: List of dictionaries with 'formula_latex' and 'description' keys.
        """
        self.current_formulas = data_list or []
        self._render_content()
    
    def show_simulation_button(self) -> None:
        """Show the simulation launch button."""
        self.simulation_button.show()
    
    def hide_simulation_button(self) -> None:
        """Hide the simulation launch button."""
        self.simulation_button.hide()
    
    def get_simulation_button(self) -> QPushButton:
        """Get the simulation button widget.
        
        Returns:
            QPushButton: The simulation launch button.
        """
        return self.simulation_button
