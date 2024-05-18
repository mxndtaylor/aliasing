from .alias import alias, aliased


class Example:
    my_alias = alias("my")

    my_aliased = aliased(my_alias)

    my_second_alias = my_aliased.alias()

    def __init__(self):
        self.my = 123

    @aliased
    def method(self):
        return 'my method call'

    method_alias1 = method.alias()

    @method.alias
    def method_alias2(self): ...


if __name__ == "__main__":
    example = Example()
    assert example.my == 123
    assert example.my_alias == 123
    assert example.my_aliased == 123
    assert example.my_second_alias == 123
    assert example.method() == 'my method call'
    assert example.method_alias1() == 'my method call'
    assert example.method_alias2() == 'my method call'
