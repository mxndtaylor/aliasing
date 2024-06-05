from typing import Any

from .core import alias, aliased


class Example:
    my_alias = alias("my")

    my_aliased = aliased(my_alias)

    my_second_alias = my_aliased.alias()

    def __init__(self) -> None:
        self.my = 123

    @aliased
    def method(self) -> str:
        return "my method call"

    method_alias1 = method.alias()

    @method.alias
    def method_alias2(self) -> Any: ...


if __name__ == "__main__":
    example = Example()
    print(example.method.__code__ is example.method_alias2.__code__)
    print(example.method.__code__ is example.method_alias1.__code__)

    # all of these are 123
    print(example.my)
    print(example.my_alias)
    print(example.my_aliased)
    print(example.my_second_alias)

    # all of these are 'my method call'
    print(example.method())
    print(example.method_alias1())
    print(example.method_alias2())

    # includes:
    #   method, method_alias1, method_alias2,
    #   my, my_alias, my_aliased, my_second_alias
    print(dir(example))
