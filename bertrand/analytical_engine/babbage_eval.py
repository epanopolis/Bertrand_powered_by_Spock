"""
Step 3. Evaluation of the parsed list.

"""
from bertrand.language_services.dictionaries.errors import Errors

# pylint: disable=missing-function-docstring
class Knuth:
    """The Spock Evaluator/Interpreter."""
    def __init__(self, code):
        self.code = code

    def bool_values(self, rpn):
        """
        Normalize boolean tokens in-place. Accepts ⊤/T/True -> True and
        ⊥/F/False -> False.
        """
        for t in rpn:
            if 'value' not in t:
                t['value'] = "unknown"
            typ = t.get('token_type')
            lex = t.get('lexeme')
            if typ == 'boolean':
                if lex in ('⊤', 'T', 'True', 'true', '1'):
                    t['value'] = True
                elif lex in ('⊥', 'F', 'False', 'false', '∅', '0'):
                    t['value'] = False


    _unary_ops = ("¬", "!", "∃", "∀", "¬∃", "¬∀", "!∃", "!∀")

    def _res_bldr(self, res):
        if isinstance(res, dict):
            return res
        if isinstance(res, bool):
            return {'lexeme': res, 'token_type': 'boolean', 'value': res}
        if isinstance(res, str):
            return {'lexeme': res, 'token_type': 'identifier', 'value': "unknown"}
        return {'lexeme': repr(res), 'token_type': 'identifier', 'value': "unknown"}

    def _eval_unary(self, op, a):
        a_val = a.get("value")
        a_lex = a.get("lexeme")

        if op in ("¬", "!"):
            return f"(¬{a_lex})" if a_val == "unknown" else (not a_val)

        if op in ("∃", "¬∃", "!∃"):
            if op in ("¬∃", "!∃"):
                return f"(¬∃{a_lex})" if a_val == "unknown" else (not a_val)
            return f"(∃{a_lex})" if a_val == "unknown" else a_val

        if op in ("∀", "¬∀", "!∀"):
            if op in ("¬∀", "!∀"):
                return f"(¬∀{a_lex})" if a_val == "unknown" else (not a_val)
            return f"(∀{a_lex})" if a_val == "unknown" else a_val

        raise Errors(f"Unknown unary operator: {op}")

    def and_(self, a, b):
        a_val = a["value"]
        b_val = b["value"]
        a_lex = a.get("lexeme")
        b_lex = b.get("lexeme")

        if ((a_val == "unknown") and (b_val in ("unknown", True))) or \
           ((b_val == "unknown") and (a_val in ("unknown", True))):
            return f"({a_lex} ∧ {b_lex})"
        if False in (a_val, b_val):
            return False
        return (a_val and b_val)

    def inc_or(self, a, b):
        a_val = a["value"]
        b_val = b["value"]
        a_lex = a.get("lexeme")
        b_lex = b.get("lexeme")

        if ((a_val == "unknown") and (b_val in ("unknown", False))) or \
           ((b_val == "unknown") and (a_val in ("unknown", False))):
            return f"({a_lex} ∨ {b_lex})"
        if True in (a_val, b_val):
            return True
        return (a_val or b_val)

    def nand(self, a, b):
        a_val = a["value"]
        b_val = b["value"]
        a_lex = a.get("lexeme")
        b_lex = b.get("lexeme")

        if ((a_val == "unknown") and (b_val in ("unknown", True))) or \
           ((b_val == "unknown") and (a_val in ("unknown", True))):
            return f"({a_lex} ↑ {b_lex})"
        if False in (a_val, b_val):
            return True
        return not (a_val and b_val)

    def nor(self, a, b):
        a_val = a["value"]
        b_val = b["value"]
        a_lex = a.get("lexeme")
        b_lex = b.get("lexeme")

        if ((a_val == "unknown") and (b_val in ("unknown", False))) or \
           ((b_val == "unknown") and (a_val in ("unknown", False))):
            return f"({a_lex} ↓ {b_lex})"
        if True in (a_val, b_val):
            return False
        return not (a_val or b_val)

    def exc_or(self, a, b):
        a_val = a["value"]
        b_val = b["value"]
        a_lex = a.get("lexeme")
        b_lex = b.get("lexeme")

        if (a_val == "unknown") or (b_val == "unknown"):
            return f"({a_lex} ⨁ {b_lex})"
        return (a_val and (not b_val)) or ((not a_val) and b_val)

    def imp(self, a, b):
        a_val = a["value"]
        b_val = b["value"]
        a_lex = a.get("lexeme")
        b_lex = b.get("lexeme")

        if a_val is False:
            return True
        if b_val is True:
            return True
        if (a_val != "unknown") and (b_val != "unknown"):
            return (not a_val) or b_val
        return f"({a_lex} → {b_lex})"

    def bi_imp(self, a, b):
        a_val = a["value"]
        b_val = b["value"]
        a_lex = a.get("lexeme")
        b_lex = b.get("lexeme")

        if (a_val == "unknown") or (b_val == "unknown"):
            return f"({a_lex} ↔ {b_lex})"
        return (a_val and b_val) or ((not a_val) and (not b_val))

    def eqv(self, a, b):
        a_val = a["value"]
        b_val = b["value"]
        a_lex = a.get("lexeme")
        b_lex = b.get("lexeme")

        if (a_val == "unknown") or (b_val == "unknown"):
            return f"({a_lex} ≡ {b_lex})"
        return (a_val and b_val) or ((not a_val) and (not b_val))

    def memb(self, op, a, b):
        a_lex = a.get("lexeme")
        b_lex = b.get("lexeme")
        return f"({a_lex} {op} {b_lex})"

    def subst(self, rpn, a, b):
        a_val = a.get("value")
        b_val = b.get("value")
        a_lex = a.get("lexeme")
        b_lex = b.get("lexeme")

        def next_pos_by_index_value(start_pos, target_index, key='index'):
            return next(
                (i for i in range(start_pos, len(rpn)) if rpn[i].get(key) == target_index),
                None
            )

        def rewrite_sequence_by_index(start_pos=0, first_index=b_val,
                                      index_key='index',
                                      substitute_field='lexeme',
                                      substitute_with=a_lex):
            """
            If first_index is an int, substitute by sequential index values.
            If not, substitute by matching identifier lexeme (b_lex).
            """
            rewritten_positions = []

            def as_bool(x):
                if isinstance(x, bool):
                    return x
                if x in ('⊤', 'T', 'True'):
                    return True
                if x in ('⊥', 'F', 'False'):
                    return False
                return None

            bool_target = as_bool(a_val) if a_val is not None else as_bool(a_lex)
            # If we're substituting a boolean, write into the 'value' field; else use caller's field
            eff_field = 'value' if bool_target is not None else substitute_field
            eff_value = bool_target if bool_target is not None else substitute_with

            if isinstance(first_index, int):
                pos = next_pos_by_index_value(start_pos, first_index, key=index_key)
                if pos is None:
                    return rewritten_positions

                current_index = first_index
                while pos is not None:
                    if eff_field in rpn[pos]:
                        rpn[pos][eff_field] = eff_value
                        rewritten_positions.append(pos)
                    current_index += 1
                    pos = next_pos_by_index_value(pos, current_index, key=index_key)

                return rewritten_positions

            target_lex = b_lex
            for i in range(start_pos, len(rpn)):
                if rpn[i].get('token_type') == 'identifier' and rpn[i].get('lexeme') == target_lex:
                    # if the target field doesn't exist yet, create it (keeps change scoped)
                    if eff_field not in rpn[i]:
                        rpn[i][eff_field] = "unknown"
                    rpn[i][eff_field] = eff_value
                    rewritten_positions.append(i)
            return rewritten_positions

        rewrite_sequence_by_index()
        return f"({a_lex} / {b_lex})"

    def _eval_binary(self, op, a, b, rpn):
        res = None

        if op == '/':
            res = self.subst(rpn, a, b)

        elif op in ('∈', '∉'):
            res = self.memb(op, a, b)

        else:
            func = {
                '∧': self.and_,
                '∨': self.inc_or,
                '↑': self.nand,
                '↓': self.nor,
                '⨁': self.exc_or,
                '→': self.imp,
                '↔': self.bi_imp,
                '≡': self.eqv,
            }.get(op)

            if func is None:
                raise Errors(f"Unknown binary operator: {op}")

            res = func(a, b)

        return res

    def eval_rpn(self, rpn):
        """The evaluator."""
        stack = []
        op_jail = []

        self.bool_values(rpn)

        # Obtain operator and operands and check for arity underflow -----------
        for tok in rpn:
            if tok["token_type"] != "operator":
                stack.append(tok)
                if op_jail and op_jail[-1]['lexeme'] in self._unary_ops:
                    tok = op_jail.pop(-1)
                elif len(stack) < 2:
                    continue

            # NOTE: intentionally `if` (not `elif`) so a popped unary op can
            # be evaluated immediately
            if tok["token_type"] == "operator":
                if op_jail:
                    op_jail.insert(0, tok)
                    tok = op_jail.pop(-1)

                op = tok["lexeme"]
                arity = 1 if op in self._unary_ops else 2

                if len(stack) < arity:
                    op_jail.insert(0, tok)
                    continue

                if arity == 1:
                    a = stack.pop(-1)
                    res = self._eval_unary(op, a)
                else:
                    b = stack.pop(-1)
                    a = stack.pop(-1)
                    res = self._eval_binary(op, a, b, rpn)

                stack.append(self._res_bldr(res))
                continue

        return stack
    def pretty_print(self, result_stack):
        """Format final output. Sets print as their values only."""
        def _set_to_string(d):
            parts = []
            for v in d.values():
                parts.append(_set_to_string(v) if isinstance(v, dict) else str(v))
            return '{' + ', '.join(parts) + '}'

        def _collapse_set_dict_repr(s, with_braces=True):
            # Replace any repr like {('str','a'): 'a', ('str','b'): 'b'} with "{a, b}"
            out, i, n = [], 0, len(s)
            while i < n:
                if i + 1 < n and s[i] == "{" and s[i+1] == "(":
                    # find matching '}'
                    depth, j = 0, i
                    while j < n:
                        if s[j] == "{":
                            depth += 1
                        elif s[j] == "}":
                            depth -= 1
                            if depth == 0:
                                break
                        j += 1
                    sub = s[i:j+1] if j < n else s[i:]
                    # extract values after "): '...'"
                    vals, p = [], 0
                    while True:
                        k = sub.find("):", p)
                        if k == -1:
                            break
                        q1 = sub.find("'", k + 2)
                        if q1 == -1:
                            break
                        q2 = sub.find("'", q1 + 1)
                        if q2 == -1:
                            break
                        vals.append(sub[q1+1:q2])
                        p = q2 + 1
                    out.append(("{" if with_braces else "") +
                        ", ".join(vals) + ("}" if with_braces else ""))
                    i = j + 1 if j < n else n
                else:
                    out.append(s[i])
                    i += 1
            return "".join(out)

        pretty_string = ''

        for item in result_stack:
            if not item:
                continue
            # use the FINAL token from each evaluated row
            popped_item = item[-1]

            lex = popped_item.get("lexeme")
            tok_type = popped_item.get("token_type")

            # --- sets as dict tokens: show only values
            if tok_type == 'set' and isinstance(lex, dict):
                line = _set_to_string(lex)
                pretty_string += line + "\n"
                continue

            # --- everything else: if it's a string, collapse any embedded set dict reprs
            if isinstance(lex, str):
                lex = _collapse_set_dict_repr(lex, with_braces=True)  # set False to drop braces
                pretty_string += lex + "\n"
            elif isinstance(lex, bool):
                pretty_string += ("True" if lex else "False") + "\n"
            elif isinstance(lex, dict):
                # non-set dict fallback
                pretty_string += repr(lex) + "\n"
            else:
                pretty_string += str(lex) + "\n"

        return pretty_string

    def sep_and_format(self, result):
        """ Separate errors from the result and format output """
        # 1) If it's already a string (often an error string), pass it through
        if isinstance(result, str):
            return result

        # 2) If it's an exception, show it
        if isinstance(result, BaseException):
            return f"Error: {result}"

        # 3) If it's a dict that signals an error, show the message/error
        if isinstance(result, dict):
            if result.get("success") is False or "error" in result:
                return result.get("message") or result.get("error") or str(result)
        return result

    def engine(self):
        """The hub for evaluation/intepretation."""
        result = []
        expr_stmt_stack = self.code

        while expr_stmt_stack:
            try:
                expr_stmt = expr_stmt_stack.pop(0)
                result.append(self.eval_rpn(expr_stmt))

            except Exception as e:
                raise Errors(f"Unexpected evaluation error: {e}") from e

        result = self.sep_and_format(result)

        return self.pretty_print(result)
