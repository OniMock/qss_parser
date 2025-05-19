# QSS Parser

![PyPI Version](https://img.shields.io/pypi/v/qss-parser)
![Python Version](https://img.shields.io/pypi/pyversions/qss-parser)
![License](https://img.shields.io/pypi/l/qss-parser)
![Build Status](https://github.com/OniMock/qss_parser/actions/workflows/ci.yml/badge.svg)
![Last Commit](https://img.shields.io/github/last-commit/OniMock/qss_parser)
![Downloads](https://img.shields.io/pypi/dm/qss-parser)
![Wheel](https://img.shields.io/pypi/wheel/qss-parser)
![Open Issues](https://img.shields.io/github/issues/OniMock/qss_parser)
[![codecov](https://codecov.io/gh/OniMock/qss_parser/graph/badge.svg?token=BOYP3Y65CE)](https://codecov.io/gh/OniMock/qss_parser)
[![Documentation Status](https://readthedocs.org/projects/qss-parser/badge/?version=latest)](https://qss-parser.readthedocs.io/en/latest/?badge=latest)

<p align="center">
  <img src="https://raw.githubusercontent.com/OniMock/.github/refs/heads/main/.resources/qss-parser.jpg" width="500" />
</p>
**QSS Parser** is a lightweight, robust, and dependency-free Python library for parsing and validating Qt Style Sheets (QSS), the stylesheet language used to customize the appearance of Qt widgets. It enables developers to validate QSS syntax, parse styles into structured objects, and extract styles for specific Qt widgets based on object names, class names, attribute selectors, pseudo-states, and pseudo-elements. Ideal for PyQt or PySide applications, this library simplifies programmatic management of QSS styles.

## Table of Contents

- [Features](#features)
- [Installation](#installation)
- [Usage](#usage)
  - [Complete Example](#complete-example)
  - [Basic Parsing and Style Extraction](#basic-parsing-and-style-extraction)
  - [Handling Parser Events](#handling-parser-events)
  - [Validating QSS Syntax](#validating-qss-syntax)
  - [Parsing QSS with Attribute Selectors and Pseudo-States](#parsing-qss-with-attribute-selectors-and-pseudo-states)
  - [Parsing QSS with Variables](#parsing-qss-with-variables)
  - [Integration with Qt Applications](#integration-with-qt-applications)
- [API Reference](#api-reference)
- [Contributing](#contributing)
- [Testing](#testing)
- [License](#license)
- [Support](#support)
- [Donate](#donate)
- [Acknowledgements](#acknowledgements)

## Features

- **Comprehensive QSS Validation**: Detects syntax errors including missing semicolons, unclosed braces, properties outside blocks, invalid selectors, and unsupported pseudo-states or pseudo-elements.
- **Variable Support**: Parses `@variables` blocks, resolves variable references (e.g., `var(--primary-color)`), and handles nested variables with circular reference detection.
- **Structured Parsing**: Converts QSS into `QSSRule` and `QSSProperty` objects for easy programmatic manipulation of selectors and properties.
- **Style Extraction**: Retrieves styles for Qt widgets based on object names, class names, attribute selectors (e.g., `[data-value="complex string"]`), pseudo-states (e.g., `:hover`), and pseudo-elements (e.g., `::handle`).
- **Advanced Selector Handling**: Supports complex selectors, including attribute selectors with spaces or special characters, composite selectors (e.g., `QPushButton#myButton`), and duplicate selector filtering with error reporting.
- **Pseudo-State and Pseudo-Element Validation**: Ensures pseudo-states (e.g., `:hover`, `:focus`) and pseudo-elements (e.g., `::tab`, `::indicator`) conform to Qt's supported list, with detailed error messages.
- **Lightweight and Dependency-Free**: Requires no external dependencies, ensuring seamless integration into any Python project.
- **Plugin-Based Architecture**: Extensible design with plugins for selectors, properties, and variables, enabling custom parsing logic.
- **Robust Testing**: Includes a comprehensive test suite covering validation, parsing, style extraction, variable resolution, and edge cases like duplicate selectors.

## Installation

Install `qss-parser` using `pip`:

```bash
pip install qss-parser
```

### Requirements

- Python 3.6 or higher
- No external dependencies for core functionality.
- For Qt integration, install `PyQt5`, `PyQt6`, `PySide2`, or `PySide6` (not included in package dependencies).

To install with Qt support (e.g., PyQt5):

```bash
pip install qss-parser PyQt5
```

## Usage

The `qss-parser` library offers an intuitive API for validating, parsing, and applying QSS styles. Below are examples showcasing its capabilities, focusing on the `parse()`, `on()`, `to_string()`, and `get_styles_for()` methods.

### Complete Example

Explore a complete example in the [examples directory](https://github.com/OniMock/qss_parser/tree/main/examples).

### Basic Parsing and Style Extraction

Parse a QSS string, extract styles for a widget, and convert parsed rules to a formatted string.

```python
from qss_parser import QSSParser, ParserEvent
from unittest.mock import Mock

# Mock widget setup
widget = Mock()
widget.objectName.return_value = "myButton"
widget.metaObject.return_value.className.return_value = "QPushButton"

# Initialize parser
parser = QSSParser()

# Sample QSS
qss = """
#myButton {
    color: red;
}
QPushButton {
    background: blue;
}
QPushButton:hover {
    background: yellow;
}
"""

# Parse QSS
parser.parse(qss)

# Get styles for widget
styles = parser.get_styles_for(widget, include_class_if_object_name=True)
print("Styles for widget:")
print(styles)

# Convert parsed rules to string
formatted_qss = parser.to_string()
print("\nFormatted QSS:")
print(formatted_qss)
```

**Output**:

```
Styles for widget:
#myButton {
    color: red;
}
QPushButton {
    background: blue;
}
QPushButton:hover {
    background: yellow;
}

Formatted QSS:
#myButton {
    color: red;
}
QPushButton {
    background: blue;
}
QPushButton:hover {
    background: yellow;
}
```

### Handling Parser Events

Use the `on()` method to subscribe to parser events (`rule_added`, `error_found`, `variable_defined`, `parse_completed`).

```python
from qss_parser import QSSParser, ParserEvent
from unittest.mock import Mock

# Mock widget
widget = Mock()
widget.objectName.return_value = "myButton"
widget.metaObject.return_value.className.return_value = "QPushButton"

# Initialize parser
parser = QSSParser()

# Define event handlers
def on_rule_added(rule):
    print(f"Rule added: {rule.selector}")

def on_error_found(error):
    print(f"Error: {error}")

def on_variable_defined(name, value):
    print(f"Variable defined: {name} = {value}")

def on_parse_completed():
    print("Parsing completed")

# Register event handlers
parser.on(ParserEvent.RULE_ADDED, on_rule_added)
parser.on(ParserEvent.ERROR_FOUND, on_error_found)
parser.on(ParserEvent.VARIABLE_DEFINED, on_variable_defined)
parser.on(ParserEvent.PARSE_COMPLETED, on_parse_completed)

# Sample QSS with variables and an error
qss = """
@variables {
    --primary-color: blue;
}
#myButton {
    color: var(--primary-color);
}
QPushButton {
    background: green
}
"""

# Parse QSS
parser.parse(qss)

# Get styles for widget
styles = parser.get_styles_for(widget)
print("\nStyles for widget:")
print(styles)
```

**Output**:

```
Variable defined: --primary-color = blue
Rule added: #myButton
Rule added: QPushButton
Error: Error on line 8: Property missing ';': background: green
Parsing completed

Styles for widget:
#myButton {
    color: blue;
}
```

### Validating QSS Syntax

Use parses.on with error event to validate QSS syntax and report errors.

```python
from qss_parser import QSSParser, ParserEvent

# Initialize parser
parser = QSSParser()

# Register error handler
def on_error_found(error):
    print(f"Error: {error}")
parser.on(ParserEvent.ERROR_FOUND, on_error_found)

# Sample QSS with syntax error
qss = """
QPushButton {
    color: blue
}
QFrame {
    font-size: 12px;
    color: blue
}
QFrame {
    font-size: 12px
    color: blue
}
"""

# Validate QSS
parser.parse(qss)

# Convert parsed rules to string (only valid rules)
formatted_qss = parser.to_string()
print("\nFormatted QSS (valid rules):")
print(formatted_qss)
```

**Output**:

```
Error: Error on line 10: Property missing ';': font-size: 12px
Parsing completed

Formatted QSS (valid rules):
QPushButton {
    color: blue;
}

QFrame {
    font-size: 12px;
    color: blue;
}
```

### Parsing QSS with Attribute Selectors and Pseudo-States

Parse QSS with complex attribute selectors, pseudo-states, and pseudo-elements, and extract styles for a widget.

```python
from qss_parser import QSSParser, ParserEvent
from unittest.mock import Mock

# Mock widget
widget = Mock()
widget.objectName.return_value = "myButton"
widget.metaObject.return_value.className.return_value = "QPushButton"

# Initialize parser
parser = QSSParser()

# Register parse completion handler
def on_parse_completed():
    print("Parsing completed")
parser.on(ParserEvent.PARSE_COMPLETED, on_parse_completed)

# Sample QSS
qss = """
QPushButton[data-value="complex string"] {
    color: blue;
}
QPushButton:hover {
    background: yellow;
}
QPushButton::indicator {
    border: 2px solid gray;
}
#myButton QPushButton {
    font-weight: bold;
}
"""

# Parse QSS
parser.parse(qss)

# Get styles with additional selectors
styles = parser.get_styles_for(
    widget,
    additional_selectors=["QPushButton"],
    include_class_if_object_name=True
)
print("Styles for widget:")
print(styles)

# Convert parsed rules to string
formatted_qss = parser.to_string()
print("\nFormatted QSS:")
print(formatted_qss)
```

**Output**:

```
Parsing completed
Styles for widget:
#myButton QPushButton {
    font-weight: bold;
}
QPushButton[data-value="complex string"] {
    color: blue;
}
QPushButton:hover {
    background: yellow;
}
QPushButton::indicator {
    border: 2px solid gray;
}

Formatted QSS:
QPushButton[data-value="complex string"] {
    color: blue;
}
QPushButton:hover {
    background: yellow;
}
QPushButton::indicator {
    border: 2px solid gray;
}
#myButton QPushButton {
    font-weight: bold;
}
```

### Parsing QSS with Variables

Parse QSS with a `@variables` block, resolve nested variables, and extract styles.

```python
from qss_parser import QSSParser, ParserEvent
from unittest.mock import Mock

# Mock widget
widget = Mock()
widget.objectName.return_value = "myButton"
widget.metaObject.return_value.className.return_value = "QPushButton"

# Initialize parser
parser = QSSParser()

# Register variable defined handler
def on_variable_defined(name, value):
    print(f"Variable defined: {name} = {value}")
parser.on(ParserEvent.VARIABLE_DEFINED, on_variable_defined)

# Sample QSS
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
QPushButton:hover {
    background: yellow;
}
"""

# Parse QSS
parser.parse(qss)

# Get styles for widget
styles = parser.get_styles_for(widget, include_class_if_object_name=True)
print("\nStyles for widget:")
print(styles)

# Convert parsed rules to string
formatted_qss = parser.to_string()
print("\nFormatted QSS:")
print(formatted_qss)
```

**Output**:

```
Variable defined: --base-color = #0000ff
Variable defined: --primary-color = #0000ff
Variable defined: --font-size = 14px

Styles for widget:
#myButton {
    color: #0000ff;
    font-size: 14px;
    background: white;
}
QPushButton:hover {
    background: yellow;
}

Formatted QSS:
#myButton {
    color: #0000ff;
    font-size: 14px;
    background: white;
}
QPushButton:hover {
    background: yellow;
}
```

### Integration with Qt Applications

Apply parsed QSS styles to a PyQt5 widget, using event handlers for debugging.

```python
from PyQt5.QtWidgets import QApplication, QPushButton
from qss_parser import QSSParser, ParserEvent
import sys

# Initialize Qt application
app = QApplication(sys.argv)

# Initialize parser
parser = QSSParser()

# Register event handlers
def on_error_found(error):
    print(f"Error: {error}")
def on_parse_completed():
    print("Parsing completed")
parser.on(ParserEvent.ERROR_FOUND, on_error_found)
parser.on(ParserEvent.PARSE_COMPLETED, on_parse_completed)

# Load QSS from file
with open("styles.qss", "r", encoding="utf-8") as f:
    qss = f.read()

# Parse QSS
parser.parse(qss)

# Create button
button = QPushButton("Click Me")
button.setObjectName("myButton")

# Apply styles
styles = parser.get_styles_for(button, include_class_if_object_name=True)
button.setStyleSheet(styles)

# Print formatted QSS
formatted_qss = parser.to_string()
print("Formatted QSS:")
print(formatted_qss)

# Show button
button.show()

# Run application
sys.exit(app.exec_())
```

**Example `styles.qss`**:

```qss
QPushButton {
    background: blue;
}
#myButton {
    color: red;
}
QPushButton:hover {
    background: yellow;
}
```

**Output**:

```
Parsing completed
Formatted QSS:
QPushButton {
    background: blue;
}
#myButton {
    color: red;
}
QPushButton:hover {
    background: yellow;
}
```

## API Reference

### `QSSParser` Class

Main class for parsing and managing QSS.

- **Methods**:
  - `parse(qss_text: str) -> None`: Parses QSS into `QSSRule` objects.
  - `get_styles_for(widget: WidgetProtocol, fallback_class: Optional[str] = None, additional_selectors: Optional[List[str]] = None, include_class_if_object_name: bool = False) -> str`: Retrieves QSS styles for a widget.
  - `on(event: ParserEvent, handler: Callable[..., None]) -> None`: Registers handlers for events (`rule_added`, `error_found`, `variable_defined`, `parse_completed`).
  - `to_string() -> str`: Returns formatted QSS for all parsed rules.

### `QSSRule` Class

Represents a QSS rule with selector and properties.

- **Attributes**:

  - `selector: str`: Selector (e.g., `#myButton`, `QPushButton[data-value="value"]`).
  - `properties: List[QSSProperty]`: List of properties.
  - `object_name: Optional[str]`: Object name (e.g., `myButton` for `#myButton`).
  - `class_name: Optional[str]`: Class name (e.g., `QPushButton`).
  - `attributes: List[str]`: Attribute selectors (e.g., `[data-value="value"]`).
  - `pseudo_states: List[str]`: Pseudo-states (e.g., `:hover`).

- **Methods**:
  - `add_property(name: str, value: str) -> None`: Adds a property.
  - `clone_without_pseudo_elements() -> QSSRule`: Returns a copy without pseudo-elements.

### `QSSProperty` Class

Represents a QSS property.

- **Attributes**:

  - `name: str`: Property name (e.g., `color`).
  - `value: str`: Property value (e.g., `blue`).

- **Methods**:
  - `to_dict() -> QSSPropertyDict`: Converts to dictionary.

### `SelectorUtils` Class

Utility for selector parsing and validation.

- **Static Methods**:
  - `is_complete_rule(line: str) -> bool`: Checks if a line is a complete rule.
  - `extract_attributes(selector: str) -> List[str]`: Extracts attribute selectors.
  - `normalize_selector(selector: str) -> str`: Normalizes selector formatting.
  - `parse_selector(selector: str) -> Tuple[Optional[str], Optional[str], List[str], List[str]]`: Parses selector components.
  - `validate_selector_syntax(selector: str, line_num: int) -> List[str]`: Validates selector syntax.

### `VariableManager` Class

Manages QSS variables.

- **Methods**:
  - `parse_variables(block: str, start_line: int = 1, on_variable_defined: Optional[Callable[[str, str], None]] = None) -> List[str]`: Parses variable block.
  - `resolve_variable(value: str) -> Tuple[str, Optional[str]]`: Resolves variable references.

### `QSSStyleSelector` Class

Selects styles for widgets.

- **Methods**:
  - `get_styles_for(rules: List[QSSRule], widget: WidgetProtocol, ...) -> str`: Retrieves styles for a widget.

### `QSSParserPlugin` and Derived Plugins

- `QSSParserPlugin`: Abstract base class for plugins.
- `SelectorPlugin`: Handles selectors and rules, including duplicate selector filtering.
- `PropertyPlugin`: Processes property declarations.
- `VariablePlugin`: Manages `@variables` blocks.

## Contributing

Contributions are welcome! To contribute:

1. Fork the [repository](https://github.com/OniMock/qss_parser).
2. Create a branch (`git checkout -b feature/my-feature`).
3. Implement changes, adhering to the coding style.
4. Run tests (`python -m unittest discover tests`).
5. Submit a pull request with a clear description.

See [CONTRIBUTING.md](CONTRIBUTING.md) for details.

### Code Style

- Adhere to [PEP 8](https://www.python.org/dev/peps/pep-0008/).
- Use type hints per [PEP 484](https://www.python.org/dev/peps/pep-484/).
- Provide clear, concise docstrings for public methods and classes.

## Testing

The test suite in `tests/` covers validation, parsing, style extraction, and variable resolution. Run tests with:

```bash
python -m unittest discover tests
```

For multi-version testing, use `tox`:

```bash
pip install tox
tox
```

Ensure all tests pass before submitting pull requests.

## License

Licensed under the MIT License. See [LICENSE](LICENSE) for details.

## Support

For issues or questions:

- Open an issue on [GitHub](https://github.com/OniMock/qss_parser/issues).
- Contact [Onimock](mailto:onimock@gmail.com).

## Donate

🌟 **Support QSS Parser with a Donation!** 🌟

If you find QSS Parser helpful and want to support its development, consider making a donation via Web3 wallets. Your contributions help maintain and improve this open-source project! 🙏

<p align="center">
<img src="https://raw.githubusercontent.com/OniMock/.github/refs/heads/main/.resources/crypto_wallet.svg" width="150" />
</p>

| Blockchain                                                                                                                                                      | Address                                                          | QR Code                                                                                                                    |
| --------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------- |
| <img src="https://raw.githubusercontent.com/OniMock/.github/refs/heads/main/.resources/svg/eth_logo.svg" width="30" align="center"> EVM (ETH, BSC, RON, POL...) | `0xD42f8604634d3882b3CeCB4408c10ae745182dEF`                     | <img src="https://raw.githubusercontent.com/OniMock/.github/refs/heads/main/.resources/qrcode/qrcode_evm.jpg" width="120"> |
| <img src="https://raw.githubusercontent.com/OniMock/.github/refs/heads/main/.resources/svg/sol_logo.svg" width="30" align="center"> Solana (SOL)                | `3fFV5c3pnp9zG81Q3wNsteCPN4zJkpBd3Gm5X2iQ6MK8`                   | <img src="https://raw.githubusercontent.com/OniMock/.github/refs/heads/main/.resources/qrcode/qrcode_sol.jpg" width="120"> |
| <img src="https://raw.githubusercontent.com/OniMock/.github/refs/heads/main/.resources/svg/btc_logo.svg" width="30" align="center"> Bitcoin (BTC)               | `bc1pde34mu568t8sqph708huu7z5p4ecgxv7g90vv0wq72spxrlzuz9s3ge2h5` | <img src="https://raw.githubusercontent.com/OniMock/.github/refs/heads/main/.resources/qrcode/qrcode_btc.jpg" width="120"> |

**How to Donate**:

1. Copy the wallet address for your preferred blockchain.
2. Send your donation using a Web3 wallet (e.g., MetaMask, Trust Wallet).
3. Include a note with your GitHub username (optional) for a shoutout in our Acknowledgements!

⚠️ **Important**: Always verify wallet addresses before sending funds. We are not responsible for transactions sent to incorrect addresses.

Thank you for supporting QSS Parser! 💖

## Acknowledgements

- Gratitude to the Qt community for QSS documentation.
- Inspired by the need for programmatic QSS handling in PyQt/PySide.
- Thanks to contributors and users for feedback and enhancements.
