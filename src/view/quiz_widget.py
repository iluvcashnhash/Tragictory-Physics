"""
Quiz widget module for Tragictory Physics.

This module contains the QuizWidget class that presents multiple-choice
questions and evaluates the user's answers.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QRadioButton, QButtonGroup, QPushButton
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from typing import List


class QuizWidget(QWidget):
    """Widget for displaying and evaluating multiple-choice quiz questions.

    Provides a question label, radio-button answer options, a result label,
    and Submit / Back buttons.
    """

    def __init__(self) -> None:
        """Initialize the quiz widget with all UI components."""
        super().__init__()

        self._correct_index: int = -1
        self._radio_buttons: List[QRadioButton] = []

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(40, 40, 40, 40)
        main_layout.setSpacing(20)

        self._setup_question_label(main_layout)
        self._setup_options_area(main_layout)
        self._setup_result_label(main_layout)
        self._setup_buttons(main_layout)

    # ------------------------------------------------------------------
    # Setup helpers
    # ------------------------------------------------------------------

    def _setup_question_label(self, parent_layout: QVBoxLayout) -> None:
        """Create the question text label."""
        self._question_label = QLabel()
        self._question_label.setWordWrap(True)
        font = QFont()
        font.setPointSize(15)
        font.setBold(True)
        self._question_label.setFont(font)
        self._question_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        parent_layout.addWidget(self._question_label)

    def _setup_options_area(self, parent_layout: QVBoxLayout) -> None:
        """Create the container and button group for radio buttons."""
        self._button_group = QButtonGroup(self)
        self._button_group.setExclusive(True)

        self._options_layout = QVBoxLayout()
        self._options_layout.setSpacing(10)
        parent_layout.addLayout(self._options_layout)

    def _setup_result_label(self, parent_layout: QVBoxLayout) -> None:
        """Create the result feedback label (hidden initially)."""
        self._result_label = QLabel()
        self._result_label.setWordWrap(True)
        font = QFont()
        font.setPointSize(13)
        font.setBold(True)
        self._result_label.setFont(font)
        self._result_label.hide()
        parent_layout.addWidget(self._result_label)

    def _setup_buttons(self, parent_layout: QVBoxLayout) -> None:
        """Create the Submit and Back buttons."""
        self._submit_button = QPushButton("Ответить")
        self._submit_button.setMinimumHeight(38)
        self._submit_button.clicked.connect(self._on_submit_clicked)

        self._back_button = QPushButton("← Вернуться к теории")
        self._back_button.setMinimumHeight(38)

        button_layout = QHBoxLayout()
        button_layout.addWidget(self._submit_button)
        button_layout.addWidget(self._back_button)
        button_layout.addStretch()

        parent_layout.addLayout(button_layout)
        parent_layout.addStretch()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def load_question(self, question_data: dict) -> None:
        """Load a new question into the widget.

        Clears any previously rendered radio buttons, creates new ones from
        ``question_data['options']``, and hides the result label.

        Args:
            question_data: Dictionary with keys:
                - 'question_text' (str): The question to display.
                - 'options' (list[str]): Answer option strings.
                - 'correct_index' (int): Index of the correct option.
        """
        # Clear previous radio buttons from layout and button group
        for radio in self._radio_buttons:
            self._options_layout.removeWidget(radio)
            self._button_group.removeButton(radio)
            radio.deleteLater()
        self._radio_buttons.clear()

        # Store correct index for later evaluation
        self._correct_index = question_data.get('correct_index', -1)

        # Set question text
        self._question_label.setText(question_data.get('question_text', ''))

        # Create radio buttons for each option
        for idx, option_text in enumerate(question_data.get('options', [])):
            radio = QRadioButton(option_text)
            radio.setStyleSheet("font-size: 13px; padding: 4px 0;")
            self._button_group.addButton(radio, idx)
            self._options_layout.addWidget(radio)
            self._radio_buttons.append(radio)

        # Hide result from any previous question
        self._result_label.hide()
        self._result_label.setText("")

    def check_answer(self, correct_index: int) -> None:
        """Evaluate the selected answer and display feedback.

        Colors the result label green for a correct answer and red for an
        incorrect one.

        Args:
            correct_index: The 0-based index of the correct answer option.
        """
        selected_id = self._button_group.checkedId()

        if selected_id == -1:
            self._result_label.setText("Выберите вариант ответа.")
            self._result_label.setStyleSheet("color: #e0a830;")
            self._result_label.show()
            return

        if selected_id == correct_index:
            self._result_label.setText("✓ Правильно!")
            self._result_label.setStyleSheet("color: #4ec94e;")
        else:
            correct_text = ""
            if 0 <= correct_index < len(self._radio_buttons):
                correct_text = self._radio_buttons[correct_index].text()
            self._result_label.setText(
                f"✗ Неправильно. Правильный ответ: «{correct_text}»"
            )
            self._result_label.setStyleSheet("color: #e05555;")

        self._result_label.show()

    def get_back_button(self) -> QPushButton:
        """Return the back-to-theory button.

        Returns:
            QPushButton: The back button widget.
        """
        return self._back_button

    def get_submit_button(self) -> QPushButton:
        """Return the submit / check answer button.

        Returns:
            QPushButton: The submit button widget.
        """
        return self._submit_button

    # ------------------------------------------------------------------
    # Internal slots
    # ------------------------------------------------------------------

    def _on_submit_clicked(self) -> None:
        """Handle the Submit button click by evaluating the current answer."""
        self.check_answer(self._correct_index)
