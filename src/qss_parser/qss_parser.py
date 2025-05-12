"""
QSS Parser for parsing and applying Qt Style Sheets (QSS).

This module provides a robust parser for QSS, supporting variables, attribute selectors,
pseudo-states, and hierarchical selectors. It includes style selection and an extensible
plugin system for custom parsing logic. Validation is performed during parsing, with errors
reported via the 'error_found' event.
"""

import logging
import re
from abc import ABC, abstractmethod
from typing import (
    Callable,
    Dict,
    Final,
    List,
    Optional,
    Pattern,
    Protocol,
    Set,
    Tuple,
    TypedDict,
)

# === Constants ===


class Constants:
    """Centralized constants for regex patterns and other static values."""

    ATTRIBUTE_PATTERN: Final[str] = (
        r'\[\w+(?:(?:~|=|\|=|\^=|\$=|\*=)(?:"[^"]*"|[^\s"\]]*))?[^[]*\]'
    )
    COMPILED_ATTRIBUTE_PATTERN: Final[Pattern[str]] = re.compile(ATTRIBUTE_PATTERN)
    VARIABLE_PATTERN: Final[str] = r"var\((--[\w-]+)\)"
    COMPLETE_RULE_PATTERN: Final[str] = r"^\s*[^/][^{}]*\s*\{[^}]*\}\s*$"
    PSEUDO_PATTERN: Final[str] = r"(\w+|#[-\w]+|\[.*?\])\s*(:{1,2})\s*(\w+)"
    CLASS_ID_PATTERN: Final[str] = r"(\w+)(#[-\w]+)"
    COMBINATOR_PATTERN: Final[str] = (
        r"(\w+|#[-\w]+|\[.*?\])([> ]{1,2})(\w+|#[-\w]+|\[.*?\])"
    )


# === Protocols ===


class MetaObjectProtocol(Protocol):
    """Protocol for meta-objects providing widget metadata."""

    def className(self) -> str:
        """Return the widget's class name (e.g., 'QPushButton')."""
        ...


class WidgetProtocol(Protocol):
    """Protocol for widgets used in QSS style application."""

    def objectName(self) -> str:
        """Return the widget's object name (e.g., 'myButton')."""
        ...

    def metaObject(self) -> MetaObjectProtocol:
        """Return the widget's meta-object containing metadata."""
        ...


class PropertyProcessorProtocol(Protocol):
    """Protocol for processing QSS properties."""

    def process_property(
        self,
        line: str,
        rules: List["QSSRule"],
        variable_manager: "VariableManager",
        line_num: int,
    ) -> None:
        """
        Process a property line and add it to the given rules.

        Args:
            line: The property line to process (e.g., 'color: blue;').
            rules: The list of rules to add the property to.
            variable_manager: Manager for resolving variables in property values.
            line_num: Line number for error reporting.
        """
        ...


class RuleHandlerProtocol(Protocol):
    """Protocol for handling QSS rules."""

    def handle_rule(self, rule: "QSSRule") -> None:
        """
        Handle a new or updated rule.

        Args:
            rule: The rule to add or merge.
        """
        ...


class ErrorHandlerProtocol(Protocol):
    """Protocol for handling errors."""

    def dispatch_error(self, error: str) -> None:
        """
        Dispatch an error message to registered handlers.

        Args:
            error: The error message to dispatch.
        """
        ...


# === Core Data Structures ===


class QSSPropertyDict(TypedDict):
    """Typed dictionary for representing a QSS property."""

    name: str
    value: str


class QSSProperty:
    """Represents a single QSS property with a name and value."""

    def __init__(self, name: str, value: str) -> None:
        """
        Initialize a QSS property with normalized name and value.

        Args:
            name: The property name (e.g., 'color').
            value: The property value (e.g., 'blue').
        """
        self.name: str = name.strip()
        self.value: str = value.strip()

    def __repr__(self) -> str:
        """Return a string representation of the property."""
        return f"{self.name}: {self.value}"

    def to_dict(self) -> QSSPropertyDict:
        """Convert the property to a dictionary."""
        return {"name": self.name, "value": self.value}


class QSSRule:
    """Represents a QSS rule with a selector and properties."""

    def __init__(self, selector: str, original: Optional[str] = None) -> None:
        """
        Initialize a QSS rule.

        Args:
            selector: The CSS selector (e.g., '#myButton', 'QPushButton').
            original: The original QSS text for the rule, if provided.
        """
        self.selector: str = selector.strip()
        self.properties: List[QSSProperty] = []
        self.original: str = original or ""
        self.object_name: Optional[str] = None
        self.class_name: Optional[str] = None
        self.attributes: List[str] = []
        self.pseudo_states: List[str] = []
        self._parse_selector()

    def _parse_selector(self) -> None:
        """
        Parse the selector to extract object name, class name, attributes, and pseudo-states.
        Updates instance attributes accordingly.
        """
        (
            self.object_name,
            self.class_name,
            self.attributes,
            self.pseudo_states,
        ) = SelectorUtils.parse_selector(self.selector)

    def add_property(self, name: str, value: str) -> None:
        """
        Add a normalized property to the rule.

        Args:
            name: The property name.
            value: The property value.
        """
        self.properties.append(QSSProperty(name, value))

    def clone_without_pseudo_elements(self) -> "QSSRule":
        """
        Create a copy of the rule without pseudo-elements or pseudo-states.

        Returns:
            A new rule instance with the same properties but without pseudo-elements.
        """
        base_selector = self.selector.split("::")[0]
        clone = QSSRule(base_selector)
        clone.properties = self.properties.copy()
        clone.original = QSSFormatter.format_rule(base_selector, self.properties)
        return clone

    def __repr__(self) -> str:
        """Return a string representation of the rule."""
        props = "\n\t".join(str(p) for p in self.properties)
        return f"{self.selector} {{\n\t{props}\n}}"

    def __hash__(self) -> int:
        """Compute a hash for the rule based on selector and properties."""
        return hash((self.selector, tuple((p.name, p.value) for p in self.properties)))

    def __eq__(self, other: object) -> bool:
        """
        Compare this rule with another for equality.

        Args:
            other: Another object to compare with.

        Returns:
            True if the rules have the same selector and properties, else False.
        """
        if not isinstance(other, QSSRule):
            return False
        return self.selector == other.selector and self.properties == other.properties


