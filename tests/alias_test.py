import warnings

import pytest

from aliasing import (
    alias,
    CircularAliasError,
    TrampleAliasError,
    TrampleAliasWarning,
)

PROP_NAME = "prop"


class AliasTest:
    my_alias: alias
    prop: str


def _alias_tester():
    class AliasTester(AliasTest):
        my_alias = alias(PROP_NAME)

        def __init__(self):
            self.prop: str = "anything"

    return AliasTester


def test_alias_init():
    alias_test_cls = _alias_tester()
    alias_test = alias_test_cls()
    assert alias_test.my_alias == alias_test.prop


def test_alias_get_prop():
    alias_test_cls = _alias_tester()
    alias_test = alias_test_cls()
    assert getattr(alias_test, "my_alias") == alias_test.prop


def test_alias_set_prop():
    alias_test_cls = _alias_tester()
    alias_test = alias_test_cls()
    with pytest.raises(NotImplementedError) as exc_info:
        alias_test.my_alias = ""

    assert (
        exc_info.value.args[0]
        == "cannot set the value of read-only alias my_alias"
    )
    assert alias_test.my_alias == alias_test.prop


def test_alias_doc():
    alias_test_cls = _alias_tester()
    alias_test = alias_test_cls()
    assert alias_test.my_alias.__doc__ == alias_test.prop.__doc__
    assert alias_test_cls.my_alias.__doc__ == f"Alias for {PROP_NAME}"


def test_alias_attach_to_instance():
    class AliasAttachTest:
        def __init__(self):
            self.prop: str = "anything"

    alias_test1 = AliasAttachTest()
    alias_test2 = AliasAttachTest()
    alias_name = "my_attached_alias"
    my_alias = alias(PROP_NAME, alias_name=alias_name)
    my_alias.attach(alias_test1)
    assert hasattr(alias_test1, alias_name) and getattr(alias_test1, alias_name) == alias_test1.prop
    assert isinstance(alias_test1, AliasAttachTest)
    assert not hasattr(AliasAttachTest, alias_name) and my_alias not in AliasAttachTest.__dict__.values()
    assert not hasattr(alias_test2, alias_name)


def test_alias_attach_to_class_non_isolated():
    class AliasAttachTest:
        def __init__(self):
            self.prop: str = "anything"

    alias_test1 = AliasAttachTest()
    alias_test2 = AliasAttachTest()
    alias_name = "my_attached_alias"
    my_alias = alias(PROP_NAME, alias_name=alias_name)
    my_alias.attach(AliasAttachTest)
    assert hasattr(alias_test1, alias_name) and getattr(alias_test1, alias_name) == alias_test1.prop
    assert hasattr(alias_test2, alias_name) and getattr(alias_test2, alias_name) == alias_test2.prop
    assert alias_test1.__class__ == AliasAttachTest and alias_test2.__class__ == AliasAttachTest
    assert hasattr(AliasAttachTest, alias_name) and my_alias in AliasAttachTest.__dict__.values()


def test_alias_attach_err():
    class AliasAttachTest:
        def __init__(self):
            self.prop: str = "anything"

    alias_test = AliasAttachTest()
    my_alias = alias(PROP_NAME)
    with pytest.raises(RuntimeError) as exc_info:
        my_alias.attach(alias_test)

    assert exc_info.value.args[0] == "must provide name to attach alias"
    assert my_alias not in AliasAttachTest.__dict__.values()


def test_alias_attach_name_on_attach():
    class AliasAttachTest:
        def __init__(self):
            self.prop: str = "anything"

    alias_test = AliasAttachTest()
    my_alias = alias(PROP_NAME)
    my_alias.attach(alias_test, "my_second_attached_alias")
    assert getattr(alias_test, "my_second_attached_alias") == alias_test.prop


def test_alias_trample_on_attach_err():
    class AliasAttachTest:
        def __init__(self):
            self.prop: str = "anything"

    alias_name = "my_alias_name"
    alias_test = AliasAttachTest()
    my_alias = alias(PROP_NAME, alias_name=alias_name)
    my_alias.attach(alias_test)
    second_alias = alias(PROP_NAME, alias_name=alias_name)
    with pytest.raises(TrampleAliasError) as exc_info:
        second_alias.attach(alias_test)

    assert isinstance(exc_info.value, TrampleAliasError)
    assert exc_info.value.args[0] == (
        f"Owner class {AliasAttachTest.__name__} already has member with name"
        f" {alias_name}. Cannot override it with alias for {PROP_NAME} by default,"
        " pass `trample_ok=True` to override the member anyway."
    )


