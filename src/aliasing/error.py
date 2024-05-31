class AliasWarning(UserWarning):
    pass


class AliasError(Exception):
    pass


class CircularAliasError(AliasError):
    """when the aliases refer back to each other"""

    pass


class TrampleAliasError(AliasError):
    """when the alias would override an already existing member"""

    pass


class TrampleAliasWarning(AliasWarning):
    """
    when the alias would override an already existing member,
    but the user has opted to forcible override it
    """

    pass