# === Utility Classes ===


class VariableManager:
    """Manages QSS variables defined in @variables blocks and resolves var() references."""

    def __init__(self) -> None:
        """Initialize the variable manager with an empty variable dictionary."""
        self._variables: Dict[str, str] = {}
        self._logger: logging.Logger = logging.getLogger(__name__)

    def parse_variables(
        self,
        block: str,
        start_line: int = 1,
        on_variable_defined: Optional[Callable[[str, str], None]] = None,
    ) -> List[str]:
        """
        Parse a @variables block and store the variables.

        Args:
            block: The content of the @variables block (e.g., '--primary-color: #ffffff;').
            start_line: Starting line number for error reporting, by default 1.
            on_variable_defined: Optional callback to invoke when a variable is defined.

        Returns:
            List[str]: List of error messages for invalid variable declarations.
        """
        errors: List[str] = []
        lines = block.split(";")
        for i, line in enumerate(lines, start=start_line):
            line = line.strip()
            if not line:
                continue
            if not line.startswith("--"):
                errors.append(
                    f"Invalid variable name on line {i}: Must start with '--': {line}"
                )
                continue
            parts = line.split(":", 1)
            if len(parts) != 2 or not parts[0].strip() or not parts[1].strip():
                errors.append(f"Malformed variable declaration on line {i}: {line}")
                continue
            name, value = parts
            name = name.strip()
            value = value.strip()
            self._variables[name] = value
            if on_variable_defined:
                on_variable_defined(name, value)
        return errors

    def resolve_variable(self, value: str) -> Tuple[str, Optional[str]]:
        """
        Resolve var(--name) references in a property value recursively.

        Args:
            value: The property value containing var(--name) references.

        Returns:
            Tuple[str, Optional[str]]: A tuple of the resolved value and an error message
            if a variable is undefined or a circular reference is detected.
        """
        visited: Set[str] = set()
        errors: List[str] = []

        def replace_var(match: re.Match[str]) -> str:
            var_name = match.group(1)
            if var_name in visited:
                error_msg = f"Circular variable reference detected: {var_name}"
                self._logger.warning(error_msg)
                errors.append(error_msg)
                return match.group(0)
            if var_name not in self._variables:
                return match.group(0)
            visited.add(var_name)
            resolved_value = self._variables[var_name]
            nested_value = re.sub(
                Constants.VARIABLE_PATTERN, replace_var, resolved_value
            )
            visited.remove(var_name)
            return nested_value

        resolved_value = re.sub(Constants.VARIABLE_PATTERN, replace_var, value)
        undefined_vars = [
            match.group(1)
            for match in re.finditer(Constants.VARIABLE_PATTERN, value)
            if match.group(1) not in self._variables and match.group(1) not in visited
        ]
        error = None
        if errors:
            error = errors[0]
        elif undefined_vars:
            error = f"Undefined variables: {', '.join(undefined_vars)}"
        return resolved_value, error


