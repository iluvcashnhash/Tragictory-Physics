"""
Theory widget module for Tragictory Physics.

This module contains the TheoryWidget class that displays theory content
and formulas using QWebEngineView with MathJax for professional LaTeX rendering.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
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
        self.current_title: str = ""
        
        # Create main layout
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(20, 20, 20, 20)
        self.layout.setSpacing(15)
        
        # Initialize UI components
        self._setup_title_label()
        self._setup_web_view()
        self._setup_simulation_button()
    
    def _setup_title_label(self) -> None:
        """Title is now handled inside HTML content."""
        pass
    
    def _setup_web_view(self) -> None:
        """Setup the web engine view for HTML content with MathJax."""
        self.web_view = QWebEngineView()
        self.layout.addWidget(self.web_view)
    
    def _setup_simulation_button(self) -> None:
        """Setup the simulation launch button (hidden by default)."""
        self.simulation_button = QPushButton("Запустить симуляцию")
        self.simulation_button.setMinimumWidth(200)  # Fixed minimum width
        self.simulation_button.hide()  # Hidden initially
        
        # Create horizontal layout for button with right alignment
        button_layout = QHBoxLayout()
        button_layout.addStretch()  # Push button to the right
        button_layout.addWidget(self.simulation_button)
        
        # Add button layout to main layout
        self.layout.addLayout(button_layout)
    
    def _render_content(self) -> None:
        """Render the complete HTML content with MathJax support."""
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
                        <style>
                body {{
                    margin: 0;
                    padding: 0;
                    background-color: #1e1e1e;
                    color: #d4d4d4;
                    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
                    line-height: 1.6;
                }}
                
                .container {{
                    max-width: 800px;
                    margin: 0 auto;
                    padding: 40px 20px;
                }}
                
                h1 {{
                    color: #ffffff;
                    border-bottom: 1px solid #333;
                    padding-bottom: 10px;
                    margin-top: 0;
                    margin-bottom: 20px;
                }}
                
                h2, h3, h4, h5, h6 {{
                    color: #ffffff;
                    margin-top: 24px;
                    margin-bottom: 16px;
                }}
                
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
                    margin-top: 30px;
                    background-color: #252526;
                    border-radius: 8px;
                    overflow: hidden;
                }}
                
                th, td {{
                    border: 1px solid #333;
                    padding: 16px;
                    text-align: left;
                }}
                
                th {{
                    background-color: #2d2d30;
                    font-weight: 600;
                    color: #ffffff;
                }}
                
                tr:nth-child(even) {{
                    background-color: #2a2a2a;
                }}
                
                .formula {{
                    font-family: 'Times New Roman', serif;
                    font-size: 16px;
                    background-color: #2a2a2a;
                    padding: 12px;
                    border-radius: 6px;
                    margin: 8px 0;
                    display: block;
                    text-align: center;
                    border: 1px solid #3e3e42;
                    color: #ffffff;
                    font-weight: 500;
                    letter-spacing: 0.5px;
                }}
                
                .formula-description {{
                    color: #b3b3b3;
                    font-style: italic;
                    margin-top: 8px;
                }}
                
                /* Style for common LaTeX symbols */
                .formula {{
                    /* Common mathematical symbols styling */
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>{self.current_title}</h1>
                {self.current_theory}
                {self._generate_formulas_html()}
            </div>
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
            
            # Clean up LaTeX formula - remove $$ symbols and add basic formatting
            clean_formula = formula_latex.replace('$$', '').strip()
            
            # Basic LaTeX to readable format conversion
            clean_formula = clean_formula.replace('\\sum', '∑')
            clean_formula = clean_formula.replace('\\vec', '')
            clean_formula = clean_formula.replace('\\cdot', '·')
            clean_formula = clean_formula.replace('\\frac', '(')
            clean_formula = clean_formula.replace('}{', ')/(')
            clean_formula = clean_formula.replace('{', '').replace('}', '')
            clean_formula = clean_formula.replace('\\nu', 'ν')
            clean_formula = clean_formula.replace('\\alpha', 'α')
            clean_formula = clean_formula.replace('\\implies', '→')
            clean_formula = clean_formula.replace('\\cdot', '·')
            
            formulas_html += f"""
                <tr>
                    <td>
                        <div class="formula">{clean_formula}</div>
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
        self.current_title = text
        self._render_content()
    
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
