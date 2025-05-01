# QSS Parser

![PyPI Version](https://img.shields.io/pypi/v/qss-parser)
![Python Version](https://img.shields.io/pypi/pyversions/qss-parser)
![License](https://img.shields.io/pypi/l/qss-parser)
![Build Status](https://github.com/yourusername/qss-parser/actions/workflows/ci.yml/badge.svg)

**QSS Parser** is a lightweight and robust Python library designed to parse and validate Qt Style Sheets (QSS), the stylesheet language used by Qt applications to customize the appearance of widgets. It enables developers to validate QSS syntax, parse QSS into structured rules, and extract styles for specific Qt widgets based on their object names, class names, or additional selectors. This library is particularly useful for developers working with PyQt or PySide applications who need to manage and apply QSS styles programmatically.

## Table of Contents

- [Features](#features)
- [Installation](#installation)
- [Usage](#usage)
  - [Complete Example](#complete-example)
  - [Basic Example](#basic-example)
  - [Validating QSS Syntax](#validating-qss-syntax)
  - [Parsing QSS and Extracting Styles](#parsing-qss-and-extracting-styles)
  - [Integration with Qt Applications](#integration-with-qt-applications)
- [API Reference](#api-reference)
- [Contributing](#contributing)
- [Testing](#testing)
- [License](#license)
- [Support](#support)
- [Acknowledgements](#acknowledgements)

## Features

- **QSS Validation**: Checks QSS for syntax errors such as missing semicolons, unclosed braces, properties outside blocks, and invalid selectors.
- **Structured Parsing**: Converts QSS into a structured representation with `QSSRule` and `QSSProperty` objects, making it easy to manipulate styles programmatically.
- **Style Extraction**: Retrieves styles for Qt widgets based on their object names, class names, pseudo-states, pseudo-elements, or additional selectors.
- **Flexible Selector Support**: Handles complex selectors, including pseudo-states (e.g., `:hover`), pseudo-elements (e.g., `::handle`), and composite selectors.
- **Lightweight and Dependency-Free**: No external dependencies required, ensuring easy integration into any Python project.
- **Extensible Design**: Built with a modular structure to support future enhancements, such as advanced selector matching or QSS generation.
- **Comprehensive Testing**: Includes a robust test suite to ensure reliability and correctness.

## Installation

To install `qss-parser`, use `pip`:

```bash
pip install qss-parser
```

### Requirements

- Python 3.6 or higher
- No external dependencies are required for core functionality.
- For integration with Qt applications, you may need `PyQt5`, `PyQt6`, or `PySide2`/`PySide6` (not included in the package dependencies).

To install with Qt support (e.g., PyQt5):

```bash
pip install qss-parser PyQt5
```

## Usage

The `qss-parser` library provides a simple and intuitive API for validating, parsing, and applying QSS styles. Below are several examples to demonstrate its capabilities.

### Complete Example
Check complete example [here](https://github.com/OniMock/qss_parser/tree/main/tests)

### Basic Example

This example shows how to validate and parse a QSS string and retrieve styles for a mock widget.

```python
from qss_parser import QSSParser
from unittest.mock import Mock

# Create a mock widget
widget = Mock()
widget.objectName.return_value = "myButton"
widget.metaObject.return_value.className.return_value = "QPushButton"

# Initialize the parser
parser = QSSParser()

# Sample QSS
qss = """
#myButton {
    color: red;
}
QPushButton {
    background: blue;
}
"""

# Validate QSS format
errors = parser.check_format(qss)
if errors:
    print("Invalid QSS format:")
    for error in errors:
        print(error)
else:
    # Parse and retrieve styles
    parser.parse(qss)
    styles = parser.get_styles_for(widget)
    print("Styles for widget:")
    print(styles)
```

**Output**:
```
Styles for widget:
#myButton {
    color: red;
}
```

### Validating QSS Syntax

The `check_format` method validates QSS syntax and returns a list of error messages for any issues found.

```python
from qss_parser import QSSParser

parser = QSSParser()
qss = """
QPushButton {
    color: blue
}
"""

errors = parser.check_format(qss)
for error in errors:
    print(error)
```

**Output**:
```
Error on line 3: Property missing ';': color: blue
```

### Parsing QSS and Extracting Styles

The `parse` method converts QSS into a list of `QSSRule` objects, and `get_styles_for` retrieves styles for a widget with customizable options.

```python
from qss_parser import QSSParser
from unittest.mock import Mock

# Create a mock widget
widget = Mock()
widget.objectName.return_value = "titleLeftApp"
widget.metaObject.return_value.className.return_value = "QWidget"

parser = QSSParser()
qss = """
#titleLeftApp {
    font: 12pt "Segoe UI Semibold";
}
QWidget {
    background: gray;
}
"""

parser.parse(qss)
styles = parser.get_styles_for(
    widget,
    include_class_if_object_name=True,
    fallback_class="QFrame",
    additional_selectors=[".customClass"]
)
print(styles)
```

**Output**:
```
#titleLeftApp {
    font: 12pt "Segoe UI Semibold";
}
QWidget {
    background: gray;
}
```

### Integration with Qt Applications

This example demonstrates how to use `qss-parser` in a real PyQt5 application to apply styles to a widget.

```python
from PyQt5.QtWidgets import QApplication, QPushButton
from qss_parser import QSSParser
import sys

# Initialize the Qt application
app = QApplication(sys.argv)

# Initialize the parser
parser = QSSParser()

# Load QSS from a file
with open("styles.qss", "r", encoding="utf-8") as f:
    qss = f.read()

# Validate QSS
errors = parser.check_format(qss)
if errors:
    print("Invalid QSS format:")
    for error in errors:
        print(error)
    sys.exit(1)

# Parse QSS
parser.parse(qss)

# Create a button
button = QPushButton("Click Me")
button.setObjectName("myButton")

# Apply styles
styles = parser.get_styles_for(button, include_class_if_object_name=True)
button.setStyleSheet(styles)

# Show the button
button.show()

# Run the application
sys.exit(app.exec_())
```

## API Reference

### `QSSParser` Class

The main class for parsing and managing QSS.

- **Methods**:
  - `check_format(qss_text: str) -> List[str]`: Validates QSS syntax and returns a list of error messages.
  - `parse(qss_text: str)`: Parses QSS into a list of `QSSRule` objects.
  - `get_styles_for(widget, fallback_class: Optional[str] = None, additional_selectors: Optional[List[str]] = None, include_class_if_object_name: bool = False) -> str`: Retrieves QSS styles for a widget based on its object name, class name, and optional parameters.
  - `__repr__() -> str`: Returns a string representation of all parsed rules.

### `QSSRule` Class

Represents a QSS rule with a selector and properties.

- **Attributes**:
  - `selector: str`: The rule's selector (e.g., `#myButton`, `QPushButton:hover`).
  - `properties: List[QSSProperty]`: List of properties in the rule.
  - `original: str`: The original QSS text for the rule.

- **Methods**:
  - `add_property(name: str, value: str)`: Adds a property to the rule.
  - `clone_without_pseudo_elements() -> QSSRule`: Creates a copy of the rule without pseudo-elements.

### `QSSProperty` Class

Represents a single QSS property.

- **Attributes**:
  - `name: str`: The property name (e.g., `color`).
  - `value: str`: The property value (e.g., `blue`).

## Contributing

We welcome contributions to `qss-parser`! To contribute:

1. **Fork the Repository**: Fork the [qss-parser repository](https://github.com/OniMock/qss_parser) on GitHub.
2. **Create a Branch**: Create a new branch for your feature or bug fix (`git checkout -b feature/my-feature`).
3. **Make Changes**: Implement your changes and ensure they follow the project's coding style.
4. **Run Tests**: Run the test suite to verify your changes (`python -m unittest discover tests`).
5. **Submit a Pull Request**: Push your branch to your fork and open a pull request with a clear description of your changes.

Please read our [Contributing Guidelines](CONTRIBUTING.md) for more details.

### Code Style

- Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) for Python code style.
- Use type hints where applicable (per [PEP 484](https://www.python.org/dev/peps/pep-0484/)).
- Write clear, concise docstrings for all public methods and classes.

## Testing

The library includes a comprehensive test suite located in the `tests/` directory. To run the tests:

```bash
python -m unittest discover tests
```

To ensure compatibility across Python versions, you can use `tox`:

```bash
pip install tox
tox
```

Please ensure all tests pass before submitting a pull request.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Support

If you encounter issues or have questions, please:

- **Open an Issue**: Report bugs or request features on the [GitHub Issues page](https://github.com/yourusername/qss-parser/issues).
- **Contact the Maintainer**: Reach out to [Your Name](mailto:your.email@example.com) for direct support.

## Acknowledgements

- Thanks to the Qt community for their extensive documentation on QSS.
- Inspired by the need for programmatic QSS handling in PyQt/PySide applications.
- Special thanks to contributors and users who provide feedback and improvements.