class SelectorUtils:
    """Utility class for parsing and normalizing QSS selectors."""

    @staticmethod
    def is_complete_rule(line: str) -> bool:
        """
        Check if the line is a complete QSS rule (selector + { + properties + }).

        Args:
            line: The line to check.

        Returns:
            bool: True if the line is a complete QSS rule, else False.
        """
        return bool(re.match(Constants.COMPLETE_RULE_PATTERN, line))

    @staticmethod
    def extract_attributes(selector: str) -> List[str]:
        """
        Extract attribute selectors from a QSS selector.

        Args:
            selector: The selector to parse (e.g., 'QPushButton[data-value="complex"]').

        Returns:
            List[str]: List of attribute selectors (e.g., ['[data-value="complex"]']).
        """
        return Constants.COMPILED_ATTRIBUTE_PATTERN.findall(selector)

    @staticmethod
    def normalize_selector(selector: str) -> str:
        """
        Normalize a selector by removing extra spaces around combinators and between parts,
        while preserving spaces within attribute selectors.

        Args:
            selector: The selector to normalize.

        Returns:
            str: The normalized selector.
        """
        selectors = [s.strip() for s in selector.split(",") if s.strip()]
        normalized_selectors = []
        for sel in selectors:
            attributes = SelectorUtils.extract_attributes(sel)
            temp_placeholders = [f"__ATTR_{i}__" for i in range(len(attributes))]
            temp_sel = sel
            for placeholder, attr in zip(temp_placeholders, attributes):
                temp_sel = temp_sel.replace(attr, placeholder)

            temp_sel = re.sub(r"(\w+)(#[-\w]+)", r"\1 \2", temp_sel)
            temp_sel = re.sub(r"\s*>\s*", " > ", temp_sel)
            temp_sel = re.sub(r"\s+", " ", temp_sel)
            temp_sel = temp_sel.strip()

            for placeholder, attr in zip(temp_placeholders, attributes):
                temp_sel = temp_sel.replace(placeholder, attr)

            normalized_selectors.append(temp_sel)
        return ", ".join(normalized_selectors)

    @staticmethod
    def parse_selector(
        selector: str,
    ) -> Tuple[Optional[str], Optional[str], List[str], List[str]]:
        """
        Parse a selector into object name, class name, attributes, and pseudo-states.

        Args:
            selector: The selector to parse.

        Returns:
            Tuple[Optional[str], Optional[str], List[str], List[str]]: A tuple of
            (object_name, class_name, attributes, pseudo_states).
        """
        object_name: Optional[str] = None
        class_name: Optional[str] = None
        attributes = SelectorUtils.extract_attributes(selector)
        pseudo_states: List[str] = []

        selector_clean = Constants.COMPILED_ATTRIBUTE_PATTERN.sub("", selector)
        selector_clean = re.sub(r"::\w+", "", selector_clean)
        parts = selector_clean.split(":")
        main_selector = parts[0].strip()
        pseudo_states = [p.strip() for p in parts[1:] if p.strip()]

        selector_parts = [
            part.strip() for part in re.split(r"\s+", main_selector) if part.strip()
        ]
        for part in selector_parts:
            if part.startswith("#"):
                object_name = part[1:]
            elif part and not class_name:
                class_name = part

        return object_name, class_name, attributes, pseudo_states

    @staticmethod
    def validate_selector_syntax(selector: str, line_num: int) -> List[str]:
        """
        Validate the syntax of a QSS selector, checking for spacing issues, malformed attributes,
        and duplicate selectors.

        Args:
            selector: The selector to validate.
            line_num: The line number for error reporting.

        Returns:
            List[str]: List of error messages for invalid selector syntax.
        """
        errors: List[str] = []
        selector = selector.strip()

        selectors = [s.strip() for s in selector.split(",") if s.strip()]
        if len(selectors) > 1:
            seen_selectors: Set[str] = set()
            for sel in selectors:
                if sel in seen_selectors:
                    errors.append(
                        f"Error on line {line_num}: Duplicate selector '{sel}' in comma-separated list"
                    )
                seen_selectors.add(sel)
            for sel in selectors:
                if ":" in sel and not sel.endswith(":"):
                    errors.append(
                        f"Error: Pseudo-states in comma-separated selectors are not supported. "
                        f"Split into separate rules for {selector}"
                    )
                    return errors

        for sel in selectors:
            attributes = SelectorUtils.extract_attributes(sel)
            for attr in attributes:
                if not re.match(
                    r'\[\w+(?:(?:~|=|\|=|\^=|\$=|\*=)(?:"[^"]*"|[^\s"\]]*))?[^[]*\]',
                    attr,
                ):
                    errors.append(
                        f"Error on line {line_num}: Invalid selector: '{sel}'. "
                        f"Malformed attribute selector '{attr}'"
                    )
                if re.match(r"\[\w+(?:~|=|\|=|\^=|\$=|\*=)\]", attr):
                    errors.append(
                        f"Error on line {line_num}: Invalid selector: '{sel}'. "
                        f"Malformed attribute selector '{attr}'"
                    )

            parts = re.split(r"([>]\s*)", sel)
            for part in parts:
                if part.strip() in ["", ">"]:
                    continue
                sub_parts = part.split()
                for i, sub_part in enumerate(sub_parts):
                    if sub_part.startswith("[") and i > 0:
                        errors.append(
                            f"Error on line {line_num}: Invalid selector: '{sel}'. "
                            f"Space not allowed before attribute selector '{sub_part}'"
                        )

            matches = re.finditer(Constants.PSEUDO_PATTERN, sel)
            for match in matches:
                prefix, colon, pseudo = match.groups()
                full_match = match.group(0)
                if re.search(r"\s+:{1,2}\s*", full_match):
                    pseudo_type = "pseudo-element" if colon == "::" else "pseudo-state"
                    errors.append(
                        f"Error on line {line_num}: Invalid spacing in selector: '{sel}'. "
                        f"No space allowed between '{prefix}' and '{colon}{pseudo}' ({pseudo_type})"
                    )

            for match in re.finditer(Constants.COMBINATOR_PATTERN, sel):
                left, combinator, right = match.groups()
                if combinator not in [" ", ">"]:
                    errors.append(
                        f"Error on line {line_num}: Invalid combinator in selector: '{sel}'. "
                        f"Invalid combinator '{combinator}' between '{left}' and '{right}'"
                    )

        return errors


class QSSFormatter:
    """Utility class for formatting QSS rules and properties."""

    @staticmethod
    def format_rule(selector: str, properties: List[QSSProperty]) -> str:
        """
        Format a QSS rule in the standardized QSS format.

        Args:
            selector: The selector for the rule.
            properties: The properties to include.

        Returns:
            str: The formatted rule string.
        """
        normalized_selector = SelectorUtils.normalize_selector(selector)
        props = "\n".join(f"    {p.name}: {p.value};" for p in properties)
        return f"{normalized_selector} {{\n{props}\n}}\n"


