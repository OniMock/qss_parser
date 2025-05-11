import logging
import os
import sys
import unittest
from typing import List, Set
from unittest.mock import Mock

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))
from qss_parser import QSSParser, QSSRule, QSSValidator

logging.basicConfig(level=logging.DEBUG)


class TestQSSParserValidation(unittest.TestCase):
    def setUp(self) -> None:
        """
        Set up the test environment for validation tests.
        """
        self.validator: QSSValidator = QSSValidator()

    def test_check_format_valid_qss(self) -> None:
        """
        Test QSS with valid format, expecting no errors.
        """
        qss: str = """
        QPushButton {
            color: blue;
            background: white;
        }
        #myButton {
            font-size: 12px;
        }
        """
        errors: List[str] = self.validator.check_format(qss)
        self.assertEqual(errors, [], "Valid QSS should return no errors")

    def test_check_format_missing_semicolon(self) -> None:
        """
        Test QSS with a property missing a semicolon.
        """
        qss: str = """
        QPushButton {
            color: blue
            background: white;
        }
        """
        errors: List[str] = self.validator.check_format(qss)
        expected: List[str] = ["Error on line 3: Property missing ';': color: blue"]
        self.assertEqual(errors, expected, "Should report property missing ';'")

    def test_check_format_extra_closing_brace(self) -> None:
        """
        Test QSS with a closing brace without a matching opening brace.
        """
        qss: str = """
        QPushButton {
            color: blue;
        }
        }
        """
        errors: List[str] = self.validator.check_format(qss)
        expected: List[str] = [
            "Error on line 5: Closing brace '}' without matching '{': }"
        ]
        self.assertEqual(
            errors, expected, "Should report closing brace without matching '{'"
        )

    def test_check_format_unclosed_brace(self) -> None:
        """
        Test QSS with an unclosed opening brace.
        """
        qss: str = """
        QPushButton {
            color: blue;
            background: white;
        #myButton {
            font-size: 12px;
        """
        errors: List[str] = self.validator.check_format(qss)
        expected: List[str] = [
            "Error on line 6: Unclosed brace '{' for selector: #myButton"
        ]
        self.assertEqual(errors, expected, "Should report unclosed brace")

    def test_check_format_property_outside_block(self) -> None:
        """
        Test QSS with a property outside a block.
        """
        qss: str = """
        color: blue;
        QPushButton {
            background: white;
        }
        """
        errors: List[str] = self.validator.check_format(qss)
        expected: List[str] = ["Error on line 2: Property outside block: color: blue;"]
        self.assertEqual(errors, expected, "Should report property outside block")

    def test_check_format_ignore_comments(self) -> None:
        """
        Test that comments are ignored during validation.
        """
        qss: str = """
        /* Comment with { and without ; */
        QPushButton {
            color: blue;
        }
        """
        errors: List[str] = self.validator.check_format(qss)
        self.assertEqual(errors, [], "Comments should not generate errors")

    def test_check_format_multi_line_property(self) -> None:
        """
        Test QSS with a property split across multiple lines without a semicolon.
        """
        qss: str = """
        QPushButton {
            color:
            blue
        }
        """
        errors: List[str] = self.validator.check_format(qss)
        expected: List[str] = ["Error on line 4: Property missing ';': color: blue"]
        self.assertEqual(
            errors, expected, "Should report multi-line property missing ';'"
        )

    def test_check_format_multiple_errors(self) -> None:
        """
        Test QSS with multiple errors (missing semicolon, unclosed brace).
        """
        qss: str = """
        QPushButton {
            color: blue
        #myButton {
            font-size: 12px
        background: gray;
        """
        errors: List[str] = self.validator.check_format(qss)
        expected: List[str] = [
            "Error on line 3: Property missing ';': color: blue",
            "Error on line 5: Property missing ';': font-size: 12px",
            "Error on line 6: Unclosed brace '{' for selector: #myButton",
        ]
        self.assertEqual(errors, expected, "Should report all errors")

    def test_check_format_empty_selector(self) -> None:
        """
        Test QSS with an empty selector before an opening brace.
        """
        qss: str = """
        {
            color: blue;
        }
        """
        errors: List[str] = self.validator.check_format(qss)
        expected: List[str] = ["Error on line 2: Empty selector before '{': {"]
        self.assertEqual(errors, expected, "Should report empty selector")

    def test_check_format_single_line_rule(self) -> None:
        """
        Test validation of a single-line QSS rule.
        """
        qss: str = """
        /* Comment */
        QWidget {color: blue;}
        #titleApp QPushButton {color: red;}
        """
        errors: List[str] = self.validator.check_format(qss)
        self.assertEqual(errors, [], "Valid single-line rule should return no errors")

    def test_check_format_with_pseudo_rule(self) -> None:
        """
        Test QSS with a valid single-line rule with pseudo-elements.
        """
        qss: str = """
        QScrollBar::handle:vertical {
            background: darkgray;
        }
        """
        errors: List[str] = self.validator.check_format(qss)
        self.assertEqual(errors, [], "Valid rule with pseudo should return no errors")

    def test_check_format_with_single_line_rule_pseudo_rule(self) -> None:
        """
        Test QSS with a valid single-line rule with pseudo-elements.
        """
        qss: str = """
        QScrollBar::handle:vertical { background: darkgray; }
        """
        errors: List[str] = self.validator.check_format(qss)
        self.assertEqual(errors, [], "Valid rule with pseudo should return no errors")

    def test_check_format_invalid_single_line_rule(self) -> None:
        """
        Test QSS with an invalid single-line rule (missing semicolon).
        """
        qss: str = """
        #titleLeftApp { font: 12pt "Segoe UI Semibold" }
        """
        errors: List[str] = self.validator.check_format(qss)
        expected: List[str] = [
            "Error on line 2: Property missing ';': font: 12pt \"Segoe UI Semibold\""
        ]
        self.assertEqual(
            errors, expected, "Should report missing semicolon in single-line rule"
        )

    def test_check_format_invalid_property(self) -> None:
        """
        Test QSS with an invalid property (empty value).
        """
        qss: str = """
        QPushButton {
            color: ;
        }
        """
        errors: List[str] = self.validator.check_format(qss)
        expected: List[str] = ["Error on line 3: Malformed property: color:"]
        self.assertEqual(errors, expected, "Should report invalid property")

    def test_check_format_complex_property_value(self) -> None:
        """
        Test QSS with properties containing complex values (e.g., commas, quotes).
        """
        qss: str = """
        QPushButton {
            font: 12pt "Segoe UI, Arial";
            background: url(image.png);
        }
        """
        errors: List[str] = self.validator.check_format(qss)
        self.assertEqual(errors, [], "Complex property values should be valid")

    def test_check_format_complex_for_attribute_selector(self) -> None:
        """
        Test QSS with properties containing complex values (e.g., [select]).
        """
        qss: str = """
        #btn_save[selected="true"]:hover {
            border-left: 22px solid qlineargradient(spread:pad, x1:0.034, y1:0, x2:0.216, y2:0, stop:0.499 rgba(255, 121, 198, 255), stop:0.5 rgba(85, 170, 255, 0));
            background-color: rgb(98, 114, 164);
        }
        """
        errors: List[str] = self.validator.check_format(qss)
        self.assertEqual(errors, [], "Complex attributes values should be valid")

    def test_check_format_complex_for_attribute_selector_with_class_and_id(
        self,
    ) -> None:
        """
        Test QSS with properties containing complex values (e.g., [select]).
        """
        qss: str = """
        QPushButton #btn_save[selected="true"]:hover {
            border-left: 22px solid qlineargradient(spread:pad, x1:0.034, y1:0, x2:0.216, y2:0, stop:0.499 rgba(255, 121, 198, 255), stop:0.5 rgba(85, 170, 255, 0));
            background-color: rgb(98, 114, 164);
        }
        """
        errors: List[str] = self.validator.check_format(qss)
        self.assertEqual(errors, [], "Complex attributes values should be valid")

    def test_check_format_nested_comments(self) -> None:
        """
        Test QSS with nested comments.
        """
        qss: str = """
        /* /* nested comment */ */
        QPushButton {
            color: blue;
        }
        """
        errors: List[str] = self.validator.check_format(qss)
        self.assertEqual(errors, [], "Nested comments should be ignored")

    def test_check_format_selector_with_extra_spaces(self) -> None:
        """
        Test QSS with selectors containing extra spaces.
        """
        qss: str = """
        QWidget   >   QPushButton {
            color: blue;
        }
        """
        errors: List[str] = self.validator.check_format(qss)
        self.assertEqual(errors, [], "Selectors with extra spaces should be valid")

    def test_check_format_property_empty_value_no_semicolon(self) -> None:
        """
        Test QSS with a property that has an empty value and no semicolon.
        """
        qss: str = """
        QPushButton {
            color:
        }
        """
        errors: List[str] = self.validator.check_format(qss)
        expected: List[str] = ["Error on line 3: Property missing ';': color:"]
        self.assertEqual(
            errors, expected, "Should report empty value property as malformed"
        )

    def test_check_format_invalid_class_id_spacing(self) -> None:
        """
        Test QSS with invalid selector missing space between class and ID (e.g., QPushButton#btn_save).
        """
        qss: str = """
        QPushButton#btn_save {
            color: blue;
        }
        """
        errors: List[str] = self.validator.check_format(qss)
        expected: List[str] = [
            "Error on line 2: Invalid selector: 'QPushButton#btn_save'. "
            "Space required between class and ID in 'QPushButton#btn_save'"
        ]
        self.assertEqual(
            errors, expected, "Should report missing space between class and ID"
        )

    def test_check_format_various_combinator_spacing(self) -> None:
        """
        Test QSS with various valid spacing around combinators.
        """
        qss: str = """
        QWidget > QPushButton {
            color: blue;
        }
        QWidget>QPushButton {
            color: red;
        }
        QWidget    >    QPushButton {
            color: green;
        }
        """
        errors: List[str] = self.validator.check_format(qss)
        self.assertEqual(
            errors, [], "Various spacing around combinators should be valid"
        )

    def test_check_format_invalid_pseudo_spacing(self) -> None:
        """
        Test QSS with invalid spacing before pseudo-states or pseudo-elements.
        """
        qss: str = """
        #btn_save :hover {
            color: blue;
        }
        #btn_save ::pressed {
            background: red;
        }
        QPushButton #btn_save :hover {
            border: 1px solid black;
        }
        """
        errors: List[str] = self.validator.check_format(qss)
        expected: List[str] = [
            "Error on line 2: Invalid spacing in selector: '#btn_save :hover'. "
            "No space allowed between '#btn_save' and ':hover' (pseudo-state)",
            "Error on line 5: Invalid spacing in selector: '#btn_save ::pressed'. "
            "No space allowed between '#btn_save' and '::pressed' (pseudo-element)",
            "Error on line 8: Invalid spacing in selector: 'QPushButton #btn_save :hover'. "
            "No space allowed between '#btn_save' and ':hover' (pseudo-state)",
        ]
        self.assertEqual(
            errors,
            expected,
            "Should report invalid spacing before pseudo-states/elements",
        )

    def test_check_format_valid_attribute_spacing(self) -> None:
        """
        Test QSS with valid selectors with or without space before attribute selectors.
        """
        qss: str = """
        QPushButton[selected="true"] {
            color: blue;
        }
        QPushButton [selected="true"] {
            background: red;
        }
        #btn_save[selected="true"] {
            border: 1px solid black;
        }
        #btn_save [selected="true"] {
            font-size: 12px;
        }
        """
        errors: List[str] = self.validator.check_format(qss)
        self.assertEqual(
            errors,
            [],
            "Selectors with or without space before attributes should be valid",
        )

    def test_check_format_valid_complex_selector(self) -> None:
        """
        Test QSS with valid complex selectors from the provided example.
        """
        qss: str = """
        QPushButton #btn_save[selected="true"]:hover {
            border-left: 22px solid qlineargradient(spread:pad, x1:0.034, y1:0, x2:0.216, y2:0, stop:0.499 rgba(255, 121, 198, 255), stop:0.5 rgba(85, 170, 255, 0));
            background-color: rgb(98, 114, 164);
        }
        QPushButton #btn_save[selected="true"]:hover::pressed {
            color: red;
            background-color: rgb(98, 114, 164);
        }
        QPushButton #btn_save {
            color: red;
            background-color: rgb(98, 114, 164);
        }
        QPushButton #btn_save:vertical {
            color: orange;
            width: 10px;
            background-color: rgb(98, 114, 164);
        }
        QPushButton #btn_save:hover:!selected {
            background-color: rgb(52, 59, 72);
        }
        """
        errors: List[str] = self.validator.check_format(qss)
        self.assertEqual(errors, [], "Valid complex selectors should return no errors")

    def test_check_format_invalid_selectors_from_example(self) -> None:
        """
        Test QSS with invalid selectors from the provided example (e.g., QPushButton#btn_save, #btn_save :hover).
        """
        self.maxDiff = None
        qss: str = """
        QPushButton#btn_save[selected="true"]:hover {
            border-left: 22px solid qlineargradient(spread:pad, x1:0.034, y1:0, x2:0.216, y2:0, stop:0.499 rgba(255, 121, 198, 255), stop:0.5 rgba(85, 170, 255, 0));
            background-color: rgb(98, 114, 164);
        }
        QPushButton#btn_save[selected="true"]:hover::pressed {
            color: red;
            background-color: rgb(98, 114, 164);
        }
        QPushButton#btn_save {
            color: red;
            background-color: rgb(98, 114, 164);
        }
        QPushButton#btn_save:vertical {
            color: orange;
            width: 10px;
            background-color: rgb(98, 114, 164);
        }
        QPushButton#btn_save:hover:!selected {
            color: green;
        }
        """
        errors: List[str] = self.validator.check_format(qss)
        expected: List[str] = [
            "Error on line 2: Invalid selector: 'QPushButton#btn_save[selected=\"true\"]:hover'. "
            "Space required between class and ID in 'QPushButton#btn_save[selected=\"true\"]:hover'",
            "Error on line 6: Invalid selector: 'QPushButton#btn_save[selected=\"true\"]:hover::pressed'. "
            "Space required between class and ID in 'QPushButton#btn_save[selected=\"true\"]:hover::pressed'",
            "Error on line 10: Invalid selector: 'QPushButton#btn_save'. "
            "Space required between class and ID in 'QPushButton#btn_save'",
            "Error on line 14: Invalid selector: 'QPushButton#btn_save:vertical'. "
            "Space required between class and ID in 'QPushButton#btn_save:vertical'",
            "Error on line 19: Invalid selector: 'QPushButton#btn_save:hover:!selected'. "
            "Space required between class and ID in 'QPushButton#btn_save:hover:!selected'",
        ]
        self.assertEqual(
            errors,
            expected,
            "Should report missing space between class and ID for all invalid selectors",
        )

    def test_check_format_multiple_selectors_comma_separated(self) -> None:
        """
        Test QSS with multiple selectors separated by commas, expecting no errors.
        """
        qss: str = """
        #myButton,
        QFrame,
        #otherButton,
        QPushButton {
            color: blue;
        }
        """
        errors: List[str] = self.validator.check_format(qss)
        self.assertEqual(
            errors, [], "Multiple comma-separated selectors should be valid"
        )

    def test_check_format_multiple_selectors_comma_separated_with_pseudo_state(
        self,
    ) -> None:
        """
        Test QSS with multiple selectors including pseudo-states, expecting errors for invalid combinations.
        """
        qss: str = """
        #myButton:hover,
        QFrame:disabled {
            color: red;
        }
        """
        self.maxDiff = None
        errors: List[str] = self.validator.check_format(qss)
        expected: List[str] = [
            "Error: Pseudo-states in comma-separated selectors are not supported. "
            "Split into separate rules for #myButton:hover, QFrame:disabled"
        ]
        self.assertEqual(
            errors,
            expected,
            "Should report invalid pseudo-state in comma-separated selectors",
        )

    def test_check_format_multiple_selectors_comma_separated_with_spaces(self) -> None:
        """
        Test QSS with multiple selectors separated by commas with various spacing patterns.
        """
        qss: str = """
        #myButton,  QFrame,  #otherButton  ,QPushButton {
            color: blue;
        }
        """
        errors: List[str] = self.validator.check_format(qss)
        self.assertEqual(errors, [], "Various spacing around commas should be valid")

    def test_check_format_multiple_selectors_comma_separated_without_spaces(
        self,
    ) -> None:
        """
        Test QSS with multiple selectors separated by commas without spacing patterns.
        """
        qss: str = """
        #myButton,QFrame,#otherButton,QPushButton {
            color: blue;
        }
        """
        errors: List[str] = self.validator.check_format(qss)
        self.assertEqual(errors, [], "Without spacing around commas should be valid")


