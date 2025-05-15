import logging
import os
import sys
import unittest
from typing import List, Set, Tuple
from unittest.mock import Mock

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))
from qss_parser import ParserEvent, QSSParser, QSSRule

logging.basicConfig(level=logging.DEBUG)


class TestQSSParserParsing(unittest.TestCase):
    def setUp(self) -> None:
        """
        Set up the test environment for parsing tests.
        """
        self.parser: QSSParser = QSSParser()
        self.errors: List[str] = []
        self.parser.on(ParserEvent.ERROR_FOUND, lambda error: self.errors.append(error))
        self.qss: str = """
        #myButton {
            color: red;
        }
        QPushButton {
            background: blue;
        }
        QScrollBar {
            background: gray;
            width: 10px
        }
        QScrollBar:vertical {
            background: lightgray;
        }
        QWidget {
            font-size:12px;
        }
        QFrame {
            border: 1px solid black;
        }
        .customClass {
            border-radius: 5px;

        }
        """

    def test_parse_valid_qss(self) -> None:
        """
        Test parsing valid QSS text.
        """
        self.parser.parse(self.qss)
        self.assertEqual(
            len(self.parser._state.rules), 7, "Should parse all rules correctly"
        )
        self.assertEqual(self.errors, [], "Valid QSS should produce no errors")

    def test_parse_empty_qss(self) -> None:
        """
        Test parsing empty QSS text.
        """
        self.parser.parse("")
        self.assertEqual(
            len(self.parser._state.rules), 0, "Empty QSS should result in no rules"
        )
        self.assertEqual(self.errors, [], "Empty QSS should produce no errors")

    def test_parse_comments_only(self) -> None:
        """
        Test parsing QSS with only comments.
        """
        qss: str = """
        /* This is a comment */
        /* Another comment */
        """
        self.parser.parse(qss)
        self.assertEqual(
            len(self.parser._state.rules),
            0,
            "Comments-only QSS should result in no rules",
        )
        self.assertEqual(self.errors, [], "Comments-only QSS should produce no errors")

    def test_parse_missing_semicolon(self) -> None:
        """
        Test parsing QSS with a missing semicolon.
        """
        qss: str = """
        QPushButton {
            color: blue
            background: white;
        }
        """
        self.parser.parse(qss)
        self.assertEqual(
            len(self.parser._state.rules), 1, "Should parse valid properties only"
        )
        self.assertEqual(
            len(self.parser._state.rules[0].properties),
            1,
            "Should only include valid property",
        )
        self.assertEqual(self.parser._state.rules[0].properties[0].name, "background")
        self.assertEqual(
            self.errors,
            ["Error on line 3: Property missing ';': color: blue"],
            "Should report missing semicolon",
        )

    def test_parse_single_unclosed_rule(self) -> None:
        qss: str = """
        QPushButton {
            color: blue;
        """
        self.parser.parse(qss)
        self.assertEqual(len(self.parser._state.rules), 0)
        self.assertEqual(self.parser.to_string(), "")
        self.assertEqual(len(self.errors), 1)
        self.assertEqual(
            self.errors[0],
            "Error on line 2: Unclosed brace '{' for selector: QPushButton",
        )

    def test_parse_unclosed_brace(self) -> None:
        """
        Test parsing QSS with an unclosed brace.
        """
        qss: str = """
        QPushButton {
            color: blue;
            background: white;
        #myButton {
            font-size: 12px;
        """
        self.parser.parse(qss)
        self.assertEqual(
            len(self.parser._state.rules),
            0,
            "No rules should be parsed due to unclosed braces",
        )
        self.assertEqual(
            self.parser.to_string(),
            "",
            "to_string should return empty string for invalid QSS",
        )
        self.assertEqual(
            len(self.errors),
            2,
            "Should report unclosed brace errors for both selectors",
        )
        self.assertEqual(
            self.errors[0],
            "Error on line 2: Unclosed brace '{' for selector: QPushButton",
            "Should report unclosed brace for QPushButton",
        )
        self.assertEqual(
            self.errors[1],
            "Error on line 5: Unclosed brace '{' for selector: #myButton",
            "Should report unclosed brace #myButton",
        )

    def test_parse_property_outside_block(self) -> None:
        """
        Test parsing QSS with a property outside a block.
        """
        qss: str = """
        color: blue;
        QPushButton {
            background: white;
        }
        """
        self.parser.parse(qss)
        self.assertEqual(
            len(self.parser._state.rules), 1, "Should parse valid rule only"
        )
        self.assertEqual(self.parser._state.rules[0].selector, "QPushButton")
        self.assertEqual(
            self.errors,
            ["Error on line 2: Property outside block: color: blue;"],
            "Should report property outside block",
        )

    def test_parse_empty_selector(self) -> None:
        """
        Test parsing QSS with an empty selector.
        """
        qss: str = """
        {
            color: blue;
        }
        """
        self.parser.parse(qss)
        self.assertEqual(
            len(self.parser._state.rules), 0, "Empty selector should not produce a rule"
        )
        self.assertEqual(
            self.errors,
            ["Error on line 2: Empty selector before '{': {"],
            "Should report empty selector",
        )

    def test_parse_invalid_pseudo_spacing(self) -> None:
        """
        Test parsing QSS with invalid spacing before pseudo-_states.
        """
        qss: str = """
        #btn_save :hover {
            color: blue;
        }
        """
        self.parser.parse(qss)
        self.assertEqual(
            len(self.parser._state.rules),
            0,
            "Invalid selector should not produce a rule",
        )
        self.assertEqual(
            self.errors,
            [
                "Error on line 2: Invalid spacing in selector: '#btn_save :hover'. No space allowed between '#btn_save' and ':hover' (pseudo-state)"
            ],
            "Should report invalid pseudo spacing",
        )

    def test_parse_duplicate_selectors(self) -> None:
        """
        Test parsing QSS with duplicate selectors.
        """
        qss: str = """
        QPushButton, QPushButton, QFrame {
            color: blue;
        }
        """
        self.parser.parse(qss)
        self.assertEqual(
            len(self.parser._state.rules), 2, "Should parse unique selectors only"
        )
        selectors: Set[str] = {rule.selector for rule in self.parser._state.rules}
        self.assertEqual(selectors, {"QPushButton", "QFrame"})

    def test_parse_invalid_property_name(self) -> None:
        """
        Test parsing QSS with invalid property names.
        """
        qss: str = """
        QPushButton {
            123color: blue;
            -color: red;
        }
        """
        self.parser.parse(qss)
        self.assertEqual(
            len(self.parser._state.rules),
            1,
            "Should parse rule but skip invalid properties",
        )
        self.assertEqual(
            len(self.parser._state.rules[0].properties),
            0,
            "Should skip invalid properties",
        )
        self.assertEqual(
            self.errors,
            [
                "Error on line 3: Invalid property name: '123color'",
                "Error on line 4: Invalid property name: '-color'",
            ],
            "Should report invalid property names",
        )

    def test_parse_multiple_selectors(self) -> None:
        """
        Test parsing QSS with multiple comma-separated selectors.
        """
        qss: str = """
        QPushButton, QFrame, .customClass {
            color: blue;
        }
        """
        self.parser.parse(qss)
        self.assertEqual(
            len(self.parser._state.rules),
            3,
            "Should parse multiple selectors as separate rules",
        )
        selectors: Set[str] = {rule.selector for rule in self.parser._state.rules}
        self.assertEqual(selectors, {"QPushButton", "QFrame", ".customClass"})
        self.assertEqual(
            self.errors, [], "Valid multiple selectors should produce no errors"
        )

    def test_parse_multiple_selectors_with_pseudo_state(self) -> None:
        """
        Test parsing QSS with multiple selectors including pseudo-_states.
        """
        qss: str = """
        #myButton:hover, QFrame:disabled, #secondButton QPushButton, #anyButton QCheckBox::drop-down:disabled {
            color: red;
            width: 15px;
            height: 15px;
            border-radius: 10px;
        }
        """
        self.parser.parse(qss)
        self.assertEqual(
            len(self.parser._state.rules),
            4,
            "Pseudo-states in comma-separated selectors should accept",
        )
        self.assertEqual(
            len(self.parser._state.rules[0].properties),
            4,
            "Pseudo-states in comma-separated selectors should accept",
        )
        self.assertEqual(
            self.errors,
            [],
            "Should not report pseudo-state error",
        )

    def test_parse_attribute_selector_complex(self) -> None:
        """
        Test parsing QSS with a complex attribute selector.
        """
        qss: str = """
        QPushButton[data-value="complex string with spaces"] {
            color: blue;
        }
        """
        self.parser.parse(qss)
        self.assertEqual(len(self.parser._state.rules), 1, "Should parse one rule")
        rule: QSSRule = self.parser._state.rules[0]
        self.assertEqual(
            rule.selector, 'QPushButton[data-value="complex string with spaces"]'
        )
        self.assertEqual(rule.attributes, ['[data-value="complex string with spaces"]'])
        self.assertEqual(len(rule.properties), 1)
        self.assertEqual(rule.properties[0].name, "color")
        self.assertEqual(rule.properties[0].value, "blue")
        self.assertEqual(
            self.errors, [], "Valid attribute selector should produce no errors"
        )

    def test_parse_variables_block(self) -> None:
        """
        Test parsing a @variables block and resolving variables.
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
        self.parser.parse(qss)
        self.assertEqual(len(self.parser._state.rules), 1, "Should parse one rule")
        rule: QSSRule = self.parser._state.rules[0]
        self.assertEqual(rule.selector, "QPushButton")
        self.assertEqual(len(rule.properties), 2)
        self.assertEqual(rule.properties[0].name, "color")
        self.assertEqual(rule.properties[0].value, "#ffffff")
        self.assertEqual(rule.properties[1].name, "font-size")
        self.assertEqual(rule.properties[1].value, "14px")
        self.assertEqual(
            self.errors, [], "Valid variables block should produce no errors"
        )

    def test_parse_malformed_variables_block(self) -> None:
        """
        Test parsing a malformed @variables block.
        """
        qss: str = """
        @variables {
            primary-color: #ffffff;
            --font-size: 14px;
            --color: #bbbbbb
        }
        QPushButton {
            color: var(--primary-color);
            background: red;
            font-size: var(--font-size);

        }
        """
        self.parser.parse(qss)
        self.assertEqual(len(self.parser._state.rules), 1, "Should parse valid rule")
        rule: QSSRule = self.parser._state.rules[0]
        print(self.parser.to_string())
        self.assertEqual(rule.properties[0].value, "red")
        self.assertEqual(rule.properties[1].value, "14px")
        self.assertEqual(len(self.errors), 2, "Should report two errors")
        self.assertTrue(
            "Invalid variable name" in self.errors[0],
            "Should report invalid variable name",
        )
        self.assertTrue(
            "Undefined variables" in self.errors[1],
            "Should report invalid variable name",
        )

    def test_parse_undefined_variable(self) -> None:
        """
        Test parsing QSS with an undefined variable.
        """
        qss: str = """
        QPushButton {
            color: var(--undefined-color);
        }
        """
        self.parser.parse(qss)
        self.assertEqual(len(self.parser._state.rules), 1, "Should parse one rule")
        rule: QSSRule = self.parser._state.rules[0]
        self.assertEqual(len(rule.properties), 0, "Should not parse properties")
        self.assertEqual(len(self.errors), 1, "Should report one error")
        self.assertTrue("Undefined variables: --undefined-color" in self.errors[0])

    def test_parse_circular_variable_references(self) -> None:
        """
        Test parsing QSS with circular variable references.
        """
        qss: str = """
        @variables {
            --a: var(--b);
            --b: var(--a);
            --c: #ffffff;
            --d: var(--c);
        }
        QPushButton {
            color: var(--a);
            background: var(--c);
            border: var(--d);
        }
        """
        self.parser.parse(qss)
        self.assertEqual(len(self.parser._state.rules), 1, "Should parse one rule")
        self.assertEqual(len(self.errors), 1, "Should report circular reference")
        self.assertIn("Circular variable reference detected", self.errors[0])

    def test_parse_complex_hierarchical_selector(self) -> None:
        """
        Test parsing QSS with complex hierarchical selectors.
        """
        qss: str = """
        QWidget > QFrame > QPushButton:hover {
            border: 1px solid green;
        }
        """
        self.parser.parse(qss)
        self.assertEqual(len(self.parser._state.rules), 1, "Should parse one rule")
        rule: QSSRule = self.parser._state.rules[0]
        self.assertEqual(rule.selector, "QWidget > QFrame > QPushButton:hover")
        self.assertEqual(len(rule.properties), 1)
        self.assertEqual(rule.properties[0].name, "border")
        self.assertEqual(rule.properties[0].value, "1px solid green")
        self.assertEqual(
            self.errors, [], "Valid hierarchical selector should produce no errors"
        )

    def test_parse_invalid_pseudo_element(self) -> None:
        qss = """
        QPushButton::before {
            content: "test";
        }
        """
        self.parser.parse(qss)
        self.assertEqual(
            len(self.parser._state.rules),
            0,
            "Rule with invalid pseudo-element should not be parsed",
        )
        self.assertEqual(len(self.errors), 1, "Should report one error")
        self.assertTrue(
            "Invalid pseudo-element '::before'" in self.errors[0],
            "Should report invalid pseudo-element",
        )
        self.assertEqual(self.parser.to_string(), "", "Should return empty string")

    def test_parse_invalid_pseudo_state(self) -> None:
        qss = """
        QPushButton:invalid {
            color: blue;
        }
        """
        self.parser.parse(qss)
        self.assertEqual(
            len(self.parser._state.rules),
            0,
            "Rule with invalid pseudo-state should not be parsed",
        )
        self.assertEqual(len(self.errors), 1, "Should report one error")
        self.assertTrue(
            "Invalid pseudo-state ':invalid'" in self.errors[0],
            "Should report invalid pseudo-state",
        )
        self.assertEqual(self.parser.to_string(), "", "Should return empty string")

    def test_parse_variables_block_single_line(self) -> None:
        """
        Test parsing a single-line QSS rule with multiple properties and variables.
        """
        qss: str = """
        @variables {
            --primary-color: #ffffff;
            --border-radius: 14px;
        }
        #extraCloseColumnBtn { background-color: rgba(248, 248, 242, 0); border: none; border-radius: var(--border-radius); color: var(--primary-color); }
        """
        self.parser.parse(qss)
        self.assertEqual(len(self.parser._state.rules), 1, "Should parse one rule")
        rule = self.parser._state.rules[0]
        self.assertEqual(rule.selector, "#extraCloseColumnBtn")
        self.assertEqual(len(rule.properties), 4, "Should parse all four properties")
        self.assertEqual(rule.properties[0].name, "background-color")
        self.assertEqual(rule.properties[0].value, "rgba(248, 248, 242, 0)")
        self.assertEqual(rule.properties[1].name, "border")
        self.assertEqual(rule.properties[1].value, "none")
        self.assertEqual(rule.properties[2].name, "border-radius")
        self.assertEqual(rule.properties[2].value, "14px")
        self.assertEqual(rule.properties[3].name, "color")
        self.assertEqual(rule.properties[3].value, "#ffffff")
        self.assertEqual(self.errors, [], "Single-line rule should produce no errors")

    def test_parse_single_line_multiple_properties(self) -> None:
        """
        Test parsing a single-line QSS rule with multiple properties.
        """
        qss = """
        #extraCloseColumnBtn { background-color: rgba(248, 248, 242, 0); border: none; border-radius: 14px; color: #ffffff; }
        """
        self.parser.parse(qss)
        self.assertEqual(len(self.parser._state.rules), 1, "Should parse one rule")
        rule = self.parser._state.rules[0]
        self.assertEqual(rule.selector, "#extraCloseColumnBtn")
        self.assertEqual(len(rule.properties), 4, "Should parse all four properties")
        self.assertEqual(rule.properties[0].name, "background-color")
        self.assertEqual(rule.properties[0].value, "rgba(248, 248, 242, 0)")
        self.assertEqual(rule.properties[1].name, "border")
        self.assertEqual(rule.properties[1].value, "none")
        self.assertEqual(rule.properties[2].name, "border-radius")
        self.assertEqual(rule.properties[2].value, "14px")
        self.assertEqual(rule.properties[3].name, "color")
        self.assertEqual(rule.properties[3].value, "#ffffff")
        self.assertEqual(self.errors, [], "Single-line rule should produce no errors")

    def test_parsing_multiple_selectors_separate_with_comma_in_single_line_with_pseudo_state(
        self,
    ) -> None:
        """
        Test parsing QSS with multiple selectors including pseudo-_states.
        """
        qss: str = """
        #myButton:hover, QFrame:disabled,  #secondButton QPushButton, #anyButton QCheckBox::drop-down:disabled {
            color: red;
            width: 15px;
            height: 15px;
            border-radius: 10px;
        }
        """
        self.parser.parse(qss)
        self.assertEqual(len(self.parser._state.rules), 4, "Should parse 4 rule")
        rule = self.parser._state.rules[3]
        self.assertEqual(rule.selector, "#anyButton QCheckBox::drop-down:disabled")
        self.assertEqual(rule.pseudo_states[0], "disabled", "Should have pseudo-state")
        self.assertEqual(len(rule.properties), 4, "Should parse all four properties")
        self.assertEqual(rule.properties[0].name, "color")
        self.assertEqual(rule.properties[0].value, "red")
        self.assertEqual(rule.properties[1].name, "width")
        self.assertEqual(rule.properties[1].value, "15px")
        self.assertEqual(rule.properties[2].name, "height")
        self.assertEqual(rule.properties[2].value, "15px")
        self.assertEqual(rule.properties[3].name, "border-radius")
        self.assertEqual(rule.properties[3].value, "10px")
        self.assertEqual(self.errors, [], "Single-line rule should produce no errors")

    def test_parsing_multiple_selectors_separate_with_comma_all_single_line_with_pseudo_state(
        self,
    ) -> None:
        """
        Test parsing QSS with multiple selectors including pseudo-_states.
        """
        qss: str = """
        #myButton:hover, QFrame:disabled,  #secondButton QPushButton, #anyButton QCheckBox::drop-down:disabled { color: red; width: 15px; height: 15px; border-radius: 10px;}
        """
        self.parser.parse(qss)
        self.assertEqual(len(self.parser._state.rules), 4, "Should parse 4 rule")
        rule = self.parser._state.rules[3]
        self.assertEqual(rule.selector, "#anyButton QCheckBox::drop-down:disabled")
        self.assertEqual(rule.pseudo_states[0], "disabled", "Should have pseudo-state")
        self.assertEqual(len(rule.properties), 4, "Should parse all four properties")
        self.assertEqual(rule.properties[0].name, "color")
        self.assertEqual(rule.properties[0].value, "red")
        self.assertEqual(rule.properties[1].name, "width")
        self.assertEqual(rule.properties[1].value, "15px")
        self.assertEqual(rule.properties[2].name, "height")
        self.assertEqual(rule.properties[2].value, "15px")
        self.assertEqual(rule.properties[3].name, "border-radius")
        self.assertEqual(rule.properties[3].value, "10px")
        self.assertEqual(self.errors, [], "Single-line rule should produce no errors")

    def test_parsing_multiple_selectors_separate_with_comma_in_each_line_with_pseudo_state(
        self,
    ) -> None:
        """
        Test parsing QSS with multiple selectors including pseudo-_states.
        """
        qss: str = """
        #myButton:hover,
        QFrame:disabled,
        #secondButton QPushButton,
        #anyButton QCheckBox::drop-down:disabled {
            color: red;
            width: 15px;
            height: 15px;
            border-radius: 10px;
        }
        """
        self.parser.parse(qss)
        self.assertEqual(len(self.parser._state.rules), 4, "Should parse 4 rule")
        rule = self.parser._state.rules[3]
        self.assertEqual(rule.selector, "#anyButton QCheckBox::drop-down:disabled")
        self.assertEqual(rule.pseudo_states[0], "disabled", "Should have pseudo-state")
        self.assertEqual(len(rule.properties), 4, "Should parse all four properties")
        self.assertEqual(rule.properties[0].name, "color")
        self.assertEqual(rule.properties[0].value, "red")
        self.assertEqual(rule.properties[1].name, "width")
        self.assertEqual(rule.properties[1].value, "15px")
        self.assertEqual(rule.properties[2].name, "height")
        self.assertEqual(rule.properties[2].value, "15px")
        self.assertEqual(rule.properties[3].name, "border-radius")
        self.assertEqual(rule.properties[3].value, "10px")
        self.assertEqual(self.errors, [], "Single-line rule should produce no errors")


class TestQSSParserStyleSelection(unittest.TestCase):
    def setUp(self) -> None:
        """
        Set up the test environment for style selection tests.
        """
        self.parser: QSSParser = QSSParser()
        self.errors: List[str] = []
        self.parser.on(ParserEvent.ERROR_FOUND, lambda error: self.errors.append(error))
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

    def test_get_styles_for_object_name(self) -> None:
        """
        Test style retrieval by object name.
        """
        stylesheet: str = self.parser.get_styles_for(self.widget)
        expected: str = """#myButton {
    color: red;
}"""
        self.assertEqual(stylesheet.strip(), expected.strip())
        self.assertEqual(
            self.errors, [], "Valid style retrieval should produce no errors"
        )

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
        self.assertEqual(
            self.errors, [], "Valid style retrieval should produce no errors"
        )

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
        self.assertEqual(
            self.errors, [], "Valid style retrieval should produce no errors"
        )

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
        self.assertEqual(
            self.errors, [], "Valid style retrieval should produce no errors"
        )

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

    def test_get_styles_for_object_name_no_rules_with_include_class_false(self) -> None:
        """
        Test style retrieval for an object name with no rules, including class styles.
        """
        widget: Mock = Mock()
        widget.objectName.return_value = "nonExistentButton"
        widget.metaObject.return_value.className.return_value = "QPushButton"
        stylesheet: str = self.parser.get_styles_for(
            widget, include_class_if_object_name=False
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

    def test_get_styles_for_attribute_selector(self) -> None:
        """
        Test style retrieval for a selector with attribute and pseudo-_state.
        """
        parser: QSSParser = QSSParser()
        errors: List[str] = []
        parser.on(ParserEvent.ERROR_FOUND, lambda error: errors.append(error))
        qss: str = """
        #btn_save[selected="true"]:hover {
            border-left: 22px solid qlineargradient(spread:pad, x1:0.034, y1:0, x2:0.216, y2:0, stop:0.499 rgba(255, 121, 198, 255), stop:0.5 rgba(85, 170, 255, 0));
            background-color: rgb(98, 114, 164);
        }
        """
        parser.parse(qss)
        self.assertEqual(len(parser._state.rules), 1, "Should parse one rule")
        self.assertEqual(
            parser._state.rules[0].selector, '#btn_save[selected="true"]:hover'
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
        self.assertEqual(
            errors, [], "Valid attribute selector should produce no errors"
        )

    def test_get_styles_with_variables_and_fixed_properties(self) -> None:
        """
        Test style retrieval with variables and fixed properties.
        """
        parser: QSSParser = QSSParser()
        errors: List[str] = []
        parser.on(ParserEvent.ERROR_FOUND, lambda error: errors.append(error))
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
        self.assertEqual(
            errors, [], "Valid variables and properties should produce no errors"
        )

    def test_get_styles_for_variables_block_single_line(self) -> None:
        """
        Test get style for a single-line QSS rule with multiple properties and variables.
        """
        qss: str = """
        @variables {
            --primary-color: #ffffff;
            --border-radius: 14px;
        }
        #extraCloseColumnBtn QPushButton { background-color: rgba(248, 248, 242, 0); border: none; border-radius: var(--border-radius); color: var(--primary-color); }
        """
        errors: List[str] = []
        self.parser.on(ParserEvent.ERROR_FOUND, lambda error: errors.append(error))
        self.parser.parse(qss)
        widget: Mock = Mock()
        widget.objectName.return_value = "extraCloseColumnBtn"
        widget.metaObject.return_value.className.return_value = "QPushButton"
        stylesheet: str = self.parser.get_styles_for(widget)

        expected: str = """#extraCloseColumnBtn QPushButton {
    background-color: rgba(248, 248, 242, 0);
    border: none;
    border-radius: 14px;
    color: #ffffff;
}
"""
        self.assertEqual(stylesheet.strip(), expected.strip())
        self.assertEqual(
            errors, [], "Valid variables and properties should produce no errors"
        )

    def test_get_styles_for_single_line_multiple_properties(self) -> None:
        """
        Test get style for a single-line QSS rule with multiple properties.
        """
        qss = """
        #extraCloseColumnBtn, QLabel { background-color: rgba(248, 248, 242, 0); border: none; border-radius: 14px; color: #ffffff; }
        """
        errors: List[str] = []
        self.parser.on(ParserEvent.ERROR_FOUND, lambda error: errors.append(error))
        self.parser.parse(qss)
        widget: Mock = Mock()
        widget.objectName.return_value = "extraCloseColumnBtn"
        widget.metaObject.return_value.className.return_value = "QPushButton"
        stylesheet: str = self.parser.get_styles_for(widget)
        expected: str = """#extraCloseColumnBtn {
    background-color: rgba(248, 248, 242, 0);
    border: none;
    border-radius: 14px;
    color: #ffffff;
}
"""
        self.assertEqual(stylesheet.strip(), expected.strip())
        self.assertEqual(
            errors, [], "Valid variables and properties should produce no errors"
        )

    def test_get_style_for_multiple_selectors_separate_with_comma_in_single_line_with_pseudo_state(
        self,
    ) -> None:
        """
        Test get_style_for QSS with multiple selectors including pseudo-_states.
        """
        qss: str = """
        #myButton:hover, QFrame:disabled, #secondButton QPushButton, #anyButton QCheckBox::drop-down:disabled {
            color: red;
            width: 15px;
            height: 15px;
            border-radius: 10px;
        }
        """
        errors: List[str] = []
        self.parser.on(ParserEvent.ERROR_FOUND, lambda error: errors.append(error))
        self.parser.parse(qss)
        widget: Mock = Mock()
        widget.objectName.return_value = "anyButton"
        widget.metaObject.return_value.className.return_value = "QCheckBox"
        stylesheet: str = self.parser.get_styles_for(widget)
        expected: str = """#anyButton QCheckBox::drop-down:disabled {
    color: red;
    width: 15px;
    height: 15px;
    border-radius: 10px;
}
"""
        self.assertEqual(stylesheet.strip(), expected.strip())
        self.assertEqual(
            errors,
            [],
            "Valid selector and pseudo elements/states in separate comma should produce no errors",
        )

    def test_get_style_for_multiple_selectors_separate_with_comma_in_each_line_with_pseudo_state(
        self,
    ) -> None:
        """
        Test get_style_for QSS with multiple selectors including pseudo-_states.
        """
        qss: str = """
        #myButton:hover,
        QFrame:disabled, 
        #secondButton QPushButton,
        #anyButton QCheckBox::drop-down:disabled {
            color: red;
            width: 15px;
            height: 15px;
            border-radius: 10px;
        }
        """
        errors: List[str] = []
        self.parser.on(ParserEvent.ERROR_FOUND, lambda error: errors.append(error))
        self.parser.parse(qss)
        widget: Mock = Mock()
        widget.objectName.return_value = "anyButton"
        widget.metaObject.return_value.className.return_value = "QCheckBox"
        stylesheet: str = self.parser.get_styles_for(widget)
        expected: str = """#anyButton QCheckBox::drop-down:disabled {
    color: red;
    width: 15px;
    height: 15px;
    border-radius: 10px;
}
"""
        self.assertEqual(stylesheet.strip(), expected.strip())
        self.assertEqual(
            errors,
            [],
            "Valid selector and pseudo elements/states in separate comma should produce no errors",
        )


class TestQSSParserEvents(unittest.TestCase):
    def setUp(self) -> None:
        """
        Set up the test environment for event tests.
        """
        self.parser: QSSParser = QSSParser()
        self.errors: List[str] = []
        self.parser.on(ParserEvent.ERROR_FOUND, lambda error: self.errors.append(error))
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
        self.parser.on(ParserEvent.RULE_ADDED, lambda rule: rules_added.append(rule))
        self.parser.parse(self.qss)
        self.assertEqual(len(rules_added), 2, "Should trigger rule_added for each rule")
        selectors: Set[str] = {rule.selector for rule in rules_added}
        self.assertEqual(selectors, {"QPushButton", "#myButton"})
        self.assertEqual(self.errors, [], "Valid QSS should produce no errors")

    def test_event_error_found(self) -> None:
        """
        Test the error_found event with a missing semicolon.
        """
        qss: str = """
        QPushButton {
            color: blue
            background: white;
        }
        """
        self.parser.parse(qss)
        self.assertEqual(
            len(self.parser._state.rules), 1, "Should parse valid properties"
        )
        self.assertEqual(len(self.errors), 1, "Should trigger error_found")
        self.assertIn("Property missing ';'", self.errors[0])

    def test_multiple_event_handlers(self) -> None:
        """
        Test multiple handlers for the rule_added event.
        """
        rules_added_1: List[QSSRule] = []
        rules_added_2: List[QSSRule] = []
        self.parser.on(ParserEvent.RULE_ADDED, lambda rule: rules_added_1.append(rule))
        self.parser.on(ParserEvent.RULE_ADDED, lambda rule: rules_added_2.append(rule))
        self.parser.parse(self.qss)
        self.assertEqual(
            len(rules_added_1), 2, "First handler should capture all rules"
        )
        self.assertEqual(
            len(rules_added_2), 2, "Second handler should capture all rules"
        )
        self.assertEqual(self.errors, [], "Valid QSS should produce no errors")

    def test_event_error_found_multiple(self) -> None:
        """
        Test multiple handlers for the error_found event.
        """
        errors_found_1: List[str] = []
        errors_found_2: List[str] = []
        self.parser.on(
            ParserEvent.ERROR_FOUND, lambda error: errors_found_1.append(error)
        )
        self.parser.on(
            ParserEvent.ERROR_FOUND, lambda error: errors_found_2.append(error)
        )
        qss: str = """
        QPushButton {
            color: blue
            font-size: 12px;
        }
        QFrame {
            color: blue;
            background: white
            font-size: 12px;
        }
        """
        self.parser.parse(qss)
        self.assertEqual(len(errors_found_1), 2, "First handler should capture errors")
        self.assertEqual(len(errors_found_2), 2, "Second handler should capture errors")
        self.assertIn("Property missing ';'", errors_found_1[0])
        self.assertIn("Property missing ';'", errors_found_1[1])

    def test_event_variable_defined(self) -> None:
        """
        Test the variable_defined event.
        """
        variables_defined: List[Tuple[str, str]] = []
        self.parser.on(
            ParserEvent.VARIABLE_DEFINED,
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
        self.assertEqual(
            self.errors, [], "Valid variables block should produce no errors"
        )

    def test_event_parse_completed(self) -> None:
        """
        Test the parse_completed event.
        """
        parse_completed: bool = False

        def on_parse_completed() -> None:
            nonlocal parse_completed
            parse_completed = True

        self.parser.on(ParserEvent.PARSE_COMPLETED, on_parse_completed)
        self.parser.parse(self.qss)
        self.assertTrue(parse_completed, "Should trigger parse_completed")
        self.assertEqual(self.errors, [], "Valid QSS should produce no errors")


class TestQSSParserToString(unittest.TestCase):
    def setUp(self) -> None:
        """
        Set up a new instance for each test.
        """
        self.parser = QSSParser()
        self.errors: List[str] = []
        self.parser.on(ParserEvent.ERROR_FOUND, lambda error: self.errors.append(error))

    def test_to_string_simple_rule(self) -> None:
        """
        Test to_string() with a simple QSS rule.
        """
        qss = """
        QPushButton {
            color: blue;
            background: white;
        }
        """
        self.parser.parse(qss)
        expected = "QPushButton {\n    color: blue;\n    background: white;\n}\n"
        self.assertEqual(self.parser.to_string(), expected)
        self.assertEqual(self.errors, [], "Valid QSS should produce no errors")

    def test_to_string_multiple_selectors(self) -> None:
        """
        Test to_string() with multiple comma-separated selectors.
        """
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
        self.assertEqual(self.parser.to_string(), expected)
        self.assertEqual(self.errors, [], "Valid QSS should produce no errors")

    def test_to_string_with_variables(self) -> None:
        """
        Test to_string() with a QSS rule using variables.
        """
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
        self.assertEqual(self.parser.to_string(), expected)
        self.assertEqual(
            self.errors, [], "Valid variables block should produce no errors"
        )

    def test_to_string_complex_nested_selectors_with_class_and_id_without_space(
        self,
    ) -> None:
        """
        Test to_string() with complex nested selectors.
        """
        qss = """
        QFrame > QPushButton#myButton[data-value="nested"] {
            color: purple;
            margin: 10px;
        }
        """
        self.parser.parse(qss)
        expected = 'QFrame > QPushButton #myButton[data-value="nested"] {\n    color: purple;\n    margin: 10px;\n}\n'
        self.assertEqual(self.parser.to_string(), expected)
        self.assertEqual(
            self.errors, [], "Valid nested selector should produce no errors"
        )

    def test_to_string_complex_nested_selectors_with_attribute_selector_space_invalid(
        self,
    ) -> None:
        """
        Test to_string() with complex nested selectors.
        """
        qss = """
        QFrame > QPushButton #myButton [data-value="nested"] {
            color: purple;
            margin: 10px;
        }
        """
        self.parser.parse(qss)
        self.assertEqual(self.parser.to_string(), "")
        self.assertEqual(
            self.errors,
            [
                "Error on line 2: Invalid selector: 'QFrame > QPushButton #myButton [data-value=\"nested\"]'. "
                "Space not allowed before attribute selector '[data-value=\"nested\"]'"
            ],
            "Invalid attribute selector should produce error",
        )

    def test_to_string_for_variables_block_single_line(self) -> None:
        """
        Test to_string a single-line QSS rule with multiple properties and variables.
        """
        qss: str = """
        @variables {
            --primary-color: #ffffff;
            --border-radius: 14px;
        }
        #extraCloseColumnBtn QPushButton { background-color: rgba(248, 248, 242, 0); border: none; border-radius: var(--border-radius); color: var(--primary-color); }
        """
        self.parser.parse(qss)
        expected: str = """#extraCloseColumnBtn QPushButton {
    background-color: rgba(248, 248, 242, 0);
    border: none;
    border-radius: 14px;
    color: #ffffff;
}
"""
        self.assertEqual(self.parser.to_string(), expected, "Should to string")
        self.assertEqual(self.errors, [], "Single-line rule should produce no errors")

    def test_to_string_for_single_line_multiple_properties(self) -> None:
        """
        Test to_string a single-line QSS rule with multiple properties.
        """
        qss = """
        #extraCloseColumnBtn { background-color: rgba(248, 248, 242, 0); border: none; border-radius: 14px; color: #ffffff; }
        """
        self.parser.parse(qss)
        expected: str = """#extraCloseColumnBtn {
    background-color: rgba(248, 248, 242, 0);
    border: none;
    border-radius: 14px;
    color: #ffffff;
}
"""
        self.assertEqual(self.parser.to_string().strip(), expected.strip())
        self.assertEqual(
            self.errors, [], "Valid variables and properties should produce no errors"
        )

    def test_to_string_multiple_selectors_separate_with_comma_all_single_line_with_pseudo_state(
        self,
    ) -> None:
        """
        Test to_string QSS with multiple selectors including pseudo-_states.
        """
        qss: str = """
        #myButton:hover, QFrame:disabled,  #secondButton QPushButton, #anyButton QCheckBox::drop-down:disabled { color: red; width: 15px; height: 15px; border-radius: 10px;}
        """
        self.parser.parse(qss)
        expected = """#myButton:hover {
    color: red;
    width: 15px;
    height: 15px;
    border-radius: 10px;
}

