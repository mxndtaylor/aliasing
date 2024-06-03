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

For example, in [Google's `python-fire` cli tool][2], cli commands are "generated" using
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

Or you might want to add functions which do not follow PEP 8 naming conventions:


```python
from aliasing import valiases

class Example:
    @valiases("MyFunc", "myFunc", "MY_FUNC")
    def my_func(self):
        return "foo"
```


## Advanced Usage 

### `alias` Descriptor

Since these are just python descriptors ([docs][1]), you can use them with more granularity too:

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


[1]: https://docs.python.org/3/howto/descriptor.html#primer
[2]: https://github.com/google/python-fire 

