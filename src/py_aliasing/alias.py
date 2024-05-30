from functools import wraps
from typing import Optional
from warnings import warn

from .error import CircularAliasError, TrampleAliasError, TrampleAliasWarning


class alias:
    def __init__(
        self,
        alias_for: str,
        alias_name: str | None = None,
        *,
        trample_ok: bool = False,
        _aliased: "aliased" = None,
    ):
        self._for = alias_for
        # optionally provide the name here in case you want to init it without a containing class
        self._name = alias_name
        self.__doc__ = f"Alias for {self._for}"
        self._aliased = _aliased
        self._trample_ok = trample_ok

    def __set_name__(self, owner, name):
        self._name = name

    @staticmethod
    def _get_alias_obj(owner, owner_type, name) -> Optional["alias"]:
        if (
            owner_type
            and hasattr(owner_type, "__dict__")
            and isinstance(owner_type.__dict__.get(name, None), alias)
        ):
            return owner_type.__dict__[name]
        elif (
            owner
            and hasattr(owner, "__dict__")
            and isinstance(owner.__dict__.get(name, None), alias)
        ):
            return owner.__dict__[name]
        return None

    def _validate_nested(self, owner, owner_type) -> any:
        # basic 2 ptrs
        p1 = self._get_alias_obj(owner, owner_type, self._for)
        p2 = self

        move_p2 = True
        # p2 moves slower so p1 will always resolve to non-alias first, if either do
        while isinstance(p1, alias):
            if p1 is p2:
                raise CircularAliasError(
                    f"Nested alias {self._name} references a circular alias"
                )
            p1 = self._get_alias_obj(owner, owner_type, p1._for)
            p2 = p2 if not move_p2 else self._get_alias_obj(owner, owner_type, p2._for)
            move_p2 = not move_p2
        return p1

    def __get__(self, owner, owner_type=None):
        value = None
        if isinstance(self._get_alias_obj(owner, owner_type, self._for), alias):
            # this only works for objects defining __dict__, if they have __slots__ we need getattr
            value = self._validate_nested(owner_type, owner_type)

        if value:
            # so we don't have to repeat ourselves in the elif/else's
            pass
        elif owner is None:
            # this happens when called from class level
            try:
                value = getattr(owner_type, self._for)
            except AttributeError:
                value = self
        else:
            # just return the aliased attribute
            value = getattr(owner, self._for)

        return value

    def __set__(self, owner, value):
        raise NotImplementedError(
            f"cannot set the value of read-only alias {self._name}"
        )

    def attach(self, owner, name: str | None = None, *, trample_ok: bool = None):
        trample_ok = trample_ok if trample_ok is not None else self._trample_ok
        name = name or self._name
        if not name:
            raise RuntimeError("must provide name to attach alias")
        cls = owner
        if type(cls) is not type:
            # we have to attach the descriptor to the class, not the instance
            # this way we support both
            cls = type(cls)
        if hasattr(cls, name):
            message = f"Owner class {cls.__name__} already has member with name {name}."
            if trample_ok:
                message += (
                    f" Overriding with alias for {self._for}."
                    f" Pass `trample_ok=False` to disallow this behavior."
                )
                warn(message, TrampleAliasWarning)
            else:
                message += (
                    f" Cannot override it with alias for {self._for} by default,"
                    f" pass `trample_ok=True` to override the member anyway."
                )
                raise TrampleAliasError(message)
        setattr(cls, name, self)
        # needs to happen after setattr as that's when it happens in the
        # typical descriptor workflow. In this class's current implementation,
        # the statement has no effect, but in the future this might not be the case
        # and consumer child classes might add functionality to __set_name__
        self.__set_name__(owner, name)


class aliased:
    def __init__(self, func):
        self._func = func
        self._aliases: list[alias] = []
        self._original: aliased = self

        name = ""

        if isinstance(func, alias):
            aliased_: aliased | None = getattr(func, "_aliased", None)
            if isinstance(aliased_, aliased):
                self._original: aliased = aliased_._original
            else:
                name = getattr(func, "_for")
        elif isinstance(func, aliased):
            self._original: aliased = func

        if self._original is not self:
            self._func = getattr(self._original, "_func")
            self._init_doc = getattr(self._original, "_init_doc")
            self._aliases = getattr(self._original, "_aliases")
            # possible source or undesired/unexpected behavior if called directly
            name = self._original._name
        elif not name:
            name = func.__name__

        self._name = name
        self._init_doc = func.__doc__

        self._private_name = ""
        self._refresh_name()

        self._doc_sep = "\n"
        self._doc = self._init_doc
        self._refresh_doc()

    def _refresh_doc(self):
        alias_list = ",".join(
            filter(None, map(lambda a: getattr(a, "_name", None), self._aliases))
        )
        aliases_prefix = f"(aliases {alias_list})" if self._aliases else ""
        # renders a docstring like "(aliases method1,method2)\n<your original doc string here"
        self._doc = self._doc_sep.join(filter(None, [aliases_prefix, self._init_doc]))
        self.__doc__ = self._doc

    def _refresh_name(self, name: str | None = None):
        self._name = name or self._name
        self._private_name = f"_aliased_{self._name}"

    def __set_name__(self, owner, name: str):
        self._refresh_name(name)
        func = self._func
        self._init_doc = func.__doc__
        setattr(owner, self._private_name, func)

    def __get__(self, owner, owner_type=None):
        self._refresh_doc()
        if owner is None:
            try:
                return getattr(owner_type, self._private_name)
            except AttributeError:
                return self

        func = getattr(owner, self._private_name)

        if callable(func):

            @wraps(func)
            def wrapper(*args, **kwargs):
                return func(*args, **kwargs)

            wrapper.__doc__ = self._doc
            return wrapper

        return func

    def alias(self, member: any = None, *, trample_ok: bool = None) -> alias:
        name: str | None
        if member is not None and hasattr(member, "__name__"):
            name = member.__name__
        elif member is not None and isinstance(member, str):
            name = member
        elif member is None:
            # rely on __set_name__ or attach to assign the name
            name = None
        else:
            raise RuntimeError(
                f"could not resolve alias name from non-None, non-str member {member}"
                f" without `__name__` attribute"
            )

        new_alias = alias(
            alias_for=self._original._name,
            alias_name=name,
            _aliased=self._original,
            trample_ok=trample_ok,
        )
        self._aliases.append(new_alias)
        return new_alias
