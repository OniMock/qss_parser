from PySide6.QtWidgets import (  # type: ignore
    QApplication,
    QMainWindow,
    QPushButton,
    QLabel,
    QVBoxLayout,
    QWidget,
)
from qss_parser import QSSParser, QSSRule, ParserEvent
import sys
from typing import Optional


class MainWindow(QMainWindow):
    """Main window demonstrating the usage of QSSParser with PySide6."""

    def __init__(self) -> None:
        """Initialize the main window and set up the QSS parser and UI."""
        super().__init__()
        self.setWindowTitle("QSS Parser Example with PySide6")
        self.setGeometry(100, 100, 400, 300)

        # Initialize the QSS parser
        self.parser: QSSParser = QSSParser()

        # Register event handlers
        self.parser.on(ParserEvent.RULE_ADDED, self.on_rule_added)
        self.parser.on(ParserEvent.ERROR_FOUND, self.on_error_found)

        # Create widgets
        self.button: QPushButton = QPushButton("Click Me")
        self.button.setObjectName("myButton")
        self.button.setProperty("data-value", "complex string with spaces")

        self.label: QLabel = QLabel("Styled Label")
        self.label.setObjectName("myLabel")

        self.custom_widget: QWidget = QWidget()
        self.custom_widget.setObjectName("customWidget")
        self.custom_widget.setProperty("theme", "dark")

        # Set up layout
        layout: QVBoxLayout = QVBoxLayout()
        layout.addWidget(self.button)
        layout.addWidget(self.label)
        layout.addWidget(self.custom_widget)

        # Set up central widget
        container: QWidget = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        # Load and apply QSS
        self.qss: Optional[str] = None
        self.apply_styles()

    def on_rule_added(self, rule: QSSRule) -> None:
        """
        Callback for when a new rule is added during QSS parsing.

        Args:
            rule (QSSRule): The parsed QSS rule.
        """
        print(f"New rule parsed: {rule.selector}")

    def on_error_found(self, error: str) -> None:
        """
        Callback for when a parsing error is encountered.

        Args:
            error (str): The error message.
        """
        print(f"QSS error: {error}")

    def apply_styles(self) -> None:
        """
        Load QSS from a file and apply styles to the widgets.

        This method reads a QSS file, parses it using QSSParser, and applies
        the parsed styles to the button, label, and custom widget.
        """
        try:
            # Load QSS from file
            with open("styles.qss", "r", encoding="utf-8") as f:
                self.qss = f.read()

            # Parse QSS
            self.parser.parse(self.qss)

            # Apply styles to widgets
            button_styles: str = self.parser.get_styles_for(
                self.button,
                fallback_class="QFrame",
                include_class_if_object_name=True,
                additional_selectors=[".customClass"],
            )
            self.button.setStyleSheet(button_styles)
            print(f"Button styles applied:\n{button_styles}")

            label_styles: str = self.parser.get_styles_for(
                self.label, include_class_if_object_name=True
            )
            self.label.setStyleSheet(label_styles)
            print(f"Label styles applied:\n{label_styles}")

            custom_widget_styles: str = self.parser.get_styles_for(
                self.custom_widget,
                fallback_class="QWidget",
                additional_selectors=['[theme="dark"]'],
            )
            self.custom_widget.setStyleSheet(custom_widget_styles)
            print(f"Custom widget styles applied:\n{custom_widget_styles}")

            print("All styles applied successfully.")
        except FileNotFoundError:
            print("Error: styles.qss file not found.")
        except Exception as e:
            print(f"Error applying styles: {str(e)}")


def main() -> None:
    """Create and run the PySide6 application."""
    app: QApplication = QApplication(sys.argv)
    window: MainWindow = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
