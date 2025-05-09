import logging
import re
from abc import ABC, abstractmethod
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Optional,
    Protocol,
    Set,
    Tuple,
    TypedDict,
    Match,
)


class MetaObjectProtocol(Protocol):
    """
    Protocol defining the interface for a meta-object, which provides metadata about a widget.
    """

    def className(self) -> str:
        """
        Retrieves the class name of the widget.

        Returns:
            str: The class name of the widget (e.g., 'QPushButton').
        """
        ...


class WidgetProtocol(Protocol):
    """
    Protocol defining the interface for a widget, used in QSS style application.
    """

    def objectName(self) -> str:
        """
        Retrieves the object name of the widget.

        Returns:
            str: The object name of the widget (e.g., 'myButton').
        """
        ...

    def metaObject(self) -> MetaObjectProtocol:
        """
        Retrieves the meta-object containing metadata about the widget.

        Returns:
            MetaObjectProtocol: The meta-object of the widget.
        """
        ...


class QSSPropertyDict(TypedDict):
    """
    Typed dictionary for representing a QSS property.
    """

    name: str
    value: str


class QSSProperty:
    """
    Represents a single QSS property with a name and value.
    """

    def __init__(self, name: str, value: str) -> None:
        """
        Initializes a QSS property with a name and value.

        Args:
            name (str): The name of the property (e.g., 'color').
            value (str): The value of the property (e.g., 'blue').
        """
        self.name: str = name.strip()
        self.value: str = value.strip()

    def __repr__(self) -> str:
        """
        Returns a string representation of the property.

        Returns:
            str: A string in the format 'name: value'.
        """
        return f"{self.name}: {self.value}"

    def to_dict(self) -> QSSPropertyDict:
        """
        Converts the property to a dictionary.

        Returns:
            QSSPropertyDict: Dictionary with 'name' and 'value' keys.
        """
        return {"name": self.name, "value": self.value}


class VariableManager:
    """
    Manages QSS variables defined in @variables blocks and resolves var() references.
    """

    def __init__(self) -> None:
        """
        Initializes the variable manager.
        """
        self._variables: Dict[str, str] = {}
        self._logger: logging.Logger = logging.getLogger(__name__)

    def parse_variables(self, block: str) -> List[str]:
        """
        Parses a @variables block and stores the variables.

        Args:
            block (str): The content of the @variables block (e.g., '--primary-color: #ffffff;').

        Returns:
            List[str]: List of error messages for invalid variable declarations.
        """
        errors: List[str] = []
        lines = block.split(";")
        for i, line in enumerate(lines, start=1):
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
            self._variables[name.strip()] = value.strip()
        return errors

    def resolve_variable(self, value: str) -> Tuple[str, Optional[str]]:
        """
        Resolves var(--name) references in a property value recursively.

        Args:
            value (str): The property value containing var(--name) references.

        Returns:
            Tuple[str, Optional[str]]: The resolved value and an error message if a variable is undefined or a loop is detected.
        """
        visited: Set[str] = set()
        pattern = r"var\((--[\w-]+)\)"

        def replace_var(match: Match[str]) -> str:
            var_name = match.group(1)
            if var_name in visited:
                self._logger.warning(
                    f"Circular variable reference detected: {var_name}"
                )
                return match.group(0)  # Return original to avoid infinite loop
            if var_name not in self._variables:
                return match.group(0)  # Keep original if undefined
            visited.add(var_name)
            resolved_value = self._variables[var_name]
            # Recursively resolve nested var() references
            nested_value = re.sub(pattern, replace_var, resolved_value)
            visited.remove(var_name)
            return nested_value

        resolved_value = re.sub(pattern, replace_var, value)
        undefined_vars = [
            match.group(1)
            for match in re.finditer(pattern, value)
            if match.group(1) not in self._variables and match.group(1) not in visited
        ]
        error = (
            f"Undefined variables: {', '.join(undefined_vars)}"
            if undefined_vars
            else None
        )
        return resolved_value, error


