from functools import wraps
from typing import Optional, List, Any, cast, Type
from warnings import warn

from .error import CircularAliasError, TrampleAliasError, TrampleAliasWarning


class alias:
    def __init__(
        self,
        alias_for: str,
        alias_name: Optional[str] = None,
        *,
        trample_ok: bool = False,
        _aliased: Optional["aliased"] = None,
    ):
        self._for = alias_for
        # optionally provide name
        # in case of initializing without containing class
        self._name = alias_name
        self.__doc__ = f"Alias for {self._for}"
        self._aliased = _aliased
        self._trample_ok = trample_ok

    def __set_name__(self, owner: Any, name: str) -> None:
        self._name = name

    @staticmethod
    def _get_alias_obj(
        owner: Any, owner_type: Any, name: str
    ) -> Optional["alias"]:
        if (
            owner
            and hasattr(owner, "__dict__")
            and isinstance(owner.__dict__.get(name, None), alias)
        ):
            return cast(alias, owner.__dict__[name])
        elif (
            owner_type
            and hasattr(owner_type, "__dict__")
            and isinstance(owner_type.__dict__.get(name, None), alias)
        ):
            return cast(alias, owner_type.__dict__[name])
        return None

    def _validate_nested(self, owner: Any, owner_type: Any) -> Any:
        # basic 2 ptrs
        p1: Any = self._get_alias_obj(owner, owner_type, self._for)
        p2 = self

        move_p2 = True
        while isinstance(p1, alias):
            if p1 is p2:
                raise CircularAliasError(
                    f"Nested alias {self._name} references a circular alias"
                )
            p1 = self._get_alias_obj(owner, owner_type, p1._for)
            # p2 moves slower so p1 always resolves to first, if either do
            # meaning p2 always has type alias here
            p2 = cast(
                alias,
                (
                    p2
                    if not move_p2
                    else self._get_alias_obj(owner, owner_type, p2._for)
                ),
            )
            move_p2 = not move_p2
        return p1

    def __get__(self, owner: Any, owner_type: Optional[Any] = None) -> Any:
        value = None
        if isinstance(
            self._get_alias_obj(owner, owner_type, self._for), alias
        ):
            # this only works for objects defining __dict__,
            # if they have __slots__ we need getattr,
            # hence checking value for truthiness after this
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

    def __set__(self, owner: Any, value: Any) -> None:
        raise NotImplementedError(
            f"cannot set the value of read-only alias {self._name}"
        )

    def __attach_class(
        self, cls: Type[Any], name: str, *, trample_ok: Optional[bool] = None
    ):
        if hasattr(cls, name):
            message = (
                f"Owner class {cls.__name__}"
                f" already has member with name {name}."
            )
            if trample_ok:
                message += (
                    f" Overriding with alias for {self._for}. Pass"
                    " `trample_ok=False` to disallow this behavior."
                )
                warn(message, TrampleAliasWarning)
            else:
                message += (
                    f" Cannot override it with alias for {self._for} by"
                    " default, pass `trample_ok=True` to override the member"
                    " anyway."
                )
                raise TrampleAliasError(message)
        setattr(cls, name, self)
        # needs to happen after setattr as that's when it happens in the
        # typical descriptor workflow. In this class's current implementation,
        # the statement has no effect, but in the future it might have one
        # or consumer child classes might add functionality to __set_name__
        self.__set_name__(cls, name)

    def __attach_instance(
        self, instance: Any, name: str, *, trample_ok: Optional[bool] = None
    ):
        cls = type(instance)

        # hash and compare so we minimize the number of classes created here
        instance_hash = hash(instance)
        class_hash = hash(cls)
        instance_hash_key = "_aliasing_instance_hash"
        class_hash_key = "_aliasing_class_hash"
        if hasattr(cls, class_hash_key):
            class_hash = hash(cls.__base__)

        if (
            not hasattr(cls, instance_hash_key)
            or not hasattr(cls, class_hash_key)
            or getattr(cls, instance_hash_key, None) != instance_hash
            or getattr(cls, class_hash_key, None) != class_hash
        ):
            # dynamically create a new class that only this instance will use
            tmp_class = type(
                cls.__name__,
                (cls,),
                {
                    instance_hash_key: instance_hash,
                    class_hash_key: class_hash,
                },
            )
            tmp_class.__doc__ = (
                f""" class for aliasing '{self._for}' under '{self._name}'"""
            )
            # I don't like modifying the class of the instance like this
            # but as long as the end user is using 'isinstance'
            # instead of direct class comparisons it should be okay.
            instance.__class__ = tmp_class
            cls = tmp_class

        # we attach here instead of during the dynamic class creation because
        # we follow same attachment process no matter what:
        # - attach to class
        # - attach to instance with new tmp class
        # - attach to instance with existing tmp class
        # all use same attachment process
        self.__attach_class(cls, name, trample_ok=trample_ok)

    def attach(
        self,
        owner: Any,
        name: Optional[str] = None,
        *,
        trample_ok: Optional[bool] = None,
    ) -> None:
        if owner is None:
            raise RuntimeError("cannot attach alias to None")

        name = name or self._name
        if not name:
            raise RuntimeError("must provide name to attach alias")

        trample_ok = trample_ok if trample_ok is not None else self._trample_ok
        if type(owner) is not type:
            # we have to attach the descriptor to the class, not the instance
            # this way we support both
            self.__attach_instance(owner, name, trample_ok=trample_ok)
        else:
            self.__attach_class(owner, name, trample_ok=trample_ok)