class TestQSSParserParsing(unittest.TestCase):
    def setUp(self) -> None:
        """
        Set up the test environment for parsing tests.
        """
        self.parser: QSSParser = QSSParser()
        self.qss: str = """
        #myButton {
            color: red;
        }
        QPushButton {
            background: blue;
        }
        QScrollBar {
            background: gray;
            width: 10px;
        }
        QScrollBar:vertical {
            background: lightgray;
        }
        QWidget {
            font-size: 12px;
        }
        QFrame {
            border: 1px solid black;
        }
        .customClass {
            border-radius: 5px;
        }
        """
        self.parser.parse(self.qss)

    def test_parse_valid_qss(self) -> None:
        """
        Test parsing valid QSS text.
        """
        self.assertEqual(
            len(self.parser._state.rules), 7, "Should parse all rules correctly"
        )

    def test_parse_empty_qss(self) -> None:
        """
        Test parsing empty QSS text.
        """
        parser: QSSParser = QSSParser()
        parser.parse("")
        self.assertEqual(
            len(parser._state.rules), 0, "Empty QSS should result in no rules"
        )

    def test_parse_comments_only(self) -> None:
        """
        Test parsing QSS with only comments.
        """
        parser: QSSParser = QSSParser()
        qss: str = """
        /* This is a comment */
        /* Another comment */
        """
        parser.parse(qss)
        self.assertEqual(
            len(parser._state.rules), 0, "Comments-only QSS should result in no rules"
        )

    def test_parse_malformed_property(self) -> None:
        """
        Test parsing QSS with a malformed property.
        """
        parser: QSSParser = QSSParser()
        qss: str = """
        QPushButton {
            color: blue;
            margin: ;
            background
        }
        """
        parser.parse(qss)
        self.assertEqual(
            len(parser._state.rules), 1, "Should parse valid properties only"
        )
        self.assertEqual(
            len(parser._state.rules[0].properties),
            1,
            "Should only include valid property",
        )

    def test_parse_multiple_selectors(self) -> None:
        """
        Test parsing QSS with multiple selectors in a single rule.
        """
        parser: QSSParser = QSSParser()
        qss: str = """
        QPushButton, QFrame, .customClass {
            color: blue;
        }
        """
        parser.parse(qss)
        self.assertEqual(
            len(parser._state.rules),
            3,
            "Should parse multiple selectors as separate rules",
        )
        selectors: Set[str] = {rule.selector for rule in parser._state.rules}
        self.assertEqual(selectors, {"QPushButton", "QFrame", ".customClass"})

    def test_parse_duplicate_properties(self) -> None:
        """
        Test parsing QSS with duplicate properties in a single rule, ensuring the last value is kept.
        """
        parser: QSSParser = QSSParser()
        qss: str = """
        QPushButton {
            color: blue;
            color: red;
        }
        """
        parser.parse(qss)
        self.assertEqual(len(parser._state.rules), 1, "Should parse one rule")
        self.assertEqual(
            len(parser._state.rules[0].properties),
            2,
            "Should keep only the last value for duplicate properties",
        )
        self.assertEqual(
            parser._state.rules[0].properties[1].value,
            "red",
            "Should retain the last value (red) for duplicate property 'color'",
        )

    def test_parse_attribute_selector_complex(self) -> None:
        """
        Test parsing QSS with a complex attribute selector.
        """
        qss: str = """
        QPushButton [data-value="complex string with spaces"] {
            color: blue;
        }
        """
        parser: QSSParser = QSSParser()
        parser.parse(qss)
        self.assertEqual(len(parser._state.rules), 1, "Should parse one rule")
        rule: QSSRule = parser._state.rules[0]
        self.assertEqual(
            rule.selector, 'QPushButton [data-value="complex string with spaces"]'
        )
        self.assertEqual(rule.attributes, ['[data-value="complex string with spaces"]'])
        self.assertEqual(len(rule.properties), 1)
        self.assertEqual(rule.properties[0].name, "color")
        self.assertEqual(rule.properties[0].value, "blue")

    def test_parse_variables_block(self) -> None:
        """
        Test parsing a @variables block and resolving variables in properties.
        """
        qss: str = """
        @variables {
            --primary-color: #ffffff;
            --font-size: 14px;
        }
        QPushButton {
            color: var(--primary-color);
            font-size: var(--font-size);
        }
        """
        parser: QSSParser = QSSParser()
        parser.parse(qss)
        self.assertEqual(len(parser._state.rules), 1, "Should parse one rule")
        rule: QSSRule = parser._state.rules[0]
        self.assertEqual(rule.selector, "QPushButton")
        self.assertEqual(len(rule.properties), 2)
        self.assertEqual(rule.properties[0].name, "color")
        self.assertEqual(rule.properties[0].value, "#ffffff")
        self.assertEqual(rule.properties[1].name, "font-size")
        self.assertEqual(rule.properties[1].value, "14px")

    def test_undefined_variable(self) -> None:
        """
        Test handling of undefined variables, ensuring an error is reported.
        """
        errors = []

        def error_handler(error: str) -> None:
            errors.append(error)

        qss: str = """
        QPushButton {
            color: var(--undefined-color);
        }
        """
        parser: QSSParser = QSSParser()
        parser.on("error_found", error_handler)
        parser.parse(qss)
        self.assertEqual(len(parser._state.rules), 1, "Should parse one rule")
        rule: QSSRule = parser._state.rules[0]
        self.assertEqual(rule.properties[0].value, "var(--undefined-color)")
        self.assertEqual(len(errors), 1)
        self.assertTrue("Undefined variables: --undefined-color" in errors[0])

    def test_malformed_variables_block(self) -> None:
        """
        Test parsing a malformed @variables block, ensuring errors are reported.
        """
        errors = []

        def error_handler(error: str) -> None:
            errors.append(error)

        qss: str = """
        @variables {
            primary-color: #ffffff;
            --font-size: 14px
        }
        QPushButton {
            color: var(--primary-color);
            background: #ffffff;
        }
        """
        parser: QSSParser = QSSParser()
        parser.on("error_found", error_handler)
        parser.parse(qss)
        self.assertEqual(len(errors), 2)
        self.assertTrue("Invalid variable name" in errors[0])
        self.assertEqual(len(parser._state.rules), 1)
        rule: QSSRule = parser._state.rules[0]
        self.assertEqual(rule.properties[0].value, "var(--primary-color)")
        self.assertEqual(rule.properties[1].value, "#ffffff")

    def test_variables_with_complex_values(self) -> None:
        """
        Test parsing variables with complex values, such as gradients or multi-part values.
        """
        qss: str = """
        @variables {
            --gradient: linear-gradient(to right, #ff0000, #00ff00);
        }
        QPushButton {
            background: var(--gradient);
        }
        """
        parser: QSSParser = QSSParser()
        parser.parse(qss)
        self.assertEqual(len(parser._state.rules), 1, "Should parse one rule")
        rule: QSSRule = parser._state.rules[0]
        self.assertEqual(rule.selector, "QPushButton")
        self.assertEqual(len(rule.properties), 1)
        self.assertEqual(rule.properties[0].name, "background")
        self.assertEqual(
            rule.properties[0].value, "linear-gradient(to right, #ff0000, #00ff00)"
        )

    def test_nested_variables(self) -> None:
        """
        Test resolving variables that reference other variables.
        """
        qss: str = """
        @variables {
            --base-color: #0000ff;
            --button-color: var(--base-color);
        }
        QPushButton {
            color: var(--button-color);
        }
        """
        parser: QSSParser = QSSParser()
        parser.parse(qss)
        self.assertEqual(len(parser._state.rules), 1, "Should parse one rule")
        rule: QSSRule = parser._state.rules[0]
        self.assertEqual(rule.selector, "QPushButton")
        self.assertEqual(len(rule.properties), 1)
        self.assertEqual(rule.properties[0].name, "color")
        self.assertEqual(rule.properties[0].value, "#0000ff")

    def test_parse_multiple_selectors_comma_separated(self) -> None:
        """
        Test parsing QSS with multiple comma-separated selectors into separate rules.
        """
        qss: str = """
        #myButton, QFrame, .customClass {
            color: blue;
        }
        """
        parser: QSSParser = QSSParser()
        parser.parse(qss)

        self.assertEqual(len(parser._state.rules), 3)

        selectors = {rule.selector for rule in parser._state.rules}
        self.assertEqual(selectors, {"#myButton", "QFrame", ".customClass"})

        for rule in parser._state.rules:
            self.assertEqual(len(rule.properties), 1)
            self.assertEqual(rule.properties[0].name, "color")
            self.assertEqual(rule.properties[0].value, "blue")

    def test_parse_multiple_selectors_comma_separated_without_spaces(self) -> None:
        """
        Test parsing QSS with multiple comma-separated selectors into separate rules.
        """
        qss: str = """
        #myButton,QFrame,.customClass {
            color: blue;
        }
        """
        parser: QSSParser = QSSParser()
        parser.parse(qss)

        self.assertEqual(len(parser._state.rules), 3)

        selectors = {rule.selector for rule in parser._state.rules}
        self.assertEqual(selectors, {"#myButton", "QFrame", ".customClass"})

        for rule in parser._state.rules:
            self.assertEqual(len(rule.properties), 1)
            self.assertEqual(rule.properties[0].name, "color")
            self.assertEqual(rule.properties[0].value, "blue")

    def test_parse_multiple_selectors_comma_separated_by_line(self) -> None:
        """
        Test parsing QSS with multiple comma-separated by line selectors into separate rules.
        """
        qss: str = """
        #myButton,
        QFrame,
        .customClass {
            color: blue;
        }
        """
        parser: QSSParser = QSSParser()
        parser.parse(qss)

        self.assertEqual(len(parser._state.rules), 3)

        selectors = {rule.selector for rule in parser._state.rules}
        self.assertEqual(selectors, {"#myButton", "QFrame", ".customClass"})

        for rule in parser._state.rules:
            self.assertEqual(len(rule.properties), 1)
            self.assertEqual(rule.properties[0].name, "color")
            self.assertEqual(rule.properties[0].value, "blue")


