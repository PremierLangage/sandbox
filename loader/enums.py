from enum import IntEnum, unique


@unique
class LoaderErrCode(IntEnum):
    ALREADY_PRESENT = -1,
    DATA_NOT_PRESENT = -2,
    NON_EXISTANT_PARENT = -3,
    FROZEN_RESOURCE_NON_EXISTANT = -4,