class DefaultPropertyProcessor:
    """Default implementation for processing QSS properties."""

    def __init__(self, error_handler: ErrorHandlerProtocol) -> None:
        """
        Initialize the property processor.

        Args:
            error_handler: Callback for reporting errors during property processing.
        """
        self._error_handler = error_handler
        self._logger: logging.Logger = logging.getLogger(__name__)

    def process_property(
        self,
        line: str,
        rules: List[QSSRule],
        variable_manager: VariableManager,
        line_num: int,
    ) -> None:
        """
        Process a property line and add it to the given rules.

        Args:
            line: The property line to process (e.g., 'color: blue;').
            rules: The list of rules to add the property to.
            variable_manager: Manager for resolving variables in property values.
            line_num: Line number for error reporting.
        """
        line = line.strip()
        if not rules or not line:
            self._logger.debug(
                f"Skipping empty property line or no rules on line {line_num}"
            )
            return
        parts = line.split(":", 1)
        if len(parts) != 2:
            self._error_handler.dispatch_error(
                f"Error on line {line_num}: Malformed property: {line}"
            )
            return
        name = parts[0].strip()
        value = parts[1].strip().rstrip(";").strip()
        if not name or not value:
            self._error_handler.dispatch_error(
                f"Error on line {line_num}: Invalid property: Empty name or value in '{line}'"
            )
            return
        if not self._is_valid_property_name(name):
            self._error_handler.dispatch_error(
                f"Error on line {line_num}: Invalid property name: '{name}'"
            )
            return
        resolved_value, error = variable_manager.resolve_variable(value)
        if error:
            self._error_handler.dispatch_error(f"Error on line {line_num}: {error}")
            return
        normalized_line = f"{name}: {resolved_value};"
        for rule in rules:
            rule.original += f"    {normalized_line}\n"
            rule.add_property(name, resolved_value)
        self._logger.debug(f"Processed property on line {line_num}: {normalized_line}")

    def _is_valid_property_name(self, name: str) -> bool:
        """
        Check if a property name is valid according to QSS conventions.

        Args:
            name: The property name to validate.

        Returns:
            bool: True if the property name is valid, else False.
        """
        return bool(re.match(r"^[a-zA-Z][a-zA-Z0-9-]*$", name))


# === Parser State ===


class ParserState:
    """Holds the state of the QSS parser, including rules and parsing context."""

    def __init__(self) -> None:
        """Initialize the parser state."""
        self.rules: List[QSSRule] = []
        self.buffer: str = ""
        self.in_comment: bool = False
        self.in_rule: bool = False
        self.in_variables: bool = False
        self.current_selectors: List[str] = []
        self.original_selector: Optional[str] = None
        self.current_rules: List[QSSRule] = []
        self.variable_buffer: str = ""
        self.current_line: int = 1
        self.property_lines: List[str] = []
        self.rule_start_line: int = 0

    def reset(self) -> None:
        """Reset the parser state to initial values."""
        self.rules = []
        self.buffer = ""
        self.in_comment = False
        self.in_rule = False
        self.in_variables = False
        self.current_selectors = []
        self.original_selector = None
        self.current_rules = []
        self.variable_buffer = ""
        self.current_line = 1
        self.property_lines = []
        self.rule_start_line = 0


# === Plugins ===


class QSSParserPlugin(ABC):
    """Abstract base class for QSS parser plugins."""

    @abstractmethod
    def process_line(
        self, line: str, state: ParserState, variable_manager: VariableManager
    ) -> bool:
        """
        Process a line of QSS text.

        Args:
            line: The line to process.
            state: The current parser state.
            variable_manager: Manager for resolving variables.

        Returns:
            bool: True if the line was handled, else False.
        """
        pass


class BaseQSSPlugin(QSSParserPlugin):
    """Abstract base class for QSS parser plugins, providing common functionality."""

    def __init__(self, error_handler: ErrorHandlerProtocol) -> None:
        """
        Initialize the base plugin.

        Args:
            error_handler: Callback for reporting errors.
        """
        self._error_handler = error_handler
        self._logger: logging.Logger = logging.getLogger(__name__)

    def _process_property_line(
        self,
        line: str,
        state: ParserState,
        property_processor: PropertyProcessorProtocol,
        variable_manager: VariableManager,
    ) -> bool:
        """
        Process a property line, handling buffering and splitting by semicolons.

        Args:
            line: The line to process.
            state: The current parser state.
            property_processor: Processor for handling individual properties.
            variable_manager: Manager for resolving variables.

        Returns:
            bool: True if the line was handled, else False.
        """
        line = line.strip()
        if (
            not state.in_rule
            or not state.current_rules
            or state.in_comment
            or state.in_variables
        ):
            return False

        if ";" in line:
            full_line = (state.buffer + " " + line).strip() if state.buffer else line
            state.buffer = ""
            parts = full_line.split(";")
            for part in parts[:-1]:
                if part.strip():
                    property_processor.process_property(
                        part.strip() + ";",
                        state.current_rules,
                        variable_manager,
                        state.current_line,
                    )
            if parts[-1].strip():
                state.buffer = parts[-1].strip()
            return True

        state.buffer = (state.buffer + " " + line).strip()
        return True