class TestQSSParserStyleSelection(unittest.TestCase):
    def setUp(self) -> None:
        """
        Set up the test environment for style selection tests.
        """
        self.parser: QSSParser = QSSParser()
        self.qss: str = """
        #myButton {
            color: red;
        }
        QPushButton {
            background: blue;
        }
        QScrollBar {
            background: gray;
            width: 10px;
        }
        QScrollBar:vertical {
            background: lightgray;
        }
        QWidget {
            font-size: 12px;
        }
        QFrame {
            border: 1px solid black;
        }
        .customClass {
            border-radius: 5px;
        }
        """
        self.widget: Mock = Mock()
        self.widget.objectName.return_value = "myButton"
        self.widget.metaObject.return_value.className.return_value = "QPushButton"
        self.widget_no_name: Mock = Mock()
        self.widget_no_name.objectName.return_value = ""
        self.widget_no_name.metaObject.return_value.className.return_value = (
            "QScrollBar"
        )
        self.widget_no_qss: Mock = Mock()
        self.widget_no_qss.objectName.return_value = "verticalScrollBar"
        self.widget_no_qss.metaObject.return_value.className.return_value = "QScrollBar"
        self.parser.parse(self.qss)

    def test_get_styles_for_object_name(self) -> None:
        """
        Test style retrieval by object name.
        """
        stylesheet: str = self.parser.get_styles_for(self.widget)
        expected: str = """#myButton {
    color: red;
}"""
        self.assertEqual(stylesheet.strip(), expected.strip())

    def test_get_styles_for_class_name_no_object_name(self) -> None:
        """
        Test style retrieval by class name when no object name is provided.
        """
        stylesheet: str = self.parser.get_styles_for(self.widget_no_name)
        expected: str = """QScrollBar {
    background: gray;
    width: 10px;
}
QScrollBar:vertical {
    background: lightgray;
}"""
        self.assertEqual(stylesheet.strip(), expected.strip())

    def test_get_styles_for_object_name_no_qss_fallback_class(self) -> None:
        """
        Test fallback to class name when object name has no styles.
        """
        stylesheet: str = self.parser.get_styles_for(self.widget_no_qss)
        expected: str = """QScrollBar {
    background: gray;
    width: 10px;
}
QScrollBar:vertical {
    background: lightgray;
}"""
        self.assertEqual(stylesheet.strip(), expected.strip())

    def test_get_styles_for_include_class_if_object_name(self) -> None:
        """
        Test including class styles when an object name is provided.
        """
        stylesheet: str = self.parser.get_styles_for(
            self.widget, include_class_if_object_name=True
        )
        expected: str = """#myButton {
    color: red;
}
QPushButton {
    background: blue;
}"""
        self.assertEqual(stylesheet.strip(), expected.strip())

    def test_get_styles_for_fallback_class_when_have_object_name(self) -> None:
        """
        Test style retrieval with a fallback class when an object name is provided.
        """
        stylesheet: str = self.parser.get_styles_for(
            self.widget, fallback_class="QWidget"
        )
        expected: str = """#myButton {
    color: red;
}"""
        self.assertEqual(stylesheet.strip(), expected.strip())

    def test_get_styles_for_fallback_class_when_without_object_name(self) -> None:
        """
        Test style retrieval with a fallback class when no object name is provided.
        """
        widget: Mock = Mock()
        widget.objectName.return_value = "oiiio"
        widget.metaObject.return_value.className.return_value = "QFrame"
        stylesheet: str = self.parser.get_styles_for(widget, fallback_class="QWidget")
        expected: str = """QFrame {
    border: 1px solid black;
}"""
        self.assertEqual(stylesheet.strip(), expected.strip())

    def test_get_styles_for_fallback_class_when_without_object_name_and_class(
        self,
    ) -> None:
        """
        Test style retrieval with a fallback class when neither object name nor class has styles.
        """
        widget: Mock = Mock()
        widget.objectName.return_value = "oiiio"
        widget.metaObject.return_value.className.return_value = "Ola"
        stylesheet: str = self.parser.get_styles_for(widget, fallback_class="QWidget")
        expected: str = """QWidget {
    font-size: 12px;
}"""
        self.assertEqual(stylesheet.strip(), expected.strip())

    def test_get_styles_for_additional_selectors(self) -> None:
        """
        Test style retrieval with additional selectors.
        """
        stylesheet: str = self.parser.get_styles_for(
            self.widget, additional_selectors=["QFrame", ".customClass"]
        )
        expected: str = """#myButton {
    color: red;
}
.customClass {
    border-radius: 5px;
}
QFrame {
    border: 1px solid black;
}"""
        self.assertEqual(stylesheet.strip(), expected.strip())

    def test_get_styles_for_all_parameters(self) -> None:
        """
        Test style retrieval with all parameters combined.
        """
        stylesheet: str = self.parser.get_styles_for(
            self.widget,
            fallback_class="QWidget",
            additional_selectors=["QFrame"],
            include_class_if_object_name=True,
        )
        expected: str = """#myButton {
    color: red;
}
QFrame {
    border: 1px solid black;
}
QPushButton {
    background: blue;
}"""
        self.assertEqual(stylesheet.strip(), expected.strip())

    def test_get_styles_for_invalid_selector(self) -> None:
        """
        Test style retrieval with an invalid additional selector.
        """
        stylesheet: str = self.parser.get_styles_for(
            self.widget, additional_selectors=["InvalidClass"]
        )
        expected: str = """#myButton {
    color: red;
}"""
        self.assertEqual(stylesheet.strip(), expected.strip())

    def test_get_styles_for_composite_selector(self) -> None:
        """
        Test style retrieval with composite selectors.
        """
        parser: QSSParser = QSSParser()
        qss: str = """
        QScrollBar QWidget {
            margin: 5px;
        }
        QScrollBar:vertical QWidget {
            padding: 2px;
        }
        """
        parser.parse(qss)
        widget: Mock = Mock()
        widget.objectName.return_value = ""
        widget.metaObject.return_value.className.return_value = "QScrollBar"
        stylesheet: str = parser.get_styles_for(widget)
        expected: str = """QScrollBar QWidget {
    margin: 5px;
}
QScrollBar:vertical QWidget {
    padding: 2px;
}"""
        self.assertEqual(stylesheet.strip(), expected.strip())

    def test_get_styles_for_multiple_selectors(self) -> None:
        """
        Test style retrieval with multiple selectors in a single rule.
        """
        parser: QSSParser = QSSParser()
        qss: str = """
        QPushButton, QScrollBar {
            color: green;
        }
        """
        parser.parse(qss)
        widget: Mock = Mock()
        widget.objectName.return_value = ""
        widget.metaObject.return_value.className.return_value = "QScrollBar"
        stylesheet: str = parser.get_styles_for(widget)
        expected: str = """QScrollBar {
    color: green;
}"""
        self.assertEqual(stylesheet.strip(), expected.strip())

    def test_get_styles_for_fallback_class_and_additional_selectors(self) -> None:
        """
        Test style retrieval combining fallback class and additional selectors.
        """
        stylesheet: str = self.parser.get_styles_for(
            self.widget, fallback_class="QWidget", additional_selectors=["QFrame"]
        )
        expected: str = """#myButton {
    color: red;
}
QFrame {
    border: 1px solid black;
}"""
        self.assertEqual(stylesheet.strip(), expected.strip())

    def test_get_styles_for_include_class_and_additional_selectors(self) -> None:
        """
        Test style retrieval combining include_class_if_object_name and additional selectors.
        """
        stylesheet: str = self.parser.get_styles_for(
            self.widget,
            additional_selectors=[".customClass"],
            include_class_if_object_name=True,
        )
        expected: str = """#myButton {
    color: red;
}
.customClass {
    border-radius: 5px;
}
QPushButton {
    background: blue;
}"""
        self.assertEqual(stylesheet.strip(), expected.strip())

    def test_get_styles_for_object_name_no_rules(self) -> None:
        """
        Test style retrieval for an object name with no rules, including class styles.
        """
        widget: Mock = Mock()
        widget.objectName.return_value = "nonExistentButton"
        widget.metaObject.return_value.className.return_value = "QPushButton"
        stylesheet: str = self.parser.get_styles_for(
            widget, include_class_if_object_name=True
        )
        expected: str = """QPushButton {
    background: blue;
}"""
        self.assertEqual(stylesheet.strip(), expected.strip())

    def test_get_styles_for_fallback_class_no_rules(self) -> None:
        """
        Test style retrieval with a fallback class that has no rules.
        """
        stylesheet: str = self.parser.get_styles_for(
            self.widget, fallback_class="NonExistentClass"
        )
        expected: str = """#myButton {
    color: red;
}"""
        self.assertEqual(stylesheet.strip(), expected.strip())

    def test_get_styles_for_mixed_additional_selectors(self) -> None:
        """
        Test style retrieval with a mix of valid and invalid additional selectors.
        """
        stylesheet: str = self.parser.get_styles_for(
            self.widget, additional_selectors=["QFrame", "InvalidClass"]
        )
        expected: str = """#myButton {
    color: red;
}
QFrame {
    border: 1px solid black;
}"""
        self.assertEqual(stylesheet.strip(), expected.strip())

    def test_get_styles_for_pseudo_state_combination(self) -> None:
        """
        Test style retrieval with combined pseudo-states.
        """
        parser: QSSParser = QSSParser()
        qss: str = """
        QPushButton:hover:focus {
            color: green;
        }
        """
        parser.parse(qss)
        widget: Mock = Mock()
        widget.objectName.return_value = ""
        widget.metaObject.return_value.className.return_value = "QPushButton"
        stylesheet: str = parser.get_styles_for(widget)
        expected: str = """QPushButton:hover:focus {
    color: green;
}"""
        self.assertEqual(stylesheet.strip(), expected.strip())

    def test_get_styles_for_pseudo_element_selector(self) -> None:
        """
        Test style retrieval with pseudo-element selectors.
        """
        parser: QSSParser = QSSParser()
        qss: str = """
        QScrollBar::handle {
            background: darkgray;
        }
        """
        parser.parse(qss)
        widget: Mock = Mock()
        widget.objectName.return_value = ""
        widget.metaObject.return_value.className.return_value = "QScrollBar"
        stylesheet: str = parser.get_styles_for(widget)
        expected: str = """QScrollBar::handle {
    background: darkgray;
}"""
        self.assertEqual(stylesheet.strip(), expected.strip())

    def test_get_styles_for_empty_qss_with_parameters(self) -> None:
        """
        Test style retrieval with empty QSS and parameters.
        """
        parser: QSSParser = QSSParser()
        parser.parse("")
        widget: Mock = Mock()
        widget.objectName.return_value = "myButton"
        widget.metaObject.return_value.className.return_value = "QPushButton"
        stylesheet: str = parser.get_styles_for(
            widget,
            fallback_class="QWidget",
            additional_selectors=["QFrame"],
            include_class_if_object_name=True,
        )
        self.assertEqual(stylesheet, "", "Empty QSS should return empty stylesheet")

    def test_get_styles_for_duplicate_rules(self) -> None:
        """
        Test style retrieval with duplicate rules.
        """
        parser: QSSParser = QSSParser()
        qss: str = """
        QPushButton {
            color: blue;
        }
        QPushButton {
            background: white;
        }
        """
        parser.parse(qss)
        widget: Mock = Mock()
        widget.objectName.return_value = ""
        widget.metaObject.return_value.className.return_value = "QPushButton"
        stylesheet: str = parser.get_styles_for(widget)
        expected: str = """QPushButton {
    color: blue;
    background: white;
}"""
        self.assertEqual(stylesheet.strip(), expected.strip())

    def test_get_styles_for_missing_closing_brace(self) -> None:
        """
        Test style retrieval with QSS missing a closing brace.
        """
        parser: QSSParser = QSSParser()
        qss: str = """
        QPushButton {
            color: blue;
        """
        parser.parse(qss)
        widget: Mock = Mock()
        widget.objectName.return_value = ""
        widget.metaObject.return_value.className.return_value = "QPushButton"
        stylesheet: str = parser.get_styles_for(widget)
        self.assertEqual(
            stylesheet, "", "Incomplete QSS should return empty stylesheet"
        )

    def test_get_styles_for_hierarchical_selector(self) -> None:
        """
        Test style retrieval with hierarchical selectors.
        """
        parser: QSSParser = QSSParser()
        qss: str = """
        QWidget > QFrame QPushButton {
            border: 1px solid green;
        }
        """
        parser.parse(qss)
        widget: Mock = Mock()
        widget.objectName.return_value = ""
        widget.metaObject.return_value.className.return_value = "QPushButton"
        stylesheet: str = parser.get_styles_for(widget)
        expected: str = """QWidget > QFrame QPushButton {
    border: 1px solid green;
}"""
        self.assertEqual(stylesheet.strip(), expected.strip())

    def test_get_styles_for_complex_nested_selector(self) -> None:
        """
        Test style retrieval with complex nested selectors.
        """
        parser: QSSParser = QSSParser()
        qss: str = """
        QWidget QFrame > QPushButton {
            border: 1px solid green;
        }
        """
        parser.parse(qss)
        widget: Mock = Mock()
        widget.objectName.return_value = ""
        widget.metaObject.return_value.className.return_value = "QPushButton"
        stylesheet: str = parser.get_styles_for(widget)
        expected: str = """QWidget QFrame > QPushButton {
    border: 1px solid green;
}"""
        self.assertEqual(stylesheet.strip(), expected.strip())

    def test_get_styles_for_complex_selector(self) -> None:
        """
        Test style retrieval with complex selectors including pseudo-states.
        """
        parser: QSSParser = QSSParser()
        qss: str = """
        QWidget QFrame > QPushButton:hover {
            border: 1px solid green;
        }
        """
        parser.parse(qss)
        widget: Mock = Mock()
        widget.objectName.return_value = ""
        widget.metaObject.return_value.className.return_value = "QPushButton"
        stylesheet: str = parser.get_styles_for(widget)
        expected: str = """QWidget QFrame > QPushButton:hover {
    border: 1px solid green;
}"""
        self.assertEqual(stylesheet.strip(), expected.strip())

    def test_get_styles_for_selector_with_extra_spaces(self) -> None:
        """
        Test style retrieval with a selector containing extra spaces.
        """
        parser: QSSParser = QSSParser()
        qss: str = """
        QWidget   >   QPushButton {
            border: 1px solid green;
        }
        """
        parser.parse(qss)
        widget: Mock = Mock()
        widget.objectName.return_value = ""
        widget.metaObject.return_value.className.return_value = "QPushButton"
        stylesheet: str = parser.get_styles_for(widget)
        expected: str = """QWidget > QPushButton {
    border: 1px solid green;
}"""
        self.assertEqual(stylesheet.strip(), expected.strip())

    def test_check_format_valid_variables_block(self) -> None:
        """
        Test validation of a valid @variables block in QSS text.
        """
        qss: str = """
        @variables {
            --primary-color: #ffffff;
            --font-size: 14px;
        }
        QPushButton {
            color: var(--primary-color);
            font-size: var(--font-size);
        }
        """
        parser: QSSParser = QSSParser()
        errors = parser.check_format(qss)
        self.assertEqual(
            len(errors), 0, "Valid @variables block should not produce errors"
        )

    def test_check_format_malformed_variables_block(self) -> None:
        """
        Test validation of a malformed @variables block, ensuring errors are reported.
        """
        qss: str = """
        @variables {
            primary-color: #ffffff;
            --font-size: 14px
        }
        QPushButton {
            color: var(--primary-color);
        }
        """
        parser: QSSParser = QSSParser()
        errors = parser.check_format(qss)
        self.assertGreater(
            len(errors), 0, "Malformed @variables block should produce errors"
        )
        self.assertTrue(
            any("Property missing ';'" in error for error in errors),
            "Should report missing semicolon error",
        )

    def test_check_format_nested_variables_block(self) -> None:
        """
        Test validation of a nested @variables block, which should be rejected.
        """
        qss: str = """
        QPushButton {
            @variables {
                --primary-color: #ffffff;
            }
        }
        """
        parser: QSSParser = QSSParser()
        errors = parser.check_format(qss)
        self.assertGreater(
            len(errors), 0, "Nested @variables block should produce errors"
        )
        self.assertTrue(
            any("Nested @variables block" in error for error in errors),
            "Should report nested @variables block error",
        )

    def test_check_format_variables_and_rules(self) -> None:
        """
        Test validation of QSS text with both @variables and regular rules.
        """
        qss: str = """
        @variables {
            --primary-color: #ffffff;
        }
        QPushButton {
            color: var(--primary-color);
        }
        QLabel {
            background-color: var(--primary-color);
        }
        """
        parser: QSSParser = QSSParser()
        errors = parser.check_format(qss)
        self.assertEqual(
            len(errors),
            0,
            "Valid QSS with @variables and rules should not produce errors",
        )

    def test_get_styles_for_attribute_selector(self) -> None:
        """
        Test style retrieval for a selector with attribute and pseudo-state.
        """
        parser: QSSParser = QSSParser()
        qss: str = """
        #btn_save[selected="true"]:hover {
            border-left: 22px solid qlineargradient(spread:pad, x1:0.034, y1:0, x2:0.216, y2:0, stop:0.499 rgba(255, 121, 198, 255), stop:0.5 rgba(85, 170, 255, 0));
            background-color: rgb(98, 114, 164);
        }
        """
        errors: List[str] = parser.check_format(qss)
        self.assertEqual(
            errors, [], "Valid QSS with attribute selector should return no errors"
        )

        parser.parse(qss)
        self.assertEqual(
            len(parser._state.rules),
            1,
            "Should parse one rule and one base rule without pseudo-states",
        )
        self.assertEqual(
            parser._state.rules[0].selector, '#btn_save[selected="true"]:hover'
        )
        self.assertEqual(len(parser._state.rules[0].properties), 2)
        self.assertEqual(parser._state.rules[0].properties[0].name, "border-left")
        self.assertEqual(
            parser._state.rules[0].properties[0].value,
            "22px solid qlineargradient(spread:pad, x1:0.034, y1:0, x2:0.216, y2:0, stop:0.499 rgba(255, 121, 198, 255), stop:0.5 rgba(85, 170, 255, 0))",
        )
        self.assertEqual(parser._state.rules[0].properties[1].name, "background-color")
        self.assertEqual(
            parser._state.rules[0].properties[1].value, "rgb(98, 114, 164)"
        )

        widget: Mock = Mock()
        widget.objectName.return_value = "btn_save"
        widget.metaObject.return_value.className.return_value = "QPushButton"
        stylesheet: str = parser.get_styles_for(widget)
        expected: str = """#btn_save[selected="true"]:hover {
    border-left: 22px solid qlineargradient(spread:pad, x1:0.034, y1:0, x2:0.216, y2:0, stop:0.499 rgba(255, 121, 198, 255), stop:0.5 rgba(85, 170, 255, 0));
    background-color: rgb(98, 114, 164);
}"""
        self.assertEqual(stylesheet.strip(), expected.strip())

    def test_get_styles_for_attribute_selector_with_class_and_id(self) -> None:
        """
        Test style retrieval for a selector with class and id with attribute and pseudo-state.
        """
        parser: QSSParser = QSSParser()
        qss: str = """
        QPushButton #btn_save[selected="true"]:hover {
            border-left: 22px solid qlineargradient(spread:pad, x1:0.034, y1:0, x2:0.216, y2:0, stop:0.499 rgba(255, 121, 198, 255), stop:0.5 rgba(85, 170, 255, 0));
            background-color: rgb(98, 114, 164);
        }
        """
        errors: List[str] = parser.check_format(qss)
        self.assertEqual(
            errors, [], "Valid QSS with attribute selector should return no errors"
        )

        parser.parse(qss)
        self.assertEqual(
            len(parser._state.rules),
            1,
            "Should parse one rule and one base rule without pseudo-states",
        )
        self.assertEqual(
            parser._state.rules[0].selector,
            'QPushButton #btn_save[selected="true"]:hover',
        )
        self.assertEqual(len(parser._state.rules[0].properties), 2)
        self.assertEqual(parser._state.rules[0].properties[0].name, "border-left")
        self.assertEqual(
            parser._state.rules[0].properties[0].value,
            "22px solid qlineargradient(spread:pad, x1:0.034, y1:0, x2:0.216, y2:0, stop:0.499 rgba(255, 121, 198, 255), stop:0.5 rgba(85, 170, 255, 0))",
        )
        self.assertEqual(parser._state.rules[0].properties[1].name, "background-color")
        self.assertEqual(
            parser._state.rules[0].properties[1].value, "rgb(98, 114, 164)"
        )

        widget: Mock = Mock()
        widget.objectName.return_value = "btn_save"
        widget.metaObject.return_value.className.return_value = "QPushButton"
        stylesheet: str = parser.get_styles_for(widget)
        expected: str = """QPushButton #btn_save[selected="true"]:hover {
    border-left: 22px solid qlineargradient(spread:pad, x1:0.034, y1:0, x2:0.216, y2:0, stop:0.499 rgba(255, 121, 198, 255), stop:0.5 rgba(85, 170, 255, 0));
    background-color: rgb(98, 114, 164);
}"""
        self.assertEqual(stylesheet.strip(), expected.strip())

    def test_qss_parser_handles_attribute_and_pseudo_combinations(self) -> None:
        """
        Test style retrieval for a selector with class and id with attribute and pseudo-state.
        Ensures the last value for duplicate properties is retained (CSS standard).
        """
        self.maxDiff = None
        parser: QSSParser = QSSParser()
        qss: str = """
        QPushButton #btn_save[selected="true"]:hover {
            border-left: 22px solid qlineargradient(spread:pad, x1:0.034, y1:0, x2:0.216, y2:0, stop:0.499 rgba(255, 121, 198, 255), stop:0.5 rgba(85, 170, 255, 0));
            background-color: rgb(98, 114, 164);
        }
        QPushButton #btn_save[selected="true"]:hover {
            color: red;
            background-color: rgb(97, 114, 164);
        }
        QPushButton #btn_save[selected="true"]:hover::pressed {
            color: red;
            background-color: rgb(98, 114, 164);
        }
        QPushButton #btn_save[selected="true"]:hover::pressed {
            color: blue;
            font-size: 10px;
            background-color: rgb(98, 114, 152);
        }
        QPushButton #btn_save {
            color: red;
            background-color: rgb(98, 114, 164);
        }
        QPushButton #btn_save {
            color: blue;
            background-color: rgb(98, 114, 164);
        }
        QPushButton #btn_save:vertical {
            color: orange;
            width: 10px;
            background-color: rgb(98, 114, 164);
        }
        QPushButton #btn_save:vertical {
            color: blue;
            font-size: 10px;
            background-color: rgb(98, 114, 164);
        }
        QPushButton #btn_save:hover:!selected {
            background-color: rgb(52, 59, 72);
        }
        QPushButton #btn_save:hover:!selected {
            color: green;
        }
        """
        errors: List[str] = parser.check_format(qss)
        self.assertEqual(
            errors, [], "Valid QSS with attribute selector should return no errors"
        )

        parser.parse(qss)
        self.assertEqual(
            len(parser._state.rules),
            5,
            "Should parse four unique rules after merging duplicates",
        )
        hover_rule = next(
            (
                r
                for r in parser._state.rules
                if r.selector == 'QPushButton #btn_save[selected="true"]:hover'
            ),
            None,
        )
        self.assertIsNotNone(hover_rule, "Hover rule should exist")
        self.assertEqual(
            len(hover_rule.properties), 3, "Hover rule should have three properties"
        )
        self.assertEqual(hover_rule.properties[0].name, "border-left")
        self.assertEqual(
            hover_rule.properties[0].value,
            "22px solid qlineargradient(spread:pad, x1:0.034, y1:0, x2:0.216, y2:0, stop:0.499 rgba(255, 121, 198, 255), stop:0.5 rgba(85, 170, 255, 0))",
        )
        self.assertEqual(hover_rule.properties[1].name, "background-color")
        self.assertEqual(
            hover_rule.properties[1].value,
            "rgb(97, 114, 164)",
            "Should retain the last background-color value",
        )
        self.assertEqual(hover_rule.properties[2].name, "color")
        self.assertEqual(
            hover_rule.properties[2].value, "red", "Should retain the last color value"
        )

        widget: Mock = Mock()
        widget.objectName.return_value = "btn_save"
        widget.metaObject.return_value.className.return_value = "QPushButton"
        stylesheet: str = parser.get_styles_for(widget)
        expected: str = """QPushButton #btn_save {
    color: blue;
    background-color: rgb(98, 114, 164);
}
QPushButton #btn_save:hover:!selected {
    background-color: rgb(52, 59, 72);
    color: green;
}
QPushButton #btn_save:vertical {
    color: blue;
    width: 10px;
    background-color: rgb(98, 114, 164);
    font-size: 10px;
}
QPushButton #btn_save[selected="true"]:hover {
    border-left: 22px solid qlineargradient(spread:pad, x1:0.034, y1:0, x2:0.216, y2:0, stop:0.499 rgba(255, 121, 198, 255), stop:0.5 rgba(85, 170, 255, 0));
    background-color: rgb(97, 114, 164);
    color: red;
}
QPushButton #btn_save[selected="true"]:hover::pressed {
    color: blue;
    background-color: rgb(98, 114, 152);
    font-size: 10px;
}"""
        self.assertEqual(stylesheet.strip(), expected.strip())

    def test_get_styles_with_empty_id_and_fallback_and_additional_selector(
        self,
    ) -> None:
        """
        Test style retrieval for a selector with class and id with attribute and pseudo-state.
        """
        parser: QSSParser = QSSParser()
        qss: str = """
        #myButton {
            color: red;
        }
        QPushButton {
            background: blue;
        }
        QPushButton:hover {
            background: green;
        }
        QScrollBar:hover {
            background: blue;
        }
        QFrame {
            background: yellow;
        }
        """
        errors: List[str] = parser.check_format(qss)
        self.assertEqual(
            errors, [], "Valid QSS with attribute selector should return no errors"
        )

        parser.parse(qss)
        self.assertEqual(
            len(parser._state.rules),
            5,
            "Should parse one rule and one base rule without pseudo-states",
        )
        self.assertEqual(
            parser._state.rules[0].selector,
            "#myButton",
        )
        self.assertEqual(len(parser._state.rules[0].properties), 1)
        self.assertEqual(parser._state.rules[0].properties[0].name, "color")
        self.assertEqual(
            parser._state.rules[0].properties[0].value,
            "red",
        )
        widget: Mock = Mock()
        widget.objectName.return_value = "QFrame btn_save"
        widget.metaObject.return_value.className.return_value = "QPushButton"
        stylesheet: str = parser.get_styles_for(widget, "QScrollBar", ["QFrame"])
        expected: str = """
QFrame {
    background: yellow;
}
QPushButton {
    background: blue;
}
QPushButton:hover {
    background: green;
}
"""
        self.assertEqual(stylesheet.strip(), expected.strip())

    def test_get_styles_for_complex_hierarchical_selector(self) -> None:
        """
        Test style retrieval with a complex hierarchical selector.
        """
        parser: QSSParser = QSSParser()
        qss: str = """
        QWidget > QFrame QPushButton #myButton:hover {
            border: 2px solid red;
        }
        """
        parser.parse(qss)
        widget: Mock = Mock()
        widget.objectName.return_value = "myButton"
        widget.metaObject.return_value.className.return_value = "QPushButton"
        stylesheet: str = parser.get_styles_for(widget)
        expected: str = """QWidget > QFrame QPushButton #myButton:hover {
    border: 2px solid red;
}"""
        self.assertEqual(stylesheet.strip(), expected.strip())

    def test_get_styles_with_variables_and_fixed_properties(self) -> None:
        """
        Test style retrieval with variables and fixed properties in the same rule.
        """
        parser: QSSParser = QSSParser()
        qss: str = """
        @variables {
            --primary-color: #ff0000;
            --font-size: 16px;
        }
        QPushButton {
            color: var(--primary-color);
            font-size: var(--font-size);
            background: white;
            border: 1px solid black;
        }
        """
        parser.parse(qss)
        widget: Mock = Mock()
        widget.objectName.return_value = ""
        widget.metaObject.return_value.className.return_value = "QPushButton"
        stylesheet: str = parser.get_styles_for(widget)
        expected: str = """QPushButton {
    color: #ff0000;
    font-size: 16px;
    background: white;
    border: 1px solid black;
}"""
        self.assertEqual(stylesheet.strip(), expected.strip())

    def test_get_styles_with_nested_variables_and_fixed_properties(self) -> None:
        """
        Test style retrieval with nested variables and fixed properties.
        """
        parser: QSSParser = QSSParser()
        qss: str = """
        @variables {
            --base-color: #0000ff;
            --primary-color: var(--base-color);
        }
        #myButton {
            color: var(--primary-color);
            background: white;
            padding: 5px;
        }
        """
        parser.parse(qss)
        widget: Mock = Mock()
        widget.objectName.return_value = "myButton"
        widget.metaObject.return_value.className.return_value = "QPushButton"
        stylesheet: str = parser.get_styles_for(widget)
        expected: str = """#myButton {
    color: #0000ff;
    background: white;
    padding: 5px;
}"""
        self.assertEqual(stylesheet.strip(), expected.strip())

    def test_get_styles_with_undefined_variable_and_fixed_properties(self) -> None:
        """
        Test style retrieval with an undefined variable and fixed properties.
        """
        parser: QSSParser = QSSParser()
        errors = []

        def error_handler(error: str) -> None:
            errors.append(error)

        parser.on("error_found", error_handler)
        qss: str = """
        QPushButton {
            color: var(--undefined-color);
            font-size: 14px;
            border: none;
        }
        """
        parser.parse(qss)
        widget: Mock = Mock()
        widget.objectName.return_value = ""
        widget.metaObject.return_value.className.return_value = "QPushButton"
        stylesheet: str = parser.get_styles_for(widget)
        expected: str = """QPushButton {
    color: var(--undefined-color);
    font-size: 14px;
    border: none;
}"""
        self.assertEqual(stylesheet.strip(), expected.strip())
        self.assertEqual(len(errors), 1)
        self.assertTrue("Undefined variables: --undefined-color" in errors[0])

    def test_get_styles_with_variables_and_attribute_selector(self) -> None:
        """
        Test style retrieval with variables in a rule with an attribute selector.
        """
        parser: QSSParser = QSSParser()
        qss: str = """
        @variables {
            --hover-color: #00ff00;
        }
        QPushButton[selected="true"]:hover {
            color: var(--hover-color);
            background: transparent;
            border-radius: 5px;
        }
        """
        parser.parse(qss)
        widget: Mock = Mock()
        widget.objectName.return_value = ""
        widget.metaObject.return_value.className.return_value = "QPushButton"
        stylesheet: str = parser.get_styles_for(widget)
        expected: str = """QPushButton[selected="true"]:hover {
    color: #00ff00;
    background: transparent;
    border-radius: 5px;
}"""
        self.assertEqual(stylesheet.strip(), expected.strip())

    def test_get_styles_with_multiple_rules_and_variables(self) -> None:
        """
        Test style retrieval with multiple rules, some using variables and others not.
        """
        parser: QSSParser = QSSParser()
        qss: str = """
        @variables {
            --primary-color: #ffffff;
            --border-width: 2px;
        }
        #myButton {
            color: var(--primary-color);
            border: var(--border-width) solid black;
        }
        QPushButton {
            background: blue;
            font-size: 12px;
        }
        """
        parser.parse(qss)
        widget: Mock = Mock()
        widget.objectName.return_value = "myButton"
        widget.metaObject.return_value.className.return_value = "QPushButton"
        stylesheet: str = parser.get_styles_for(
            widget, include_class_if_object_name=True
        )
        expected: str = """#myButton {
    color: #ffffff;
    border: 2px solid black;
}
QPushButton {
    background: blue;
    font-size: 12px;
}"""
        self.assertEqual(stylesheet.strip(), expected.strip())

    def test_get_styles_with_variable_and_non_variable_rules(self) -> None:
        """
        Test style retrieval when the QSS contains both variable-based and direct rules.
        Ensures correct resolution and merging of styles for widgets with object names and additional selectors.
        """
        parser: QSSParser = QSSParser()
        qss: str = """
        @variables {
            --primary-color: #ffffff;
            --border-width: 2px;
        }
        #myButton,
        QPushButton {
            color: var(--primary-color);
            border: var(--border-width) solid black;
        }
        QPushButton {
            color: green;
            background: blue;
            font-size: 12px;
        }
        QFrame {
            color: blue;
            background: red;
            font-size: 12px;
        }
        #myButton QFrame {
            color: yellow;
            background: orange;
            font-size: 12px;
        }
        """
        parser.parse(qss)
        widget: Mock = Mock()
        widget.objectName.return_value = "myButton"
        widget.metaObject.return_value.className.return_value = "QPushButton"
        stylesheet: str = parser.get_styles_for(
            widget, include_class_if_object_name=True, additional_selectors=["QFrame"]
        )
        expected: str = """#myButton {
    color: #ffffff;
    border: 2px solid black;
}
QFrame {
    color: blue;
    background: red;
    font-size: 12px;
}
QPushButton {
    color: green;
    border: 2px solid black;
    background: blue;
    font-size: 12px;
}"""
        self.assertEqual(stylesheet.strip(), expected.strip())