QFrame:disabled {
    color: red;
    width: 15px;
    height: 15px;
    border-radius: 10px;
}

#secondButton QPushButton {
    color: red;
    width: 15px;
    height: 15px;
    border-radius: 10px;
}

#anyButton QCheckBox::drop-down:disabled {
    color: red;
    width: 15px;
    height: 15px;
    border-radius: 10px;
}
"""
        self.assertEqual(self.parser.to_string().strip(), expected.strip())
        self.assertEqual(self.errors, [], "Single-line rule should produce no errors")

    def test_parsing_multiple_selectors_separate_with_comma_in_each_line_with_pseudo_state(
        self,
    ) -> None:
        """
        Test parsing QSS with multiple selectors including pseudo-_states.
        """
        qss: str = """
        #myButton:hover,
        QFrame:disabled,
        #secondButton QPushButton,
        #anyButton QCheckBox::drop-down:disabled {
            color: red;
            width: 15px;
            height: 15px;
            border-radius: 10px;
        }
        """
        self.parser.parse(qss)
        expected = """#myButton:hover {
    color: red;
    width: 15px;
    height: 15px;
    border-radius: 10px;
}

QFrame:disabled {
    color: red;
    width: 15px;
    height: 15px;
    border-radius: 10px;
}

#secondButton QPushButton {
    color: red;
    width: 15px;
    height: 15px;
    border-radius: 10px;
}

