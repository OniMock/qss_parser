from typing import List, Optional, Tuple
import re


class QSSProperty:
    def __init__(self, name: str, value: str):
        """
        Initialize a QSS property with a name and value.

        Args:
            name (str): The name of the property (e.g., 'color').
            value (str): The value of the property (e.g., 'blue').
        """
        self.name = name.strip()
        self.value = value.strip()

    def __repr__(self):
        """
        Return a string representation of the property.

        Returns:
            str: A string in the format 'name: value'.
        """
        return f"{self.name}: {self.value}"


class QSSRule:
    def __init__(self, selector: str, original: Optional[str] = None):
        """
        Initialize a QSS rule with a selector and optional original text.

        Args:
            selector (str): The CSS selector for the rule
            (e.g., '#myButton', 'QPushButton').
            original (Optional[str]): The original QSS text
            for the rule, if provided.
        """
        self.selector = selector.strip()
        self.properties: List[QSSProperty] = []
        self.original = original or ""
        self._parse_selector()

    def _parse_selector(self):
        """
        Parse the selector to extract object name, class name, and pseudo-states.

        Sets instance attributes:
            object_name: The object name if the selector starts with '#'.
            class_name: The class name if the selector does not start with '#'.
            pseudo_states: List of pseudo-states (e.g., ':hover', ':focus').
        """
        self.object_name = None
        self.class_name = None
        self.pseudo_states = []

        parts = self.selector.split(":")
        main_selector = parts[0]
        self.pseudo_states = parts[1:] if len(parts) > 1 else []

        if main_selector.startswith("#"):
            self.object_name = main_selector[1:]
        else:
            self.class_name = main_selector

    def add_property(self, name: str, value: str):
        """
        Add a property to the rule.

        Args:
            name (str): The name of the property.
            value (str): The value of the property.
        """
        self.properties.append(QSSProperty(name, value))

    def clone_without_pseudo_elements(self):
        """
        Create a copy of the rule without pseudo-elements.

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
        Format a rule in the standardized QSS format.

        Args:
            selector (str): The selector for the rule.
            properties (List[QSSProperty]): The properties to include.

        Returns:
            str: Formatted rule string.
        """
        props = "\n".join(f"\t{p.name}: {p.value};" for p in properties)
        return f"{selector} {{\n{props}\n}}\n"

    def __repr__(self):
        """
        Return a string representation of the rule.

        Returns:
            str: A string in the format 'selector { properties }'.
        """
        props = "\n\t".join(str(p) for p in self.properties)
        return f"{self.selector} {{\n\t{props}\n}}"

    def __hash__(self):
        """
        Compute a hash for the rule to enable deduplication in sets.

        Returns:
            int: Hash value based on the selector and properties.
        """
        return hash((self.selector, tuple((p.name, p.value) for p in self.properties)))

    def __eq__(self, other):
        """
        Compare this rule with another for equality.

        Args:
            other: Another object to compare with.

        Returns:
            bool: True if the rules have the same selector and properties, False otherwise.
        """
        if not isinstance(other, QSSRule):
            return False
        return self.selector == other.selector and self.properties == other.properties