class TestQSSParserEvents(unittest.TestCase):
    def setUp(self) -> None:
        """
        Set up the test environment for event tests.
        """
        self.parser: QSSParser = QSSParser()
        self.qss: str = """
        QPushButton {
            color: blue;
        }
        #myButton {
            font-size: 12px;
        }
        """

    def test_event_rule_added(self) -> None:
        """
        Test the rule_added event.
        """
        rules_added: List[QSSRule] = []
        self.parser.on("rule_added", lambda rule: rules_added.append(rule))
        self.parser.parse(self.qss)
        self.assertEqual(len(rules_added), 2, "Should trigger rule_added for each rule")
        selectors: Set[str] = {rule.selector for rule in rules_added}
        self.assertEqual(
            selectors, {"QPushButton", "#myButton"}, "Should capture all selectors"
        )

    def test_event_error_found(self) -> None:
        """
        Test the error_found event.
        """
        errors_found: List[str] = []
        self.parser.on("error_found", lambda error: errors_found.append(error))
        qss: str = """
        QPushButton {
            color: blue
        }
        """
        self.parser.check_format(qss)
        self.assertEqual(len(errors_found), 1, "Should trigger error_found")
        self.assertIn("Property missing ';'", errors_found[0])

    def test_multiple_event_handlers(self) -> None:
        """
        Test multiple handlers for the rule_added event.
        """
        rules_added_1: List[QSSRule] = []
        rules_added_2: List[QSSRule] = []
        self.parser.on("rule_added", lambda rule: rules_added_1.append(rule))
        self.parser.on("rule_added", lambda rule: rules_added_2.append(rule))
        self.parser.parse(self.qss)
        self.assertEqual(
            len(rules_added_1), 2, "First handler should capture all rules"
        )
        self.assertEqual(
            len(rules_added_2), 2, "Second handler should capture all rules"
        )

    def test_event_error_found_multiple(self) -> None:
        """
        Test multiple handlers for the error_found event.
        """
        errors_found_1: List[str] = []
        errors_found_2: List[str] = []
        self.parser.on("error_found", lambda error: errors_found_1.append(error))
        self.parser.on("error_found", lambda error: errors_found_2.append(error))
        qss: str = """
        QPushButton {
            color: blue
        }
        """
        self.parser.check_format(qss)
        self.assertEqual(len(errors_found_1), 1, "First handler should capture error")
        self.assertEqual(len(errors_found_2), 1, "Second handler should capture error")

    def test_event_rule_added_with_pseudo(self) -> None:
        """
        Test the rule_added event with pseudo-states and pseudo-elements.
        """
        qss: str = """
        QPushButton {
            color: blue;
        }
        #myButton {
            font-size: 12px;
        }
        QPushButton:hover {
            background: green;
        }
        QScrollBar::vertical {
            background: yellow;
        }
        """
        rules_added: List[QSSRule] = []
        self.parser.on("rule_added", lambda rule: rules_added.append(rule))
        self.parser.parse(qss)
        self.assertEqual(
            len(rules_added),
            5,
            "Should trigger rule_added for each rule including base rules",
        )
        selectors: Set[str] = {rule.selector for rule in rules_added}
        self.assertEqual(
            selectors,
            {
                "QPushButton",
                "#myButton",
                "QPushButton:hover",
                "QScrollBar::vertical",
                "QPushButton",
            },
            "Should capture all selectors including base rule for pseudo-state",
        )

    def test_event_rule_added_multiple_selectors(self) -> None:
        """
        Test the rule_added event for a rule with multiple selectors.
        """
        qss: str = """
        QPushButton, QFrame {
            color: blue;
        }
        """
        rules_added: List[QSSRule] = []
        self.parser.on("rule_added", lambda rule: rules_added.append(rule))
        self.parser.parse(qss)
        self.assertEqual(
            len(rules_added), 2, "Should trigger rule_added for each selector"
        )
        selectors: Set[str] = {rule.selector for rule in rules_added}
        self.assertEqual(
            selectors, {"QPushButton", "QFrame"}, "Should capture all selectors"
        )

    def test_event_variable_defined(self) -> None:
        """
        Test the variable_defined event.
        """
        variables_defined: List[tuple[str, str]] = []
        self.parser.on(
            "variable_defined",
            lambda name, value: variables_defined.append((name, value)),
        )
        qss: str = """
        @variables {
            --color: blue;
        }
        """
        self.parser.parse(qss)
        self.assertEqual(len(variables_defined), 1, "Should trigger variable_defined")
        self.assertEqual(variables_defined[0], ("--color", "blue"))

    def test_event_parse_completed(self) -> None:
        """
        Test the parse_completed event.
        """
        parse_completed: bool = False

        def on_parse_completed() -> None:
            nonlocal parse_completed
            parse_completed = True

        self.parser.on("parse_completed", on_parse_completed)
        self.parser.parse(self.qss)
        self.assertTrue(parse_completed, "Should trigger parse_completed")

    def test_event_invalid_rule_skipped(self) -> None:
        """
        Test the invalid_rule_skipped event.
        """
        invalid_rules: List[str] = []
        self.parser.on("invalid_rule_skipped", lambda rule: invalid_rules.append(rule))
        qss: str = """
        QPushButton {
            color: blue
        """
        self.parser.parse(qss)
        self.assertEqual(len(invalid_rules), 1, "Should trigger invalid_rule_skipped")
        self.assertIn("color: blue", invalid_rules[0])


