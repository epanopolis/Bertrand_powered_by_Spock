"""
Error handling.

"""
import traceback

error = {  # … your existing table …
    # "Exit_49": "Runtime error",
}

PY_EXC_TO_EXIT = {
    AssertionError: "Exit_34",
    AttributeError: "Exit_35",
    EOFError: "Exit_36",
    ImportError: "Exit_39",
    ModuleNotFoundError: "Exit_40",
    IndexError: "Exit_41",
    KeyError: "Exit_42",
    KeyboardInterrupt: "Exit_43",
    MemoryError: "Exit_44",
    NameError: "Exit_45",
    NotImplementedError: "Exit_46",
    OverflowError: "Exit_47",
    RecursionError: "Exit_48",
    RuntimeError: "Exit_49",
    SyntaxError: "Exit_53",
    TypeError: "Exit_57",
    UnboundLocalError: "Exit_58",
    UnicodeError: "Exit_59",
    UnicodeDecodeError: "Exit_60",
    UnicodeEncodeError: "Exit_61",
    UnicodeTranslateError: "Exit_62",
    OSError: "Exit_64",
}

class Errors(Exception):
    """
    Exception handling.
    
    """
    def __init__(self, message, *, code="Exit_49", details=None,
        stack_trace=None):
        super().__init__(message)
        self.code = code
        self.details = details or self._callsite()
        self.stack_trace = stack_trace

    @staticmethod
    def _callsite():
        tb = traceback.extract_stack()[:-2]  # caller of Errors(...)
        last = tb[-1] if tb else None
        return {
            "file_name": last.filename if last else None,
            "line_number": last.lineno if last else None,
            "function_name": last.name if last else None,
        }

    @classmethod
    def from_exception(cls, e, *, message=None):
        """
        Exception handling.
        
        """
        code = PY_EXC_TO_EXIT.get(type(e), "Exit_49")
        tbe = traceback.TracebackException.from_exception(e)
        stack = "".join(tbe.format())
        last = tbe.stack[-1] if tbe.stack else None
        details = {
            "file_name": last.filename if last else None,
            "line_number": last.lineno if last else None,
            "function_name": last.name if last else None,
        }
        return cls(message or str(e), code=code, details=details,
            stack_trace=stack)

    def error_report(self):
        """Error reporting."""
        return {
            "system_exit": self.code,
            "system_exit_text": error.get(self.code, "Unknown error"),
            "message": str(self),
            "file": self.details.get("file_name"),
            "line_number": self.details.get("line_number"),
            "function_name": self.details.get("function_name"),
            "stack_trace": self.stack_trace,
        }