class SelectorPlugin(BaseQSSPlugin):
    """Plugin for handling QSS selector lines."""

    def __init__(
        self,
        property_processor: PropertyProcessorProtocol,
        rule_handler: RuleHandlerProtocol,
        error_handler: ErrorHandlerProtocol,
    ) -> None:
        """
        Initialize the selector plugin.

        Args:
            property_processor: Processor for handling properties.
            rule_handler: Handler for adding or merging rules.
            error_handler: Callback for reporting errors.
        """
        super().__init__(error_handler)
        self._property_processor = property_processor
        self._rule_handler = rule_handler

    def process_line(
        self, line: str, state: ParserState, variable_manager: VariableManager
    ) -> bool:
        """
        Process selector-related lines (e.g., starting/ending rules, complete rules).

        Args:
            line: The line to process.
            state: The current parser state.
            variable_manager: Manager for resolving variables.

        Returns:
            bool: True if the line was handled, else False.
        """
        line = line.strip()
        if not line or state.in_comment or state.in_variables:
            return False

        if SelectorUtils.is_complete_rule(line):
            self._process_complete_rule(line, state, variable_manager)
            return True

        if line.endswith(","):
            selector_part = line[:-1].strip()
            if selector_part:
                normalized_selector = SelectorUtils.normalize_selector(selector_part)
                selectors = [
                    s.strip() for s in normalized_selector.split(",") if s.strip()
                ]
                state.current_selectors.extend(selectors)
            return True

        if line.endswith("{") and not state.in_rule:
            state.buffer = ""
            state.property_lines = []
            selector_part = line[:-1].strip()
            if selector_part:
                normalized_selector = SelectorUtils.normalize_selector(selector_part)
                selectors = [
                    s.strip() for s in normalized_selector.split(",") if s.strip()
                ]
                state.current_selectors.extend(selectors)
            if not state.current_selectors and not selector_part:
                self._error_handler.dispatch_error(
                    f"Error on line {state.current_line}: Empty selector before '{{': {{"
                )
                state.in_rule = True
                state.rule_start_line = state.current_line
                return True
            full_selector = ", ".join(state.current_selectors)
            errors = SelectorUtils.validate_selector_syntax(
                full_selector, state.current_line
            )
            if errors:
                for error in errors:
                    self._error_handler.dispatch_error(error)
                if any("Duplicate selector" in error for error in errors):
                    seen_selectors = set()
                    unique_selectors = []
                    for sel in state.current_selectors:
                        if sel not in seen_selectors:
                            unique_selectors.append(sel)
                            seen_selectors.add(sel)
                    state.current_selectors = unique_selectors
                else:
                    state.current_selectors = []
                if not state.current_selectors:
                    state.in_rule = True
                    state.rule_start_line = state.current_line
                    return True
            state.original_selector = ", ".join(state.current_selectors)
            state.current_rules = [
                QSSRule(sel, original=f"{sel} {{\n") for sel in state.current_selectors
            ]
            state.in_rule = True
            state.rule_start_line = state.current_line
            state.current_selectors = []
            return True

        if line == "}" and state.in_rule:
            if state.property_lines:
                base_line = state.rule_start_line + 1
                for i, prop_line in enumerate(state.property_lines[:-1]):
                    line_num = base_line + i
                    if not prop_line.strip().endswith(";"):
                        self._error_handler.dispatch_error(
                            f"Error on line {line_num}: Property missing ';': {prop_line}"
                        )
                        continue
                    try:
                        self._property_processor.process_property(
                            prop_line,
                            state.current_rules,
                            variable_manager,
                            line_num,
                        )
                    except Exception as e:
                        self._error_handler.dispatch_error(
                            f"Error on line {line_num}: Invalid property: {prop_line} ({str(e)})"
                        )

                last_prop = state.property_lines[-1].strip()
                if last_prop:
                    line_num = base_line + len(state.property_lines) - 1
                    parts = last_prop.split(":", 1)
                    if len(parts) != 2 or not parts[0].strip() or not parts[1].strip():
                        self._error_handler.dispatch_error(
                            f"Error on line {line_num}: Invalid last property: {last_prop}"
                        )
                    else:
                        try:
                            self._property_processor.process_property(
                                last_prop
                                + (";" if not last_prop.endswith(";") else ""),
                                state.current_rules,
                                variable_manager,
                                line_num,
                            )
                        except Exception as e:
                            self._error_handler.dispatch_error(
                                f"Error on line {line_num}: Invalid last property: {last_prop} ({str(e)})"
                            )

            for rule in state.current_rules:
                rule.original += "}\n"
                self._rule_handler.handle_rule(rule)

            state.current_rules = []
            state.in_rule = False
            state.current_selectors = []
            state.original_selector = None
            state.property_lines = []
            state.buffer = ""
            state.rule_start_line = 0
            return True

        if line.endswith("{") and state.in_rule:
            self._error_handler.dispatch_error(
                f"Error on line {state.rule_start_line}: Unclosed brace '{{' for selector: {state.original_selector}"
            )
            state.current_rules = []
            state.in_rule = False
            state.current_selectors = []
            state.original_selector = None
            state.property_lines = []
            state.buffer = ""
            selector_part = line[:-1].strip()
            if selector_part:
                normalized_selector = SelectorUtils.normalize_selector(selector_part)
                selectors = [
                    s.strip() for s in normalized_selector.split(",") if s.strip()
                ]
                state.current_selectors.extend(selectors)
            if not state.current_selectors and not selector_part:
                self._error_handler.dispatch_error(
                    f"Error on line {state.current_line}: Empty selector before '{{': {{"
                )
                state.in_rule = True
                state.rule_start_line = state.current_line
                return True
            full_selector = ", ".join(state.current_selectors)
            errors = SelectorUtils.validate_selector_syntax(
                full_selector, state.current_line
            )
            if errors:
                for error in errors:
                    self._error_handler.dispatch_error(error)
                if any("Duplicate selector" in error for error in errors):
                    seen_selectors = set()
                    unique_selectors = []
                    for sel in state.current_selectors:
                        if sel not in seen_selectors:
                            unique_selectors.append(sel)
                            seen_selectors.add(sel)
                    state.current_selectors = unique_selectors
                else:
                    state.current_selectors = []
                if not state.current_selectors:
                    state.in_rule = True
                    state.rule_start_line = state.current_line
                    return True
            state.original_selector = ", ".join(state.current_selectors)
            state.current_rules = [
                QSSRule(sel, original=f"{sel} {{\n") for sel in state.current_selectors
            ]
            state.in_rule = True
            state.rule_start_line = state.current_line
            state.current_selectors = []
            return True

        return False

    def _process_complete_rule(
        self, line: str, state: ParserState, variable_manager: VariableManager
    ) -> None:
        """
        Process a complete QSS rule in a single line.

        Args:
            line: The line containing the complete rule.
            state: The current parser state.
            variable_manager: Manager for resolving variables.
        """
        match = re.match(r"^\s*([^/][^{}]*)\s*\{([^}]*)\}\s*$", line)
        if not match:
            self._error_handler.dispatch_error(
                f"Error on line {state.current_line}: Malformed rule: {line}"
            )
            return
        selector, properties = match.groups()
        normalized_selector = SelectorUtils.normalize_selector(selector.strip())
        selectors = [s.strip() for s in normalized_selector.split(",") if s.strip()]
        if not selectors:
            return
        state.current_selectors = selectors
        state.original_selector = normalized_selector
        state.current_rules = [
            QSSRule(sel, original=f"{sel} {{\n") for sel in selectors
        ]
        if properties.strip():
            prop_lines = [p.strip() for p in properties.split(";") if p.strip()]
            for i, prop_line in enumerate(prop_lines[:-1]):
                if not prop_line.endswith(";"):
                    self._error_handler.dispatch_error(
                        f"Error on line {state.current_line}: Property missing ';': {prop_line}"
                    )
                    continue
                try:
                    self._property_processor.process_property(
                        prop_line,
                        state.current_rules,
                        variable_manager,
                        state.current_line,
                    )
                except Exception as e:
                    self._error_handler.dispatch_error(
                        f"Error on line {state.current_line}: Invalid property: {prop_line} ({str(e)})"
                    )
            last_prop = prop_lines[-1].strip()
            if last_prop:
                parts = last_prop.split(":", 1)
                if len(parts) != 2 or not parts[0].strip() or not parts[1].strip():
                    self._error_handler.dispatch_error(
                        f"Error on line {state.current_line}: Invalid last property: {last_prop}"
                    )
                else:
                    try:
                        self._property_processor.process_property(
                            last_prop + (";" if not last_prop.endswith(";") else ""),
                            state.current_rules,
                            variable_manager,
                            state.current_line,
                        )
                    except Exception as e:
                        self._error_handler.dispatch_error(
                            f"Error on line {state.current_line}: Invalid last property: {last_prop} ({str(e)})"
                        )

        for rule in state.current_rules:
            if rule.properties:
                rule.original += "}\n"
                self._rule_handler.handle_rule(rule)

        state.current_rules = []
        state.current_selectors = []
        state.original_selector = None
        state.property_lines = []


