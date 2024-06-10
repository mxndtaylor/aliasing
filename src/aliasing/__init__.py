from .core import alias, aliased
from .virtual_alias import valiased, valiases, auto_alias
from .error import (
    AliasError,
    CircularAliasError,
    TrampleAliasError,
    TrampleAliasWarning,
)

__all__ = [
    "alias",
    "aliased",
    "valiased",
    "valiases",
    "auto_alias",
    "AliasError",
    "CircularAliasError",
    "TrampleAliasError",
    "TrampleAliasWarning",
]
