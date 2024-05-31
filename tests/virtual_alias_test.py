import warnings

import pytest

from aliasing import TrampleAliasWarning, TrampleAliasError, valiases


class VirtualAliasTest:
    @valiases("method1", "method2")
    def method(self):
        return "my method return"


def test_valiases_dir():
    va = VirtualAliasTest()
    filtered_dir = set(filter(lambda x: x.startswith("method"), dir(va)))
    expected_dir = {"method", "method1", "method2"}
    assert filtered_dir == expected_dir


def test_valias_dict():
    filtered_dict_keys = set(
        filter(lambda x: x.startswith("method"), VirtualAliasTest.__dict__.keys())
    )
    expected_dict_keys = {"method", "method1", "method2"}
    assert filtered_dict_keys == expected_dict_keys


def test_valiases():
    va = VirtualAliasTest()
    assert va.method() == va.method1()
    assert va.method() == va.method2()


def test_valias_trample_warning():
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")

        class WarningTest:
            @valiases("method2", trample_ok=["method2"])
            def method1(self): ...

            def method2(self): ...

        assert len(w) == 1
        assert issubclass(w[-1].category, TrampleAliasWarning)
        assert str(w[-1].message) == (
            f"Owner class {WarningTest.__name__} already has member with name"
            f" {WarningTest.method2.__name__}. Overriding with alias for"
            f" {WarningTest.method1.__name__}. Remove '{WarningTest.method2.__name__}'"
            f" from the `trample_ok` list parameter to disallow this behavior."
        )


def test_valias_trample_err():
    with pytest.raises(RuntimeError) as exc_info:

        class ErrorTest:
            @valiases("method2")
            def method1(self): ...

            def method2(self): ...

    trample_error = exc_info.value.__cause__

    assert isinstance(trample_error, TrampleAliasError)
    assert trample_error.args[0] == (
        f"Owner class ErrorTest already has member with name"
        f" method2. Cannot override it with alias for"
        f" method1 by default, pass"
        f" `trample_ok=['method2']` to override the member"
        f" anyway."
    )
