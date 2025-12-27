"""
Step 2. Parse the tokens. Generate an execution list for evaluation.

"""
# pylint: disable=relative-beyond-top-level

import ast
from .dictionaries.errors import Errors
from .dictionaries.tokens import op_prec_dict, op_assoc
from .base_parser import BaseParser

# pylint: disable=too-few-public-methods
class _SetContainerParser:
    """Internal helper so Turing.set_container() stays small (pylint)."""

    def __init__(self, turing):
        self.turing = turing
        self.token_list = turing.token_list
        self.stack = [{}]
        self.cur_dict = self.stack[-1]
        self.data_str = ""

    def parse(self):
        """
        Parse a set container starting at current_position; return dict 
        or None.

        """
        token = self.turing.current_token()
        new_char = getattr(token, "lexeme", None)

        # Accept optional leading 'set' (consume 1 token, not 3 characters)
        if new_char == "set":
            self.turing.current_position += 1
            token = self.turing.current_token()
            new_char = getattr(token, "lexeme", None)

        if new_char is None or new_char != "{":
            return None

        self._open_outer()

        try:
            return self._parse_body()
        except RuntimeError as e:
            raise Errors(f"Runtime error: {e}") from e

    # ------------------------- core loop -------------------------

    def _parse_body(self):
        while self._not_eof():
            token = self.turing.current_token()
            new_char = getattr(token, "lexeme", None)

            if self._consume_set_keyword_for_nested(new_char):
                continue

            result = self._step(token, new_char)
            if result is not None:
                return result

        self._raise_if_unclosed()
        return self.stack[0]

    def _step(self, token, new_char):
        if new_char == "{":
            self._flush_scalar()
            self._descend()
            return None

        if new_char == ",":
            self._flush_scalar()
            self.turing.current_position += 1
            return None

        if new_char == "}":
            return self._close_set(token)

        if token.token_type == "statement":
            raise RuntimeError("A statement may not be in an expression.")

        # accumulate scalar content
        if new_char:
            self.data_str += new_char
        self.turing.current_position += 1
        return None

    # ------------------------- helpers -------------------------

    def _not_eof(self):
        return (
            self.turing.current_position < len(self.token_list)
            and getattr(self.turing.current_token(), "lexeme", None) != "$$"
        )

    def _peek(self, offset=1):
        idx = self.turing.current_position + offset
        if 0 <= idx < len(self.token_list):
            return self.token_list[idx]
        return None

    def _open_outer(self):
        # push a frame for the opening '{' we just matched
        outer_dict = {}
        self.cur_dict |= outer_dict
        self.stack.append(outer_dict)
        self.cur_dict = outer_dict
        self.turing.current_position += 1  # consume '{'

    def _consume_set_keyword_for_nested(self, new_char):
        # Support 'set{' for nested sets: look ahead by 1 token, not 3
        if new_char != "set":
            return False
        nxt = self._peek(1)
        if getattr(nxt, "lexeme", None) != "{":
            return False
        self._flush_scalar()
        self.turing.current_position += 1  # consume 'set'
        return True  # next loop sees '{'

    def _flush_scalar(self):
        """Flush any pending scalar into the current dict."""
        if not self.data_str:
            return
        display = ", ".join(
            s.strip() for s in self.data_str.splitlines() if s.strip()
        )
        key = ("str", display)
        self.cur_dict[key] = display
        self.data_str = ""

    def _descend(self):
        """Descend into a new child set."""
        new_dict = {}
        # preserve your merge style (no-op on empty but keeps pattern)
        self.cur_dict |= new_dict
        self.stack.append(new_dict)
        self.cur_dict = new_dict
        self.turing.current_position += 1  # consume '{'

    def _close_set(self, token):
        # capture line/column from the CLOSING brace
        close_line = getattr(token, "line", None)
        close_col = getattr(token, "column", None)

        # flush any trailing scalar before closing
        self._flush_scalar()

        if len(self.stack) == 1:
            raise Errors(
                f"Unmatched closing delimiter: }} "
                f"at line {close_line}, column {close_col}"
            )

        closed = self.cur_dict

        # pop and restore parent
        self.stack.pop()
        self.cur_dict = self.stack[-1]
        self.turing.current_position += 1  # consume '}'

        # OUTERMOST close → return the SET with line/column from closing brace
        if len(self.stack) == 1:
            if not closed:
                return {
                    "lexeme": "∅",
                    "token_type": "boolean",
                    "line": close_line,
                    "column": close_col,
                    "value": False,
                }
            return {
                "lexeme": closed,
                "token_type": "set",
                "line": close_line,
                "column": close_col,
                "value": "unknown",
            }

        # nested close → ADD the child as a single element (do NOT merge)
        child_display = self._set_display(closed)
        key = ("set", child_display)
        self.cur_dict[key] = closed
        return None

    def _raise_if_unclosed(self):
        # if we didn’t cleanly close the outermost '{'
        if len(self.stack) == 1:
            return

        last = self.turing.current_token()
        lline = getattr(last, "line", None)
        lcol = getattr(last, "column", None)
        raise Errors(
            f"Unmatched opening delimiter: {{ (expected '}}' "
            f"before line {lline}, column {lcol})"
        )

    @staticmethod
    def _set_display(d):
        """Stringify a set-dict's values, recursing for nested sets."""
        if not d:
            return "∅"
        parts = []
        for v in d.values():
            if isinstance(v, dict):
                parts.append(_SetContainerParser._set_display(v))
            else:
                parts.append(str(v))
        return "{" + ", ".join(parts) + "}"

