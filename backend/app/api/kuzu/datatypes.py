from uuid import UUID

KUZU_TO_PYTHON_TYPES = {
    "INT8": int,
    "INT16": int,
    "INT32": int,
    "INT64": int,
    "INT128": int,
    "UINT8": int,
    "UINT16": int,
    "UINT32": int,
    "UINT64": int,
    "FLOAT": float,
    "DOUBLE": float,
    "DECIMAL": float,
    "BOOLEAN": bool,
    "UUID": UUID,
    "STRING": str,
    # TODO: handle all datatypes
}
