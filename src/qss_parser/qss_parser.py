import logging
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import (
    Callable,
    Dict,
    Final,
    List,
    Match,
    Optional,
    Pattern,
    Protocol,
    Set,
    Tuple,
    TypedDict,
)


class Constants:
    """
    A class containing constant values and patterns used throughout the QSS parser.

    This class defines regular expression patterns and lists of valid pseudo-elements
    and pseudo-states used in Qt Style Sheets (QSS).

    Attributes:
        ATTRIBUTE_PATTERN (str): Regular expression pattern for matching QSS attribute selectors.
        COMPILED_ATTRIBUTE_PATTERN (Pattern[str]): Compiled version of ATTRIBUTE_PATTERN for better performance.
        VARIABLE_PATTERN (str): Regular expression pattern for matching QSS variable declarations.
        COMPLETE_RULE_PATTERN (str): Regular expression pattern for matching complete QSS rules.
        PSEUDO_PATTERN (str): Regular expression pattern for matching pseudo-elements and pseudo-states.
        CLASS_ID_PATTERN (str): Regular expression pattern for matching class and ID combinations.
        COMBINATOR_PATTERN (str): Regular expression pattern for matching QSS combinators.
        PSEUDO_ELEMENTS (List[str]): List of valid QSS pseudo-elements.
        PSEUDO_STATES (List[str]): List of valid QSS pseudo-states.
    """

    ATTRIBUTE_PATTERN: Final[str] = (
        r'\[\w+(?:(?:~|=|\|=|\^=|\$=|\*=)(?:"[^"]*"|[^\s"\]]*))?[^[]*\]'
    )
    COMPILED_ATTRIBUTE_PATTERN: Final[Pattern[str]] = re.compile(ATTRIBUTE_PATTERN)
    VARIABLE_PATTERN: Final[str] = r"var\((--[\w-]+)\)"
    COMPLETE_RULE_PATTERN: Final[str] = r"^\s*[^/][^{}]*\s*\{[^}]*\}\s*$"
    PSEUDO_PATTERN: Final[str] = r"(\w+|#[-\w]+|\[.*?\])\s*(:{1,2})\s*([-\w]+)"
    CLASS_ID_PATTERN: Final[str] = r"(\w+)(#[-\w]+)"
    COMBINATOR_PATTERN: Final[str] = (
        r"(\w+|#[-\w]+|\[.*?\])([> ]{1,2})(\w+|#[-\w]+|\[.*?\])"
    )

    PSEUDO_ELEMENTS: Final[List[str]] = [
        "::add-line",
        "::add-page",
        "::branch",
        "::chunk",
        "::close-button",
        "::corner",
        "::down-arrow",
        "::down-button",
        "::drop-down",
        "::float-button",
        "::groove",
        "::indicator",
        "::handle",
        "::icon",
        "::item",
        "::left-arrow",
        "::menu-arrow",
        "::menu-button",
        "::menu-indicator",
        "::right-arrow",
        "::pane",
        "::scroller",
        "::section",
        "::separator",
        "::sub-line",
        "::sub-page",
        "::tab",
        "::tab-bar",
        "::tear",
        "::tearoff",
        "::text",
        "::title",
        "::up-arrow",
        "::up-button",
        "::horizontalHeader",  # SUBWIDGET (SubControl) - Refactor in future
        "::verticalHeader",  # SUBWIDGET (SubControl) - Refactor in future
    ]
    PSEUDO_STATES: Final[List[str]] = [
        ":active",
        ":adjoins-item",
        ":alternate",
        ":bottom",
        ":checked",
        ":closable",
        ":closed",
        ":default",
        ":disabled",
        ":editable",
        ":edit-focus",
        ":enabled",
        ":exclusive",
        ":first",
        ":flat",
        ":floatable",
        ":focus",
        ":has-children",
        ":has-siblings",
        ":horizontal",
        ":hover",
        ":indeterminate",
        ":last",
        ":left",
        ":maximized",
        ":middle",
        ":minimized",
        ":movable",
        ":no-frame",
        ":non-exclusive",
        ":off",
        ":on",
        ":only-one",
        ":open",
        ":next-selected",
        ":pressed",
        ":previous-selected",
        ":read-only",
        ":right",
        ":selected",
        ":top",
        ":unchecked",
        ":vertical",
        ":window",
    ]


class MetaObjectProtocol(Protocol):
    """
    Protocol defining the interface for Qt meta objects.

    This protocol represents the minimal interface required for accessing
    Qt meta object information, specifically the class name.
    """

    def className(self) -> str: ...


