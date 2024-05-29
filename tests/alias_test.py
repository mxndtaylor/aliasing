import pytest

from py_aliasing.alias import alias
from py_aliasing.error import CircularAliasError

PROP_NAME = "prop"


class AliasTest:
    my_alias = alias(PROP_NAME)

    def __init__(self):
        self.prop: str = "anything"


def test_alias_init():
    alias_test = AliasTest()
    assert alias_test.my_alias == alias_test.prop


def test_alias_get_prop():
    alias_test = AliasTest()
    assert getattr(alias_test, "my_alias") == alias_test.prop


def test_alias_set_prop():
    alias_test = AliasTest()
    with pytest.raises(NotImplementedError) as exc_info:
        alias_test.my_alias = ""

    assert exc_info.value.args[0] == "cannot set the value of read-only alias my_alias"
    assert alias_test.my_alias == alias_test.prop


def test_alias_doc():
    alias_test = AliasTest()
    assert alias_test.my_alias.__doc__ == alias_test.prop.__doc__
    assert AliasTest.my_alias.__doc__ == f"Alias for {PROP_NAME}"


class AliasAttachTest:
    def __init__(self):
        self.prop: str = "anything"


def test_alias_attach():
    alias_test = AliasAttachTest()
    my_alias = alias(PROP_NAME, alias_name="my_attached_alias")
    my_alias.attach(alias_test)
    assert getattr(alias_test, "my_attached_alias") == alias_test.prop
    assert my_alias in AliasAttachTest.__dict__.values()


def test_alias_attach_err():
    alias_test = AliasAttachTest()
    my_alias = alias(PROP_NAME)
    with pytest.raises(RuntimeError) as exc_info:
        my_alias.attach(alias_test)

    assert exc_info.value.args[0] == "must provide name to attach alias"
    assert my_alias not in AliasAttachTest.__dict__.values()


def test_alias_attach_name_on_attach():
    alias_test = AliasAttachTest()
    my_alias = alias(PROP_NAME)
    my_alias.attach(alias_test, "my_second_attached_alias")
    assert getattr(alias_test, "my_second_attached_alias") == alias_test.prop


class TestCircAlias:
    # 2 alias circle
    prop1 = alias('prop2')
    prop2 = alias('prop1')

    # alias refers to a circular alias
    prop3 = alias('prop2')

    # 1 alias circle
    prop4 = alias('prop4')

    # 3 alias circle
    prop5 = alias('prop7')
    prop6 = alias('prop5')
    prop7 = alias('prop6')

    @staticmethod
    def _err_message(name) -> str:
        return f"Nested alias {name} references a circular alias"

    def test_len_2_circle(self):
        with pytest.raises(CircularAliasError) as exc_info:
            p = self.prop1
        assert exc_info.value.args[0] == self._err_message('prop1')
        with pytest.raises(CircularAliasError) as exc_info:
            p = self.prop2
        assert exc_info.value.args[0] == self._err_message('prop2')

    def test_len_1_circle(self):
        with pytest.raises(CircularAliasError) as exc_info:
            p = self.prop4
        assert exc_info.value.args[0] == self._err_message('prop4')

    def test_len_3_circle(self):
        with pytest.raises(CircularAliasError) as exc_info:
            p = self.prop5
        assert exc_info.value.args[0] == self._err_message('prop5')
        with pytest.raises(CircularAliasError) as exc_info:
            p = self.prop6
        assert exc_info.value.args[0] == self._err_message('prop6')
        with pytest.raises(CircularAliasError) as exc_info:
            p = self.prop7
        assert exc_info.value.args[0] == self._err_message('prop7')

    def test_reference_to_circle(self):
        with pytest.raises(CircularAliasError) as exc_info:
            p = self.prop3
        assert exc_info.value.args[0] == self._err_message('prop3')