class TestQSSParserToString(unittest.TestCase):
    """Test cases for the to_string() method of QSSParser."""

    def setUp(self) -> None:
        """Set up a new instance for each test."""
        self.parser = QSSParser()
        self.validator = QSSValidator()

    def test_to_string_simple_rule(self) -> None:
        """Test to_string() with a simple QSS rule."""
        qss = """
        QPushButton {
            color: blue;
            background: white;
        }
        """
        self.parser.parse(qss)
        expected = "QPushButton {\n    color: blue;\n    background: white;\n}\n"
        self.assertEqual(
            self.parser.to_string(),
            expected,
            "to_string should format a simple rule with semicolons",
        )

    def test_to_string_multiple_selectors(self) -> None:
        """Test to_string() with multiple comma-separated selectors."""
        qss = """
        #myButton, QFrame, .customClass {
            font-size: 12px;
            border: 1px solid black;
        }
        """
        self.parser.parse(qss)
        expected = (
            "#myButton {\n    font-size: 12px;\n    border: 1px solid black;\n}\n\n"
            "QFrame {\n    font-size: 12px;\n    border: 1px solid black;\n}\n\n"
            ".customClass {\n    font-size: 12px;\n    border: 1px solid black;\n}\n"
        )
        self.assertEqual(
            self.parser.to_string(),
            expected,
            "to_string should handle multiple selectors correctly",
        )

    def test_to_string_with_variables(self) -> None:
        """Test to_string() with a QSS rule using variables."""
        qss = """
        @variables {
            --primary-color: #ff0000;
            --font-size: 14px;
        }
        QPushButton {
            color: var(--primary-color);
            font-size: var(--font-size);
        }
        """
        self.parser.parse(qss)
        expected = "QPushButton {\n    color: #ff0000;\n    font-size: 14px;\n}\n"
        self.assertEqual(
            self.parser.to_string(),
            expected,
            "to_string should resolve variables and format with semicolons",
        )

    def test_to_string_with_pseudo_state(self) -> None:
        """Test to_string() with a rule containing a pseudo-state."""
        qss = """
        QPushButton:hover {
            background: yellow;
            border: none;
        }
        """
        self.parser.parse(qss)
        expected = (
            "QPushButton:hover {\n    background: yellow;\n    border: none;\n}\n"
        )
        self.assertEqual(
            self.parser.to_string(),
            expected,
            "to_string should handle pseudo-states correctly",
        )

    def test_to_string_with_attribute_selector(self) -> None:
        """Test to_string() with a rule using an attribute selector."""
        qss = """
        QPushButton[data-value="special"] {
            color: green;
            padding: 5px;
        }
        """
        self.parser.parse(qss)
        expected = 'QPushButton[data-value="special"] {\n    color: green;\n    padding: 5px;\n}\n'
        self.assertEqual(
            self.parser.to_string(),
            expected,
            "to_string should handle attribute selectors correctly",
        )

    def test_to_string_multiple_rules(self) -> None:
        """Test to_string() with multiple distinct rules."""
        qss = """
        #myButton {
            color: red;
        }
        QFrame {
            border: 2px solid blue;
        }
        .customClass {
            font-weight: bold;
        }
        """
        self.parser.parse(qss)
        expected = (
            "#myButton {\n    color: red;\n}\n\n"
            "QFrame {\n    border: 2px solid blue;\n}\n\n"
            ".customClass {\n    font-weight: bold;\n}\n"
        )
        self.assertEqual(
            self.parser.to_string(),
            expected,
            "to_string should handle multiple distinct rules",
        )

    def test_to_string_outputs_multiple_independent_rules_correctly(self) -> None:
        """
        Tests whether the to_string() method correctly returns multiple distinct QSS rules,
        each with its own selector and without any combination between them.
        Checks that the expected order and formatting are preserved.
        """
        self.maxDiff = None
        qss = """
        QComboBox QAbstractItemView {
            background-color: purple;
            border: 1px solid rgb(98, 114, 164);
            color: yellow;
            font-size: 12pt;
            font-family: Segoe UI;
            padding: 10px;
            selection-background-color: rgb(39, 44, 54);
            show-decoration-selected: 0;
            outline: none;
        }
        QComboBox QScrollBar {
            background-color: red;
            border: 1px solid rgb(98, 114, 164);
            color: purple;
            font-size: 12pt;
            font-family: Arial;
            padding: 10px;
            selection-background-color: rgb(39, 44, 54);
            show-decoration-selected: 0;
            outline: none;
        }
        QComboBox {
            background-color: green;
            border: 1px solid rgb(98, 114, 164);
            color: red;
            font-size: 12pt;
            font-family: Times New Roman;
            padding: 10px;
        }
        QComboBox {
            background-color: blue;
            border: 1px solid rgb(98, 114, 164);
            color: green;
            font-size: 12pt;
            font-family: Comic Sans MS;
            padding: 10px;
            selection-background-color: rgb(39, 44, 54);
            show-decoration-selected: 0;
            outline: none;
        }"""
        self.parser.parse(qss)
        expected = """QComboBox QAbstractItemView {
    background-color: purple;
    border: 1px solid rgb(98, 114, 164);
    color: yellow;
    font-size: 12pt;
    font-family: Segoe UI;
    padding: 10px;
    selection-background-color: rgb(39, 44, 54);
    show-decoration-selected: 0;
    outline: none;
}

QComboBox QScrollBar {
    background-color: red;
    border: 1px solid rgb(98, 114, 164);
    color: purple;
    font-size: 12pt;
    font-family: Arial;
    padding: 10px;
    selection-background-color: rgb(39, 44, 54);
    show-decoration-selected: 0;
    outline: none;
}

QComboBox {
    background-color: blue;
    border: 1px solid rgb(98, 114, 164);
    color: green;
    font-size: 12pt;
    font-family: Comic Sans MS;
    padding: 10px;
    selection-background-color: rgb(39, 44, 54);
    show-decoration-selected: 0;
    outline: none;
}
"""
        self.assertEqual(
            self.parser.to_string(),
            expected,
            "to_string should handle multiple distinct rules",
        )

    def test_to_string_merges_and_splits_multiple_overlapping_selectors_correctly(
        self,
    ) -> None:
        """
        Tests whether to_string() correctly merges properties from multiple rules
        and splits comma-separated selectors into distinct blocks with the appropriate
        combined declarations.
        Ensures that overlapping selectors are handled correctly and order is preserved.
        """
        self.maxDiff = None
        qss = """
        #btn_home, QPushButton, #btn_save {
            background-color: red;
            border: 2px;
            padding: 10px;
            color: red;
            text-align: left;
        }
        #btn_home,
        QPushButton {
            background-color: green;
            border: none;

        }
        #btn_save {
            background-color: purple;
            text-align: right;

        }"""
        self.parser.parse(qss)
        expected = """#btn_home {
    background-color: green;
    border: none;
    padding: 10px;
    color: red;
    text-align: left;
}

QPushButton {
    background-color: green;
    border: none;
    padding: 10px;
    color: red;
    text-align: left;
}

#btn_save {
    background-color: purple;
    border: 2px;
    padding: 10px;
    color: red;
    text-align: right;
}
"""
        self.assertEqual(
            self.parser.to_string(),
            expected,
            "to_string should handle multiple distinct rules",
        )

    def test_to_string_resolves_variables_and_expands_composite_selectors_correctly(
        self,
    ) -> None:
        """
        Tests whether to_string() correctly resolves variables defined in @variables blocks
        and applies them to the appropriate rules.
        Also checks that selectors with pseudo-states and compound structure
        (e.g., #id .class:hover) are maintained with substituted values.
        """
        self.maxDiff = None
        qss = """
        @variables {
            --primary-color: purple;
            --font-family: "Segoe UI";
            --font-size: 10pt;
        }
        #topMenu .QPushButton {
            background-position: left center;
            background-repeat: no-repeat;
            border: none;
            font-family: var(--font-family);
            font-size: var(--font-size);
            background-color: var(--primary-color);
            text-align: left;
        }
        #topMenu .QPushButton:hover {
            font-size: var(--font-size);
        }
        #topMenu .QPushButton:pressed {
            background-color: red;
            color: var(--primary-color);
        }"""
        self.parser.parse(qss)
        expected = """#topMenu .QPushButton {
    background-position: left center;
    background-repeat: no-repeat;
    border: none;
    font-family: "Segoe UI";
    font-size: 10pt;
    background-color: purple;
    text-align: left;
}

#topMenu .QPushButton:hover {
    font-size: 10pt;
}

#topMenu .QPushButton:pressed {
    background-color: red;
    color: purple;
}
"""
        self.assertEqual(
            self.parser.to_string(),
            expected,
            "to_string should handle multiple distinct rules",
        )

    def test_to_string_empty_qss(self) -> None:
        """Test to_string() with empty QSS input."""
        qss = ""
        self.parser.parse(qss)
        expected = ""
        self.assertEqual(
            self.parser.to_string(),
            expected,
            "to_string should return empty string for empty QSS",
        )

    def test_to_string_comments_only(self) -> None:
        """Test to_string() with QSS containing only comments."""
        qss = """
        /* This is a comment */
        /* Another comment */
        """
        self.parser.parse(qss)
        expected = ""
        self.assertEqual(
            self.parser.to_string(),
            expected,
            "to_string should return empty string for QSS with only comments",
        )

    def test_to_string_complex_nested_selectors(self) -> None:
        """Test to_string() with complex nested selectors."""
        qss = """
        QFrame > QPushButton#myButton[data-value="nested"] {
            color: purple;
            margin: 10px;
        }
        """
        self.parser.parse(qss)
        expected = 'QFrame > QPushButton#myButton[data-value="nested"] {\n    color: purple;\n    margin: 10px;\n}\n'
        self.assertEqual(
            self.parser.to_string(),
            expected,
            "to_string should handle complex nested selectors",
        )


if __name__ == "__main__":
    unittest.main()