#anyButton QCheckBox::drop-down:disabled {
    color: red;
    width: 15px;
    height: 15px;
    border-radius: 10px;
}
"""
        self.assertEqual(self.parser.to_string().strip(), expected.strip())
        self.assertEqual(self.errors, [], "Single-line rule should produce no errors")


class TestQSSParserQProperty(unittest.TestCase):
    def setUp(self) -> None:
        """
        Set up the test environment for qproperty parsing tests.
        """
        self.parser: QSSParser = QSSParser()
        self.errors: List[str] = []
        self.parser.on(ParserEvent.ERROR_FOUND, lambda error: self.errors.append(error))
        self.qss: str = """
        QPushButton {
            qproperty-icon: url(:/icons/test.png);
            qproperty-text: "Click Me";
            color: blue;
        }
        #customButton {
            qproperty-enabled: false;
            background: gray;
        }
        .iconButton[qproperty-icon="url(:/icons/test.png)"] {
            border: 1px solid black;
        }
        """

    def test_parse_qproperty_attributes(self) -> None:
        """
        Test parsing QSS with valid qproperty attributes.
        """
        self.parser.parse(self.qss)
        self.assertEqual(
            len(self.parser._state.rules), 3, "Should parse all rules correctly"
        )
        self.assertEqual(
            self.errors, [], "Valid qproperty QSS should produce no errors"
        )

        # Test QPushButton rule
        push_button_rule: QSSRule = self.parser._state.rules[0]
        self.assertEqual(push_button_rule.selector, "QPushButton")
        self.assertEqual(len(push_button_rule.properties), 3)
        self.assertEqual(push_button_rule.properties[0].name, "qproperty-icon")
        self.assertEqual(push_button_rule.properties[0].value, "url(:/icons/test.png)")
        self.assertEqual(push_button_rule.properties[1].name, "qproperty-text")
        self.assertEqual(push_button_rule.properties[1].value, '"Click Me"')
        self.assertEqual(push_button_rule.properties[2].name, "color")
        self.assertEqual(push_button_rule.properties[2].value, "blue")

        # Test #customButton rule
        custom_button_rule: QSSRule = self.parser._state.rules[1]
        self.assertEqual(custom_button_rule.selector, "#customButton")
        self.assertEqual(len(custom_button_rule.properties), 2)
        self.assertEqual(custom_button_rule.properties[0].name, "qproperty-enabled")
        self.assertEqual(custom_button_rule.properties[0].value, "false")
        self.assertEqual(custom_button_rule.properties[1].name, "background")
        self.assertEqual(custom_button_rule.properties[1].value, "gray")

        # Test .iconButton rule with qproperty in selector
        icon_button_rule: QSSRule = self.parser._state.rules[2]
        self.assertEqual(
            icon_button_rule.selector,
            '.iconButton[qproperty-icon="url(:/icons/test.png)"]',
        )
        self.assertEqual(len(icon_button_rule.properties), 1)
        self.assertEqual(icon_button_rule.properties[0].name, "border")
        self.assertEqual(icon_button_rule.properties[0].value, "1px solid black")
        self.assertEqual(
            icon_button_rule.attributes, ['[qproperty-icon="url(:/icons/test.png)"]']
        )

    def test_get_styles_for_qproperty(self) -> None:
        """
        Test style retrieval for a widget with qproperty attributes.
        """
        self.parser.parse(self.qss)
        widget: Mock = Mock()
        widget.objectName.return_value = "customButton"
        widget.metaObject.return_value.className.return_value = "QPushButton"

        stylesheet: str = self.parser.get_styles_for(widget)
        expected: str = """#customButton {
    qproperty-enabled: false;
    background: gray;
}"""
        self.assertEqual(stylesheet.strip(), expected.strip())
        self.assertEqual(
            self.errors, [], "Valid qproperty style retrieval should produce no errors"
        )

    def test_get_styles_for_qproperty_with_class_and_object_name(self) -> None:
        """
        Test style retrieval including class styles for a widget with qproperty attributes.
        """
        self.parser.parse(self.qss)
        widget: Mock = Mock()
        widget.objectName.return_value = "customButton"
        widget.metaObject.return_value.className.return_value = "QPushButton"

        stylesheet: str = self.parser.get_styles_for(
            widget, include_class_if_object_name=True
        )
        expected: str = """#customButton {
    qproperty-enabled: false;
    background: gray;
}
QPushButton {
    qproperty-icon: url(:/icons/test.png);
    qproperty-text: "Click Me";
    color: blue;
}"""
        self.assertEqual(stylesheet.strip(), expected.strip())
        self.assertEqual(
            self.errors, [], "Valid qproperty style retrieval should produce no errors"
        )

    def test_parse_invalid_qproperty_name(self) -> None:
        """
        Test parsing QSS with an invalid qproperty name.
        """
        qss: str = """
        QPushButton {
            qproperty-123invalid: true;
            color: blue;
        }
        """
        self.parser.parse(qss)
        self.assertEqual(
            len(self.parser._state.rules), 1, "Should parse rule with valid properties"
        )
        rule: QSSRule = self.parser._state.rules[0]
        self.assertEqual(len(rule.properties), 1, "Should skip invalid qproperty")
        self.assertEqual(rule.properties[0].name, "color")
        self.assertEqual(rule.properties[0].value, "blue")
        self.assertEqual(len(self.errors), 1, "Should report invalid qproperty name")
        self.assertTrue(
            "Invalid property name: 'qproperty-123invalid'" in self.errors[0]
        )

    def test_to_string_with_qproperty(self) -> None:
        """
        Test to_string() output for QSS rules with qproperty attributes.
        """
        self.parser.parse(self.qss)
        expected: str = """QPushButton {
    qproperty-icon: url(:/icons/test.png);
    qproperty-text: "Click Me";
    color: blue;
}

#customButton {
    qproperty-enabled: false;
    background: gray;
}

.iconButton[qproperty-icon="url(:/icons/test.png)"] {
    border: 1px solid black;
}
"""
        self.assertEqual(self.parser.to_string(), expected)
        self.assertEqual(
            self.errors, [], "Valid qproperty QSS should produce no errors"
        )

    def test_event_qproperty_defined(self) -> None:
        """
        Test the rule_added event for rules containing qproperty attributes.
        """
        rules_added: List[QSSRule] = []
        self.parser.on(ParserEvent.RULE_ADDED, lambda rule: rules_added.append(rule))
        self.parser.parse(self.qss)
        print(rules_added)
        print("Teste", self.parser.to_string())
        self.assertEqual(
            len(rules_added), 3, "Should trigger rule_added for each qproperty rule"
        )
        selectors: set = {rule.selector for rule in rules_added}
        self.assertEqual(
            selectors,
            {
                "QPushButton",
                "#customButton",
                '.iconButton[qproperty-icon="url(:/icons/test.png)"]',
            },
            "Should capture all selectors with qproperty attributes",
        )
        self.assertEqual(
            self.errors, [], "Valid qproperty QSS should produce no errors"
        )


if __name__ == "__main__":
    unittest.main()
