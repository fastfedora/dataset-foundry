import logging
from pydantic import BaseModel
from typing import Any, List

logger = logging.getLogger(__name__)


class CommandResult(BaseModel):
    command: List[Any]
    returncode: int | None
    stdout: str
    stderr: str = ""

    @property
    def success(self) -> bool:
        return self.returncode == 0

    def __str__(self):
        """
        Return a string representation of the command result. If debugging is enabled, include
        the stdout and stderr in the string.
        """
        debugging = logger.isEnabledFor(logging.DEBUG)
        include_error = debugging or not self.success
        status = "SUCCESS" if self.success else "FAILED"
        stderr = f", stderr: {self.stderr}" if self.stderr else ""
        stdout = f", stdout: {self.stdout}" if debugging and self.stdout else ""
        error = f" (code: {self.returncode}{stderr}{stdout})" if include_error else ""

        return f"{status}{error}"
