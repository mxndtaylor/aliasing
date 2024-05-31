from aliasing.alias import alias, aliased

PROP_NAME = "prop"


class AliasedTester:
    prop_alias = aliased(alias(PROP_NAME))

    def __init__(self):
        self.prop = "anything at all"
        self.aliased_val = "wah wah"

    @prop_alias.alias
    def second_prop_alias(self): ...

    @prop_alias.alias
    class PropPascalCase: ...

    @aliased
    def aliased_method(self):
        return self.aliased_val

    @aliased_method.alias
    class PascalCaseMethod: ...

    @aliased_method.alias
    def normal_alias(self): ...

    @aliased
    @aliased_method.alias
    def nested_alias(self): ...

    @nested_alias.alias
    def alias_of_nested_alias(self): ...

    @aliased
    class AliasedInnerClass:
        def __init__(self, prop):
            self.prop = prop

        def __eq__(self, other):
            return isinstance(other, type(self)) and self.prop == other.prop

    @AliasedInnerClass.alias
    class NormalClassAlias: ...

    snake_case_class_alias = AliasedInnerClass.alias()

    @AliasedInnerClass.alias
    def method_class_alias(self): ...

    @classmethod
    @AliasedInnerClass.alias
    def cls_method_class_alias(cls): ...

    # staticmethod breaks descriptors when placed after,
    # so it must be applied before
    @AliasedInnerClass.alias
    @staticmethod
    def static_method_class_alias(): ...

    @aliased
    @staticmethod
    def aliased_static_method():
        return "my static method"

    @aliased_static_method.alias
    @staticmethod
    def aliased_static_method_alias(): ...

    # similarly to staticmethod breaking it, classmethod breaks the aliased.alias method
    @aliased
    @classmethod
    def aliased_class_method(cls):
        return "my class method"

    @aliased_class_method.alias
    @classmethod
    def aliased_class_method_alias(cls): ...


class TestAliased:
    tester_cls = AliasedTester
    tester = tester_cls()

    def test_prop_alias(self):
        assert self.tester.prop_alias == self.tester.prop

    def test_second_prop_alias(self):
        assert self.tester.second_prop_alias == self.tester.prop

    def test_prop_pascal_case(self):
        assert self.tester.PropPascalCase == self.tester.prop

    @classmethod
    def test_prop_doc(cls):
        assert cls.tester_cls.prop_alias.__doc__ == f"Alias for {PROP_NAME}"
        assert cls.tester_cls.second_prop_alias.__doc__ == f"Alias for {PROP_NAME}"
        assert cls.tester_cls.PropPascalCase.__doc__ == f"Alias for {PROP_NAME}"

    def test_aliased_method(self):
        assert self.tester.aliased_method() == self.tester.aliased_val

    def test_aliased_method_alias(self):
        assert self.tester.normal_alias() == self.tester.aliased_val

    def test_method_pascal_case(self):
        assert self.tester.PascalCaseMethod() == self.tester.aliased_val

    def test_aliased_method_doc(self):
        alias_delimiter = ","

        alias_names = [
            "PascalCaseMethod",
            "normal_alias",
            "nested_alias",
            # having this last one here ensures nested aliases are working
            "alias_of_nested_alias",
        ]
        start = "(aliases "
        end = ")"
        doc = self.tester.aliased_method.__doc__
        assert doc[: len(start)] == start

        end_index = doc.find(end, len(start))
        assert end_index > len(start)

        middle = doc[len(start) : end_index]
        parsed_names = middle.split(alias_delimiter)
        assert len(parsed_names) == len(alias_names) and set(parsed_names) & set(
            alias_names
        ) == set(alias_names)

    def test_nested_alias(self):
        assert self.tester.nested_alias() == self.tester.aliased_val

    def test_alias_of_nested_alias(self):
        assert self.tester.alias_of_nested_alias() == self.tester.aliased_val

    @classmethod
    def test_aliased_class(cls):
        inner_class = cls.tester_cls.AliasedInnerClass("test_val")
        assert type(cls.tester_cls.AliasedInnerClass) is type
        assert inner_class.prop == "test_val"

    @classmethod
    def test_aliased_class_alias(cls):
        val = "my val"
        original = cls.tester_cls.AliasedInnerClass(val)
        aliased_instance = cls.tester_cls.NormalClassAlias(val)
        assert original == aliased_instance
        assert isinstance(original, cls.tester_cls.AliasedInnerClass)
        assert isinstance(original, cls.tester_cls.NormalClassAlias)
        assert isinstance(aliased_instance, cls.tester_cls.AliasedInnerClass)
        assert isinstance(aliased_instance, cls.tester_cls.NormalClassAlias)

    @classmethod
    def test_snake_case_class_alias(cls):
        val = "my val"
        assert isinstance(
            cls().tester_cls.snake_case_class_alias(val),
            cls.tester_cls.AliasedInnerClass,
        )
        assert isinstance(
            cls.tester_cls.method_class_alias(val), cls.tester_cls.AliasedInnerClass
        )
        assert isinstance(
            cls.tester_cls.cls_method_class_alias(val), cls.tester_cls.AliasedInnerClass
        )
        assert isinstance(
            cls.tester_cls.static_method_class_alias(val),
            cls.tester_cls.AliasedInnerClass,
        )

    @classmethod
    def test_aliased_class_methods(cls):
        assert (
            cls.tester_cls.aliased_class_method()
            == cls.tester_cls.aliased_class_method_alias()
        )

    @classmethod
    def test_aliased_static_methods(cls):
        assert (
            cls.tester_cls.aliased_static_method()
            == cls.tester_cls.aliased_static_method_alias()
        )