class QSSParser:
    def __init__(self):
        """
        Initialize the QSS parser with an empty state.
        """
        self._reset()

    def _reset(self):
        """
        Reset the parser's internal state.

        Initializes:
            rules: List of parsed QSS rules.
            _current_rule: Current rule being processed (None initially).
            _buffer: Buffer for accumulating property lines.
            _in_comment: Flag indicating if inside a comment block.
            _in_rule: Flag indicating if inside a rule block.
            _current_selectors: List of current selectors being processed.
            _original_selector: Original selector text for the current rule.
        """
        self.rules: List[QSSRule] = []
        self._current_rule: Optional[QSSRule] = None
        self._buffer = ""
        self._in_comment = False
        self._in_rule = False
        self._current_selectors: List[str] = []
        self._original_selector: Optional[str] = None

    def check_format(self, qss_text: str) -> List[str]:
        """
        Validate the format of QSS text, checking for unclosed braces, properties without semicolons,
        extra closing braces, and malformed rules.

        Args:
            qss_text (str): The QSS text to validate.

        Returns:
            List[str]: List of error messages in the format:
                       "Error on line {num}: {description}: {content}".
                       Returns an empty list if the format is correct.

        Example:
            >>> parser = QSSParser()
            >>> qss = "QPushButton { color: blue }"
            >>> parser.check_format(qss)
            ['Error on line 1: Property missing ';': color: blue']
        """
        errors = []
        lines = qss_text.splitlines()
        in_comment = False
        in_rule = False
        open_braces = 0
        current_selector = ""
        last_line_num = 0
        property_buffer = ""

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

            # Check for a complete single-line rule (e.g., "#selector { prop: value; }")
            if self._is_complete_rule(line):
                errors.extend(self._validate_complete_rule(line, line_num))
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

                property_buffer, new_errors = self._process_property_line_for_format(
                    line, property_buffer, line_num
                )
                errors.extend(new_errors)
                last_line_num = line_num
            else:
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
                    # Flag lines that look like selectors but lack an opening brace
                    if self._is_potential_selector(line):
                        errors.append(
                            f"Error on line {line_num}: Selector without opening brace '{{': {line}"
                        )

        errors.extend(
            self._finalize_validation(
                open_braces, current_selector, property_buffer, last_line_num
            )
        )

        return errors

    def _is_complete_rule(self, line: str) -> bool:
        """
        Check if the line is a complete QSS rule (selector + { + properties + }).

        Args:
            line (str): The line to check.

        Returns:
            bool: True if the line is a complete QSS rule, False otherwise.
        """
        return bool(re.match(r"^\s*[^/][^{}]*\s*\{[^}]*\}\s*$", line))

    def _validate_complete_rule(self, line: str, line_num: int) -> List[str]:
        """
        Validate a complete QSS rule in a single line.

        Args:
            line (str): The line containing the complete rule.
            line_num (int): The line number in the QSS text.

        Returns:
            List[str]: List of error messages for the rule, if any.
        """
        errors = []
        # Extract selector and properties
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
        Check if the line could be a selector (but not a complete rule or property).

        Args:
            line (str): The line to check.

        Returns:
            bool: True if the line looks like a selector, False otherwise.
        """
        # Exclude lines that are complete rules, properties, or comments
        return (
            not self._is_complete_rule(line)
            and not self._is_property_line(line)
            and not line.startswith("/*")
            and "*/" not in line
            and not line == "}"
            and bool(re.match(r"^\s*[^/][^{};]*\s*$", line))
        )

    # [Rest of the methods unchanged]
    def _handle_comments(self, line: str, in_comment: bool) -> bool:
        """
        Check if the line starts a comment block.

        Args:
            line (str): The line to check.
            in_comment (bool): Whether the parser is currently inside a comment block.

        Returns:
            bool: True if the line starts a new comment block, False otherwise.
        """
        return line.startswith("/*") and not in_comment

    def _validate_selector(self, line: str, line_num: int) -> Tuple[List[str], str]:
        """
        Validate a line containing a selector and an opening brace.

        Args:
            line (str): The line to validate.
            line_num (int): The line number in the QSS text.

        Returns:
            Tuple[List[str], str]: A tuple containing a list of error messages and the extracted selector.
        """
        errors = []
        selector = line[:-1].strip()
        if not selector:
            errors.append(
                f"Error on line {line_num}: Empty selector before '{{': {line}"
            )
        return errors, selector

    def _is_property_line(self, line: str) -> bool:
        """
        Check if the line contains a property (e.g., 'color: blue;').

        Args:
            line (str): The line to check.

        Returns:
            bool: True if the line is a valid property line, False otherwise.
        """
        return ":" in line and ";" in line

    def _process_property_line_for_format(
        self, line: str, buffer: str, line_num: int
    ) -> Tuple[str, List[str]]:
        """
        Process a property line for format validation, accumulating in the buffer and checking for semicolons.

        Args:
            line (str): The current line to process.
            buffer (str): The buffer of accumulated properties.
            line_num (int): The current line number.

        Returns:
            Tuple[str, List[str]]: Updated buffer and list of error messages.
        """
        errors = []
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
                if part.strip():
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
        Validate pending properties in the buffer, checking for missing semicolons.

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
        Validate final conditions, such as unclosed braces or pending properties.

        Args:
            open_braces (int): Number of open braces.
            current_selector (str): The current selector being processed.
            buffer (str): The buffer of pending properties.
            last_line_num (int): The last line number processed.

        Returns:
            List[str]: List of error messages for final validation issues.
        """
        errors = []
        if open_braces > 0 and current_selector:
            errors.append(
                f"Error on line {last_line_num}: Unclosed brace '{{' for selector: {current_selector}"
            )
        errors.extend(self._validate_pending_properties(buffer, last_line_num))
        return errors

    def parse(self, qss_text: str):
        """
        Parse QSS text into a list of QSSRule objects.

        Args:
            qss_text (str): The QSS text to parse.
        """
        self._reset()
        lines = qss_text.splitlines()
        for line in lines:
            self._process_line(line)
        if self._buffer.strip():
            self._process_property_line(self._buffer)

    def _process_line(self, line: str):
        """
        Process a single line of QSS text.

        Args:
            line (str): The line to process.
        """
        line = line.strip()
        if not line or self._in_comment:
            if "*/" in line:
                self._in_comment = False
            return
        if line.startswith("/*"):
            self._in_comment = True
            return
        # Handle complete single-line rule
        if self._is_complete_rule(line):
            self._process_complete_rule(line)
            return
        if line.endswith("{") and not self._in_rule:
            selector_part = line[:-1].strip()
            selectors = [s.strip() for s in selector_part.split(",") if s.strip()]
            if not selectors:
                return
            self._current_selectors = selectors
            self._original_selector = selector_part
            self._current_rules = []
            for sel in selectors:
                rule = QSSRule(sel, original=f"{sel} {{\n")
                self._current_rules.append(rule)
            self._in_rule = True
            return
        if line == "}" and self._in_rule:
            for rule in self._current_rules:
                rule.original += "}\n"
                self._add_rule(rule)
            self._current_rules = []
            self._in_rule = False
            self._current_selectors = []
            self._original_selector = None
            return
        if self._in_rule and self._current_rules:
            if ";" in line:
                full_line = (
                    (self._buffer + " " + line).strip() if self._buffer else line
                )
                self._buffer = ""
                parts = full_line.split(";")
                for part in parts[:-1]:
                    if part.strip():
                        self._process_property_line(part.strip() + ";")
                if parts[-1].strip():
                    self._buffer = parts[-1].strip()
            else:
                self._buffer = (self._buffer + " " + line).strip()

    def _process_complete_rule(self, line: str):
        """
        Process a complete QSS rule in a single line.

        Args:
            line (str): The line containing the complete rule.
        """
        match = re.match(r"^\s*([^/][^{}]*)\s*\{([^}]*)\}\s*$", line)
        if not match:
            return
        selector, properties = match.groups()
        selector = selector.strip()
        selectors = [s.strip() for s in selector.split(",") if s.strip()]
        if not selectors:
            return
        self._current_selectors = selectors
        self._original_selector = selector
        self._current_rules = []
        for sel in selectors:
            rule = QSSRule(sel, original=f"{sel} {{\n")
            self._current_rules.append(rule)
        if properties.strip():
            prop_parts = properties.split(";")
            for part in prop_parts:
                part = part.strip()
                if part:
                    self._process_property_line(part + ";")
        for rule in self._current_rules:
            rule.original += "}\n"
            self._add_rule(rule)
        self._current_rules = []
        self._current_selectors = []
        self._original_selector = None

    def _process_property_line(self, line: str):
        """
        Process a property line and add it to the current rules.

        Args:
            line (str): The property line to process.
        """
        line = line.rstrip(";")
        if not self._current_rules:
            return
        parts = line.split(":", 1)
        if len(parts) == 2:
            name, value = parts
            if name.strip() and value.strip():
                normalized_line = f"{name.strip()}: {value.strip()};"
                for rule in self._current_rules:
                    rule.original += f"    {normalized_line}\n"
                    rule.add_property(name.strip(), value.strip())

    def _add_rule(self, rule: QSSRule):
        """
        Add a rule to the parser's rule list, merging with existing rules if necessary.

        Args:
            rule (QSSRule): The rule to add.
        """
        for existing_rule in self.rules:
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
                return
        self.rules.append(rule)
        if (
            ":" in rule.selector
            and "::" not in rule.selector
            and "," not in rule.selector
        ):
            base_rule = rule.clone_without_pseudo_elements()
            base_rule_tuple = (
                base_rule.selector,
                tuple((p.name, p.value) for p in base_rule.properties),
            )
            existing_rules = [
                (r.selector, tuple((p.name, p.value) for p in r.properties))
                for r in self.rules
            ]
            if base_rule_tuple not in existing_rules:
                self.rules.append(base_rule)

    def get_styles_for(
        self,
        widget,
        fallback_class: Optional[str] = None,
        additional_selectors: Optional[List[str]] = None,
        include_class_if_object_name: bool = False,
    ) -> str:
        """
        Retrieve QSS styles for a given widget.

        Args:
            widget: The widget to retrieve styles for.
            fallback_class (Optional[str]): Fallback class to use if no styles are found.
            additional_selectors (Optional[List[str]]): Additional selectors to include.
            include_class_if_object_name (bool): Whether to include class styles if an object name is present.

        Returns:
            str: The concatenated QSS styles for the widget.
        """
        object_name = widget.objectName()
        class_name = widget.metaObject().className()
        styles = set()
        object_name_styles = set()
        class_name_styles = set()

        if object_name:
            object_name_styles = self._get_rules_for_selector(f"#{object_name}")
            styles.update(object_name_styles)
            if include_class_if_object_name:
                class_name_styles = self._get_rules_for_selector(class_name)
                styles.update(class_name_styles)

        if not object_name or not object_name_styles:
            class_name_styles = self._get_rules_for_selector(class_name)
            styles.update(class_name_styles)

        if fallback_class and not object_name_styles and not class_name_styles:
            styles.update(self._get_rules_for_selector(fallback_class))

        if additional_selectors:
            for selector in additional_selectors:
                styles.update(self._get_rules_for_selector(selector))

        unique_styles = sorted(set(styles), key=lambda r: r.selector)
        return "\n".join(r.original.rstrip("\n") for r in unique_styles)

    def _get_rules_for_selector(self, selector: str) -> List[QSSRule]:
        """
        Retrieve rules matching a given selector.

        Args:
            selector (str): The selector to match.

        Returns:
            List[QSSRule]: List of matching QSS rules.
        """
        matching_rules = set()
        base_selector = selector.split("::")[0].split(":")[0]
        for rule in self.rules:
            rule_selectors = [s.strip() for s in rule.selector.split(",")]
            for sel in rule_selectors:
                sel_parts = [part.strip() for part in sel.split()]
                if sel == selector:
                    matching_rules.add(rule)
                    continue
                if len(sel_parts) == 1:
                    part_base = sel.split("::")[0].split(":")[0]
                    if part_base == base_selector:
                        matching_rules.add(rule)
                elif sel_parts[0].split("::")[0].split(":")[0] == base_selector:
                    matching_rules.add(rule)
        return list(matching_rules)

    def __repr__(self):
        """
        Return a string representation of the parser.

        Returns:
            str: A string containing all rules, separated by double newlines.
        """
        return "\n\n".join(str(rule) for rule in self.rules)
