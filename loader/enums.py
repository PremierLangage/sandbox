from enum import IntEnum, unique


@unique
class LoaderErrCode(IntEnum):
    ALREADY_PRESENT = -1,
    DATA_NOT_PRESENT = -2,
    