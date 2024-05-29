from py_aliasing.alias import alias, aliased

PROP_NAME = "prop"


class AliasedTester:
    prop_alias = aliased(alias(PROP_NAME))

    def __init__(self):
        self.prop = "anything at all"
        self.aliased_val = "wah wah"

    @prop_alias.alias
    def second_prop_alias(self): ...

    @prop_alias.alias
    class PropPascalCase:
        ...

    @aliased
    def aliased_method(self):
        return self.aliased_val

    @aliased_method.alias
    class PascalCaseMethod:
        ...

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
    class NormalClassAlias:
        ...

    snake_case_class_alias = AliasedInnerClass.alias()

    @AliasedInnerClass.alias
    def method_class_alias(self): ...

    @classmethod
    @AliasedInnerClass.alias
    def cls_method_class_alias(cls): ...

    @staticmethod
    @AliasedInnerClass.alias
    def static_method_class_alias(): ...


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
        assert isinstance(cls().tester_cls.snake_case_class_alias(val), cls.tester_cls.AliasedInnerClass)
        assert isinstance(cls.tester_cls.method_class_alias(val), cls.tester_cls.AliasedInnerClass)
        assert isinstance(cls.tester_cls.cls_method_class_alias(val), cls.tester_cls.AliasedInnerClass)
        assert isinstance(cls.tester_cls.static_method_class_alias(val), cls.tester_cls.AliasedInnerClass)
