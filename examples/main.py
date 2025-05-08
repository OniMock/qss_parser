from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QPushButton,
    QLabel,
    QVBoxLayout,
    QWidget,
)
from qss_parser import QSSParser, QSSRule
import sys


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("QSS Parser Example with PySide6")
        self.setGeometry(100, 100, 400, 300)

        # Initialize the QSS parser
        self.parser = QSSParser()

        # Register event handlers
        self.parser.on("rule_added", self.on_rule_added)
        self.parser.on("error_found", self.on_error_found)

        # Create widgets
        self.button = QPushButton("Click Me")
        self.button.setObjectName("myButton")
        self.button.setProperty("data-value", "complex string with spaces")

        self.label = QLabel("Styled Label")
        self.label.setObjectName("myLabel")

        self.custom_widget = QWidget()
        self.custom_widget.setObjectName("customWidget")
        self.custom_widget.setProperty("theme", "dark")

        # Set up layout
        layout = QVBoxLayout()
        layout.addWidget(self.button)
        layout.addWidget(self.label)
        layout.addWidget(self.custom_widget)

        # Set up central widget
        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        # Load and apply QSS
        self.qss = None
        self.apply_styles()

    def on_rule_added(self, rule: QSSRule) -> None:
        """
        Callback for when a new rule is added during parsing.
        """
        print(f"New rule parsed: {rule.selector}")

    def on_error_found(self, error: str) -> None:
        """
        Callback for when a parsing error is found.
        """
        print(f"QSS error: {error}")

    def apply_styles(self):
        try:
            # Load QSS from file
            with open("styles.qss", "r", encoding="utf-8") as f:
                self.qss = f.read()

            errors = self.parser.check_format(self.qss)
            if errors:
                print("Invalid QSS format detected:")
                for error in errors:
                    print(error)
                return

            # Parse QSS
            self.parser.parse(self.qss)

            # Apply styles to widgets
            button_styles = self.parser.get_styles_for(
                self.button,
                fallback_class="QFrame",
                include_class_if_object_name=True,
                additional_selectors=[".customClass"],
            )
            self.button.setStyleSheet(button_styles)
            print(f"Button styles applied:\n{button_styles}")

            label_styles = self.parser.get_styles_for(
                self.label, include_class_if_object_name=True
            )
            self.label.setStyleSheet(label_styles)
            print(f"Label styles applied:\n{label_styles}")

            custom_widget_styles = self.parser.get_styles_for(
                self.custom_widget,
                fallback_class="QWidget",
                additional_selectors=['[theme="dark"]'],
            )
            self.custom_widget.setStyleSheet(custom_widget_styles)
            print(f"Custom widget styles applied:\n{custom_widget_styles}")

            print("All styles applied successfully.")
        except Exception as e:
            print(f"Error applying styles: {e}")


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
