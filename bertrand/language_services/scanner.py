"""  
Step 1 in the process: scanning.

"""
# pylint: disable=too-many-instance-attributes
from .dictionaries.errors import Errors

class Shannon:
    """
    This is the center of scanning operations, providing helper methods for the
    lexer.
    """

    def __init__(self, token_dict):
        self.token_dict = token_dict
        self.current_position = -1  # This compensates for first two
        self.current_line = 0       # characters taken by line number and period
        self.current_column = 1     # column gets reset to 1 on each line anyway
        self.token_list = []
        self.source = ""
        self.token = {
            "lexeme": "",
            "token_type": "",
            "line": self.current_line,
            "column": self.current_column,
            "position": self.current_position,  # fix the name here too
            }

    # Receives the source file from scanner.
    # and prepares it for parsing.
    def scan_source(self, source):
        """
        This is the primary function for managing the scanning process.

        """
        # normalize line endings
        self.source = source.replace('\r\n', '\n').replace('\r', '\n')

        self.source = self.strip_block_comments(self.source)

        # enforce your "$$" terminator rule
        if not self.source.endswith("$$"):
            raise Errors("Source must end with '$$'")

        # prepare first line (your existing logic)
        self.handle_newline()  # only affects the first newline/line-number case

        # ensure we accumulate a fresh list for this run
        self.token_list = []

        # run the scan and RETURN the entire list to the caller
        scanned_token_list = self.begin_scan()
        return scanned_token_list

    def begin_scan(self):
        """It all starts here."""
        vn = VonNeumann(self.token_dict)
        vn.source = self.source

        # >>> sync the scan cursor from Shannon to VonNeumann <<<
        vn.current_position = self.current_position
        vn.current_line = self.current_line
        vn.current_column = self.current_column

        tokens = []
        while True:
            self.token = vn.lexer()  # lexer returns a token object

            if self.token.lexeme == "$$":   # stop at EOF sentinel
                tokens.append(self.token)
                break

            if self.token.lexeme != '':     # collect non-empty tokens
                tokens.append(self.token)

        return tokens  # full list for the caller

    def advance_position(self, length=1):
        """
        Handles movement through the token string,
        including sending strings to the newline handler.
        
        """
        for _ in range(length):
            if self.current_position < len(self.source) - 1:
                if self.source[self.current_position] == "\n":
                    self.handle_newline()
                else:
                    self.current_column += 1
                    if self.source[self.current_position] in (",",";"):
                        self.current_line +=1
                        self.current_position +=1
                        return
                self.current_position += 1

    def handle_newline(self):
        """
        Reset column to 1 and increment line number when a newline is
        encountered, and skip initial line number and a single following decimal
        point at the beginning of each line.

        """

        self.current_line += 1
        self.current_column = 1
        if self.current_line == 1:
            self.current_column = 0

        decimal_found = False
        consumed_nbr = False

        # Ensure the bounds check guards both digit and dot tests
        while (self.source[self.current_position + 1].isdigit()
            or self.source[self.current_position + 1] == '.'
            and self.current_position < len(self.source) - 1
            and not decimal_found):

            nxt = self.source[self.current_position + 1]
            if nxt.isdigit():
                self.current_position += 1
                consumed_nbr = True
                continue

            if nxt == '.':
                decimal_found = True
                if consumed_nbr is False:
                    decimal_found = False
                self.current_position += 1

            # If we consumed digits/dot, move one more so we end up AFTER the
            # last skipped char. This covers the initial call (not via
            # advance_position) to avoid leaving '.' as the current char.

            if consumed_nbr and self.current_position < len(self.source) - 1:
                self.current_position += 1

        if (consumed_nbr is False) or (decimal_found is False):
            raise Errors("No line number and/or period at the start of a " +
                "new physical line")

        # If no line number was found by handler
        # advance col on newline for first line
        # because the current position has not
        # advanced and -1 will cause the lexer
        # to throw an error.
        if self.current_position == -1:
            self.current_position = 1

        if ((self.source[self.current_position] != ' ') or
            (self.source[self.current_position + 1] != ' ')):
            raise Errors("There must be at least two spaces after each " +
                "line number")

    def numeric(self):
        """Number token factory"""
        numeric_token = ''

        # Check if the first character is valid
        if not self.source[self.current_position].isdigit():
            raise Errors(f"""Token not yet defined or implemented
             '{self.source[self.current_position]}' at line {self.current_line},
             column {self.current_column}""")

        # Build the numeric token
        present_position = self.current_position
        # We go one less than maximum to prevent crashing if no EOF characters

        while present_position < len(self.source) - 1:
            current_char = self.source[present_position]
            # Allow only digits
            if current_char.isdigit():
                numeric_token += current_char
                present_position += 1
            else:
                return numeric_token

        return None

    def identifier(self):
        """Identifier factory"""
        identifier_token = ''

        # Check if the first character is valid
        if not (self.source[self.current_position].isalpha() or
            self.source[self.current_position] == "_"):
            raise Errors("Token not yet defined or implemented "
                "'{self.source[self.current_position]} '" 
                "at line {self.current_line}, column {self.current_column}")

        # Build the identifier token
        present_position = self.current_position
        # We go one less than maximum to prevent crashing if no EOF characters

        while present_position < len(self.source) - 1:
            current_char = self.source[present_position]
            # Allow only alphanumeric characters, underscores, or apostrophes
            if current_char.isalnum() or current_char in ("_" , "'"):
                identifier_token += current_char
                present_position += 1

            else:
                return identifier_token

        return identifier_token

    def strip_block_comments(self, source: str) -> str:
        """
        Comment stripper
        """
        out = []
        i = 0
        n = len(source)
        in_comment = False

        while i < n:
            # Start of comment: "/*"
            if not in_comment and source[i:i+2] == '/*':
                in_comment = True
                i += 2
                continue

            # End of comment: "*/"
            if in_comment and source[i:i+2] == '*/':
                in_comment = False
                i += 2
                continue

            # Inside a comment: skip characters
            if in_comment:
                i += 1
                continue

            # Normal character
            out.append(source[i])
            i += 1

        return ''.join(out)

    def boolean_conv(self, bool_lex):
        """Negation eliminator."""
        if (len(bool_lex) == 2 and bool_lex[0] in {'¬', '!'} and bool_lex[1] in
            {'¬', '!'}):
            return ''  # double-negation cases

        base = {'∧': '↑', '&': '↑', '∨': '↓', '⨁': '≡', '≡': '⨁',
                '↓': '∨', '↑': '∧', 'T': 'F', 'F': 'T', '⊤': '⊥', '⊥': '⊤',
                '∃': '¬∀', '∀': '¬∃','∈': '∉','∉': '∈',
                '∅': 'T', '0': 'T', '1': 'F'
        }

        if len(bool_lex) == 2 and bool_lex[0] in {'¬', '!'}:
            return base.get(bool_lex[1], bool_lex)

        return bool_lex  # unchanged if it doesn't match the pattern