class PropertyPlugin(BaseQSSPlugin):
    """Plugin for handling QSS property lines."""

    def __init__(
        self,
        property_processor: PropertyProcessorProtocol,
        error_handler: ErrorHandlerProtocol,
    ) -> None:
        """
        Initialize the property plugin.

        Args:
            property_processor: Processor for handling properties.
            error_handler: Callback for reporting errors.
        """
        super().__init__(error_handler)
        self._property_processor = property_processor

    def process_line(
        self, line: str, state: ParserState, variable_manager: VariableManager
    ) -> bool:
        """
        Collect property-related lines within a rule for later processing.

        Args:
            line: The line to process.
            state: The current parser state.
            variable_manager: Manager for resolving variables.

        Returns:
            bool: True if the line was handled as a property, else False.
        """
        line = line.strip()
        if not state.in_rule or state.in_comment or state.in_variables:
            return False
        if line.endswith("{") or line == "}":
            return False
        if line:
            state.property_lines.append(line)
        return True


class VariablePlugin(QSSParserPlugin):
    """Plugin for handling QSS @variables blocks."""

    def __init__(self, error_handler: ErrorHandlerProtocol) -> None:
        """
        Initialize the variable plugin.

        Args:
            error_handler: Callback for reporting errors during variable parsing.
        """
        self._error_handler = error_handler
        self._logger: logging.Logger = logging.getLogger(__name__)

    def process_line(
        self, line: str, state: ParserState, variable_manager: VariableManager
    ) -> bool:
        """
        Process variable-related lines (e.g., @variables blocks).

        Args:
            line: The line to process.
            state: The current parser state.
            variable_manager: Manager for resolving variables.

        Returns:
            bool: True if the line was handled, else False.
        """
        line = line.strip()
        if state.in_comment:
            if "*/" in line:
                state.in_comment = False
            return True
        if line.startswith("/*"):
            state.in_comment = True
            return True
        if line == "@variables {" and not state.in_rule:
            state.in_variables = True
            state.variable_buffer = ""
            return True
        if state.in_variables:
            if line == "}":

                def dispatch_variable_defined(name: str, value: str) -> None:
                    if isinstance(self._error_handler, QSSParser):
                        for handler in self._error_handler._event_handlers.get(
                            "variable_defined", []
                        ):
                            handler(name, value)

                errors = variable_manager.parse_variables(
                    state.variable_buffer,
                    state.current_line,
                    on_variable_defined=dispatch_variable_defined,
                )
                for error in errors:
                    self._error_handler.dispatch_error(error)
                state.in_variables = False
                state.variable_buffer = ""
                return True
            state.variable_buffer = (state.variable_buffer + " " + line).strip()
            return True
        return False