class Turing(BaseParser):
    """Primary parser for handling tokens."""

    def parse(self):
        """The primary departure point for parsing."""
        parsed_obj_list = []
        turbo_spec = TurboSpec()

        while True:
            tok = self.current_token()
            if tok is None:
                # No more tokens and we never saw "$$"
                raise Errors("Unexpected end of tokens (missing '$$' EOF).")
            if getattr(tok, "lexeme", None) == "$$":
                break

            try:
                parser_obj = self.try_parsers()
                if parser_obj:
                    if self.token_list[self.current_position - 1].lexeme == ".":
                        tokens = list(self._flatten(parser_obj))
                        self._check_infix_operands(tokens)
                        parsed_obj_list.extend([parser_obj])
                        if (self.current_position + 1) < len(self.token_list):
                            raise Errors("Premature termination by period")
                        break

                    tokens = list(self._flatten(parser_obj))
                    self._check_infix_operands(tokens)
                    parsed_obj_list.extend([parser_obj])

                else:
                    raise Errors(f"Failed to parse token '{tok}' at index" + \
                        "{self.current_position}")

            except RuntimeError as e:
                raise Errors(f"parsing error: {e}") from e

        if not self.only_whitespace_after_last_period():
            raise Errors("Terminal period missing from end of last statement")

        finished_list = turbo_spec.prep_bracket_list(parsed_obj_list)

        return finished_list

    def try_parsers(self):
        """The hub for postfix and sub-group container parsing."""
        parsers = [self.parse_postfix_delim, self.parse_containing_delim]
        for parser_method in parsers:
            parser_obj = parser_method()
            if parser_obj:
                return parser_obj
        return None

    def parse_postfix_delim(self):
        """ Statement/Expression-Statement Parser """
        result = []

        # pylint: disable=access-member-before-definition
        while self.current_position < len(self.token_list):
            token = self.current_token()
            if token is None:
                break

            lex = getattr(token, "lexeme", None)

            # Leave EOF for parse() to see; do NOT advance past "$$" here.
            if lex == "$$":
                return result if result else None

            # parser.py — inside parse_postfix_delim(), in 'statement' branch:
            if token.token_type == "statement":
                sub_obj_list = statement_parser.parse()
                # pylint: disable=attribute-defined-outside-init
                # sync Turing cursor with the statement parser
                self.current_position = statement_parser.cur_pos
                if not sub_obj_list:
                    continue
                result.append(sub_obj_list)
                continue

            if lex == ")":
                raise Errors("Closing parentheses without matching opening " \
                    "parentheses")

            if lex == "(":
                sub_obj_list = self.parse_containing_delim()
                if not sub_obj_list:
                    continue
                result.append(sub_obj_list)
                continue

            if lex == "set":
                new_dict = self.set_container()
                if not new_dict:
                    continue
                # Dictionary values in set
                result.append(new_dict)
                continue

            if lex not in (".", "$$"):
                # append dictionary form so downstream code sees dict tokens
                result.append(token.to_map())
                self.current_position += 1
                continue

            # Delimiters: consume and return the collected statement
            if lex == ".":
                self.current_position += 1
            # For "$$", we return without consuming it.
            return result

        return None

    def parse_containing_delim(self):
        """Parsing for nested sub-groups and individual expressions."""
        tok = self.current_token()
        if tok is None or getattr(tok, "lexeme", None) != "(":
            return None

        if self.current_token().lexeme != "(":
            return None

        stack = []  # Use this to track nested lists
        current_list = []  # The current list to append tokens
        stack.append(current_list)  # Push the initial list onto the stack
        self.current_position += 1

        while (self.current_position < len(self.token_list)) and \
            self.current_token().lexeme != "$$":
            token = self.current_token()

            if token.lexeme in ('.',';'):
                raise Errors("Unexpected termination of token list with " + \
                    "open parentheses")

            if token.lexeme not in ["(", ")"]:
                if token.token_type != "statement":
                # Append token's dictionary representation to the current list
                    current_list.append(token.to_map())
                    self.current_position += 1
                    continue

                raise RuntimeError("A statement may not be present in an " +
                    "expression.")

            if token.lexeme == "(":
                # Start a new nested list and make it the current list
                new_list = []
                # Append the new list to the current one
                current_list.append(new_list)
                stack.append(new_list)  # Push the new list onto the stack
                current_list = new_list  # Update the current list
                self.current_position += 1
                continue

            if token.lexeme == ")":
                if not stack:
                    raise Errors(f"Unmatched closing delimiter: {token.lexeme}")
                stack.pop()  # Pop the current list

                if stack:
                    current_list = stack[-1]  # Return to the parent list
                self.current_position += 1

                # If the stack is empty, we've closed all parentheses
                if not stack:
                    return current_list
                continue

        if stack:
            raise Errors(f"Unmatched opening delimiter: {stack[-1]}")

        return stack[0]  # Return the top-level list

    def set_container(self):
        """ set container parser"""
        return _SetContainerParser(self).parse()

