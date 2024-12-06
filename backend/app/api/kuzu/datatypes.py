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
    # TIMESTAMP
    # TODO: handle all datatypes
}

NUMERIC_PROPERTY_TYPES: list[str] = [
    "INT8",
    "INT16",
    "INT32",
    "INT64",
    "INT128",
    "UINT8",
    "UINT16",
    "UINT32",
    "UINT64",
    "FLOAT",
    "DOUBLE",
    "DECIMAL",
]

SYMBOLIC_PROPERTY_TYPES = [
    "BOOLEAN",
    "UUID",
    "STRING",
]