class WidgetProtocol(Protocol):
    """
    Protocol defining the interface for Qt widgets.

    This protocol represents the minimal interface required for accessing
    Qt widget information, including object name and meta object data.
    """

    def objectName(self) -> str: ...
    def metaObject(self) -> MetaObjectProtocol: ...


class PropertyProcessorProtocol(Protocol):
    """
    Protocol defining the interface for QSS property processors.

    This protocol defines how property lines in QSS should be processed
    and added to rules.
    """

    def process_property(
        self,
        line: str,
        rules: List["QSSRule"],
        variable_manager: "VariableManager",
        line_num: int,
    ) -> None: ...


class RuleHandlerProtocol(Protocol):
    """
    Protocol defining the interface for QSS rule handlers.

    This protocol defines how QSS rules should be handled after they
    are parsed and validated.
    """

    def handle_rule(self, rule: "QSSRule") -> None: ...


class ErrorHandlerProtocol(Protocol):
    """
    Protocol defining the interface for error handlers.

    This protocol defines how parsing errors should be handled and
    dispatched during QSS processing.
    """

    def dispatch_error(self, error: str) -> None: ...


class QSSPropertyDict(TypedDict):
    """
    TypedDict defining the structure of a QSS property dictionary.

    Attributes:
        name (str): The name of the QSS property.
        value (str): The value of the QSS property.
    """

    name: str
    value: str


@dataclass
class QSSProperty:
    """
    A dataclass representing a QSS property with its name and value.

    This class handles the storage and formatting of individual QSS properties,
    ensuring proper string formatting and dictionary conversion.

    Attributes:
        name (str): The name of the QSS property.
        value (str): The value of the QSS property.
    """

    name: str
    value: str

    def __post_init__(self) -> None:
        """
        Post-initialization hook that strips whitespace from name and value.
        """
        object.__setattr__(self, "name", self.name.strip())
        object.__setattr__(self, "value", self.value.strip())

    def __repr__(self) -> str:
        """
        Returns a string representation of the property in QSS format.

        Returns:
            str: The property formatted as "name: value"
        """
        return f"{self.name}: {self.value}"

    def to_dict(self) -> QSSPropertyDict:
        """
        Converts the property to a dictionary format.

        Returns:
            QSSPropertyDict: A dictionary containing the property name and value.
        """
        return {"name": self.name, "value": self.value}


class QSSRule:
    """
    A class representing a QSS rule with its selector and properties.

    This class handles the parsing and storage of QSS rules, including selector
    parsing and property management.

    Attributes:
        selector (str): The CSS selector for this rule.
        properties (List[QSSProperty]): List of properties associated with this rule.
        object_name (Optional[str]): The object name extracted from the selector.
        class_name (Optional[str]): The class name extracted from the selector.
        attributes (List[str]): List of attributes extracted from the selector.
        pseudo_states (List[str]): List of pseudo-states extracted from the selector.
    """

    def __init__(self, selector: str) -> None:
        """
        Initialize a QSS rule with the given selector.

        Args:
            selector (str): The CSS selector for this rule.
        """
        self.selector: str = selector.strip()
        self.properties: List[QSSProperty] = []
        self.object_name: Optional[str] = None
        self.class_name: Optional[str] = None
        self.attributes: List[str] = []
        self.pseudo_states: List[str] = []
        self._parse_selector()

    def _parse_selector(self) -> None:
        """
        Parse the selector to extract object name, class name, attributes,
        and pseudo-states.
        """
        (
            self.object_name,
            self.class_name,
            self.attributes,
            self.pseudo_states,
        ) = SelectorUtils.parse_selector(self.selector)

    def add_property(self, name: str, value: str) -> None:
        """
        Add a new property to the rule.

        Args:
            name (str): The name of the property.
            value (str): The value of the property.
        """
        self.properties.append(QSSProperty(name, value))

    def clone_without_pseudo_elements(self) -> "QSSRule":
        """
        Create a copy of this rule without pseudo-elements.

        Returns:
            QSSRule: A new rule with the same properties but without pseudo-elements
                    in the selector.
        """
        base_selector = self.selector.split("::")[0]
        clone = QSSRule(base_selector)
        clone.properties = self.properties.copy()
        return clone

    def __repr__(self) -> str:
        """
        Returns a string representation of the rule in QSS format.

        Returns:
            str: The rule formatted as "selector { properties }".
        """
        props = "\n\t".join(str(p) for p in self.properties)
        return f"{self.selector} {{\n\t{props}\n}}"

    def __hash__(self) -> int:
        """
        Calculate a hash value for the rule based on its selector and properties.

        Returns:
            int: Hash value for the rule.
        """
        return hash((self.selector, tuple((p.name, p.value) for p in self.properties)))

    def __eq__(self, other: object) -> bool:
        """
        Compare this rule with another for equality.

        Args:
            other (object): Another object to compare with.

        Returns:
            bool: True if the rules are equal, False otherwise.
        """
        if not isinstance(other, QSSRule):
            return False
        return self.selector == other.selector and self.properties == other.properties