# pylint: disable=too-few-public-methods
class _RpnGenerator:
    """
    Internal helper so TurboSpec.rpn_generator() stays small (pylint).

    Rules:
      - LOWER precedence numbers in op_prec_dict bind tighter.
      - Associativity read from op_assoc (default 'L').
      - Unary prefix ops: '¬', '!' (and '∀', '∃' if present).
      - Depth increases => push virtual '('; decreases => pop until '('.
      - Left-to-right order uses 'column' if present; otherwise falls back 
        to: (depth, GPAD, PIG) which preserves in-group order.

    Returns: list[list[dict]]  # one RPN list per input line

    """

    def __init__(self, object_list):
        self.object_list = object_list

    # ------------------------- public entry -------------------------

    def generate(self):
        """ I can't remember what this function does """
        by_line = self._group_by_line()
        final = []
        for ln in self._sorted_lines(by_line):
            final.append(self._line_to_rpn(by_line[ln]))
        return final

    # ------------------------- grouping / ordering -------------------------

    @staticmethod
    def _sorted_lines(by_line):
        return sorted(by_line, key=lambda x: (x is None, x))  # None last

    def _group_by_line(self):
        by_line = {}
        for t in self.object_list:
            if not isinstance(t, dict):
                continue
            ln = t.get("line")
            try:
                ln = int(ln)
            except RuntimeError as e:
                raise Errors(f"Unknown error: {e}") from e
            by_line.setdefault(ln, []).append(t)
        return by_line

    def _line_to_rpn(self, tokens_for_line):
        tokens = sorted(tokens_for_line, key=self._col_key)
        base_depth = self._base_depth(tokens)

        out = []        # output queue (RPN)
        op_stack = []   # [("LPAREN", depth_marker) | ("OP", token_dict)]
        cur_depth = base_depth

        for t in tokens:
            cur_depth = self._sync_depth(
                cur_depth, 
                self._depth(t), 
                out, 
                op_stack)

            self._process_token(
                t, 
                out, 
                op_stack)

        self._close_remaining_depth(cur_depth, base_depth, out, op_stack)
        self._drain_ops(out, op_stack)
        return out

    @staticmethod
    def _base_depth(tokens):
        if not tokens:
            return 0
        return min(_RpnGenerator._depth(t) for t in tokens)

    # ------------------------- token classification -------------------------

    @staticmethod
    def _is_operand(t):
        # Treat sets like literals so they flow through the RPN queue
        return isinstance(t, dict) and t.get("token_type") in \
            ("identifier", "boolean", "number", "set")

    @staticmethod
    def _is_operator(t):
        if not isinstance(t, dict):
            return False
        if t.get("token_type") == "operator":
            return True
        # Only consider string lexemes for operator-table membership
        lx = t.get("lexeme")
        if not isinstance(lx, str):
            return False
        return lx.strip() in op_prec_dict

    @staticmethod
    def _lex(t):
        lx = t.get("lexeme")
        return lx.strip() if isinstance(lx, str) else ""

    @staticmethod
    def _depth(t):
        try:
            return int(t.get("depth", 0))
        except RuntimeError:
            return 0

    def _col_key(self, t):
        # Prefer real source column; otherwise fall back to (depth, GPAD, PIG)
        col = t.get("column", None)
        if isinstance(col, int):
            return (col, self._depth(t), t.get("GPAD", 0), t.get("pig", 0))
        try:
            return (int(col), self._depth(t), t.get("gpad", 0), t.get("pig", 0))
        except RuntimeError:
            return (
                10**9
                + self._depth(t) * 10_000
                + int(t.get("gpad", 0)) * 100
                + int(t.get("pig", 0) or 0),
                self._depth(t),
                t.get("gpad", 0),
                t.get("pig", 0),
            )

    # ------------------------- precedence / associativity ---------------------

    @staticmethod
    def _prec(lex):
        # Lower number = tighter (higher binding power)
        try:
            return int(op_prec_dict.get(lex, 10**6))
        except RuntimeError:
            # if someone put strings like "2" in the table, coerce here
            try:
                return int(str(op_prec_dict.get(lex)))
            except RuntimeError:
                return 10**6

    @staticmethod
    def _assoc(lex):
        return (op_assoc.get(lex) or 'L')  # default to left-assoc

    def _pop_while_top_tighter_or_equal_left(self, op_stack, cur_lex):
        cur_p = self._prec(cur_lex)
        cur_a = self._assoc(cur_lex)  # 'L' or 'R'
        while op_stack and op_stack[-1][0] == "OP":
            top_lex = self._lex(op_stack[-1][1])
            tp = self._prec(top_lex)
            if (tp < cur_p) or (tp == cur_p and cur_a == 'L'):
                yield op_stack.pop()[1]
            else:
                break

    # ------------------------- shunting-yard core -------------------------

    def _process_token(self, t, out, op_stack):
        if self._is_operand(t):
            out.append(t)
            return

        if self._is_operator(t):
            lex = self._lex(t)

            # For all operators (unary or binary), use precedence & assoc
            # Unary prefix works naturally: it waits on the stack until its
            # operand has been emitted, then is popped by a later op/end/close.
            for popped in self._pop_while_top_tighter_or_equal_left(
                op_stack, 
                lex):
                out.append(popped)
            op_stack.append(("OP", t))
            return

        # ignore anything else (delimiters shouldn't be here at this stage)

    def _sync_depth(self, cur_depth, new_depth, out, op_stack):
        cur_depth = self._open_virtual_parens(cur_depth, new_depth, op_stack)
        cur_depth = self._close_virtual_parens(
            cur_depth, 
            new_depth, 
            out, 
            op_stack)
        return cur_depth

    @staticmethod
    def _open_virtual_parens(cur_depth, new_depth, op_stack):
        while cur_depth < new_depth:
            op_stack.append(("LPAREN", cur_depth + 1))
            cur_depth += 1
        return cur_depth

    @staticmethod
    def _close_virtual_parens(cur_depth, new_depth, out, op_stack):
        while cur_depth > new_depth:
            while op_stack and op_stack[-1][0] != "LPAREN":
                out.append(op_stack.pop()[1])
            if op_stack and op_stack[-1][0] == "LPAREN":
                op_stack.pop()
            cur_depth -= 1
        return cur_depth

    def _close_remaining_depth(self, cur_depth, base_depth, out, op_stack):
        # Close any remaining open virtual parens for this line
        self._close_virtual_parens(cur_depth, base_depth, out, op_stack)

    @staticmethod
    def _drain_ops(out, op_stack):
        # Pop any remaining operators
        while op_stack:
            tag, val = op_stack.pop()
            if tag == "OP":
                out.append(val)
            # stray LPAREN (malformed input) is ignored on purpose

