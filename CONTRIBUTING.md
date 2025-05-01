# Contributing to QSS Parser

Thank you for considering contributing to **QSS Parser**! We welcome contributions from the community to improve this lightweight Python library for parsing and validating Qt Style Sheets (QSS). Whether you're fixing bugs, adding features, improving documentation, or writing tests, your efforts help make this project better for everyone.

This document outlines the process for contributing to the project, including how to set up your development environment, submit issues, and create pull requests.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [How Can I Contribute?](#how-can-i-contribute)
  - [Reporting Bugs](#reporting-bugs)
  - [Suggesting Features](#suggesting-features)
  - [Contributing Code](#contributing-code)
- [Development Setup](#development-setup)
- [Coding Guidelines](#coding-guidelines)
- [Submitting a Pull Request](#submitting-a-pull-request)
- [Testing](#testing)
- [Documentation](#documentation)
- [Contact](#contact)

## Code of Conduct

By participating in this project, you agree to abide by our [Code of Conduct](CODE_OF_CONDUCT.md). We are committed to fostering an inclusive and respectful community. Please ensure all interactions are professional and constructive.

## How Can I Contribute?

There are several ways to contribute to QSS Parser:

### Reporting Bugs

If you encounter a bug, please open an issue on the [GitHub Issues page](https://github.com/OniMock/qss_parser/issues). To help us address the issue effectively, include:

- A clear title and description of the bug.
- Steps to reproduce the issue.
- Expected and actual behavior.
- Your environment (e.g., Python version, PySide6/PyQt5 version, operating system).
- Any relevant logs or screenshots.

Use the "Bug Report" issue template if available.

### Suggesting Features

We welcome ideas for new features or enhancements! To propose a feature:

- Open an issue on the [GitHub Issues page](https://github.com/OniMock/qss_parser/issues).
- Use the "Feature Request" issue template if available.
- Provide a clear description of the feature, its use case, and potential benefits.
- Include examples or mockups if applicable.

### Contributing Code

You can contribute code by fixing bugs, implementing features, or improving existing functionality. Follow the steps below to get started.

## Development Setup

To set up a development environment for QSS Parser:

1. **Fork the Repository**:
   - Fork the [qss-parser repository](https://github.com/OniMock/qss_parser) on GitHub.

2. **Clone Your Fork**:
   ```bash
   git clone https://github.com/OniMock/qss_parser.git
   cd qss-parser
   ```

3. **Create a Virtual Environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

4. **Install Dependencies**:
   ```bash
   pip install -r requirements-dev.txt
   ```
   If `requirements-dev.txt` doesn’t exist, install the following:
   ```bash
   pip install pytest PySide6
   ```

5. **Install the Project in Editable Mode**:
   ```bash
   pip install -e .
   ```

6. **Verify Setup**:
   Run the test suite to ensure everything is set up correctly:
   ```bash
   python -m unittest discover tests
   ```

## Coding Guidelines

To ensure consistency and quality, please adhere to the following guidelines:

- **Code Style**:
  - Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) for Python code style.
  - Use 4 spaces for indentation.
  - Keep line length under 88 characters where possible.

- **Type Hints**:
  - Use type hints as per [PEP 484](https://www.python.org/dev/peps/pep-484/) for public methods and classes.
  - Example: `def check_format(qss_text: str) -> List[str]:`

- **Docstrings**:
  - Write clear, concise docstrings for all public classes, methods, and functions using the Google Python Style Guide.
  - Example:
    ```python
    def check_format(qss_text: str) -> List[str]:
        """Validate the format of QSS text.

        Args:
            qss_text: The QSS text to validate.

        Returns:
            A list of error messages, empty if the format is valid.
        """
    ```

- **Commit Messages**:
  - Write clear, descriptive commit messages.
  - Use the present tense (e.g., "Add support for pseudo-elements" instead of "Added").
  - Reference related issues (e.g., "Fix #123: Handle missing semicolons").

- **Modularity**:
  - Keep changes focused and avoid unrelated modifications in a single pull request.
  - Ensure new code is backward-compatible unless explicitly agreed upon.

## Submitting a Pull Request

To submit a pull request (PR):

1. **Create a Branch**:
   - Create a new branch for your changes:
     ```bash
     git checkout -b feature/my-feature
     ```
   - Use descriptive branch names (e.g., `fix/bug-123`, `feature/pseudo-element-support`).

2. **Make Changes**:
   - Implement your changes, following the [Coding Guidelines](#coding-guidelines).
   - Update tests in the `tests/` directory to cover your changes.

3. **Run Tests**:
   - Ensure all tests pass:
     ```bash
     python -m unittest discover tests
     ```

4. **Commit Changes**:
   - Commit your changes with a clear message:
     ```bash
     git commit -m "Add support for composite selectors (#456)"
     ```

5. **Push to Your Fork**:
   ```bash
   git push origin feature/my-feature
   ```

6. **Open a Pull Request**:
   - Go to the [qss_parser repository](https://github.com/OniMock/qss_parser) on GitHub.
   - Click "New Pull Request" and select your branch.
   - Provide a clear title and description, referencing any related issues (e.g., "Closes #123").
   - Use the PR template if available.

7. **Address Feedback**:
   - Respond to review comments and make necessary changes.
   - Push updates to the same branch to update the PR.

Pull requests will be reviewed by the maintainers, and we aim to provide feedback within a few days. Ensure your PR passes all CI checks (if configured) before it can be merged.

## Testing

Testing is critical to maintaining the reliability of QSS Parser. The test suite is located in the `tests/` directory and uses `unittest`. To run tests:

```bash
python -m unittest discover tests
```

For more comprehensive testing across Python versions, use `tox` (if configured):

```bash
pip install tox
tox
```

When contributing code:
- Add tests for new features or bug fixes in `tests/test_qss_parser.py`.
- Ensure 100% test coverage for your changes where possible.
- Update existing tests if behavior changes.

## Documentation

Documentation is essential for users and contributors. If your contribution affects the library’s API or usage:

- Update the [README.md](README.md) with relevant examples or instructions.
- Update docstrings for modified or new methods/classes.
- If adding significant features, consider updating any external documentation (e.g., on Read the Docs, if set up).

## Contact

For questions or assistance with contributing, please:
- Open an issue on the [GitHub Issues page](https://github.com/OniMock/qss_parser/issues).
- Contact the maintainer at [your.email@example.com](mailto:onimock@gmail.com).

We appreciate your contributions and look forward to collaborating with you!