class VariableManager:
    """
    A class for managing QSS variables and their values.

    This class handles the parsing, storage, and resolution of QSS variables,
    including handling of circular references and undefined variables.

    Attributes:
        _variables (dict): Dictionary storing variable names and their values.
        _logger (logging.Logger): Logger instance for debugging and error reporting.
    """

    def __init__(self) -> None:
        """
        Initialize a new VariableManager instance.
        """
        self._variables: Dict[str, str] = {}
        self._logger = logging.getLogger(__name__)

    def parse_variables(
        self,
        block: str,
        start_line: int = 1,
        on_variable_defined: Optional[Callable[[str, str], None]] = None,
    ) -> List[str]:
        """
        Parse a block of variable declarations.

        Args:
            block (str): The text block containing variable declarations.
            start_line (int, optional): The starting line number for error reporting. Defaults to 1.
            on_variable_defined (Optional[Callable[[str, str], None]], optional): Callback function
                called when a variable is defined. Defaults to None.

        Returns:
            List[str]: List of error messages encountered during parsing.
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
        Resolve variable references in a value string.

        This method handles nested variable references and detects circular references.

        Args:
            value (str): The value string that may contain variable references.

        Returns:
            Tuple[str, Optional[str]]: A tuple containing:
                - The resolved value string
                - An error message if any errors occurred, None otherwise
        """
        visited: Set[str] = set()
        errors: List[str] = []

        def replace_var(match: Match[str]) -> str:
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
    """
    A utility class for handling QSS selectors.

    This class provides static methods for parsing, validating, and manipulating
    QSS selectors, including handling of attributes, pseudo-states, and
    selector normalization.
    """

    @staticmethod
    def is_complete_rule(line: str) -> bool:
        """
        Check if a line contains a complete QSS rule.

        Args:
            line (str): The line to check.

        Returns:
            bool: True if the line contains a complete rule, False otherwise.
        """
        return bool(re.match(Constants.COMPLETE_RULE_PATTERN, line))

    @staticmethod
    def extract_attributes(selector: str) -> List[str]:
        """
        Extract attribute selectors from a QSS selector.

        Args:
            selector (str): The selector to extract attributes from.

        Returns:
            List[str]: List of attribute selectors found in the selector.
        """
        return Constants.COMPILED_ATTRIBUTE_PATTERN.findall(selector)

    @staticmethod
    def normalize_selector(selector: str) -> str:
        """
        Normalize a QSS selector by standardizing spacing and formatting.

        This method handles attribute selectors, class-id combinations, and
        combinator spacing.

        Args:
            selector (str): The selector to normalize.

        Returns:
            str: The normalized selector string.
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
        Parse a QSS selector into its components.

        Args:
            selector (str): The selector to parse.

        Returns:
            Tuple[Optional[str], Optional[str], List[str], List[str]]: A tuple containing:
                - object_name: The object name if present, None otherwise
                - class_name: The class name if present, None otherwise
                - attributes: List of attribute selectors
                - pseudo_states: List of pseudo-states
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
        Validate the syntax of a QSS selector.

        This method checks for various syntax errors including:
        - Duplicate selectors in comma-separated lists
        - Invalid pseudo-states
        - Malformed attribute selectors
        - Invalid spacing
        - Invalid combinators

        Args:
            selector (str): The selector to validate.
            line_num (int): The line number for error reporting.

        Returns:
            List[str]: List of error messages for any syntax errors found.
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
                pseudo_full = f"{colon}{pseudo}"
                if colon == "::" and pseudo_full not in Constants.PSEUDO_ELEMENTS:
                    errors.append(
                        f"Error on line {line_num}: Invalid pseudo-element '{pseudo_full}' in selector: '{sel}'. "
                        f"Must be one of {', '.join(Constants.PSEUDO_ELEMENTS)}"
                    )
                elif colon == ":" and pseudo_full not in Constants.PSEUDO_STATES:
                    errors.append(
                        f"Error on line {line_num}: Invalid pseudo-state '{pseudo_full}' in selector: '{sel}'. "
                        f"Must be one of {', '.join(Constants.PSEUDO_STATES)}"
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
    """
    A utility class for formatting QSS rules.

    This class provides static methods for converting QSS rules into properly
    formatted strings suitable for output or display.
    """

    @staticmethod
    def format_rule(selector: str, properties: List[QSSProperty]) -> str:
        """
        Format a QSS rule with its selector and properties.

        This method normalizes the selector and formats the properties with
        proper indentation and line breaks.

        Args:
            selector (str): The selector for the rule.
            properties (List[QSSProperty]): List of properties to format.

        Returns:
            str: The formatted QSS rule as a string.
        """
        normalized_selector = SelectorUtils.normalize_selector(selector)
        props = "\n".join(f"    {p.name}: {p.value};" for p in properties)
        return f"{normalized_selector} {{\n{props}\n}}\n"


class DefaultPropertyProcessor:
    """
    Default implementation of the PropertyProcessorProtocol.

    This class handles the processing of QSS property declarations, including
    validation and variable resolution.

    Attributes:
        _error_handler (ErrorHandlerProtocol): Handler for reporting errors.
        _logger (logging.Logger): Logger instance for debugging and error reporting.
    """

    def __init__(self, error_handler: ErrorHandlerProtocol) -> None:
        """
        Initialize a new DefaultPropertyProcessor instance.

        Args:
            error_handler (ErrorHandlerProtocol): Handler for reporting errors.
        """
        self._error_handler = error_handler
        self._logger = logging.getLogger(__name__)

    def process_property(
        self,
        line: str,
        rules: List[QSSRule],
        variable_manager: VariableManager,
        line_num: int,
    ) -> None:
        """
        Process a QSS property line and add it to the rules.

        This method validates the property syntax, resolves any variables,
        and adds the property to all applicable rules.

        Args:
            line (str): The property line to process.
            rules (List[QSSRule]): List of rules to add the property to.
            variable_manager (VariableManager): Manager for resolving variables.
            line_num (int): The line number for error reporting.
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
            rule.add_property(name, resolved_value)
        self._logger.debug(f"Processed property on line {line_num}: {normalized_line}")

    def _is_valid_property_name(self, name: str) -> bool:
        """
        Check if a property name is valid according to QSS syntax rules.

        Args:
            name (str): The property name to validate.

        Returns:
            bool: True if the property name is valid, False otherwise.
        """
        if name.startswith("qproperty-"):
            return bool(re.match(r"^qproperty-[a-zA-Z_][a-zA-Z0-9_-]*$", name))
        else:
            return bool(re.match(r"^[a-zA-Z][a-zA-Z0-9-]*$", name))