# pylint: disable=too-few-public-methods
# pylint: disable=too-many-instance-attributes
class _PrepBracketList:
    """Internal helper so TurboSpec.prep_bracket_list() stays small (pylint)."""

    i: int
    j: int
    k: int
    tree: dict
    gpad: dict
    pig_stack: list
    previous_direction: str
    new_string: str
    wrapper_flag: bool
    eof_flag: bool
    curly_depth: int
    item_wrapper_active: bool
    last_sig_char: object
    string_list: str

    def __init__(self, turbo_spec, object_list):
        object.__setattr__(self, "turbo_spec", turbo_spec)
        object.__setattr__(self, "_state", {
            "string_list": repr(object_list),

            "i": -1,
            "j": -1,
            "k": -1,
            "tree": {},   # depth -> { group_index(i) -> last_item_index(k) }
            "gpad": {},   # "group position at depth"
            "pig_stack": [],

            "previous_direction": "[",
            "new_string": "",
            "wrapper_flag": False,
            "eof_flag": False,

            # Track nesting of curly dicts so we only wrap true top-level dicts
            "curly_depth": 0,
            "item_wrapper_active": False,

            # last non-whitespace character we appended
            # (to detect ':' just before '{')
            "last_sig_char": None,
        })

    def __getattr__(self, name):
        state = object.__getattribute__(self, "_state")
        try:
            return state[name]
        except KeyError as e:
            raise AttributeError(name) from e

    def __setattr__(self, name, value):
        if name in ("turbo_spec", "_state") or name.startswith("_"):
            object.__setattr__(self, name, value)
            return
        state = object.__getattribute__(self, "_state")
        state[name] = value

    def generate(self):
        """ I don't remember what this function is for """
        self._walk()
        new_string = self._finalize()
        new_list = self.turbo_spec.string_to_list(new_string)
        new_list = self.turbo_spec.precedence_list_maker(new_list)
        return self.turbo_spec.rpn_generator(new_list)

    # ------------------------- core loop -------------------------

    def _walk(self):
        for m in self.string_list:
            action = self._handle_eof(m)
            if action == "break":
                break
            if action == "continue":
                continue

            self._latch_first_wrapper(m)

            if self._open_group(m):
                continue
            if self._close_group(m):
                continue
            if self._open_item(m):
                continue
            if self._close_item(m):
                continue

            self._passthrough(m)

    # ------------------------- steps -------------------------

    def _handle_eof(self, m):
        # --- EOF handling (unchanged) ---
        if self.j < 0:
            if m == "$" or self.eof_flag is True:
                if m == "$":
                    self.eof_flag = True
                    return "continue"
            elif self.eof_flag is True:
                if m == "$":
                    return "break"
        return None

    def _latch_first_wrapper(self, m):
        # latch the very first wrapper
        if self.wrapper_flag is False and m == "[":
            self.wrapper_flag = True
            self.new_string += m
            self.last_sig_char = "["

    def _open_group(self, m):
        # OPEN GROUP
        if m != "[" or self.wrapper_flag is not True:
            return False

        # ensure a comma between sibling lists
        if self.previous_direction == "]":
            self._ensure_sibling_comma()

        # count this nested group as an item in its parent group
        if self.j >= 0:
            self._count_nested_group_in_parent()

        # descend one depth
        self.j += 1

        # next group index at this depth
        self.i = self.gpad.get(self.j, -1) + 1
        self.gpad[self.j] = self.i

        # Start a fresh per-group item counter at the child depth
        self.pig_stack.append(-1)
        self.k = -1

        if self.j not in self.tree:
            self.tree[self.j] = {}
        self.tree[self.j][self.i] = -1

        self.previous_direction = "["
        self.new_string += f"[{self.j},{self.i},{m}"
        self.last_sig_char = "["
        return True

    def _close_group(self, m):
        # CLOSED GROUP
        if m != "]":
            return False

        self._trim_trailing_commas()
        self.new_string += "]]"  # close the actual group list and its wrapper

        if self.pig_stack:
            self.pig_stack.pop()

        self.j -= 1
        self.j = max(self.j, -1)
        self.previous_direction = "]"
        self.last_sig_char = "]"
        return True

    def _open_item(self, m):
        # OPEN ITEM
        if m != "{":
            return False

        # Only wrap as a top-level item dict when:
        #  - we are NOT currently inside any dict (curly_depth == 0),and
        #  - the previous significant char is NOT a colon
        #    (so this isn't a dict value)
        if self.curly_depth == 0 and self.last_sig_char != ":":
            if self.previous_direction == "]":
                self._ensure_sibling_comma()

            if not self.pig_stack:
                self.pig_stack.append(-1)

            self.k = self.pig_stack.pop() + 1
            self.pig_stack.append(self.k)

            self.i = self.gpad.get(self.j, -1)

            if self.j not in self.tree:
                self.tree[self.j] = {}
            self.tree[self.j][self.i] = self.k

            self.new_string += f"[{self.j},{self.i},{self.k},{m}"
            self.item_wrapper_active = True
        else:
            # This is a dict VALUE (e.g., the set dict in 'lexeme'):
            # do not wrap
            self.new_string += m

        self.curly_depth += 1
        self.last_sig_char = "{"
        return True

    def _close_item(self, m):
        # CLOSED ITEM
        if m != "}":
            return False

        self.new_string += m
        self.curly_depth = max(0, self.curly_depth - 1)

        if self.curly_depth == 0 and self.item_wrapper_active:
            self.new_string += "]"
            self.item_wrapper_active = False

        self.last_sig_char = "}"
        return True

    def _passthrough(self, m):
        # passthrough for non-delimiters
        self.new_string += m
        if m.strip():
            self.last_sig_char = m  # track ':' and other significant separators

    # ------------------------- helpers -------------------------

    def _trim_trailing_commas(self):
        while self.new_string and self.new_string[-1] in " ,":
            self.new_string = self.new_string[:-1]

    def _ensure_sibling_comma(self):
        self._trim_trailing_commas()
        self.new_string += ", "

    def _count_nested_group_in_parent(self):
        if self.pig_stack:
            k_parent = self.pig_stack.pop() + 1
            self.pig_stack.append(k_parent)
        else:
            k_parent = 0
            self.pig_stack.append(k_parent)

        i_parent = self.gpad.get(self.j, -1)
        if self.j not in self.tree:
            self.tree[self.j] = {}
        self.tree[self.j][i_parent] = k_parent

    def _finalize(self):
        if self.new_string and self.new_string[-1] == ",":
            self.new_string = self.new_string[:-1]
        self.new_string = self.new_string + "]"
        return self.new_string

