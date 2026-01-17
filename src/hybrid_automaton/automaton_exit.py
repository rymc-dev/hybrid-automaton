from dataclasses import dataclass
from .exit_codes import ExitCode

@dataclass
class AutomatonExit:
    exit_code: ExitCode
    msg: str    