@dataclass
class ParserState:
    """
    A dataclass representing the state of the QSS parser.

    This class maintains the current state of the parser, including rules being processed,
    buffers, flags, and line tracking information.

    Attributes:
        rules (List[QSSRule]): List of all parsed QSS rules.
        buffer (str): Buffer for accumulating partial property declarations.
        in_comment (bool): Flag indicating if currently parsing a comment.
        in_rule (bool): Flag indicating if currently parsing a rule.
        in_variables (bool): Flag indicating if currently parsing variables.
        current_selectors (List[str]): List of selectors being processed.
        original_selector (Optional[str]): Original selector text before processing.
        current_rules (List[QSSRule]): List of rules currently being processed.
        variable_buffer (str): Buffer for accumulating variable declarations.
        current_line (int): Current line number being processed.
        property_lines (List[str]): List of property lines in current rule.
        rule_start_line (int): Line number where current rule started.
    """

    rules: List[QSSRule] = field(default_factory=list)
    buffer: str = ""
    in_comment: bool = False
    in_rule: bool = False
    in_variables: bool = False
    current_selectors: List[str] = field(default_factory=list)
    original_selector: Optional[str] = None
    current_rules: List[QSSRule] = field(default_factory=list)
    variable_buffer: str = ""
    current_line: int = 1
    property_lines: List[str] = field(default_factory=list)
    rule_start_line: int = 0

    def reset(self) -> None:
        """
        Reset the parser state to its initial values.

        This method clears all buffers and resets all flags and counters
        to their default values.
        """
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


class QSSParserPlugin(ABC):
    """
    Abstract base class for QSS parser plugins.

    This class defines the interface that all parser plugins must implement
    to process QSS content.
    """

    @abstractmethod
    def process_line(
        self, line: str, state: ParserState, variable_manager: VariableManager
    ) -> bool:
        """
        Process a single line of QSS content.

        Args:
            line (str): The line to process.
            state (ParserState): Current state of the parser.
            variable_manager (VariableManager): Manager for handling variables.

        Returns:
            bool: True if the line was processed by this plugin, False otherwise.
        """
        pass