# === Main Parser ===


class QSSParser:
    """Main QSS parser for parsing and applying styles to widgets."""

    def __init__(
        self,
        property_processor: Optional[PropertyProcessorProtocol] = None,
        plugins: Optional[List[QSSParserPlugin]] = None,
    ) -> None:
        """
        Initialize the QSS parser.

        Args:
            property_processor: Custom processor for handling properties, by default None (uses DefaultPropertyProcessor).
            plugins: List of plugins for custom parsing logic, by default None (uses default plugins).
        """
        self._state: ParserState = ParserState()
        self._style_selector: QSSStyleSelector = QSSStyleSelector()
        self._variable_manager: VariableManager = VariableManager()
        self._event_handlers: Dict[str, List[Callable[..., None]]] = {
            "rule_added": [],
            "error_found": [],
            "variable_defined": [],
            "parse_completed": [],
        }
        self._rule_map: Dict[str, QSSRule] = {}
        self._logger: logging.Logger = logging.getLogger(__name__)

        self._error_handler: ErrorHandlerProtocol = self
        self._property_processor: PropertyProcessorProtocol = (
            property_processor if property_processor else DefaultPropertyProcessor(self)
        )

        self._plugins: List[QSSParserPlugin] = plugins or [
            VariablePlugin(self._error_handler),
            SelectorPlugin(self._property_processor, self, self._error_handler),
            PropertyPlugin(self._property_processor, self._error_handler),
        ]

    def dispatch_error(self, error: str) -> None:
        """
        Dispatch an error message to registered handlers.

        Args:
            error: The error message to dispatch.
        """
        self._logger.warning(f"Error: {error}")
        for handler in self._event_handlers["error_found"]:
            handler(error)

    def handle_rule(self, rule: QSSRule) -> None:
        """
        Handle a new or updated rule, merging with existing rules if necessary.

        Args:
            rule: The rule to add or merge.
        """
        self._logger.debug(f"Handling rule: {rule.selector}")
        existing_rule = self._rule_map.get(rule.selector)
        if existing_rule:
            prop_map = {p.name: p for p in existing_rule.properties}
            for prop in rule.properties:
                prop_map[prop.name] = prop
            existing_rule.properties = list(prop_map.values())
            existing_rule.original = QSSFormatter.format_rule(
                existing_rule.selector, existing_rule.properties
            )
            for handler in self._event_handlers["rule_added"]:
                handler(existing_rule)
        else:
            self._rule_map[rule.selector] = rule
            self._state.rules.append(rule)
            for handler in self._event_handlers["rule_added"]:
                handler(rule)

        if (
            ":" in rule.selector
            and "::" not in rule.selector
            and "," not in rule.selector
        ):
            base_rule = rule.clone_without_pseudo_elements()
            base_selector = base_rule.selector
            existing_base = self._rule_map.get(base_selector)
            if existing_base:
                prop_map = {p.name: p for p in existing_base.properties}
                for prop in base_rule.properties:
                    prop_map[prop.name] = prop
                existing_base.properties = list(prop_map.values())
                existing_base.original = QSSFormatter.format_rule(
                    base_selector, existing_base.properties
                )
                for handler in self._event_handlers["rule_added"]:
                    handler(existing_base)
            else:
                self._rule_map[base_selector] = base_rule
                self._state.rules.append(base_rule)
                for handler in self._event_handlers["rule_added"]:
                    handler(base_rule)

    def on(self, event: str, handler: Callable[..., None]) -> None:
        """
        Register an event handler for parser events.

        Args:
            event: The event to listen for ('rule_added', 'error_found', 'variable_defined', 'parse_completed').
            handler: The function to call when the event occurs.
        """
        if event in self._event_handlers:
            self._event_handlers[event].append(handler)
            self._logger.debug(f"Registered handler for event: {event}")

    def parse(self, qss_text: str) -> None:
        """
        Parse QSS text into a list of QSSRule objects, resolving variables and reporting errors.

        Args:
            qss_text: The QSS text to parse, including @variables blocks.
        """
        self._reset()
        lines = qss_text.splitlines()
        for line in lines:
            self._process_line(line)
            self._state.current_line += 1
        if self._state.buffer.strip():
            try:
                self._property_processor.process_property(
                    self._state.buffer,
                    self._state.current_rules,
                    self._variable_manager,
                    self._state.current_line,
                )
            except Exception as e:
                self.dispatch_error(
                    f"Error on line {self._state.current_line}: Invalid property: {self._state.buffer} ({str(e)})"
                )
        if self._state.variable_buffer.strip():
            errors = self._variable_manager.parse_variables(
                self._state.variable_buffer, self._state.current_line
            )
            for error in errors:
                self.dispatch_error(error)
        if self._state.in_rule and self._state.current_rules:
            self.dispatch_error(
                f"Error on line {self._state.rule_start_line}: Unclosed brace '{{' for selector: {self._state.original_selector}"
            )
            self._state.current_rules = []
            self._state.in_rule = False
            self._state.current_selectors = []
            self._state.original_selector = None
            self._state.rule_start_line = 0
        for handler in self._event_handlers["parse_completed"]:
            handler()
        self._logger.debug("Parsing completed and parse_completed event dispatched")

    def _reset(self) -> None:
        """Reset the parser's internal state."""
        self._state.reset()
        self._variable_manager = VariableManager()
        self._rule_map.clear()
        self._logger.debug("Parser state reset")

    def _process_line(self, line: str) -> None:
        """
        Process a single line of QSS text using plugins.

        Args:
            line: The line to process.
        """
        line = line.strip()
        if not line:
            return

        if (
            not self._state.in_rule
            and not self._state.in_variables
            and not self._state.in_comment
            and ":" in line
            and line.endswith(";")
        ):
            self.dispatch_error(
                f"Error on line {self._state.current_line}: Property outside block: {line}"
            )
            return

        for plugin in self._plugins:
            if plugin.process_line(line, self._state, self._variable_manager):
                break

    def get_styles_for(
        self,
        widget: WidgetProtocol,
        fallback_class: Optional[str] = None,
        additional_selectors: Optional[List[str]] = None,
        include_class_if_object_name: bool = False,
    ) -> str:
        """
        Retrieve QSS styles for a given widget.

        Args:
            widget: The widget to retrieve styles for.
            fallback_class: Fallback class to use if no styles are found, by default None.
            additional_selectors: Additional selectors to include, by default None.
            include_class_if_object_name: Whether to include class styles if an object name is present, by default False.

        Returns:
            str: The concatenated QSS styles for the widget.
        """
        return self._style_selector.get_styles_for(
            self._state.rules,
            widget,
            fallback_class,
            additional_selectors,
            include_class_if_object_name,
        )

    def __repr__(self) -> str:
        """Return a string representation of the parser."""
        return self.to_string()

    def to_string(self) -> str:
        """
        Return a string representation of the parser in standard QSS format.

        Returns:
            str: The formatted QSS string.
        """
        return "\n".join(
            QSSFormatter.format_rule(rule.selector, rule.properties)
            for rule in self._state.rules
        )


