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


class TestAliased(AliasedTester):
    def test_prop_alias(self):
        assert self.prop_alias == self.prop

    def test_second_prop_alias(self):
        assert self.second_prop_alias == self.prop

    def test_prop_pascal_case(self):
        assert self.PropPascalCase == self.prop

    def test_prop_doc(self):
        assert self.prop_alias.__doc__ == f"Alias for {PROP_NAME}"
        assert self.second_prop_alias.__doc__ == f"Alias for {PROP_NAME}"
        assert self.PropPascalCase.__doc__ == f"Alias for {PROP_NAME}"

    @classmethod
    def test_prop_alias_doc(cls):
        assert cls.prop_alias.__doc__.startswith("(aliases ")

    def test_aliased_method(self):
        assert self.aliased_method() == self.aliased_val

    def test_aliased_method_alias(self):
        assert self.normal_alias() == self.aliased_val

    def test_method_pascal_case(self):
        assert self.PascalCaseMethod() == self.aliased_val

    def test_nested_alias(self):
        assert self.nested_alias() == self.aliased_val

    def test_alias_of_nested_alias(self):
        assert self.alias_of_nested_alias() == self.aliased_val

    @classmethod
    def test_aliased_class(cls):
        inner_class = cls.AliasedInnerClass("test_val")
        assert type(cls.AliasedInnerClass) is type
        assert inner_class.prop == "test_val"

    @classmethod
    def test_aliased_class_alias(cls):
        val = "my val"
        original = cls.AliasedInnerClass(val)
        aliased_instance = cls.NormalClassAlias(val)
        assert original == aliased_instance
        assert isinstance(original, cls.AliasedInnerClass)
        assert isinstance(original, cls.NormalClassAlias)
        assert isinstance(aliased_instance, cls.AliasedInnerClass)
        assert isinstance(aliased_instance, cls.NormalClassAlias)

    @classmethod
    def test_snake_case_class_alias(cls):
        val = "my val"
        assert isinstance(cls().snake_case_class_alias(val), cls.AliasedInnerClass)
        assert isinstance(cls.method_class_alias(val), cls.AliasedInnerClass)
        assert isinstance(cls.cls_method_class_alias(val), cls.AliasedInnerClass)
        assert isinstance(cls.static_method_class_alias(val), cls.AliasedInnerClass)
