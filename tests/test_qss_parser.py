import unittest
from typing import List, Optional
from unittest.mock import Mock, patch
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))
from qss_parser import QSSProperty, QSSRule, QSSParser

class TestQSSParser(unittest.TestCase):
    def setUp(self):
        """
        Set up the test environment before each test.

        Initializes:
            parser: A QSSParser instance.
            qss: Sample QSS text for testing.
            widget: Mock widget with objectName 'myButton' and className 'QPushButton'.
            widget_no_name: Mock widget with empty objectName and className 'QScrollBar'.
            widget_no_qss: Mock widget with objectName 'verticalScrollBar' and className 'QScrollBar'.
        """
        self.parser = QSSParser()
        self.qss = """
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
        self.widget = Mock()
        self.widget.objectName.return_value = "myButton"
        self.widget.metaObject.return_value.className.return_value = "QPushButton"
        self.widget_no_name = Mock()
        self.widget_no_name.objectName.return_value = ""
        self.widget_no_name.metaObject.return_value.className.return_value = "QScrollBar"
        self.widget_no_qss = Mock()
        self.widget_no_qss.objectName.return_value = "verticalScrollBar"
        self.widget_no_qss.metaObject.return_value.className.return_value = "QScrollBar"
        self.parser.parse(self.qss)

    def test_check_format_valid_qss(self):
        """
        Test QSS with valid format, expecting no errors.
        """
        qss = """
        QPushButton {
            color: blue;
            background: white;
        }
        #myButton {
            font-size: 12px;
        }
        """
        errors = self.parser.check_format(qss)
        self.assertEqual(errors, [], "Valid QSS should return no errors")

    def test_check_format_missing_semicolon(self):
        """
        Test QSS with a property missing a semicolon.
        """
        qss = """
        QPushButton {
            color: blue
            background: white;
        }
        """
        errors = self.parser.check_format(qss)
        expected = ["Error on line 3: Property missing ';': color: blue"]
        self.assertEqual(errors, expected, "Should report property missing ';'")

    def test_check_format_extra_closing_brace(self):
        """
        Test QSS with a closing brace without a matching opening brace.
        """
        qss = """
        QPushButton {
            color: blue;
        }
        }
        """
        errors = self.parser.check_format(qss)
        expected = ["Error on line 5: Closing brace '}' without matching '{': }"]
        self.assertEqual(errors, expected, "Should report closing brace without matching '{'")

    def test_check_format_unclosed_brace(self):
        """
        Test QSS with an unclosed opening brace.
        """
        qss = """
        QPushButton {
            color: blue;
            background: white;
        #myButton {
            font-size: 12px;
        """
        errors = self.parser.check_format(qss)
        expected = [
            "Error on line 6: Unclosed brace '{' for selector: #myButton"
        ]
        self.assertEqual(errors, expected, "Should report unclosed brace")

    def test_check_format_property_outside_block(self):
        """
        Test QSS with a property outside a block.
        """
        qss = """
        color: blue;
        QPushButton {
            background: white;
        }
        """
        errors = self.parser.check_format(qss)
        expected = ["Error on line 2: Property outside block: color: blue;"]
        self.assertEqual(errors, expected, "Should report property outside block")

    def test_check_format_ignore_comments(self):
        """
        Test that comments are ignored during validation.
        """
        qss = """
        /* Comment with { and without ; */
        QPushButton {
            color: blue;
        }
        """
        errors = self.parser.check_format(qss)
        self.assertEqual(errors, [], "Comments should not generate errors")

    def test_check_format_multi_line_property(self):
        """
        Test QSS with a property split across multiple lines without a semicolon.
        """
        qss = """
        QPushButton {
            color:
            blue
        }
        """
        errors = self.parser.check_format(qss)
        expected = ["Error on line 4: Property missing ';': color: blue"]
        self.assertEqual(errors, expected, "Should report multi-line property missing ';'")

    def test_check_format_multiple_errors(self):
        """
        Test QSS with multiple errors (missing semicolon, unclosed brace).
        """
        qss = """
        QPushButton {
            color: blue
        #myButton {
            font-size: 12px
        background: gray;
        """
        errors = self.parser.check_format(qss)
        expected = [
            "Error on line 3: Property missing ';': color: blue",
            "Error on line 5: Property missing ';': font-size: 12px",
            "Error on line 6: Unclosed brace '{' for selector: #myButton"
        ]
        self.assertEqual(errors, expected, "Should report all errors")

    def test_check_format_empty_selector(self):
        """
        Test QSS with an empty selector before an opening brace.
        """
        qss = """
        {
            color: blue;
        }
        """
        errors = self.parser.check_format(qss)
        expected = ["Error on line 2: Empty selector before '{': {"]
        self.assertEqual(errors, expected, "Should report empty selector")

    def test_check_format_single_line_rule(self):
        """
        Test QSS with a valid single-line rule.
        """
        qss = """
        #titleLeftApp { font: 12pt "Segoe UI Semibold"; }
        QPushButton{color: blue;}
        """
        errors = self.parser.check_format(qss)
        self.assertEqual(errors, [], "Valid single-line rule should return no errors")

    def test_check_format_invalid_single_line_rule(self):
        """
        Test QSS with an invalid single-line rule (missing semicolon).
        """
        qss = """
        #titleLeftApp { font: 12pt "Segoe UI Semibold" }
        """
        errors = self.parser.check_format(qss)
        expected = ["Error on line 2: Property missing ';': font: 12pt \"Segoe UI Semibold\""]
        self.assertEqual(errors, expected, "Should report missing semicolon in single-line rule")

    # [Rest of the test methods unchanged]
    def test_get_styles_for_object_name(self):
        """
        Test style retrieval by object name.
        """
        stylesheet = self.parser.get_styles_for(self.widget)
        expected = """#myButton {
    color: red;
}"""
        self.assertEqual(stylesheet.strip(), expected.strip())

    def test_get_styles_for_class_name_no_object_name(self):
        """
        Test style retrieval by class name when no object name is provided.
        """
        stylesheet = self.parser.get_styles_for(self.widget_no_name)
        expected = """QScrollBar {
    background: gray;
    width: 10px;
}
QScrollBar:vertical {
    background: lightgray;
}"""
        self.assertEqual(stylesheet.strip(), expected.strip())

    def test_get_styles_for_object_name_no_qss_fallback_class(self):
        """
        Test fallback to class name when object name has no styles.
        """
        stylesheet = self.parser.get_styles_for(self.widget_no_qss)
        expected = """QScrollBar {
    background: gray;
    width: 10px;
}
QScrollBar:vertical {
    background: lightgray;
}"""
        self.assertEqual(stylesheet.strip(), expected.strip())

    def test_get_styles_for_include_class_if_object_name(self):
        """
        Test including class styles when an object name is provided.
        """
        stylesheet = self.parser.get_styles_for(self.widget, include_class_if_object_name=True)
        expected = """#myButton {
    color: red;
}
QPushButton {
    background: blue;
}"""
        self.assertEqual(stylesheet.strip(), expected.strip())

    def test_get_styles_for_fallback_class_when_have_object_name(self):
        """
        Test style retrieval with a fallback class when an object name is provided.
        """
        stylesheet = self.parser.get_styles_for(self.widget, fallback_class="QWidget")
        expected = """#myButton {
    color: red;
}"""
        self.assertEqual(stylesheet.strip(), expected.strip())

    def test_get_styles_for_fallback_class_when_without_object_name(self):
        """
        Test style retrieval with a fallback class when no object name is provided.
        """
        widget = Mock()
        widget.objectName.return_value = "oiiio"
        widget.metaObject.return_value.className.return_value = "QFrame"
        stylesheet = self.parser.get_styles_for(widget, fallback_class="QWidget")
        expected = """QFrame {
    border: 1px solid black;
}"""
        self.assertEqual(stylesheet.strip(), expected.strip())

    def test_get_styles_for_fallback_class_when_without_object_name_and_class(self):
        """
        Test style retrieval with a fallback class when neither object name nor class has styles.
        """
        widget = Mock()
        widget.objectName.return_value = "oiiio"
        widget.metaObject.return_value.className.return_value = "Ola"
        stylesheet = self.parser.get_styles_for(widget, fallback_class="QWidget")
        expected = """QWidget {
    font-size: 12px;
}"""
        self.assertEqual(stylesheet.strip(), expected.strip())

    def test_get_styles_for_additional_selectors(self):
        """
        Test style retrieval with additional selectors.
        """
        stylesheet = self.parser.get_styles_for(
            self.widget,
            additional_selectors=["QFrame", ".customClass"]
        )
        expected = """#myButton {
    color: red;
}
.customClass {
    border-radius: 5px;
}
QFrame {
    border: 1px solid black;
}"""
        self.assertEqual(stylesheet.strip(), expected.strip())

    def test_get_styles_for_all_parameters(self):
        """
        Test style retrieval with all parameters combined.
        """
        stylesheet = self.parser.get_styles_for(
            self.widget,
            fallback_class="QWidget",
            additional_selectors=["QFrame"],
            include_class_if_object_name=True
        )
        expected = """#myButton {
    color: red;
}
QFrame {
    border: 1px solid black;
}
QPushButton {
    background: blue;
}"""
        self.assertEqual(stylesheet.strip(), expected.strip())

    def test_get_styles_for_empty_qss(self):
        """
        Test style retrieval with empty QSS.
        """
        parser = QSSParser()
        parser.parse("")
        stylesheet = parser.get_styles_for(self.widget)
        self.assertEqual(stylesheet.strip(), "")

    def test_get_styles_for_invalid_selector(self):
        """
        Test style retrieval with an invalid additional selector.
        """
        stylesheet = self.parser.get_styles_for(
            self.widget,
            additional_selectors=["InvalidClass"]
        )
        expected = """#myButton {
    color: red;
}"""
        self.assertEqual(stylesheet.strip(), expected.strip())

    def test_get_styles_for_composite_selector(self):
        """
        Test style retrieval with composite selectors.
        """
        parser = QSSParser()
        qss = """
        QScrollBar QWidget {
            margin: 5px;
        }
        QScrollBar:vertical QWidget {
            padding: 2px;
        }
        """
        parser.parse(qss)
        widget = Mock()
        widget.objectName.return_value = ""
        widget.metaObject.return_value.className.return_value = "QScrollBar"
        stylesheet = parser.get_styles_for(widget)
        expected = """QScrollBar QWidget {
    margin: 5px;
}
QScrollBar:vertical QWidget {
    padding: 2px;
}"""
        self.assertEqual(stylesheet.strip(), expected.strip())

    def test_get_styles_for_multiple_selectors(self):
        """
        Test style retrieval with multiple selectors in a single rule.
        """
        parser = QSSParser()
        qss = """
        QPushButton, QScrollBar {
            color: green;
        }
        """
        parser.parse(qss)
        widget = Mock()
        widget.objectName.return_value = ""
        widget.metaObject.return_value.className.return_value = "QScrollBar"
        stylesheet = parser.get_styles_for(widget)
        expected = """QScrollBar {
    color: green;
}"""
        self.assertEqual(stylesheet.strip(), expected.strip())

    def test_get_styles_for_fallback_class_and_additional_selectors(self):
        """
        Test style retrieval combining fallback class and additional selectors.
        """
        stylesheet = self.parser.get_styles_for(
            self.widget,
            fallback_class="QWidget",
            additional_selectors=["QFrame"]
        )
        expected = """#myButton {
    color: red;
}
QFrame {
    border: 1px solid black;
}"""
        self.assertEqual(stylesheet.strip(), expected.strip())

    def test_get_styles_for_include_class_and_additional_selectors(self):
        """
        Test style retrieval combining include_class_if_object_name and additional selectors.
        """
        stylesheet = self.parser.get_styles_for(
            self.widget,
            additional_selectors=[".customClass"],
            include_class_if_object_name=True
        )
        expected = """#myButton {
    color: red;
}
.customClass {
    border-radius: 5px;
}
QPushButton {
    background: blue;
}"""
        self.assertEqual(stylesheet.strip(), expected.strip())

    def test_get_styles_for_object_name_no_rules(self):
        """
        Test style retrieval for an object name with no rules, including class styles.
        """
        widget = Mock()
        widget.objectName.return_value = "nonExistentButton"
        widget.metaObject.return_value.className.return_value = "QPushButton"
        stylesheet = self.parser.get_styles_for(widget, include_class_if_object_name=True)
        expected = """QPushButton {
    background: blue;
}"""
        self.assertEqual(stylesheet.strip(), expected.strip())

    def test_get_styles_for_fallback_class_no_rules(self):
        """
        Test style retrieval with a fallback class that has no rules.
        """
        stylesheet = self.parser.get_styles_for(
            self.widget,
            fallback_class="NonExistentClass"
        )
        expected = """#myButton {
    color: red;
}"""
        self.assertEqual(stylesheet.strip(), expected.strip())

    def test_get_styles_for_mixed_additional_selectors(self):
        """
        Test style retrieval with a mix of valid and invalid additional selectors.
        """
        stylesheet = self.parser.get_styles_for(
            self.widget,
            additional_selectors=["QFrame", "InvalidClass"]
        )
        expected = """#myButton {
    color: red;
}
QFrame {
    border: 1px solid black;
}"""
        self.assertEqual(stylesheet.strip(), expected.strip())

    def test_get_styles_for_multiple_selectors_with_pseudo_state(self):
        """
        Test style retrieval with multiple selectors including pseudo-states.
        """
        parser = QSSParser()
        qss = """
        QPushButton:hover, QScrollBar:hover {
            color: purple;
        }
        """
        parser.parse(qss)
        widget = Mock()
        widget.objectName.return_value = ""
        widget.metaObject.return_value.className.return_value = "QScrollBar"
        stylesheet = parser.get_styles_for(widget)
        expected = """QScrollBar:hover {
    color: purple;
}"""
        self.assertEqual(stylesheet.strip(), expected.strip())

    def test_get_styles_for_missing_closing_brace(self):
        """
        Test style retrieval with QSS missing a closing brace.
        """
        parser = QSSParser()
        qss = """
        QPushButton {
            color: blue;
        #myButton {
            color: red;
        """
        parser.parse(qss)
        widget = Mock()
        widget.objectName.return_value = "myButton"
        widget.metaObject.return_value.className.return_value = "QPushButton"
        stylesheet = parser.get_styles_for(widget)
        expected = ""
        self.assertEqual(stylesheet.strip(), expected.strip())

    def test_get_styles_for_malformed_property(self):
        """
        Test style retrieval with a malformed property.
        """
        parser = QSSParser()
        qss = """
        QPushButton {
            color: blue;
            margin: ;
            background
        }
        """
        parser.parse(qss)
        widget = Mock()
        widget.objectName.return_value = ""
        widget.metaObject.return_value.className.return_value = "QPushButton"
        stylesheet = parser.get_styles_for(widget)
        expected = """QPushButton {
    color: blue;
}"""
        self.assertEqual(stylesheet.strip(), expected.strip())

    def test_get_styles_for_invalid_selector(self):
        """
        Test style retrieval with an invalid selector.
        """
        parser = QSSParser()
        qss = """
        # {
            color: blue;
        }
        QPushButton {
            background: green;
        }
        """
        parser.parse(qss)
        widget = Mock()
        widget.objectName.return_value = ""
        widget.metaObject.return_value.className.return_value = "QPushButton"
        stylesheet = parser.get_styles_for(widget)
        expected = """QPushButton {
    background: green;
}"""
        self.assertEqual(stylesheet.strip(), expected.strip())

    def test_get_styles_for_complex_nested_selector(self):
        """
        Test style retrieval with a complex nested selector.
        """
        parser = QSSParser()
        qss = """
        QWidget #myWidget QPushButton {
            border: 2px solid red;
        }
        """
        parser.parse(qss)
        widget = Mock()
        widget.objectName.return_value = ""
        widget.metaObject.return_value.className.return_value = "QPushButton"
        stylesheet = parser.get_styles_for(widget)
        expected = ""
        self.assertEqual(stylesheet.strip(), expected.strip())

    def test_get_styles_for_pseudo_state_combination(self):
        """
        Test style retrieval with combined pseudo-states.
        """
        parser = QSSParser()
        qss = """
        QPushButton:hover:focus {
            color: yellow;
        }
        """
        parser.parse(qss)
        widget = Mock()
        widget.objectName.return_value = ""
        widget.metaObject.return_value.className.return_value = "QPushButton"
        stylesheet = parser.get_styles_for(widget)
        expected = """QPushButton:hover:focus {
    color: yellow;
}"""
        self.assertEqual(stylesheet.strip(), expected.strip())

    def test_get_styles_for_pseudo_element_selector(self):
        """
        Test style retrieval with a pseudo-element selector.
        """
        parser = QSSParser()
        qss = """
        QScrollBar::handle:vertical {
            background: darkgray;
        }
        """
        parser.parse(qss)
        widget = Mock()
        widget.objectName.return_value = ""
        widget.metaObject.return_value.className.return_value = "QScrollBar"
        stylesheet = parser.get_styles_for(widget)
        expected = """QScrollBar::handle:vertical {
    background: darkgray;
}"""
        self.assertEqual(stylesheet.strip(), expected.strip())

    def test_get_styles_for_empty_qss_with_parameters(self):
        """
        Test style retrieval with empty QSS and various parameters.
        """
        parser = QSSParser()
        parser.parse("")
        widget = Mock()
        widget.objectName.return_value = "myButton"
        widget.metaObject.return_value.className.return_value = "QPushButton"
        stylesheet = parser.get_styles_for(
            widget,
            fallback_class="QWidget",
            additional_selectors=["QFrame"],
            include_class_if_object_name=True
        )
        self.assertEqual(stylesheet.strip(), "")

    def test_get_styles_for_empty_qss_with_parameters_2(self):
        """
        Test style retrieval with specific QSS and parameters.
        """
        parser = QSSParser()
        qss = """
        #myButton2 QFrame {
            color: blue;
        }
        Qframe, QWidget {
            color: red;
            background: darkgray;
        }
        QWidget {
            color: green;
            background: dark;
            font: 12px;
        }
        """
        parser.parse(qss)
        widget = Mock()
        widget.objectName.return_value = "myButton"
        widget.metaObject.return_value.className.return_value = "QPushButton"
        stylesheet = parser.get_styles_for(
            widget,
            fallback_class="QWidget",
            include_class_if_object_name=False
        )
        expected = """
    QWidget {
    color: red;
    background: darkgray;
    font: 12px;
}
    """
        self.assertEqual(stylesheet.strip(), expected.strip())

    def test_get_styles_for_duplicate_rules(self):
        """
        Test style retrieval with duplicate rules.
        """
        parser = QSSParser()
        qss = """
        QPushButton {
            color: blue;
        }
        QPushButton, Qwidget {
            color: blue;
        }
        """
        parser.parse(qss)
        widget = Mock()
        widget.objectName.return_value = ""
        widget.metaObject.return_value.className.return_value = "QPushButton"
        stylesheet = parser.get_styles_for(widget)
        expected = """QPushButton {
    color: blue;
}"""
        self.assertEqual(stylesheet.strip(), expected.strip())

    def test_get_styles_for_comments_only(self):
        """
        Test style retrieval with QSS containing only comments.
        """
        parser = QSSParser()
        qss = """
        /* This is a comment */
        /* Another comment */
        """
        parser.parse(qss)
        widget = Mock()
        widget.objectName.return_value = "myButton"
        widget.metaObject.return_value.className.return_value = "QPushButton"
        stylesheet = parser.get_styles_for(widget)
        self.assertEqual(stylesheet.strip(), "")

if __name__ == '__main__':
    unittest.main()