class BaseQSSPlugin(QSSParserPlugin):
    """
    Base implementation of QSSParserPlugin.

    This class provides common functionality for QSS parser plugins, including
    error handling and property line processing.

    Attributes:
        _error_handler (ErrorHandlerProtocol): Handler for reporting errors.
        _logger (logging.Logger): Logger instance for debugging and error reporting.
    """

    def __init__(self, error_handler: ErrorHandlerProtocol) -> None:
        """
        Initialize a new BaseQSSPlugin instance.

        Args:
            error_handler (ErrorHandlerProtocol): Handler for reporting errors.
        """
        self._error_handler = error_handler
        self._logger = logging.getLogger(__name__)

    def _process_property_line(
        self,
        line: str,
        state: ParserState,
        property_processor: PropertyProcessorProtocol,
        variable_manager: VariableManager,
    ) -> bool:
        """
        Process a line containing QSS property declarations.

        This method handles both complete and partial property declarations,
        accumulating them in the state buffer as needed.

        Args:
            line (str): The line to process.
            state (ParserState): Current state of the parser.
            property_processor (PropertyProcessorProtocol): Processor for handling properties.
            variable_manager (VariableManager): Manager for handling variables.

        Returns:
            bool: True if the line was processed as a property line, False otherwise.
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
    """
    Plugin for handling QSS selectors and rules.

    This plugin processes selector declarations and manages rule creation,
    including handling of complete rules, rule start/end, and property processing.

    Attributes:
        _property_processor (PropertyProcessorProtocol): Processor for handling properties.
        _rule_handler (RuleHandlerProtocol): Handler for managing rules.
        _error_handler (ErrorHandlerProtocol): Handler for reporting errors.
    """

    def __init__(
        self,
        property_processor: PropertyProcessorProtocol,
        rule_handler: RuleHandlerProtocol,
        error_handler: ErrorHandlerProtocol,
    ) -> None:
        """
        Initialize a new SelectorPlugin instance.

        Args:
            property_processor (PropertyProcessorProtocol): Processor for handling properties.
            rule_handler (RuleHandlerProtocol): Handler for managing rules.
            error_handler (ErrorHandlerProtocol): Handler for reporting errors.
        """
        super().__init__(error_handler)
        self._property_processor = property_processor
        self._rule_handler = rule_handler

    def process_line(
        self, line: str, state: ParserState, variable_manager: VariableManager
    ) -> bool:
        """
        Process a line of QSS content, handling selectors and rules.

        This method handles complete rules, selector parts, and rule boundaries.

        Args:
            line (str): The line to process.
            state (ParserState): Current state of the parser.
            variable_manager (VariableManager): Manager for handling variables.

        Returns:
            bool: True if the line was processed by this plugin, False otherwise.
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
            return self._start_rule(line, state, variable_manager)

        if line == "}" and state.in_rule:
            return self._end_rule(state, variable_manager)

        if line.endswith("{") and state.in_rule:
            self._error_handler.dispatch_error(
                f"Error on line {state.rule_start_line}: Unclosed brace '{{' for selector: {state.original_selector}"
            )
            return self._start_rule(line, state, variable_manager)

        return False

    def _start_rule(
        self, line: str, state: ParserState, variable_manager: VariableManager
    ) -> bool:
        """
        Start processing a new QSS rule.

        This method handles the opening of a new rule block, including selector
        validation and rule creation.

        Args:
            line (str): The line containing the rule start.
            state (ParserState): Current state of the parser.
            variable_manager (VariableManager): Manager for handling variables.

        Returns:
            bool: True if the rule was successfully started.
        """
        state.buffer = ""
        state.property_lines = []
        selector_part = line[:-1].strip()
        if selector_part:
            normalized_selector = SelectorUtils.normalize_selector(selector_part)
            selectors = [s.strip() for s in normalized_selector.split(",") if s.strip()]
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
                        seen_selectors.add(sel)
                        unique_selectors.append(sel)
                state.current_selectors = unique_selectors
            else:
                state.current_selectors = []
            if not state.current_selectors:
                state.in_rule = True
                state.rule_start_line = state.current_line
                return True

        state.original_selector = ", ".join(state.current_selectors)
        state.current_rules = [QSSRule(sel) for sel in state.current_selectors]
        state.in_rule = True
        state.rule_start_line = state.current_line
        state.current_selectors = []
        return True

    def _end_rule(self, state: ParserState, variable_manager: VariableManager) -> bool:
        """
        End processing of the current QSS rule.

        This method handles the closing of a rule block, including property
        processing and rule finalization.

        Args:
            state (ParserState): Current state of the parser.
            variable_manager (VariableManager): Manager for handling variables.

        Returns:
            bool: True if the rule was successfully ended.
        """
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
                            last_prop + (";" if not last_prop.endswith(";") else ""),
                            state.current_rules,
                            variable_manager,
                            line_num,
                        )
                    except Exception as e:
                        self._error_handler.dispatch_error(
                            f"Error on line {line_num}: Invalid last property: {last_prop} ({str(e)})"
                        )

        for rule in state.current_rules:
            self._rule_handler.handle_rule(rule)

        state.current_rules = []
        state.in_rule = False
        state.current_selectors = []
        state.original_selector = None
        state.property_lines = []
        state.buffer = ""
        state.rule_start_line = 0
        return True

    def _process_complete_rule(
        self, line: str, state: ParserState, variable_manager: VariableManager
    ) -> None:
        """
        Process a complete QSS rule from a single line.

        This method handles rules that are defined entirely on one line,
        including selector validation and property processing.

        Args:
            line (str): The line containing the complete rule.
            state (ParserState): Current state of the parser.
            variable_manager (VariableManager): Manager for handling variables.
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
        errors = SelectorUtils.validate_selector_syntax(
            normalized_selector, state.current_line
        )
        if errors:
            for error in errors:
                self._error_handler.dispatch_error(error)
            if any("Duplicate selector" in error for error in errors):
                seen_selectors = set()
                unique_selectors = []
                for sel in selectors:
                    if sel not in seen_selectors:
                        seen_selectors.add(sel)
                        unique_selectors.append(sel)
                selectors = unique_selectors
            else:
                return
        if not selectors:
            return

        state.current_selectors = selectors
        state.original_selector = normalized_selector
        state.current_rules = [QSSRule(sel) for sel in selectors]
        if properties.strip():
            prop_lines = [p.strip() for p in properties.split(";") if p.strip()]
            for i, prop_line in enumerate(prop_lines):
                if not prop_line:
                    continue
                try:
                    self._property_processor.process_property(
                        prop_line + (";" if not prop_line.endswith(";") else ""),
                        state.current_rules,
                        variable_manager,
                        state.current_line,
                    )
                except Exception as e:
                    self._error_handler.dispatch_error(
                        f"Error on line {state.current_line}: Invalid property: {prop_line} ({str(e)})"
                    )

        for rule in state.current_rules:
            if rule.properties:
                self._rule_handler.handle_rule(rule)

        state.current_rules = []
        state.current_selectors = []
        state.original_selector = None
        state.property_lines = []


class PropertyPlugin(BaseQSSPlugin):
    """
    Plugin for handling QSS property declarations.

    This plugin processes property declarations within rule blocks,
    delegating the actual property processing to a property processor.

    Attributes:
        _property_processor (PropertyProcessorProtocol): Processor for handling properties.
        _error_handler (ErrorHandlerProtocol): Handler for reporting errors.
    """

    def __init__(
        self,
        property_processor: PropertyProcessorProtocol,
        error_handler: ErrorHandlerProtocol,
    ) -> None:
        """
        Initialize a new PropertyPlugin instance.

        Args:
            property_processor (PropertyProcessorProtocol): Processor for handling properties.
            error_handler (ErrorHandlerProtocol): Handler for reporting errors.
        """
        super().__init__(error_handler)
        self._property_processor = property_processor

    def process_line(
        self, line: str, state: ParserState, variable_manager: VariableManager
    ) -> bool:
        """
        Process a line containing QSS property declarations.

        This method handles property lines within rule blocks, adding them
        to the current rule's property list.

        Args:
            line (str): The line to process.
            state (ParserState): Current state of the parser.
            variable_manager (VariableManager): Manager for handling variables.

        Returns:
            bool: True if the line was processed as a property, False otherwise.
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
    """
    Plugin for handling QSS variable declarations.

    This plugin processes variable declarations within @variables blocks,
    managing the parsing and validation of variable definitions.

    Attributes:
        _error_handler (ErrorHandlerProtocol): Handler for reporting errors.
        _logger (logging.Logger): Logger instance for debugging and error reporting.
    """

    def __init__(self, error_handler: ErrorHandlerProtocol) -> None:
        """
        Initialize a new VariablePlugin instance.

        Args:
            error_handler (ErrorHandlerProtocol): Handler for reporting errors.
        """
        self._error_handler = error_handler
        self._logger = logging.getLogger(__name__)

    def process_line(
        self, line: str, state: ParserState, variable_manager: VariableManager
    ) -> bool:
        """
        Process a line that may contain variable declarations.

        This method handles the start and end of variable blocks, as well as
        the variable declarations within them.

        Args:
            line (str): The line to process.
            state (ParserState): Current state of the parser.
            variable_manager (VariableManager): Manager for handling variables.

        Returns:
            bool: True if the line was processed as part of variable handling,
                 False otherwise.
        """
        line = line.strip()
        if state.in_comment:
            if "*/" in line:
                state.in_comment = False
            return True
        if line.startswith("/*"):
            if "*/" in line:
                return True
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
                            ParserEvent.VARIABLE_DEFINED.value, []
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