class QSSStyleSelector:
    """Selects and formats QSS styles for a given widget based on rules."""

    def __init__(self) -> None:
        """Initialize the QSS style selector."""
        self._logger: logging.Logger = logging.getLogger(__name__)

    def get_styles_for(
        self,
        rules: List[QSSRule],
        widget: WidgetProtocol,
        fallback_class: Optional[str] = None,
        additional_selectors: Optional[List[str]] = None,
        include_class_if_object_name: bool = False,
    ) -> str:
        """
        Retrieve QSS styles for a widget from a list of rules.

        Args:
            rules: List of QSSRule objects to search.
            widget: The widget to retrieve styles for.
            fallback_class: Fallback class to use if no styles are found, by default None.
            additional_selectors: Additional selectors to include, by default None.
            include_class_if_object_name: Whether to include class styles if an object name is present, by default False.

        Returns:
            str: The concatenated QSS styles for the widget.
        """
        object_name: str = widget.objectName()
        class_name: str = widget.metaObject().className()
        styles: Set[QSSRule] = set()

        self._logger.debug(
            f"Retrieving styles for widget: objectName={object_name}, className={class_name}"
        )

        if object_name:
            styles.update(
                self._get_rules_for_selector(
                    rules, f"#{object_name}", object_name, class_name
                )
            )
            if include_class_if_object_name:
                styles.update(
                    self._get_rules_for_selector(
                        rules, class_name, object_name, class_name
                    )
                )

        if not object_name or not styles:
            styles.update(
                self._get_rules_for_selector(rules, class_name, object_name, class_name)
            )

        if fallback_class and not styles:
            styles.update(
                self._get_rules_for_selector(
                    rules, fallback_class, object_name, class_name
                )
            )

        if additional_selectors:
            for selector in additional_selectors:
                styles.update(
                    self._get_rules_for_selector(
                        rules, selector, object_name, class_name
                    )
                )

        unique_styles = sorted(set(styles), key=lambda r: r.selector)
        result = "\n".join(r.original.rstrip("\n") for r in unique_styles)
        self._logger.debug(f"Styles retrieved: {result}")
        return result

    def _get_rules_for_selector(
        self, rules: List[QSSRule], selector: str, object_name: str, class_name: str
    ) -> List[QSSRule]:
        """
        Retrieve rules matching a given selector, considering objectName and className constraints.

        Args:
            rules: List of QSSRule objects to search.
            selector: The selector to match (e.g., 'QPushButton', '#myButton').
            object_name: The widget's objectName.
            class_name: The widget's className.

        Returns:
            List[QSSRule]: List of matching QSS rules.
        """
        matching_rules: Set[QSSRule] = set()
        base_selector = selector.split("::")[0].split(":")[0].strip()

        for rule in rules:
            rule_selectors = [s.strip() for s in rule.selector.split(",")]
            for sel in rule_selectors:
                if sel == selector:
                    matching_rules.add(rule)
                    continue

                sel_without_attrs = Constants.COMPILED_ATTRIBUTE_PATTERN.sub(
                    "", sel
                ).strip()
                if not re.search(r"[> ]+", sel_without_attrs):
                    part_base = sel_without_attrs.split("::")[0].split(":")[0].strip()
                    if part_base == base_selector:
                        if (
                            base_selector.startswith("#")
                            and base_selector[1:] != object_name
                        ):
                            continue
                        if (
                            not base_selector.startswith("#")
                            and base_selector != class_name
                        ):
                            continue
                        matching_rules.add(rule)
                    continue

                sel_parts = [
                    part.strip()
                    for part in re.split(r"[> ]+", sel_without_attrs)
                    if part.strip()
                ]
                class_match = False
                object_match = True
                for part in sel_parts:
                    part_base = part.split("::")[0].split(":")[0].strip()
                    if part_base == class_name:
                        class_match = True
                    elif part_base.startswith("#") and part_base[1:] != object_name:
                        object_match = False
                        break

                if class_match and object_match:
                    matching_rules.add(rule)

        return list(matching_rules)