class SelectorUtils:
    """
    Utility class for parsing and normalizing QSS selectors.
    """

    _ATTRIBUTE_PATTERN = r'\[\w+(?:~|=|\|=|\^=|\$=|\*=)?(?:".*?"|[^\]]*)\]'

    @staticmethod
    def extract_attributes(selector: str) -> List[str]:
        """
        Extracts attribute selectors from a QSS selector.

        Args:
            selector (str): The selector to parse (e.g., 'QPushButton[data-value="complex"]').

        Returns:
            List[str]: List of attribute selectors (e.g., ['[data-value="complex"]']).
        """
        return re.findall(SelectorUtils._ATTRIBUTE_PATTERN, selector)

    @staticmethod
    def normalize_selector(selector: str) -> str:
        """
        Normalizes a selector by removing extra spaces around combinators and between parts,
        while preserving spaces within attribute selectors.

        Args:
            selector (str): The selector to normalize.

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
        Parses a selector into object name, class name, attributes, and pseudo-states.

        Args:
            selector (str): The selector to parse.

        Returns:
            Tuple[Optional[str], Optional[str], List[str], List[str]]: A tuple containing:
                - Object name (if selector contains '#').
                - Class name (if selector does not start with '#').
                - List of attribute selectors (e.g., ['[selected="true"]']).
                - List of pseudo-states (e.g., ['hover', 'focus']).
        """
        object_name: Optional[str] = None
        class_name: Optional[str] = None
        attributes = SelectorUtils.extract_attributes(selector)
        pseudo_states: List[str] = []

        selector_clean = re.sub(SelectorUtils._ATTRIBUTE_PATTERN, "", selector)
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


class QSSRule:
    """
    Represents a QSS rule with a selector and a list of properties.
    """

    def __init__(self, selector: str, original: Optional[str] = None) -> None:
        """
        Initializes a QSS rule with a selector and optional original text.

        Args:
            selector (str): The CSS selector for the rule (e.g., '#myButton', 'QPushButton').
            original (Optional[str]): The original QSS text for the rule, if provided.
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
        Parses the selector to extract object name, class name, attributes, and pseudo-states.

        Updates instance attributes:
            - object_name: The object name if the selector contains a '#'.
            - class_name: The class name if the selector does not start with '#'.
            - attributes: List of attribute selectors (e.g., '[selected="true"]').
            - pseudo_states: List of pseudo-states (e.g., ['hover', 'focus']).
        """
        (
            self.object_name,
            self.class_name,
            self.attributes,
            self.pseudo_states,
        ) = SelectorUtils.parse_selector(self.selector)

    def add_property(self, name: str, value: str) -> None:
        """
        Adds a property to the rule.

        Args:
            name (str): The name of the property (e.g., 'color').
            value (str): The value of the property (e.g., 'blue').
        """
        self.properties.append(QSSProperty(name, value))

    def clone_without_pseudo_elements(self) -> "QSSRule":
        """
        Creates a copy of the rule without pseudo-elements or pseudo-states.

        Returns:
            QSSRule: A new rule instance with the same properties but without pseudo-elements in the selector.
        """
        base_selector = self.selector.split("::")[0]
        clone = QSSRule(base_selector)
        clone.properties = self.properties.copy()
        clone.original = self._format_rule(base_selector, self.properties)
        return clone

    def _format_rule(self, selector: str, properties: List[QSSProperty]) -> str:
        """
        Formats a rule in the standardized QSS format.

        Args:
            selector (str): The selector for the rule.
            properties (List[QSSProperty]): The properties to include.

        Returns:
            str: Formatted rule string.
        """
        props = "\n".join(f"\t{p.name}: {p.value};" for p in properties)
        return f"{selector} {{\n{props}\n}}\n"

    def __repr__(self) -> str:
        """
        Returns a string representation of the rule.

        Returns:
            str: A string in the format 'selector { properties }'.
        """
        props = "\n\t".join(str(p) for p in self.properties)
        return f"{self.selector} {{\n\t{props}\n}}"

    def __hash__(self) -> int:
        """
        Computes a hash for the rule to enable deduplication in sets.

        Returns:
            int: Hash value based on the selector and properties.
        """
        return hash((self.selector, tuple((p.name, p.value) for p in self.properties)))

    def __eq__(self, other: object) -> bool:
        """
        Compares this rule with another for equality.

        Args:
            other (object): Another object to compare with.

        Returns:
            bool: True if the rules have the same selector and properties, False otherwise.
        """
        if not isinstance(other, QSSRule):
            return False
        return self.selector == other.selector and self.properties == other.properties