class VonNeumann(Shannon):
    """ These are the routines that perform the primary scanning functions."""
    def __init__(self, token_dict):
        super().__init__(token_dict)
        self.c = ""
        self.lexeme = ""
        self.token_type = ""

    def lexer(self):
        """The Lexer"""
        # If we're at the sentinel start (-1), advance once *before* reading.
        if self.current_position < 0:
            self.advance_position()

        while self.current_position < len(self.source):
            self.c = self.source[self.current_position]

            # Skip whitespace and postfix delimiters except "." here so callers
            # never see None and tokens properly grouped by logical line number
            if self.c.isspace() or (self.c in (",",";")):
                self.advance_position()
                continue

            # Detect tokens in this order; if nothing matched, don't return None
            tok = (self.letters()
                    or self.digits()
                    or self.dual_tokens()
                    or self.lexicon_tokens())

            return tok

        return None

    def tokenizer(self):
        '''The token builder.'''
        tok_map = {
            "lexeme": self.lexeme,
            "token_type": self.token_type,
            "line": self.current_line,
            "column": self.current_column,
            "position": self.current_position,
            "value": "unknown",
        }
        t = Grieg(tok_map)
        self.token = t
        return t

    def lexicon_tokens(self):
        """Single-character tokens"""
        if self.c in self.token_dict:
            # 1) DO NOT mutate self.source (no newline injection)
            # 2) DO NOT pre-advance; capture current char as the token
            self.token_type = self.token_dict[self.c]
            self.lexeme = self.c
            if self.c in ('∅','⊥'):
                self.lexeme = "False"
            if self.c == '⊤':
                self.lexeme = "True"
            self.advance_position(1)
            return self.tokenizer()

        return None

    def dual_tokens(self):
        """Lexer for dual tokens."""
        # Two-char tokens and comment start
        if self.current_position + 1 >= len(self.source):
            return None

        if self.c == ".":  # prevent ".$" from being tokenized.
            length = 1
            self.token_type = self.token_dict[self.c]
            self.lexeme = "."
            self.advance_position()
            return self.tokenizer()

        # IMPORTANT: do not advance position when peeking ahead
        next_char = self.source[self.current_position + 1]
        two_char_key = self.c + next_char
        if next_char.isspace() or two_char_key not in self.token_dict:
            return None

        if two_char_key in (
            '¬¬','!¬','¬!','!!','¬T','¬F','!T','!F','¬⊤','¬⊥','!⊤','!⊥','¬∧',
            '¬∨','¬⨁','¬↓','¬↑','¬&','¬≡','!∧','!∨','!⨁','!↓','!↑','!&','!≡',
            '¬∃','¬∀','!∃','!∀','¬∈','!∈','¬∉', '!∉'
            '¬∅', '!∅', '¬0', '!0', '¬1', '!1'
        ):
            mapped = self.boolean_conv(two_char_key)
            self.lexeme = mapped
            # type should match the mapped lexeme (e.g., 'T'/'F'/'⊤'/'⊥' => boolean)
            self.token_type = self.token_dict.get(mapped, "operator")
            self.advance_position(2)
            return self.tokenizer()

        if two_char_key in self.token_dict:
            length = 2
            self.token_type = self.token_dict[two_char_key]
            self.lexeme = self.source[self.current_position:
                self.current_position + length]
            self.advance_position(length)  # was: advance_position() only once
            return self.tokenizer()

        return None

    # Follow the "maximal munch" rule for identifiers and numbers.
    def letters(self):
        """Lexer for letters."""
        while self.current_position + 1 < len(self.source):

            if self.c.isalpha() or self.c in ("_", "'"):
                identifier_token = self.identifier()

                if identifier_token in self.token_dict:
                    self.token_type = self.token_dict[identifier_token]

                    if self.token_type == "boolean":
                        length = len(identifier_token)

                        if identifier_token == "T":
                            identifier_token = "True"

                        elif identifier_token == "F":
                            identifier_token = "False"

                        self.lexeme = identifier_token
                        self.advance_position(length)

                    else:
                        length = len(identifier_token)
                        self.lexeme = identifier_token
                        self.advance_position(length)

                else:
                    self.token_type = "identifier"
                    length = len(identifier_token)
                    self.lexeme = self.source[self.current_position:
                        self.current_position + length]
                    self.advance_position(length)

                self.token = self.tokenizer()
                return self.token

            return None

        return None

    def digits(self):
        """ Lexer for digits """
        while self.current_position + 1 < len(self.source):

            # IMPORTANT: if current char is not a digit, do not emit a token.
            if not self.c.isdigit():
                return None

            numeric_token = self.numeric()
            length = len(numeric_token)

            # Default: number
            self.token_type = "number"
            self.lexeme = self.source[self.current_position:
                self.current_position + length]

            # Special-case 0/1 => boolean
            if numeric_token == '0':
                length = 1
                self.token_type = "boolean"
                self.lexeme = "False"

            elif numeric_token == '1':
                length = 1
                self.token_type = "boolean"
                self.lexeme = "True"

            self.advance_position(length)
            self.token = self.tokenizer()
            return self.token

        return None

    def detectors(self):
        """ The hub of the lexer """

        self.token = self.lexicon_tokens() or self.letters() or self.digits()

        return self.token # Returns fully completed token for appending to list.

class Grieg(Shannon):
    """ The token and dictionary factory."""
    def __init__(self, tok):
        super().__init__(self)  # preserved
        # Fill the same attributes from the provided dict
        self.lexeme = tok.get("lexeme", "")
        self.token_type = tok.get("token_type", "")
        self.line = tok.get("line", 0)
        self.column = tok.get("column", 0)
        self.position = tok.get("position", -1)

    def to_map(self):
        """Returns a dictionary representation of the token."""
        return {
            "lexeme": self.lexeme,
            "token_type": self.token_type,
            "line": self.line,
            "column": self.column,
            "value": "unknown",
        }
