""" 
Repeatedly used dictionaries

"""
token_dict = {
'⊤': 'boolean',
'T': 'boolean',
'⊥': 'boolean',
'F': 'boolean',
'∃': 'operator',
'∀': 'operator',
'!⊤': 'boolean',
'!T': 'boolean',
'!⊥': 'boolean',
'!F': 'boolean',
'!∃': 'operator',
'!∀': 'operator',
'¬⊤': 'boolean',
'¬T': 'boolean',
'¬⊥': 'boolean',
'¬F': 'boolean',
'¬∃': 'operator',
'¬∀': 'operator',
'∅': 'boolean',
'1': 'boolean',
'0': 'boolean',
'True': 'boolean',
'False': 'boolean',
'true': 'boolean',
'false': 'boolean',
#'0': 'boolean', # depending on context
#'1': 'boolean', # depending on context
#'Σ': 'container',
#'a': 'container', # equivalent to there_is
#'an': 'container', # equivalent to there_is
#'this': 'container', # equivalent to there is
#'that': 'container', # equivalent to there is
#'𝔇': 'container',
#'ℛ': 'container',
#'ℱ': 'container',
#'0b': 'container',
#'0o': 'container',
#'0x': 'container',
#'0B': 'container',
#'0O': 'container',
#'0X': 'container',
#'array': 'container',
#'map': 'container',
#'list': 'container',
#'hypo': 'container',
#'sylo': 'container',
#'hypothesis': 'container',
#'lemma': 'container',
#'domain': 'container',
#'proof': 'container',
#'conclusion': 'container',
'set': 'container',
'(': 'container', # for container depending on context evaluated during parsing
')': 'container', # for container depending on context evaluated during parsing
';': 'delimeter', # for statements
',': 'delimeter', # for expressions
'.': 'delimeter', # for statements
'/*': 'delimeter', # for comments
'*/': 'delimeter', # for comments
'$$': 'delimeter', # Spock's EOF character
'{': 'container',
'}': 'container',
#'[': 'container',
#']': 'container',
#'∴': 'delimiter', # Only handled by the evaluator; not parsed
#'therefore': 'delimeter', # Only handled by the evaluator; not parsed.
#'empty': 'empty',
#"null": 'empty',
#"nil": 'empty',
#"none": 'empty',
#"undefined": 'empty',
'φ': 'identifier',
'ϕ': 'identifier',
'ψ': 'identifier',
#'\\a': 'literal',
#'\\n': 'literal',
':=': 'statement', # Assignment statement
'val': 'statement',
'¬': 'operator',
'∧': 'operator',
'∨': 'operator',
'→': 'operator',
'⨁': 'operator',
'↓': 'operator',
'↑': 'operator',
'!': 'operator',
'&': 'operator',
'↔': 'operator',
'≡': 'operator',
'/': 'operator', # Substitution, not division or negation
':': 'operator',
'¬¬': 'operator',
'!¬': 'operator',
'¬!': 'operator',
'!!': 'operator',
'¬∧': 'operator',
'¬∨': 'operator',
'¬⨁': 'operator',
'¬↓': 'operator',
'¬↑': 'operator',
'¬&': 'operator',
'¬≡': 'operator',
'!∧': 'operator',
'!∨': 'operator',
'!⨁': 'operator',
'!↓': 'operator',
'!↑': 'operator',
'!&': 'operator',
'!≡': 'operator',
'∈': 'operator',
'∉': 'operator',
'¬∈': 'operator',
'!∈': 'operator',
'¬∉': 'operator',
'!∉': 'operator',
'=': 'operator', # Comparison, not assignment
#'<<': 'operator',
#'>>': 'operator',
#'is': 'operator',
#'in': 'operator',
#'⊆': 'operator',
#'⊂': 'operator',
#'∩': 'operator',
#'∪': 'operator',
#'∆': 'operator',
#'𝒫': 'operator',
#'×': 'operator',
#'ℐ': 'operator',
#'⚬': 'operator',
#'~': 'operator',
#'%': 'operator',
#'*': 'operator',
#'-': 'operator',
#'+': 'operator',
#'|': 'operator',
#'<': 'operator', # Also used for ordered set container depending on context
#'>': 'operator', # Also used for ordered set container depending on context
#'?': 'operator',
#'div': 'operator',
#'**': 'operator',
#'!=': 'operator',
#'==': 'operator',
#'>=': 'operator',
#'<=': 'operator',
#'and': 'operator',
#'or': 'operator',
#'not': 'operator',
#'imply': 'operator',
#'implies': 'operator',
#'equals': 'operator',
#'is_equivalent_to': 'operator',
#'and_or': 'operator',
#'nor': 'operator',
#'nand': 'operator',
#'for_all': 'operator',
#'for_every': 'operator',
#'for_each': 'operator',
#'there_exists': 'operator',
#'for_some': 'operator',
#'if_and_only_if': 'operator',
#'substitutes_for': 'operator',
#'is_derived_from': 'operator',
#'derives_from': 'operator',
#'not in': 'operator',
#'is_not': 'operator',
#'+=': 'operator', # and statement
#'-=': 'operator', # and statement
#'*=': 'operator', # and statement
#'/=': 'operator', # This time / is division, also statement, not substitution
#'is_equal_to': 'operator',
#'member': 'statement',
#'then': 'statement',
#'class': 'statement',
#'self': 'statement',
#'function': 'statement',
#'else': 'statement',
#'for': 'statement',
#'if': 'statement',
#'return': 'statement',
#'super': 'statement',
#'switch': 'statement',
#'case': 'statement',
#'while': 'statement',
#'int': 'statement',
#'float': 'statement',
#'bool': 'statement',
#'ind': 'statement',
#'simplify': 'statement',
#'evaluate': 'statement',
#'prove': 'statement',
#'where': 'statement',
#'either': 'statement',
#'neither': 'statement',
#'deconstruct': 'statement',
#'state': 'statement',
#'abstract': 'statement',
#'else': 'statement',
#'elif': 'statement',
#'type': 'statement',
#'isInt': 'statement',
#'isFloat': 'statement',
#'isBool': 'statement',
#'isInd': 'statement',
#'break': 'statement',
#'continue': 'statement',
}

op_prec_dict = {
'/': 0, # Substitution not division #activated
':': 1, #activated
'∃': 1, #activated
'∀': 1, #activated
'¬∃': 1, #activated
'¬∀': 1, #activated
'!∃': 1, #activated
'!∀': 1, #activated
'!': 2, #activated # negation, not factorial
'¬': 2, #activated
'↑': 5, #activated
'&': 6, #activated
'∧': 6, #activated
'⨁': 7, #activated
'↓': 7, #activated
'∨': 9, #activated
'→': 10, #activated
'↔': 11, #activated
'≡': 11, #activated
}

op_assoc = {
'/': 'R', # Substitution not division #activated
':': 'R',
'∃': 'R',
'∀': 'R',
'!': 'R', # negation, not factorial
'¬': 'R',
'↑': 'L',
'&': 'L',
'∧': 'L',
'⨁': 'L',
'↓': 'L',
'∨': 'L',
'→': 'R',
'↔': 'L',
'≡': 'L',
}
