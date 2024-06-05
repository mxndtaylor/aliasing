# aliasing

![Tests Status](./badges/tests.svg)
![Coverage Status](./badges/coverage.svg)
![Flake8 Status](./badges/flake8.svg)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

[![PyPi](https://img.shields.io/pypi/v/aliasing)](https://pypi.org/project/aliasing)

`aliasing` is a small utility library for python which adds aliases to class members using python descriptors.

## Usage

### Direct use of `@aliased`

This is the recommended way to use the library if you are going to call the generated members in your scripts,
as it supports IDE completion.

Basic usage involves a similar process to the builtin `@property` and `@<property_name>.getter/setter`.
Instead we use `@aliased` to indicate the method whose register is being duplicated 
and `@<aliased_name>.alias` to indicate which method's name should be used to point to the "`aliased`" method:

```python
from aliasing import aliased


class Example:
    @aliased
    def method(self):
        return "my method call"

    @method.alias
    def method_alias(self): ...

# elsewhere...

example = Example()
# note that `==` and `is` always returns False for function objects
# i.e., this is False:
#   example.method == example.method
assert example.method.__code__ is example.method_alias.__code__
assert example.method_alias() == "my method call"
```

> [!TIP]
> To keep IDE completion for the methods marked with `@<aliased_name>.alias` the same
> as the method marked with `@aliased`, you must keep the signatures the same for now.
> 
> So: 
> ```python
> class Example:
>     @aliased
>     def method(self, args: str) -> str: ...
>     # This will NOT have the expected completion
>     @method.aliased
>     def method_alias1(self): ...
>     # But this will
>     @method.aliased
>     def method_alias2(self, args: str) -> str: ...
> ```
> 
> I will investigate a solution for this, but it might not present itself.

### Using "Virtual" Aliases to create a number of aliases at once

This is not strictly recommended for use in most cases unless your class will be 
processed by some framework which relies on the class members to generate something
an end-user might want.

Basic usage involves decorating your class's methods with `@valiases` and specifying the
names of however many aliases you want for that method.

For instance, if you want to make the function's old name available so as not to break the api, 
but remove it from IDE completion, you can add it as a virtual alias:

```python
from aliasing import valiases

class Example:
    @valiases("my_func_old_name")
    def my_func(self):
        return "foo"

# elsewhere
example = Example()
# this is available with auto-complete:
foo = example.my_func()
# this will _work_ but will give the user an "Unresolved attribute" warning:
foo_old = example.my_func_old_name()
```

> [!WARNING]
> In the library's current state, it would be better to use other methods to mark the 
> old function's name as deprecated, but in the future this library will hopefully
> be able to offer more support for this use-case.

This is a more convenient and shorter method of adding `alias`s to your

For example, in [Google's `python-fire` cli tool][1], cli commands are "generated" using
the members of a class, so you can easily add several commands at once using this library's
`@valiases` decorator:

```python
# fire_alias_example.py
import fire
from aliasing import valiases

class Example:
    @valiases("c", "cfg", "conf")
    def config(self):
        return "foo"

if __name__ == "__main__":
    fire.Fire(Example())
```

Then from cli, the user can call the aliased method or its aliases to achieve the same result:

```bash
$ python fire_alias_example.py config
foo
$ python fire_alias_example.py cfg
foo
$ python fire_alias_example.py conf
foo
$ python fire_alias_example.py c
foo
```

Or you might want to add names functions which do not follow PEP 8 naming conventions
without disabling your linter or ide inspection settings. 
Perhaps this code will be called in another language,
and you want to make sure the methods follow that language's style as well:


```python
from aliasing import valiases

class Example:
    @valiases("MyFunc", "myFunc", "MY_FUNC")
    def my_func(self):
        return "foo"
```


## Advanced Usage 

### `alias` Descriptor

Since `alias` objects are just python descriptors ([docs][2]), you can use them with more granularity too:

```python
from aliasing import alias


class Example:
    my_alias = alias(alias_for="prop")
    
    def __init__(self, val):
        self.prop = val

# elsewhere
example = Example(object())
assert example.prop is example.my_alias
```

You can define them independently from classes then attach them to any number of classes
without hierarchical relation.

```python
class Foo:
    def __init__(self, val):
        self.prop = val
        
class Bar:
    def __init__(self, val):
        self._prop = val
        
    @property
    def prop(self):
        return f"Bar.prop: {self._prop}"

# elsewhere
from aliasing import alias

prop_alias = alias(alias_for="prop", alias_name="my_alias")

prop_alias.attach(Foo)
prop_alias.attach(Bar)

# now both classes have the alias named "my_alias" pointing to "prop"
assert Foo('baz').my_alias == 'baz'
assert Bar('baz').my_alias == 'Bar.prop: baz'
```

You can check out the tests to see some more examples of
alternative ways to attach `alais`s to your classes.

### `aliased` Descriptor

You can also initialize `aliased` [descriptors][2] independently from classes:

```python
from aliasing import aliased



```

### `trample_ok` Parameters

By default, the `aliasing` library will raise a `TrampleAliasError` if you try to override 
existing class attributes or members without specifying `trample_ok` for that alias.

For instance, this will fail when `alias.attach` is called:

```python
class Foo:
    def __init__(self, val):
        self.prop = val
    
    @staticmethod
    def my_alias():
        return "don't trample me"

# elsewhere
from aliasing import alias

prop_alias = alias(alias_for="prop", alias_name="my_alias")

# fails with TrampleAliasError("Owner calls Foo already has member with name my_alias. [..]")
prop_alias.attach(Foo)
```

And this will fail whenever the class is imported:

```python
from aliasing import valiases

class Foo:
    # fails with TrampleAliasError("Owner class Foo already has member with name __str__. [..]")
    @valiases("__str__")
    def to_str(self): ...
```

But you can pass `trample_ok` in a couple different ways to override this behavior.

For `alias`:

```python
class Foo:
    def __init__(self, val):
        self.prop = val

    @staticmethod
    def my_alias():
        return "don't trample me"

# elsewhere
from aliasing import alias

prop_alias = alias(alias_for="prop", alias_name="my_alias")

# trample_ok causes a warning TrampleAliasWarning, but no longer fails
prop_alias.attach(Foo, trample_ok=True)

assert Foo('change is good').my_alias == 'change is good'

# OR if you prefer you can set `trample_ok` on the alias itself:
prop_alias = alias(alias_for="prop", alias_name="new_alias", trample_ok=True)
prop_alias.attach(Foo)
assert Foo('this also works').new_alias == 'this also works'
```

For `valiases`:

```python
from aliasing import valiases

class Foo:
    # trample_ok causes a warning TrampleAliasWarning, but no longer fails
    @valiases("__str__", trample_ok=['__str__'])
    def to_str(self):
        return 'new __str__ for Foo'

# I would not recommend 'trampling' magic methods like __str__
# ... but it's your life
assert Foo().__str__() == 'new __str__ for Foo'
```

The major benefit of this is that your can easily override
several methods at once if they all do the same thing (like return "NotImplemented"):

```python
import abc
from typing import Any

class CrudBase(abc.ABC):
    @abc.abstractmethod
    def create(self, name: str, data: Any) -> Any: ...

    @abc.abstractmethod
    def read(self, name: str) -> Any: ...

    @abc.abstractmethod
    def update(self, name: str, partial_data: Any) -> Any: ...

    @abc.abstractmethod
    def delete(self, name: str) -> Any: ...

# elsewhere
from aliasing import valiases
from some_persistence_lib import read_method

class ReadOnlyBase(CrudBase, abc.ABC):
    options = {'arg': 'val'}
    
    # now if any of these methods are called, they will get 'NotImplemented'
    # this saves you from redefining the same 2-liner method 3 times.
    # obviously the benefits are better the more methods there are to override
    @valiases('create', 'update', 'delete', trample_ok=['create', 'update', 'delete'])
    def _not_implemented(self, *args, **kwargs) -> Any:
        return NotImplemented
    
    def read(self, name: str) -> Any:
        return read_method(name, **self.options)
```

## Questions, Contributing, Feature requests

If you'd like to get in touch for any reason, the easiest thing is opening a GitHub issue.

Please give older issues (including closed!) a look before opening anything
and I'll try to respond whenever I can.

> [!NOTE]
> About feature requests, the plan for this library is to keep it extremely small. 
> In its present state, I think it has a bit of room to grow, but it is designed 
> with 1 thing in mind and 1 thing only: duplicating members of classes under
> different names. 
> 
> I'm more than happy to accept any and all feature requests
> that keep with this theme, but I reserve the right to deny them for any reason.
> I'll keep it reasonable, and will always be respectful.
> 
> If there is a request for something that's a little outside the scope of the
> project but maybe is related enough, I'll consider adding an 'extensions' library.


[1]: https://github.com/google/python-fire 
[2]: https://docs.python.org/3/howto/descriptor.html#primer
