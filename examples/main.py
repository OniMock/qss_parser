from PySide6.QtWidgets import QApplication, QMainWindow, QPushButton, QLabel, QVBoxLayout, QWidget
from qss_parser import QSSParser
import sys

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("QSS Parser Example with PySide6")
        self.setGeometry(100, 100, 400, 200)

        # Initialize the QSS parser
        self.parser = QSSParser()

        # Create widgets
        self.button = QPushButton("Click Me")
        self.button.setObjectName("myButton")
        
        self.label = QLabel("Styled Label")
        self.label.setObjectName("myLabel")

        # Set up layout
        layout = QVBoxLayout()
        layout.addWidget(self.button)
        layout.addWidget(self.label)

        # Set up central widget
        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        # Load and apply QSS
        self.apply_styles()

    def apply_styles(self):
        try:
            # Load QSS from file
            with open("styles.qss", "r", encoding="utf-8") as f:
                qss = f.read()

            # Validate QSS
            errors = self.parser.check_format(qss)
            if errors:
                print("Invalid QSS format:")
                for error in errors:
                    print(error)
                return

            # Parse QSS
            self.parser.parse(qss)

            # Apply styles to widgets
            button_styles = self.parser.get_styles_for(self.button, include_class_if_object_name=True)
            self.button.setStyleSheet(button_styles)

            label_styles = self.parser.get_styles_for(self.label, include_class_if_object_name=True)
            self.label.setStyleSheet(label_styles)

            print("Styles applied successfully.")
        except FileNotFoundError:
            print("Error: styles.qss file not found.")
        except Exception as e:
            print(f"Error applying styles: {e}")

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()