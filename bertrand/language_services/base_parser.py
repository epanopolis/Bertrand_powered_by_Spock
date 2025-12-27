"""
Support functions for the parser module.

"""
from .dictionaries.errors import Errors
from .dictionaries.tokens import op_prec_dict

class BaseParser:
    """Base class for parsing logic."""
    def __init__(self, token_list):
        self.token_list = token_list
        self.current_position = 0

    def current_token(self):
        """Returns the current token or None if out of bounds."""
        return (self.token_list[self.current_position] if self.current_position
            < len(self.token_list) else None)

    def advance(self):
        """Advances the current position."""
        self.current_position += 1

    def _expression_number(self, pos=None):
        """
        Return the 1-based expression number at token index `pos` in
        self.token_list.  Expression boundaries are statement delimiters
        ('.', ';', ',', '$$' or any token with token_type == 'delimiter'). As a
        fallback, a change in token.line is treated as a boundary when 
        delimiters were consumed upstream.
        
        """
        if pos is None:
            pos = self.current_position

        stmt_delims = {';', '.', ',', '$$'}
        expr_no = 1
        prev_line = None

        if not self.token_list:
            return expr_no

        try:
            pos = int(pos)
        except RuntimeError:
            pos = self.current_position

        if pos < 0:
            return expr_no
        if pos >= len(self.token_list):
            pos = len(self.token_list) - 1

        for i in range(0, pos + 1):
            tok = self.token_list[i]
            lex = getattr(tok, "lexeme", None)
            ttype = getattr(tok, "token_type", None)

            if ttype == "delimiter" or lex in stmt_delims:
                if i < pos:
                    expr_no += 1
                prev_line = None
                continue

            ln = getattr(tok, "line", None)
            if prev_line is None:
                prev_line = ln
            else:
                if (ln is not None and prev_line \
                    is not None and ln != prev_line):
                    expr_no += 1
                prev_line = ln

        return expr_no

    def _expr_loc(self, expr_no, col=None):
        if col is None:
            return f"Expression {expr_no}"
        return f"Expression {expr_no}, column {col}"

    def _raise_expr_error(self, message, token=None, pos=None):
        """Raise Errors with a consistent expression-based location prefix."""
        col = None
        if token is not None:
            if isinstance(token, dict):
                col = token.get("column")
            else:
                col = getattr(token, "column", None)

        if pos is None:
            pos = self.current_position

        expr_no = None
        try:
            expr_no = self._expression_number(pos)
        except RuntimeError:
            expr_no = None

        if expr_no is not None:
            raise Errors(f"{self._expr_loc(expr_no, col)}: {message}")

        raise Errors(message)

    def _check_infix_operands(self, node):
        """
        Recursively ensure every infix operator has an operand on both sides
        within the same container (list). Also enforces the strict '/' pattern.
        Raises Errors on the first violation.
    
        All location references are reported as expression numbers (1-based),
        rather than source line numbers.

        """
        # extend if you add more unary prefixes
        prefix_ops = {'¬', '!', '∀', '∃', '¬∀', '¬∃', '!∀', '!∃'}

        # delimiters that separate expressions/statements
        stmt_delims = {';', '.', ',', '$$'}

        def is_operand_node(n):
            # a nested list is a complete subexpression;
            # a dict with these token_types is an operand
            return (
                isinstance(n, list) or
                (isinstance(n, dict) and n.get('token_type') in
                    (
                    'identifier',
                    'boolean',
                    'number',
                    'container',
                    'set',
                    )
                )
            )

        def is_prefix_dict(d):
            return (
                isinstance(d, dict) and d.get('token_type') == 'operator' and
                d.get('lexeme') in prefix_ops
            )

        def is_infix_dict(d):
            if not (isinstance(d, dict) and d.get('token_type') == 'operator'):
                return False
            lx = d.get('lexeme')
            # any operator in the precedence table that is not a prefix op
            # is treated as infix here
            return (lx in op_prec_dict) and (lx not in prefix_ops)

        def is_stmt_delim_dict(d):
            return (
                isinstance(d, dict) and (
                    d.get('token_type') == 'delimiter' or
                    d.get('lexeme') in stmt_delims
                )
            )

        def first_leaf_dict(n):
            if isinstance(n, dict):
                return n
            if isinstance(n, list):
                for item in n:
                    got = first_leaf_dict(item)
                    if got is not None:
                        return got
            return None

        def last_leaf_dict(n):
            if isinstance(n, dict):
                return n
            if isinstance(n, list):
                for item in reversed(n):
                    got = last_leaf_dict(item)
                    if got is not None:
                        return got
            return None

        def node_first_line(n):
            d = first_leaf_dict(n)
            return d.get('line') if isinstance(d, dict) else None

        def node_last_line(n):
            d = last_leaf_dict(n)
            return d.get('line') if isinstance(d, dict) else None

        def node_first_col(n):
            d = first_leaf_dict(n)
            return d.get('column') if isinstance(d, dict) else None

        def expr_no_at_index(seq, idx):
            """
            1-based expression number within this container, based on statement
            delimiters and (fallback) line changes when delimiters were consumed

            """
            expr_no = 1
            prev_item = None

            for p in range(0, idx + 1):
                item = seq[p]

                if is_stmt_delim_dict(item):
                    if p < idx:
                        expr_no += 1
                    prev_item = None
                    continue

                if prev_item is not None:
                    ll = node_last_line(prev_item)
                    rl = node_first_line(item)
                    if ll is not None and rl is not None and ll != rl:
                        expr_no += 1

                prev_item = item

            return expr_no

        def loc_for_index(seq, idx, tok=None):
            expr_no = expr_no_at_index(seq, idx)
            col = None
            if isinstance(tok, dict):
                col = tok.get('column')
            if col is None:
                col = node_first_col(seq[idx])
            return self._expr_loc(expr_no, col)

        def err_missing(side, seq, idx, tok):
            op = tok.get('lexeme')
            raise Errors(
                f"{loc_for_index(seq, idx, tok)}: "
                f"infix operator '{op}' is missing an operand on its "
                f"{side} side."
            )

        # Recurse: lists are containers, dicts are leaves
        if isinstance(node, list):
            # first, validate each child container
            for child in node:
                if isinstance(child, list):
                    self._check_infix_operands(child)

            # then, validate infix operators within this list
            i = 0
            n = len(node)
            while i < n:
                cur = node[i]

                if isinstance(cur, list):
                    i += 1
                    continue

                if is_infix_dict(cur):
                    cur_line = node_first_line(cur)

                    # ---- check LEFT operand inside this same list ----
                    j, left_ok = i - 1, False

                    while j >= 0:
                        left = node[j]
                        if is_stmt_delim_dict(left):
                            break

                        if cur_line is not None:
                            ll = node_last_line(left)
                            if ll is not None and ll != cur_line:
                                break

                        if isinstance(left, list):
                            left_ok = True
                            break

                        if isinstance(left, dict):

                            if is_operand_node(left):
                                left_ok = True
                                break

                            if is_prefix_dict(left):
                                j -= 1
                                continue

                            # hit another operator without intervening operand
                            if left.get('token_type') == 'operator':
                                break

                        j -= 1

                    if not left_ok:
                        err_missing('left', node, i, cur)

                    # ---- check RIGHT operand inside this same list ----
                    k, right_ok = i + 1, False
                    # skip a chain of unary prefixes immediately to the right
                    while k < n and is_prefix_dict(node[k]):
                        if cur_line is not None:
                            pl = node_first_line(node[k])
                            if pl is not None and pl != cur_line:
                                break
                        k += 1

                    if k < n:
                        nxt = node[k]
                        if cur_line is not None:
                            nl = node_first_line(nxt)
                            if nl is not None and nl != cur_line:
                                nxt = None
                        if (nxt is not None) and is_operand_node(nxt):
                            right_ok = True

                    if not right_ok:
                        err_missing('right', node, i, cur)

                    # strict substitution rule: '/' must be followed
                    # immediately by id or (id), then ≡ or ↔
                    if cur.get('lexeme') == '/':
                        k = i + 1
                        if k >= n:
                            raise Errors(
                                f"{loc_for_index(node, i, cur)}: "
                                f"substitution '/' is missing the target "
                                f"variable."
                            )

                        nxt = node[k]
                        if cur_line is not None:
                            nl = node_first_line(nxt)
                            if nl is not None and nl != cur_line:
                                raise Errors(
                                    f"{loc_for_index(node, i, cur)}: "
                                    f"substitution '/' is missing the target "
                                    f"variable."
                                )

                        # Case A: '/x'
                        if (isinstance(nxt, dict) and nxt.get('token_type') == \
                            'identifier'):
                            k2 = k + 1
                            if (
                                k2 >= n or not (
                                    isinstance(node[k2], dict) and
                                    node[k2].get('token_type') == 'operator' and
                                    node[k2].get('lexeme') in {'≡', '↔'}
                                )
                            ):
                                raise Errors(
                                    f"{loc_for_index(node, i, cur)}: "
                                    f"substitution '/{nxt.get('lexeme','?')}' "
                                    f"must be "
                                    f"immediately followed by '≡' or '↔'."
                                )

                        # Case B: '/(x)' – represented here as a child list
                        # containing exactly one identifier
                        elif isinstance(nxt, list):
                            if not (
                                len(nxt) == 1 and isinstance(nxt[0], dict) and
                                nxt[0].get('token_type') == 'identifier'
                            ):
                                raise Errors(
                                    f"{loc_for_index(node, i, cur)}: "
                                    f"substitution '/' expects a single "
                                    f"identifier in parentheses "
                                    f"immediately after '/'."
                                )

                            k2 = k + 1
                            if (
                                k2 >= n or not (
                                    isinstance(node[k2], dict) and
                                    node[k2].get('token_type') == 'operator' and
                                    node[k2].get('lexeme') in {'≡', '↔'}
                                )
                            ):
                                raise Errors(
                                    f"{loc_for_index(node, i, cur)}: "
                                    f"substitution "
                                    f"'/({nxt[0].get('lexeme','?')})' must be "
                                    f"immediately followed by '≡' or '↔'."
                                )

                        else:
                            raise Errors(
                                f"{loc_for_index(node, i, cur)}: "
                                f"substitution '/' must be immediately "
                                f"followed by an "
                                f"identifier or a parenthesized identifier."
                            )

                i += 1

            # ---- check for adjacent operands (missing infix operator) ----
            # If an operand is immediately followed by another operand (or a
            # prefix-chain that leads to an operand), then an infix operator is
            # missing between them. Statement delimiters are allowed.
            p = 0
            while p < n - 1:
                left = node[p]

                if not is_operand_node(left):
                    p += 1
                    continue

                right = node[p + 1]

                # Treat a line change as an implicit expression boundary
                ll = node_last_line(left)
                rl = node_first_line(right)
                if ll is not None and rl is not None and ll != rl:
                    p += 1
                    continue

                # allow statement delimiters between expressions
                if is_stmt_delim_dict(right):
                    p += 1
                    continue

                # operand immediately followed by operand
                if is_operand_node(right):
                    loc = loc_for_index(node, p + 1, right \
                        if isinstance(right, dict) else None)
                    raise Errors(f"{loc}: two adjacent operands; "
                        f"missing infix operator between them.")

                # operand followed by unary prefix chain and then an operand
                if is_prefix_dict(right):
                    q = p + 1
                    while q < n and is_prefix_dict(node[q]):
                        q += 1
                    if q < n and is_operand_node(node[q]):
                        loc = loc_for_index(node, q, node[q] \
                        if isinstance(node[q], dict) else None)
                        raise Errors(f"{loc}: two adjacent operands; "
                        f"missing infix operator between them.")

                p += 1

            return

        # dict (leaf) → nothing to do
        return

        # no additional return needed here; success = no exception

    def _flatten(self, seq):
        stmt_delims = {';', '.', ',', '$$'}
        for x in seq:
            if isinstance(x, dict):
                yield x
            elif isinstance(x, (list, tuple)):
                yield from self._flatten(x)
            elif isinstance(x, str):
                # tolerate raw delimiters as strings
                if x in stmt_delims:
                    yield {'lexeme': x, 'token_type': 'delimiter'}
                # else ignore stray strings
            else:
                # ignore any other stray types
                pass

    def only_whitespace_after_last_period(self) -> bool:
        """
        Return True iff there is at least one '.' token and every token
        *after the last '.'* is either whitespace-like or the '$$' EOF marker.
        """
        last_dot = -1

        # Find position of the last '.' token
        for i, tok in enumerate(self.token_list):
            if getattr(tok, "lexeme", None) == ".":
                last_dot = i

        if last_dot == -1:
            # no '.' at all
            return False

        # Check all tokens after that '.'
        for tok in self.token_list[last_dot + 1:]:
            lex = getattr(tok, "lexeme", "")
            ttype = getattr(tok, "token_type", "")

            # Allow EOF marker
            if lex == "$$":
                continue

            # Allow explicit whitespace tokens, if the scanner produces them
            if isinstance(lex, str) and lex.strip() == "":
                continue
            if ttype in {"whitespace", "newline"}:
                continue

            # Anything else is a "real" token after the final '.'
            return False

        return True