class ParserEvent(Enum):
    """
    Enumeration of events that can occur during QSS parsing.

    These events can be subscribed to using the QSSParser.on() method.
    """

    RULE_ADDED = "rule_added"  # Emitted when a rule is added to the parser
    ERROR_FOUND = "error_found"  # Emitted when an error is encountered
    VARIABLE_DEFINED = "variable_defined"  # Emitted when a variable is defined
    PARSE_COMPLETED = "parse_completed"  # Emitted when parsing is complete


class QSSParser:
    """
    Main class for parsing Qt Style Sheets (QSS).

    This class coordinates the parsing of QSS content using a plugin-based
    architecture, managing the overall parsing process and maintaining the
    state of parsed rules.

    Attributes:
        _state (ParserState): Current state of the parser.
        _style_selector (QSSStyleSelector): Selector for applying styles to widgets.
        _variable_manager (VariableManager): Manager for handling variables.
        _event_handlers (Dict[str, List[Callable[..., None]]]): Event handlers.
        _rule_map (Dict[str, QSSRule]): Map of selectors to rules.
        _logger (logging.Logger): Logger instance for debugging and error reporting.
        _error_handler (ErrorHandlerProtocol): Handler for reporting errors.
        _property_processor (PropertyProcessorProtocol): Processor for properties.
        _plugins (List[QSSParserPlugin]): List of parser plugins.
    """

    def __init__(
        self,
        property_processor: Optional[PropertyProcessorProtocol] = None,
        plugins: Optional[List[QSSParserPlugin]] = None,
        logger: Optional[logging.Logger] = None,
    ) -> None:
        """
        Initialize a new QSSParser instance.

        Args:
            property_processor (Optional[PropertyProcessorProtocol]): Custom property
                processor. If None, uses DefaultPropertyProcessor.
            plugins (Optional[List[QSSParserPlugin]]): List of parser plugins.
                If None, uses default plugins.
            logger (Optional[logging.Logger]): Custom logger instance.
        """
        self._state: ParserState = ParserState()
        self._style_selector: QSSStyleSelector = QSSStyleSelector(logger=logger)
        self._variable_manager: VariableManager = VariableManager()
        self._event_handlers: Dict[str, List[Callable[..., None]]] = {
            event.value: [] for event in ParserEvent
        }
        self._rule_map: Dict[str, QSSRule] = {}
        self._logger: logging.Logger = logger or logging.getLogger(__name__)

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
        Dispatch an error message to all error handlers.

        Args:
            error (str): The error message to dispatch.
        """
        self._logger.warning(f"Error: {error}")
        for handler in self._event_handlers[ParserEvent.ERROR_FOUND.value]:
            handler(error)

    def handle_rule(self, rule: QSSRule) -> None:
        """
        Handle a newly parsed QSS rule.

        This method merges or adds the rule to the parser's rule collection
        and notifies rule handlers.

        Args:
            rule (QSSRule): The rule to handle.
        """
        self._logger.debug(f"Handling rule: {rule.selector}")
        self._merge_or_add_rule(rule)
        if (
            ":" in rule.selector
            and "::" not in rule.selector
            and "," not in rule.selector
            and not re.search(r"\[[^\]]*:[^\]]*\]", rule.selector)
        ):
            base_rule = rule.clone_without_pseudo_elements()
            self._merge_or_add_rule(base_rule)

    def _merge_or_add_rule(self, rule: QSSRule) -> None:
        """
        Merge a rule with an existing rule or add it as new.

        Args:
            rule (QSSRule): The rule to merge or add.
        """
        existing_rule = self._rule_map.get(rule.selector)
        if existing_rule:
            prop_map = {p.name: p for p in existing_rule.properties}
            for prop in rule.properties:
                prop_map[prop.name] = prop
            existing_rule.properties = list(prop_map.values())
            for handler in self._event_handlers[ParserEvent.RULE_ADDED.value]:
                handler(existing_rule)
        else:
            self._rule_map[rule.selector] = rule
            self._state.rules.append(rule)
            for handler in self._event_handlers[ParserEvent.RULE_ADDED.value]:
                handler(rule)

    def on(self, event: ParserEvent, handler: Callable[..., None]) -> None:
        """
        Register a handler for a parser event.

        Args:
            event (ParserEvent): The event to handle.
            handler (Callable[..., None]): The handler function.
        """
        event_value = event.value if isinstance(event, ParserEvent) else event
        if event_value in self._event_handlers:
            self._event_handlers[event_value].append(handler)
            self._logger.debug(f"Registered handler for event: {event_value}")

    def parse(self, qss_text: str) -> None:
        """
        Parse a QSS text string.

        This method processes the QSS text line by line using the registered
        plugins.

        Args:
            qss_text (str): The QSS text to parse.
        """
        self._reset()
        lines = qss_text.splitlines()
        for line in lines:
            self._process_line(line)
            self._state.current_line += 1
        self._finalize_parsing()
        self._logger.debug("Parsing completed and parse_completed event dispatched")

    def _reset(self) -> None:
        """
        Reset the parser state.

        This method clears all internal state and prepares for a new parse.
        """
        self._state.reset()
        self._variable_manager = VariableManager()
        self._rule_map.clear()
        self._logger.debug("Parser state reset")

    def _process_line(self, line: str) -> None:
        """
        Process a single line of QSS text.

        Args:
            line (str): The line to process.
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

    def _finalize_parsing(self) -> None:
        """
        Finalize the parsing process.

        This method handles any remaining state and dispatches the parse
        completed event.
        """
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

        for handler in self._event_handlers[ParserEvent.PARSE_COMPLETED.value]:
            handler()

    def get_styles_for(
        self,
        widget: WidgetProtocol,
        fallback_class: Optional[str] = None,
        additional_selectors: Optional[List[str]] = None,
        include_class_if_object_name: bool = False,
    ) -> str:
        """
        Get the styles that apply to a widget.

        Args:
            widget (WidgetProtocol): The widget to get styles for.
            fallback_class (Optional[str]): Fallback class name if no styles match.
            additional_selectors (Optional[List[str]]): Additional selectors to include.
            include_class_if_object_name (bool): Whether to include class styles when
                object name is present.

        Returns:
            str: The combined styles that apply to the widget.
        """
        return self._style_selector.get_styles_for(
            self._state.rules,
            widget,
            fallback_class,
            additional_selectors,
            include_class_if_object_name,
        )

    def __repr__(self) -> str:
        """
        Get a string representation of the parser.

        Returns:
            str: The string representation.
        """
        return self.to_string()

    def to_string(self) -> str:
        """
        Convert all parsed rules to a formatted string.

        Returns:
            str: The formatted QSS string.
        """
        return "\n".join(
            QSSFormatter.format_rule(rule.selector, rule.properties)
            for rule in self._state.rules
        )