class aliased:
    def __init__(self, func: Any):
        self._func = func
        self._aliases: List[alias] = []
        self._original: aliased = self

        name: str = ""

        if isinstance(func, alias):
            aliased_: Optional[aliased] = getattr(func, "_aliased", None)
            if isinstance(aliased_, aliased):
                self._original = aliased_._original
            else:
                name = getattr(func, "_for")
        elif isinstance(func, aliased):
            self._original = func

        if self._original is not self:
            self._func = getattr(self._original, "_func")
            self._init_doc = getattr(self._original, "_init_doc")
            self._aliases = getattr(self._original, "_aliases")
            # possible source or unexpected behavior if called directly
            # instead of as member in class
            name = self._original._name
        elif not name:
            name = func.__name__

        self._name: str = name
        self._init_doc = func.__doc__

        self._private_name = ""
        self._refresh_name()

        self._doc_sep = "\n"
        self._doc = self._init_doc
        self._refresh_doc()

    def _refresh_doc(self) -> None:
        alias_list = ",".join(
            filter(
                None, map(lambda a: getattr(a, "_name", None), self._aliases)
            )
        )
        aliases_prefix = f"(aliases {alias_list})" if self._aliases else ""
        # renders a docstring like:
        #   """(aliases method1,method2)\n<your original doc string here"""
        self._doc = self._doc_sep.join(
            filter(None, [aliases_prefix, self._init_doc])
        )
        self.__doc__ = self._doc

    def _refresh_name(self, name: Optional[str] = None) -> None:
        self._name = name or self._name
        self._private_name = f"_aliased_{self._name}"

    def __set_name__(self, owner: Any, name: str) -> None:
        self._refresh_name(name)
        func = self._func
        self._init_doc = func.__doc__
        setattr(owner, self._private_name, func)

    def __get__(self, owner: Any, owner_type: Optional[Any] = None) -> Any:
        self._refresh_doc()
        if owner is None:
            try:
                return getattr(owner_type, self._private_name)
            except AttributeError:
                return self

        func = getattr(owner, self._private_name)

        if callable(func):

            @wraps(func)
            def wrapper(*args: Any, **kwargs: Any) -> Any:
                return func(*args, **kwargs)

            wrapper.__doc__ = self._doc
            return wrapper

        return func

    def alias(
        self,
        member: Optional[Any] = None,
        *,
        trample_ok: Optional[bool] = None,
    ) -> alias:
        name: Optional[str]
        if member is None:
            # rely on __set_name__ or attach to assign the name
            name = None
        elif hasattr(member, "__name__"):
            name = member.__name__
        elif isinstance(member, str):
            name = member
        elif hasattr(member, "__func__"):
            # support for staticmethod in <=3.9
            name = member.__func__.__name__
        else:
            raise RuntimeError(
                "could not resolve alias name from non-None, non-str member"
                f" {member} without "
                "`__name__` attribute"
            )

        new_alias = alias(
            alias_for=self._original._name,
            alias_name=name,
            _aliased=self._original,
            trample_ok=bool(trample_ok),
        )
        self._aliases.append(new_alias)
        return new_alias
