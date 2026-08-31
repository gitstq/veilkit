"""VeilKit 自定义异常体系。

所有可预期的用户侧错误都继承 :class:`VeilKitError`，CLI 据此输出友好提示，
而不是抛出原始堆栈（使用 ``--debug`` 时仍可查看完整堆栈）。
"""


class VeilKitError(Exception):
    """VeilKit 所有业务异常的基类。"""


class CarrierError(VeilKitError):
    """载体文件不支持或已损坏（如非 8-bit RGB 的 PNG、压缩过的 WAV）。"""


class CapacityError(VeilKitError):
    """载体容量不足以承载待写入的帧。"""


class NoHiddenDataError(VeilKitError):
    """载体中没有找到 VeilKit 隐写帧（魔数校验失败）。"""


class AuthError(VeilKitError):
    """口令错误或隐写数据被篡改（HMAC 校验失败）。"""


class PasswordRequiredError(VeilKitError):
    """该隐写帧经过加密，必须提供口令才能提取。"""
