from .core import alias, aliased
from .virtual_alias import valiased, valiases
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
    "AliasError",
    "CircularAliasError",
    "TrampleAliasError",
    "TrampleAliasWarning",
]
