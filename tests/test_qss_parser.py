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
        Test QSS with a valid single-line rule.
        """
        qss: str = """
        #titleLeftApp { font: 12pt "Segoe UI Semibold"; }
        QPushButton { color: blue; }
        #titleApp QPushButton, QScrollbar::handle:vertical { font: 12pt "Segoe UI Semibold"; }
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
            len(self.parser._state.rules), 8, "Should parse all rules correctly"
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
        Test parsing QSS with duplicate properties in a single rule.
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
            "Should keep duplicate properties",
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
            2,
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
            2,
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
            7,
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


if __name__ == "__main__":
    unittest.main()