def test_alias_trample_on_attach_warning():
    class AliasAttachTest:
        def __init__(self):
            self.prop: str = "anything"

    alias_name = "my_alias_name"
    alias_test = AliasAttachTest()
    my_alias = alias(PROP_NAME, alias_name=alias_name)
    my_alias.attach(alias_test)
    second_alias = alias(PROP_NAME, alias_name=alias_name)
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        second_alias.attach(alias_test, trample_ok=True)

        assert len(w) == 1
        assert issubclass(w[-1].category, TrampleAliasWarning)
        assert str(w[-1].message) == (
            f"Owner class {AliasAttachTest.__name__} already has member with name"
            f" {alias_name}. Overriding with alias for {PROP_NAME}. Pass"
            " `trample_ok=False` to disallow this behavior."
        )


class CircAliasTester:
    prop1: alias
    prop2: alias
    prop3: alias
    prop4: alias
    prop5: alias
    prop6: alias
    prop7: alias


class TestCircAlias:
    @staticmethod
    def _circ_tester():
        class CircAliasTesterImpl(CircAliasTester):
            # 2 alias circle
            prop1 = alias("prop2")
            prop2 = alias("prop1")

            # alias refers to a circular alias
            prop3 = alias("prop2")

            # 1 alias circle
            prop4 = alias("prop4")

            # 3 alias circle
            prop5 = alias("prop7")
            prop6 = alias("prop5")
            prop7 = alias("prop6")

        return CircAliasTesterImpl()

    @staticmethod
    def _non_circ_tester():
        class NonCircAliasTesterImpl(CircAliasTester):
            prop1 = "my rop"
            # 1 alias chain
            prop2 = alias("prop1")

            # 2 alias chain
            prop3 = alias("prop2")

            # 3 alias chain
            prop4 = alias("prop3")

            # 4+ alias chain
            prop5 = alias("prop4")
            prop6 = alias("prop5")
            prop7 = alias("prop6")

        return NonCircAliasTesterImpl()

    def test_alias_chain_no_err(self):
        instance = self._non_circ_tester()
        assert instance.prop2 == instance.prop1
        assert instance.prop3 == instance.prop1
        assert instance.prop4 == instance.prop1
        assert instance.prop5 == instance.prop1
        assert instance.prop6 == instance.prop1
        assert instance.prop7 == instance.prop1

    @staticmethod
    def _err_message(name) -> str:
        return f"Nested alias {name} references a circular alias"

    def test_len_2_circle(self):
        instance = self._circ_tester()
        with pytest.raises(CircularAliasError) as exc_info:
            p = instance.prop1
        assert exc_info.value.args[0] == self._err_message("prop1")
        with pytest.raises(CircularAliasError) as exc_info:
            p = instance.prop2
        assert exc_info.value.args[0] == self._err_message("prop2")

    def test_len_1_circle(self):
        instance = self._circ_tester()
        with pytest.raises(CircularAliasError) as exc_info:
            p = instance.prop4
        assert exc_info.value.args[0] == self._err_message("prop4")

    def test_len_3_circle(self):
        instance = self._circ_tester()
        with pytest.raises(CircularAliasError) as exc_info:
            p = instance.prop5
        assert exc_info.value.args[0] == self._err_message("prop5")
        with pytest.raises(CircularAliasError) as exc_info:
            p = instance.prop6
        assert exc_info.value.args[0] == self._err_message("prop6")
        with pytest.raises(CircularAliasError) as exc_info:
            p = instance.prop7
        assert exc_info.value.args[0] == self._err_message("prop7")

    def test_reference_to_circle(self):
        instance = self._circ_tester()
        with pytest.raises(CircularAliasError) as exc_info:
            p = instance.prop3
        assert exc_info.value.args[0] == self._err_message("prop3")