class QSSStyleSelector:
    """
    Class for selecting and applying QSS styles to widgets.

    This class handles the matching of QSS rules to widgets based on their
    class names, object names, and other selectors.

    Attributes:
        _logger (logging.Logger): Logger instance for debugging and error reporting.
    """

    def __init__(self, logger: Optional[logging.Logger] = None) -> None:
        """
        Initialize a new QSSStyleSelector instance.

        Args:
            logger (Optional[logging.Logger]): Custom logger instance.
        """
        self._logger: logging.Logger = logger or logging.getLogger(__name__)

    def get_styles_for(
        self,
        rules: List[QSSRule],
        widget: WidgetProtocol,
        fallback_class: Optional[str] = None,
        additional_selectors: Optional[List[str]] = None,
        include_class_if_object_name: bool = False,
    ) -> str:
        """
        Get all styles that apply to a widget.

        This method matches rules against the widget based on its class name,
        object name, and additional selectors.

        Args:
            rules (List[QSSRule]): List of all available rules.
            widget (WidgetProtocol): The widget to get styles for.
            fallback_class (Optional[str]): Fallback class name if no styles match.
            additional_selectors (Optional[List[str]]): Additional selectors to include.
            include_class_if_object_name (bool): Whether to include class styles when
                object name is present.

        Returns:
            str: The combined styles that apply to the widget.
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
        result = "\n".join(
            QSSFormatter.format_rule(r.selector, r.properties).rstrip("\n")
            for r in unique_styles
        )
        self._logger.debug(f"Styles retrieved: {result}")
        return result

    def _get_rules_for_selector(
        self, rules: List[QSSRule], selector: str, object_name: str, class_name: str
    ) -> List[QSSRule]:
        """
        Get all rules that match a specific selector.

        This method handles complex selector matching, including attribute
        selectors and combinators.

        Args:
            rules (List[QSSRule]): List of all available rules.
            selector (str): The selector to match against.
            object_name (str): The object name of the widget.
            class_name (str): The class name of the widget.

        Returns:
            List[QSSRule]: List of matching rules.
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