class ParserState:
    """
    Holds the state of the QSS parser, including rules and parsing context.
    """

    def __init__(self) -> None:
        """
        Initializes the parser state.
        """
        self.rules: List[QSSRule] = []
        self.buffer: str = ""
        self.in_comment: bool = False
        self.in_rule: bool = False
        self.in_variables: bool = False
        self.current_selectors: List[str] = []
        self.original_selector: Optional[str] = None
        self.current_rules: List[QSSRule] = []
        self.variable_buffer: str = ""

    def reset(self) -> None:
        """
        Resets the parser state to its initial values.
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


class QSSValidator:
    """
    Validates QSS text for syntactic correctness, including variables.
    """

    def __init__(self) -> None:
        """
        Initializes the QSS validator.
        """
        self._logger: logging.Logger = logging.getLogger(__name__)

    def check_format(self, qss_text: str) -> List[str]:
        """
        Validates the format of QSS text, checking for unclosed braces, properties without semicolons,
        extra closing braces, malformed rules, and variable declarations.

        Args:
            qss_text (str): The QSS text to validate.

        Returns:
            List[str]: List of error messages in the format: "Error on line {num}: {description}: {content}".
                       Returns an empty list if the format is correct.
        """
        errors: List[str] = []
        lines = qss_text.splitlines()
        in_comment: bool = False
        in_rule: bool = False
        in_variables: bool = False
        open_braces: int = 0
        current_selector: str = ""
        last_line_num: int = 0
        property_buffer: str = ""

        for line_num, line in enumerate(lines, start=1):
            line = line.strip()
            if not line:
                continue

            if self._handle_comments(line, in_comment):
                in_comment = True
                continue
            if in_comment:
                if "*/" in line:
                    in_comment = False
                continue

            if self._is_complete_rule(line):
                errors.extend(self._validate_complete_rule(line, line_num))
                continue

            if in_variables:
                if line == "}":
                    open_braces -= 1
                    in_variables = open_braces > 0
                    continue
                property_buffer = (property_buffer + " " + line).strip()
                continue

            if in_rule:
                if line == "}":
                    if open_braces == 0:
                        errors.append(
                            f"Error on line {line_num}: Closing brace '}}' without matching '{{': {line}"
                        )
                    else:
                        errors.extend(
                            self._validate_pending_properties(
                                property_buffer, line_num - 1
                            )
                        )
                        property_buffer = ""
                        open_braces -= 1
                        in_rule = open_braces > 0
                        if not in_rule:
                            current_selector = ""
                    continue

                if line.endswith("{"):
                    if line.startswith("@variables"):
                        errors.append(
                            f"Error on line {line_num}: Nested @variables block: {line}"
                        )
                        continue
                    errors.extend(
                        self._validate_pending_properties(property_buffer, line_num - 1)
                    )
                    property_buffer = ""
                    new_errors, selector = self._validate_selector(line, line_num)
                    errors.extend(new_errors)
                    current_selector = selector
                    open_braces += 1
                    in_rule = True
                    last_line_num = line_num
                    continue

                if line.startswith("@variables"):
                    errors.append(
                        f"Error on line {line_num}: Nested @variables block: {line}"
                    )
                    continue

                property_buffer, new_errors = self._process_property_line(
                    line, property_buffer, line_num
                )
                errors.extend(new_errors)
                last_line_num = line_num
            else:
                if line == "@variables {":
                    if open_braces > 0:
                        errors.append(
                            f"Error on line {line_num}: Nested @variables block: {line}"
                        )
                    open_braces += 1
                    in_variables = True
                    last_line_num = line_num
                    continue
                if line.endswith("{"):
                    new_errors, selector = self._validate_selector(line, line_num)
                    errors.extend(new_errors)
                    current_selector = selector
                    open_braces += 1
                    in_rule = True
                    last_line_num = line_num
                elif self._is_property_line(line):
                    errors.append(
                        f"Error on line {line_num}: Property outside block: {line}"
                    )
                elif line == "}":
                    errors.append(
                        f"Error on line {line_num}: Closing brace '}}' without matching '{{': {line}"
                    )
                else:
                    if self._is_potential_selector(line):
                        errors.append(
                            f"Error on line {line_num}: Selector without opening brace '{{': {line}"
                        )

        errors.extend(
            self._finalize_validation(
                open_braces, current_selector, property_buffer, last_line_num
            )
        )

        for error in errors:
            self._logger.warning(error)

        return errors

    def _is_complete_rule(self, line: str) -> bool:
        """
        Checks if the line is a complete QSS rule (selector + { + properties + }).

        Args:
            line (str): The line to check.

        Returns:
            bool: True if the line is a complete QSS rule, False otherwise.
        """
        return bool(re.match(r"^\s*[^/][^{}]*\s*\{[^}]*\}\s*$", line))

    def _validate_complete_rule(self, line: str, line_num: int) -> List[str]:
        """
        Validates a complete QSS rule in a single line.

        Args:
            line (str): The line containing the complete rule.
            line_num (int): The line number in the QSS text.

        Returns:
            List[str]: List of error messages for the rule, if any.
        """
        errors: List[str] = []
        match = re.match(r"^\s*([^/][^{}]*)\s*\{([^}]*)\}\s*$", line)
        if not match:
            return [f"Error on line {line_num}: Malformed rule: {line}"]

        selector, properties = match.groups()
        selector = selector.strip()
        if not selector:
            errors.append(f"Error on line {line_num}: Empty selector in rule: {line}")

        if properties.strip():
            prop_parts = properties.split(";")
            for part in prop_parts[:-1]:
                part = part.strip()
                if part:
                    if ":" not in part or part.endswith(":"):
                        errors.append(
                            f"Error on line {line_num}: Malformed property: {part}"
                        )
                    elif not part.split(":", 1)[1].strip():
                        errors.append(
                            f"Error on line {line_num}: Property missing value: {part}"
                        )
            last_part = prop_parts[-1].strip()
            if last_part and not last_part.endswith(";"):
                errors.append(
                    f"Error on line {line_num}: Property missing ';': {last_part}"
                )

        return errors

    def _is_potential_selector(self, line: str) -> bool:
        """
        Checks if the line could be a selector (but not a complete rule or property).

        Args:
            line (str): The line to check.

        Returns:
            bool: True if the line looks like a selector, False otherwise.
        """
        return (
            not self._is_complete_rule(line)
            and not self._is_property_line(line)
            and not line.startswith("/*")
            and not line.startswith("@variables")
            and "*/" not in line
            and not line == "}"
            and bool(re.match(r"^\s*[^/][^{};]*\s*$", line))
        )

    def _handle_comments(self, line: str, in_comment: bool) -> bool:
        """
        Checks if the line starts a comment block.

        Args:
            line (str): The line to check.
            in_comment (bool): Whether the parser is currently inside a comment block.

        Returns:
            bool: True if the line starts a new comment block, False otherwise.
        """
        return line.startswith("/*") and not in_comment

    def _validate_selector(self, line: str, line_num: int) -> Tuple[List[str], str]:
        """
        Validates a line containing a selector and an opening brace.

        Args:
            line (str): The line to validate.
            line_num (int): The line number in the QSS text.

        Returns:
            Tuple[List[str], str]: A tuple containing a list of error messages and the extracted selector.
        """
        errors: List[str] = []
        selector = line[:-1].strip()
        if not selector:
            errors.append(
                f"Error on line {line_num}: Empty selector before '{{': {line}"
            )
        return errors, selector

    def _is_property_line(self, line: str) -> bool:
        """
        Checks if the line contains a property (e.g., 'color: blue;').

        Args:
            line (str): The line to check.

        Returns:
            bool: True if the line is a valid property line, False otherwise.
        """
        return ":" in line and ";" in line and not line.startswith("@variables")

    def _process_property_line(
        self, line: str, buffer: str, line_num: int
    ) -> Tuple[str, List[str]]:
        """
        Processes a property line for format validation, accumulating in the buffer and checking for semicolons.

        Args:
            line (str): The current line to process.
            buffer (str): The buffer of accumulated properties.
            line_num (int): The current line number.

        Returns:
            Tuple[str, List[str]]: Updated buffer and list of error messages.
        """
        errors: List[str] = []
        if ";" in line and buffer.strip():
            if not buffer.endswith(";"):
                errors.append(
                    f"Error on line {line_num - 1}: Property missing ';': {buffer.strip()}"
                )
            buffer = ""

        if ";" in line:
            full_line = (buffer + " " + line).strip() if buffer else line
            parts = full_line.split(";")
            for part in parts[:-1]:
                part = part.strip()
                if part:
                    if ":" not in part or part.strip().endswith(":"):
                        errors.append(
                            f"Error on line {line_num}: Malformed property: {part.strip()}"
                        )
            buffer = parts[-1].strip() if parts[-1].strip() else ""
        else:
            buffer = (buffer + " " + line).strip()
        return buffer, errors

    def _validate_pending_properties(self, buffer: str, line_num: int) -> List[str]:
        """
        Validates pending properties in the buffer, checking for missing semicolons.

        Args:
            buffer (str): The buffer containing pending properties.
            line_num (int): The line number to associate with errors.

        Returns:
            List[str]: List of error messages for invalid properties.
        """
        if buffer.strip() and not buffer.endswith(";"):
            return [f"Error on line {line_num}: Property missing ';': {buffer.strip()}"]
        return []

    def _finalize_validation(
        self, open_braces: int, current_selector: str, buffer: str, last_line_num: int
    ) -> List[str]:
        """
        Validates final conditions, such as unclosed braces or pending properties.

        Args:
            open_braces (int): Number of open braces.
            current_selector (str): The current selector being processed.
            buffer (str): The buffer of pending properties.
            last_line_num (int): The last line number processed.

        Returns:
            List[str]: List of error messages for final validation issues.
        """
        errors: List[str] = []
        if open_braces > 0 and current_selector:
            errors.append(
                f"Error on line {last_line_num}: Unclosed brace '{{' for selector: {current_selector}"
            )
        errors.extend(self._validate_pending_properties(buffer, last_line_num))
        return errors


class QSSStyleSelector:
    """
    Selects and formats QSS styles for a given widget based on a list of rules.
    """

    def __init__(self) -> None:
        """
        Initializes the QSS style selector.
        """
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
        Retrieves QSS styles for a given widget from a list of rules.

        Args:
            rules (List[QSSRule]): List of QSSRule objects to search.
            widget (WidgetProtocol): The widget to retrieve styles for.
            fallback_class (Optional[str]): Fallback class to use if no styles are found.
            additional_selectors (Optional[List[str]]): Additional selectors to include.
            include_class_if_object_name (bool): Whether to include class styles if an object name is present.

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
        Retrieves rules matching a given selector, considering objectName and className constraints.

        Args:
            rules (List[QSSRule]): List of QSSRule objects to search.
            selector (str): The selector to match (e.g., 'QPushButton', '#myButton').
            object_name (str): The objectName of the widget.
            class_name (str): The className of the widget.

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

                sel_without_attrs = re.sub(
                    SelectorUtils._ATTRIBUTE_PATTERN, "", sel
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


class QSSParserPlugin(ABC):
    """
    Abstract base class for QSS parser plugins, defining the interface for processing QSS lines.
    """

    @abstractmethod
    def process_line(
        self, line: str, state: ParserState, variable_manager: VariableManager
    ) -> bool:
        """
        Processes a line of QSS text.

        Args:
            line (str): The line to process.
            state (ParserState): The current parser state.
            variable_manager (VariableManager): Manager for resolving variables.

        Returns:
            bool: True if the line was handled, False otherwise.
        """
        pass


class DefaultQSSParserPlugin(QSSParserPlugin):
    """
    Default plugin for parsing QSS text, handling selectors, properties, and variables.
    """

    def __init__(self, parser: "QSSParser") -> None:
        """
        Initializes the default QSS parser plugin.

        Args:
            parser (QSSParser): Reference to the QSSParser instance for event handling.
        """
        self._parser: "QSSParser" = parser
        self._logger: logging.Logger = logging.getLogger(__name__)

    def process_line(
        self, line: str, state: ParserState, variable_manager: VariableManager
    ) -> bool:
        """
        Processes a line of QSS text using the default parsing logic.

        Args:
            line (str): The line to process.
            state (ParserState): The current parser state.
            variable_manager (VariableManager): Manager for resolving variables.

        Returns:
            bool: True if the line was handled, False otherwise.
        """
        line = line.strip()
        if not line or state.in_comment:
            if "*/" in line:
                state.in_comment = False
            return True
        if line.startswith("/*"):
            state.in_comment = True
            return True
        if self._is_complete_rule(line):
            self._process_complete_rule(line, state, variable_manager)
            return True
        if line == "@variables {" and not state.in_rule:
            state.in_variables = True
            state.variable_buffer = ""
            return True
        if state.in_variables:
            if line == "}":
                errors = variable_manager.parse_variables(state.variable_buffer)
                for error in errors:
                    for handler in self._parser._event_handlers["error_found"]:
                        handler(error)
                state.in_variables = False
                state.variable_buffer = ""
                return True
            state.variable_buffer = (state.variable_buffer + " " + line).strip()
            return True
        if line.endswith("{") and not state.in_rule:
            selector_part = line[:-1].strip()
            normalized_selector = SelectorUtils.normalize_selector(selector_part)
            selectors = [s.strip() for s in normalized_selector.split(",") if s.strip()]
            if not selectors:
                return True
            state.current_selectors = selectors
            state.original_selector = normalized_selector
            state.current_rules = [
                QSSRule(sel, original=f"{sel} {{\n") for sel in selectors
            ]
            state.in_rule = True
            return True
        if line == "}" and state.in_rule:
            for rule in state.current_rules:
                rule.original += "}\n"
                self._add_rule(rule, state)
            state.current_rules = []
            state.in_rule = False
            state.current_selectors = []
            state.original_selector = None
            return True
        if state.in_rule and state.current_rules:
            if ";" in line:
                full_line = (
                    (state.buffer + " " + line).strip() if state.buffer else line
                )
                state.buffer = ""
                parts = full_line.split(";")
                for part in parts[:-1]:
                    if part.strip():
                        self._process_property(
                            part.strip() + ";", state, variable_manager
                        )
                if parts[-1].strip():
                    state.buffer = parts[-1].strip()
            else:
                state.buffer = (state.buffer + " " + line).strip()
            return True
        return False

    def _is_complete_rule(self, line: str) -> bool:
        """
        Checks if the line is a complete QSS rule.

        Args:
            line (str): The line to check.

        Returns:
            bool: True if the line is a complete QSS rule, False otherwise.
        """
        return bool(re.match(r"^\s*[^/][^{}]*\s*\{[^}]*\}\s*$", line))

    def _process_complete_rule(
        self, line: str, state: ParserState, variable_manager: VariableManager
    ) -> None:
        """
        Processes a complete QSS rule in a single line.

        Args:
            line (str): The line containing the complete rule.
            state (ParserState): The current parser state.
            variable_manager (VariableManager): Manager for resolving variables.
        """
        match = re.match(r"^\s*([^/][^{}]*)\s*\{([^}]*)\}\s*$", line)
        if not match:
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
            prop_parts = properties.split(";")
            for part in prop_parts:
                part = part.strip()
                if part:
                    self._process_property(part + ";", state, variable_manager)
        for rule in state.current_rules:
            rule.original += "}\n"
            self._add_rule(rule, state)
        state.current_rules = []
        state.current_selectors = []
        state.original_selector = None

    def _process_property(
        self, line: str, state: ParserState, variable_manager: VariableManager
    ) -> None:
        """
        Processes a property line and adds it to the current rules, resolving variables.

        Args:
            line (str): The property line to process.
            state (ParserState): The current parser state.
            variable_manager (VariableManager): Manager for resolving variables.
        """
        line = line.rstrip(";")
        if not state.current_rules:
            return
        parts = line.split(":", 1)
        if len(parts) == 2:
            name, value = parts
            if name.strip() and value.strip():
                resolved_value, error = variable_manager.resolve_variable(value.strip())
                if error:
                    for handler in self._parser._event_handlers["error_found"]:
                        handler(error)
                normalized_line = f"{name.strip()}: {resolved_value};"
                for rule in state.current_rules:
                    rule.original += f"    {normalized_line}\n"
                    rule.add_property(name.strip(), resolved_value)

    def _add_rule(self, rule: QSSRule, state: ParserState) -> None:
        """
        Adds a rule to the parser's rule list, merging with existing rules if necessary.

        Args:
            rule (QSSRule): The rule to add.
            state (ParserState): The current parser state.
        """
        self._logger.debug(f"Adding rule: {rule.selector}")
        for existing_rule in state.rules:
            if existing_rule.selector == rule.selector:
                existing_prop_names = {p.name for p in existing_rule.properties}
                for prop in rule.properties:
                    if prop.name not in existing_prop_names:
                        existing_rule.properties.append(prop)
                existing_rule.original = (
                    f"{existing_rule.selector} {{\n"
                    + "\n".join(
                        f"    {p.name}: {p.value};" for p in existing_rule.properties
                    )
                    + "\n}\n"
                )
                for handler in self._parser._event_handlers["rule_added"]:
                    handler(existing_rule)
                return
        state.rules.append(rule)
        for handler in self._parser._event_handlers["rule_added"]:
            handler(rule)
        if (
            ":" in rule.selector
            and "::" not in rule.selector
            and "," not in rule.selector
        ):
            base_rule = rule.clone_without_pseudo_elements()
            state.rules.append(base_rule)
            for handler in self._parser._event_handlers["rule_added"]:
                handler(base_rule)


class QSSParser:
    """
    Parses QSS text, including variables, and applies styles to widgets.
    """

    def __init__(self, plugins: Optional[List[QSSParserPlugin]] = None) -> None:
        """
        Initializes the QSS parser with an empty state and optional plugins.

        Args:
            plugins (Optional[List[QSSParserPlugin]]): List of plugins for custom parsing logic.
                                             If None, uses the default plugin.
        """
        self._state: ParserState = ParserState()
        self._validator: QSSValidator = QSSValidator()
        self._style_selector: QSSStyleSelector = QSSStyleSelector()
        self._variable_manager: VariableManager = VariableManager()
        self._event_handlers: Dict[str, List[Callable[[Any], None]]] = {
            "rule_added": [],
            "error_found": [],
        }
        self._logger: logging.Logger = logging.getLogger(__name__)
        self._plugins: List[QSSParserPlugin] = plugins or [DefaultQSSParserPlugin(self)]

    def on(self, event: str, handler: Callable[[Any], None]) -> None:
        """
        Registers an event handler for parser events.

        Args:
            event (str): The event to listen for ('rule_added', 'error_found').
            handler (Callable[[Any], None]): The function to call when the event occurs.
        """
        if event in self._event_handlers:
            self._event_handlers[event].append(handler)
            self._logger.debug(f"Registered handler for event: {event}")

    def parse(self, qss_text: str) -> None:
        """
        Parses QSS text into a list of QSSRule objects, resolving variables.

        Args:
            qss_text (str): The QSS text to parse, including @variables blocks.
        """
        self._reset()
        lines = qss_text.splitlines()
        for line in lines:
            self._process_line(line)
        if self._state.buffer.strip():
            self._process_property(self._state.buffer)
        if self._state.variable_buffer.strip():
            errors = self._variable_manager.parse_variables(self._state.variable_buffer)
            for error in errors:
                for handler in self._event_handlers["error_found"]:
                    handler(error)

    def _reset(self) -> None:
        """
        Resets the parser's internal state.
        """
        self._state.reset()
        self._variable_manager = VariableManager()
        self._logger.debug("Parser state reset")

    def _process_line(self, line: str) -> None:
        """
        Processes a single line of QSS text.

        Args:
            line (str): The line to process.
        """
        for plugin in self._plugins:
            if plugin.process_line(line, self._state, self._variable_manager):
                break

    def _process_property(self, line: str) -> None:
        """
        Processes a property line and adds it to the current rules, resolving variables.

        Args:
            line (str): The property line to process.
        """
        for plugin in self._plugins:
            if isinstance(plugin, DefaultQSSParserPlugin):
                plugin._process_property(line, self._state, self._variable_manager)
                break

    def check_format(self, qss_text: str) -> List[str]:
        """
        Validates the format of QSS text, including variables.

        Args:
            qss_text (str): The QSS text to validate.

        Returns:
            List[str]: List of error messages in the format: "Error on line {num}: {description}: {content}".
                       Returns an empty list if the format is correct.
        """
        errors = self._validator.check_format(qss_text)
        for error in errors:
            for handler in self._event_handlers["error_found"]:
                handler(error)
        return errors

    def get_styles_for(
        self,
        widget: WidgetProtocol,
        fallback_class: Optional[str] = None,
        additional_selectors: Optional[List[str]] = None,
        include_class_if_object_name: bool = False,
    ) -> str:
        """
        Retrieves QSS styles for a given widget.

        Args:
            widget (WidgetProtocol): The widget to retrieve styles for.
            fallback_class (Optional[str]): Fallback class to use if no styles are found.
            additional_selectors (Optional[List[str]]): Additional selectors to include.
            include_class_if_object_name (bool): Whether to include class styles if an object name is present.

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
        """
        Returns a string representation of the parser.

        Returns:
            str: A string containing all rules, separated by double newlines.
        """
        return "\n\n".join(str(rule) for rule in self._state.rules)
