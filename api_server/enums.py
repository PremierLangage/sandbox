from enum import IntEnum, unique

@unique
class LoaderErrCode(IntEnum):
    FROZEN_RESOURCE_ALREADY_PRESENT = -1,
    DATA_NOT_PRESENT                = -2,
    DATA_NOT_VALID                  = -3,
    NON_EXISTANT_FROZEN_RESOURCE    = -4,
    FROZEN_RESOURCE_ID_NOT_PRESENT  = -5,
    FROZEN_RESOURCE_ID_NOT_IN_DB    = -6,
    
