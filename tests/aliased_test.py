from aliasing.alias import alias, aliased

PROP_NAME = "prop"


class AliasedTester:
    prop_alias: aliased
    prop: str
    aliased_val: str

    def second_prop_alias(self): ...

    class PropPascalCase: ...

    def aliased_method(self) -> str: ...

    class PascalCaseMethod: ...

    def normal_alias(self): ...

    def nested_alias(self): ...

    def alias_of_nested_alias(self): ...

    class AliasedInnerClass:
        prop: any

    class NormalClassAlias: ...

    snake_case_class_alias: alias

    def method_class_alias(self): ...

    @classmethod
    def cls_method_class_alias(cls): ...

    @staticmethod
    def static_method_class_alias(): ...

    @staticmethod
    def aliased_static_method() -> str: ...

    @staticmethod
    def aliased_static_method_alias(): ...

    # similarly to staticmethod breaking it, classmethod breaks the aliased.alias method
    @classmethod
    def aliased_class_method(cls) -> str: ...

    @classmethod
    def aliased_class_method_alias(cls): ...


class TestAliased:
    @staticmethod
    def _prop_tester():
        class AliasedPropTester(AliasedTester):
            prop_alias = aliased(alias(PROP_NAME))

            def __init__(self):
                self.prop = "anything at all"

            @prop_alias.alias
            def second_prop_alias(self): ...

            @prop_alias.alias
            class PropPascalCase: ...

        return AliasedPropTester

    @staticmethod
    def _method_tester():
        class AliasedMethodTester(AliasedTester):
            def __init__(self):
                self.aliased_val = "wah wah"

            @aliased
            def aliased_method(self):
                return self.aliased_val

            @aliased_method.alias
            class PascalCaseMethod: ...

            @aliased_method.alias
            def normal_alias(self): ...

        return AliasedMethodTester

    @staticmethod
    def _nested_method_tester():
        class NestedAliasedMethodTester(AliasedTester):
            def __init__(self):
                self.aliased_val = "wah wah"

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

        return NestedAliasedMethodTester

    @staticmethod
    def _class_tester():
        class AliasedClassTester(AliasedTester):
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

        return AliasedClassTester

    @staticmethod
    def _class_method_tester():
        class AliasedClassMethodTester(AliasedTester):
            # similarly to staticmethod breaking it, classmethod breaks the aliased.alias method
            @aliased
            @classmethod
            def aliased_class_method(cls):
                return "my class method"

            @aliased_class_method.alias
            @classmethod
            def aliased_class_method_alias(cls): ...

        return AliasedClassMethodTester

    @staticmethod
    def _static_method_tester():
        class AliasedStaticMethodTester(AliasedTester):
            @aliased
            @staticmethod
            def aliased_static_method():
                return "my static method"

            @aliased_static_method.alias
            @staticmethod
            def aliased_static_method_alias(): ...

        return AliasedStaticMethodTester

    def test_prop_alias(self):
        tester_cls = self._prop_tester()
        tester = tester_cls()
        assert tester.prop_alias == tester.prop

    def test_second_prop_alias(self):
        tester_cls = self._prop_tester()
        tester = tester_cls()
        assert tester.second_prop_alias == tester.prop

    def test_prop_pascal_case(self):
        tester_cls = self._prop_tester()
        tester = tester_cls()
        assert tester.PropPascalCase == tester.prop

    @classmethod
    def test_prop_doc(cls):
        tester_cls = cls._prop_tester()
        assert tester_cls.prop_alias.__doc__ == f"Alias for {PROP_NAME}"
        assert tester_cls.second_prop_alias.__doc__ == f"Alias for {PROP_NAME}"
        assert tester_cls.PropPascalCase.__doc__ == f"Alias for {PROP_NAME}"

    def test_aliased_method(self):
        tester_cls = self._method_tester()
        tester = tester_cls()
        assert tester.aliased_method() == tester.aliased_val

    def test_aliased_method_alias(self):
        tester_cls = self._method_tester()
        tester = tester_cls()
        assert tester.normal_alias() == tester.aliased_val

    def test_method_pascal_case(self):
        tester_cls = self._method_tester()
        tester = tester_cls()
        assert tester.PascalCaseMethod() == tester.aliased_val

    def test_aliased_method_doc(self):
        tester_cls = self._method_tester()
        tester = tester_cls()

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
        doc = tester.aliased_method.__doc__
        assert doc[: len(start)] == start

        end_index = doc.find(end, len(start))
        assert end_index > len(start)

        middle = doc[len(start) : end_index]
        parsed_names = middle.split(alias_delimiter)
        assert len(parsed_names) == len(alias_names) and set(parsed_names) & set(
            alias_names
        ) == set(alias_names)

    def test_nested_alias(self):
        tester_cls = self._nested_method_tester()
        tester = tester_cls()
        assert tester.nested_alias() == tester.aliased_val

    def test_alias_of_nested_alias(self):
        tester_cls = self._nested_method_tester()
        tester = tester_cls()
        assert tester.alias_of_nested_alias() == tester.aliased_val

    @classmethod
    def test_aliased_class(cls):
        tester_cls = cls._class_tester()
        inner_class = tester_cls.AliasedInnerClass("test_val")
        assert type(tester_cls.AliasedInnerClass) is type
        assert inner_class.prop == "test_val"

    @classmethod
    def test_aliased_class_alias(cls):
        tester_cls = cls._class_tester()
        val = "my val"
        original = tester_cls.AliasedInnerClass(val)
        aliased_instance = tester_cls.NormalClassAlias(val)
        assert original == aliased_instance
        assert isinstance(original, tester_cls.AliasedInnerClass)
        assert isinstance(original, tester_cls.NormalClassAlias)
        assert isinstance(aliased_instance, tester_cls.AliasedInnerClass)
        assert isinstance(aliased_instance, tester_cls.NormalClassAlias)

    @classmethod
    def test_snake_case_class_alias(cls):
        tester_cls = cls._class_tester()
        val = "my val"
        assert isinstance(
            tester_cls.snake_case_class_alias(val),
            tester_cls.AliasedInnerClass,
        )
        assert isinstance(
            tester_cls.method_class_alias(val), tester_cls.AliasedInnerClass
        )
        assert isinstance(
            tester_cls.cls_method_class_alias(val), tester_cls.AliasedInnerClass
        )
        assert isinstance(
            tester_cls.static_method_class_alias(val),
            tester_cls.AliasedInnerClass,
        )

    @classmethod
    def test_aliased_class_methods(cls):
        tester_cls = cls._class_tester()
        assert (
            tester_cls.aliased_class_method()
            == tester_cls.aliased_class_method_alias()
        )

    @classmethod
    def test_aliased_static_methods(cls):
        tester_cls = cls._class_tester()
        assert (
            tester_cls.aliased_static_method()
            == tester_cls.aliased_static_method_alias()
        )