class TurboSpec:
    """
    This is the final stage of parsing with top-down generation of a 
    Reverse Polish Notation list of operators and their operands for 
    bottom-up evaluation

    """
    def string_to_list(self, new_string):
        ''' Convert the string back to a list '''

        try:
            obj = ast.literal_eval(new_string)
        except SyntaxError as e:
            raise Errors(f"String is not a list/tuple literal: {e}") from e

        if isinstance(obj, list):
            return obj

        if isinstance(obj, tuple):  # allow tuples, coerce to list
            return list(obj)

        return None

    def precedence_list_maker(self, bracket_list):
        """
        Sort the dicts by depth, group position at depth (GPAD), position in
        the group (PIG) and operator precedence and include those numbers 
        in each dict.

        """
        precedence_list = []
        new_dict = {}
        stack = ["$$"]

        def to_map(depth,gpad,pig,op_prec):
            """Returns a dictionary representation of the token.""" 
            return {
                "depth": depth,
                "gpad": gpad,
                "pig": pig,
                "op_prec": op_prec,
            }

        while stack:
            while bracket_list:
                if isinstance(bracket_list[-1],list):
                    stack.append(bracket_list.pop(-1))

                elif isinstance(bracket_list[-1],int):
                    bracket_list.pop(-1)

                elif isinstance(bracket_list[-1],dict):
                    element = bracket_list.pop(-1)
                    lex = element.get("lexeme")
                    # Only attempt a table lookup
                    # if the lexeme is a simple, hashable scalar
                    if isinstance(lex, (str, int, float, bool)) or lex is None:
                        op_prec = op_prec_dict.get(lex, 99)
                    else:
                        op_prec = 99  # non-operator (e.g., set/group payloads)
                    pig = bracket_list.pop(-1)
                    gpad = bracket_list.pop(-1)
                    depth = bracket_list.pop(-1)

                    new_dict = element|to_map(depth,gpad,pig,op_prec)
                    # We are no longer concerned about reordering or
                    # repacking dicts in a certain order
                    # because these dicts will now be
                    # sorted according to their depth, GPAD, and PIG numbers.

                    precedence_list.append(new_dict)

                if not bracket_list:
                    if stack[-1] == "$$":
                        precedence_list = sorted(precedence_list, key=lambda d:
                            (d["line"],

                            d["depth"],

                            d["gpad"],

                            d["pig"],
                            ))

                        return precedence_list

                    bracket_list = stack.pop()

    def rpn_generator(self, object_list):
        """
        Convert per-line infix tokens to RPN using depth as virtual parentheses.
        (implementation moved into _RpnGenerator to satisfy pylint limits)
        """
        return _RpnGenerator(object_list).generate()

    def prep_bracket_list(self, object_list):
        """
        This is the hub of the RPN execution list generation.
        Here the content, having been converted from a list into a string, gets 
        an extra wrapper for each nested list, and the inner list will be 
        prepended with numbers designating the nested list's left-to-right 
        position at its nesting depth (GPAD) and a number for the depth itself, 
        both starting at zero. Any "stranded" non-list items not actually in a  
        list, particularly those between nestings and not at level zero (which 
        otherwise end up getting skipped during stack storage) will get their  
        own single wrapping with prepending of the dimension numbers.        
        """
        return _PrepBracketList(self, object_list).generate()
