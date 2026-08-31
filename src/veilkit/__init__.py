"""VeilKit —— 零依赖、本地优先的多载体隐写工具箱。

Public API::

    hide_bytes / reveal_bytes      PNG/BMP/WAV 二进制载体隐写
    hide_text  / reveal_text       零宽字符文本隐写
    capacity_bits / capacity_human 载体容量评估
"""

from .core import (
    SUPPORTED_BINARY_TYPES,
    capacity_bits,
    capacity_human,
    detect_type,
    hide_bytes,
    hide_text,
    reveal_bytes,
    reveal_text,
)
from .errors import (
    AuthError,
    CapacityError,
    CarrierError,
    NoHiddenDataError,
    PasswordRequiredError,
    VeilKitError,
)

__version__ = "1.0.0"

__all__ = [
    "__version__",
    "SUPPORTED_BINARY_TYPES",
    "hide_bytes",
    "reveal_bytes",
    "hide_text",
    "reveal_text",
    "capacity_bits",
    "capacity_human",
    "detect_type",
    "VeilKitError",
    "CarrierError",
    "CapacityError",
    "NoHiddenDataError",
    "AuthError",
    "PasswordRequiredError",
]
