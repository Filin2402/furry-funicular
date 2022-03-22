from typing import Any


class WithResultException(BaseException):
    def __init__(self, root_cause: BaseException):
        super().__init__(None, None)
        self.__result = None
        self.__root_cause = None
        self.root_cause = root_cause

    @property
    def result(self):
        return self.__result

    @result.setter
    def result(self, result: Any):
        self.__result = result

    @property
    def root_cause(self):
        return self.__root_cause

    @root_cause.setter
    def root_cause(self, cause: BaseException):
        self.__root_cause = cause
        self.args = cause.args
