import logging

from .command_result import CommandResult

logger = logging.getLogger(__name__)


class UnitTestResult(CommandResult):
    num_passed: int
    num_failed: int

    @property
    def total_tests(self) -> int:
        return self.num_passed + self.num_failed

    @property
    def success(self) -> bool:
        return self.returncode == 0 and self.num_passed > 0 and self.num_failed == 0

    def __str__(self):
        """
        Return a string representation of the unit test result. If debugging is enabled, include
        the stdout and stderr in the string.
        """
        debugging = logger.isEnabledFor(logging.DEBUG)
        include_error = debugging or not self.success
        status = "SUCCESS" if self.success else "FAILED"
        passed = f"{self.num_passed} passed" if self.num_passed > 0 else ""
        failed = f"{self.num_failed} failed" if self.num_failed > 0 else ""
        stderr = f", stderr: {self.stderr}" if self.stderr else ""
        stdout = f", stdout: {self.stdout}" if debugging and self.stdout else ""
        error = f" (code: {self.returncode}{stderr}{stdout})" if include_error else ""

        if self.total_tests > 0:
            message = f"{self.total_tests} tests - {passed} {failed}"
        else:
            message = "no tests found"

        if passed and failed:
            passed += ","

        return f"{status}: {message}{error}"
