# QSS Parser

![PyPI Version](https://img.shields.io/pypi/v/qss-parser)
![Python Version](https://img.shields.io/pypi/pyversions/qss-parser)
![License](https://img.shields.io/pypi/l/qss-parser)
![Build Status](https://github.com/OniMock/qss_parser/actions/workflows/ci.yml/badge.svg)

**QSS Parser** is a lightweight and robust Python library designed to parse and validate Qt Style Sheets (QSS), the stylesheet language used by Qt applications to customize the appearance of widgets. It enables developers to validate QSS syntax, parse QSS into structured rules, and extract styles for specific Qt widgets based on their object names, class names, attributes, or additional selectors. This library is particularly useful for developers working with PyQt or PySide applications who need to manage and apply QSS styles programmatically.

## Table of Contents

- [Features](#features)
- [Installation](#installation)
- [Usage](#usage)
  - [Complete Example](#complete-example)
  - [Basic Example](#basic-example)
  - [Validating QSS Syntax](#validating-qss-syntax)
  - [Parsing QSS with Attribute Selectors](#parsing-qss-with-attribute-selectors)
  - [Parsing QSS with Variables](#parsing-qss-with-variables)
  - [Integration with Qt Applications](#integration-with-qt-applications)
- [API Reference](#api-reference)
- [Contributing](#contributing)
- [Testing](#testing)
- [License](#license)
- [Support](#support)
- [Acknowledgements](#acknowledgements)

## Features

- **QSS Validation**: Checks QSS for syntax errors such as missing semicolons, unclosed braces, properties outside blocks, and invalid selectors.
- **Variable Support**: Parses `@variables` blocks, resolves variable references (e.g., `var(--primary-color)`), and supports nested variables for flexible style definitions.
- **Structured Parsing**: Converts QSS into a structured representation with `QSSRule` and `QSSProperty` objects, making it easy to manipulate styles programmatically.
- **Style Extraction**: Retrieves styles for Qt widgets based on their object names, class names, attribute selectors (e.g., `[data-value="complex string"]`), pseudo-states (e.g., `:hover`), or pseudo-elements (e.g., `::handle`).
- **Advanced Selector Support**: Handles complex selectors, including attribute selectors with spaces or special characters, composite selectors (e.g., `QPushButton #myButton`), and normalized selector processing to ensure consistent parsing.
- **Lightweight and Dependency-Free**: No external dependencies required, ensuring easy integration into any Python project.
- **Extensible Design**: Built with a plugin-based architecture to support custom parsing logic and future enhancements.
- **Comprehensive Testing**: Includes a robust test suite covering validation, parsing, style extraction, and variable resolution, ensuring reliability and correctness.

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

Check the complete example [here](https://github.com/OniMock/qss_parser/tree/main/examples).

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

### Parsing QSS with Attribute Selectors

This example demonstrates parsing QSS with complex attribute selectors and extracting styles for a widget.

```python
from qss_parser import QSSParser
from unittest.mock import Mock

# Create a mock widget
widget = Mock()
widget.objectName.return_value = "myButton"
widget.metaObject.return_value.className.return_value = "QPushButton"

parser = QSSParser()
qss = """
QPushButton[data-value="complex string with spaces"] {
    color: blue;
}
"""

parser.parse(qss)
styles = parser.get_styles_for(widget)
print("Styles for widget:")
print(styles)
```

**Output**:

```
Styles for widget:
QPushButton[data-value="complex string with spaces"] {
    color: blue;
}
```

### Parsing QSS with Variables

This example demonstrates parsing QSS with a `@variables` block, including nested variables, and extracting styles for a widget.

```python
from qss_parser import QSSParser
from unittest.mock import Mock

# Create a mock widget
widget = Mock()
widget.objectName.return_value = "myButton"
widget.metaObject.return_value.className.return_value = "QPushButton"

parser = QSSParser()
qss = """
@variables {
    --base-color: #0000ff;
    --primary-color: var(--base-color);
    --font-size: 14px;
}
#myButton {
    color: var(--primary-color);
    font-size: var(--font-size);
    background: white;
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
    color: #0000ff;
    font-size: 14px;
    background: white;
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
  - `get_styles_for(widget, fallback_class: Optional[str] = None, additional_selectors: Optional[List[str]] = None, include_class_if_object_name: bool = False) -> str`: Retrieves QSS styles for a widget based on its object name, class name, attribute selectors, and optional parameters.
  - `on(event: str, handler: Callable[[Any], None])`: Registers an event handler for parser events (`rule_added`, `error_found`).
  - `__repr__() -> str`: Returns a string representation of all parsed rules.

### `QSSRule` Class

Represents a QSS rule with a selector and properties.

- **Attributes**:

  - `selector: str`: The rule's selector (e.g., `#myButton`, `QPushButton[data-value="value"]`).
  - `properties: List[QSSProperty]`: List of properties in the rule.
  - `original: str`: The original QSS text for the rule.
  - `attributes: List[str]`: List of attribute selectors (e.g., `[data-value="complex string"]`).
  - `pseudo_states: List[str]`: List of pseudo-states (e.g., `hover`, `focus`).
  - `object_name: Optional[str]`: The object name if present (e.g., `myButton` for `#myButton`).
  - `class_name: Optional[str]`: The class name if present (e.g., `QPushButton`).

- **Methods**:
  - `add_property(name: str, value: str)`: Adds a property to the rule.
  - `clone_without_pseudo_elements() -> QSSRule`: Creates a copy of the rule without pseudo-elements or pseudo-states.

### `QSSProperty` Class

Represents a single QSS property.

- **Attributes**:

  - `name: str`: The property name (e.g., `color`).
  - `value: str`: The property value (e.g., `blue`).

- **Methods**:
  - `to_dict() -> QSSPropertyDict`: Converts the property to a dictionary.

### `QSSValidator` Class

Validates QSS syntax.

- **Methods**:
  - `check_format(qss_text: str) -> List[str]`: Validates QSS syntax and returns a list of error messages.

### `QSSStyleSelector` Class

Selects and formats QSS styles for widgets.

- **Methods**:
  - `get_styles_for(rules: List[QSSRule], widget, ...)`: Retrieves styles for a widget from a list of rules.

### `QSSParserPlugin` and `DefaultQSSParserPlugin`

- `QSSParserPlugin`: Abstract base class for parser plugins.
- `DefaultQSSParserPlugin`: Default plugin for parsing QSS, handling selectors and properties with advanced normalization for attribute selectors.

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
- Use type hints where applicable (per [PEP 484](https://www.python.org/dev/peps/pep-484/)).
- Write clear, concise docstrings for all public methods and classes.

## Testing

The library includes a comprehensive test suite located in the `tests/` directory, covering validation, parsing, style extraction, and variable resolution. To run the tests:

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

- **Open an Issue**: Report bugs or request features on the [GitHub Issues page](https://github.com/OniMock/qss_parser/issues).
- **Contact the Maintainer**: Reach out to [Onimock](mailto:onimock@gmail.com) for direct support.

## Acknowledgements

- Thanks to the Qt community for their extensive documentation on QSS.
- Inspired by the need for programmatic QSS handling in PyQt/PySide applications.
- Special thanks to contributors and users who provide feedback and improvements.
