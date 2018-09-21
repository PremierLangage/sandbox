# coding: utf-8

from enum import IntEnum, unique


@unique
class SandboxErrCode(IntEnum):
    UNKNOWN = -1
    TIMEOUT = -2
    CONTEXT_NOT_FOUND = -3
    GRADER_NOT_INT = -4
