import warnings
from typing import List, Optional, Any, Union, Sequence, Iterable

from .core import aliased
from .error import TrampleAliasWarning, TrampleAliasError


class valiased(aliased):
    """
    returned from valiases.__call__

    descriptor that adds the named aliases to the object
    during the __set_name__ phase
    """

    def __init__(
        self, func: Any, *aliases: str, trample_ok: Optional[List[str]] = None
    ):
        super().__init__(func)
        trample_ok = trample_ok or []
        self._aliases = list(
            map(
                lambda name: self.alias(name, trample_ok=(name in trample_ok)),
                aliases,
            )
        )

    def __set_name__(self, owner: Any, name: str) -> None:
        super().__set_name__(owner, name)
        is_warn = is_err = False
        msg = ""
        try:
            warnings.filterwarnings("error", category=TrampleAliasWarning)
            for alias in self._aliases:
                try:
                    alias.attach(owner)
                except TrampleAliasWarning as w:
                    msg = str(w.args[0]).replace(
                        "Pass `trample_ok=False`",
                        f"Remove '{alias._name}' from the "
                        "`trample_ok` list parameter",
                    )
                    is_warn = True
                except TrampleAliasError as e:
                    msg = str(e.args[0]).replace(
                        "trample_ok=True",
                        f"trample_ok=['{alias._name}']",
                    )
                    is_err = True
        finally:
            warnings.resetwarnings()
        if is_warn:
            warnings.warn(msg, category=TrampleAliasWarning)
        if is_err:
            raise TrampleAliasError(msg)


class valiases:
    """
    Usage:
        @valiases("a", "b")
        def method(): ...
        ...
        assert method() == a()
    """

    def __init__(self, *aliases: str, trample_ok: Optional[List[str]] = None):
        self._aliases = aliases
        self._trample_ok = trample_ok

    def __call__(self, func: Any) -> valiased:
        return valiased(func, *self._aliases, trample_ok=self._trample_ok)


class auto_alias:
    def __init__(
            self,
            *,
            short: Optional[Union[int, Sequence[int], bool]] = None,
            trample_ok: Optional[List[str]] = None,
    ):
        self.trample_ok = trample_ok or []

        self._short = None
        self._short_indices = None
        if isinstance(short, Iterable):
            self._short_indices = list(short)
        elif isinstance(short, int):
            self._short_indices = [short]
        else:
            self._short = bool(short)

    def _generate_short(self, name: str) -> list[str]:
        results: list[str] = []

        for i in range(1, len(name)):
            if self._short or i in self._short_indices:
                results.append(name[:i])

        return results

    def __call__(self, func: Any) -> valiased:
        name = func.__name__
        aliases = self._generate_short(name=name)
        return valiased(func, *aliases, trample_ok=self.trample_ok)
