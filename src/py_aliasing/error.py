class AliasError(Exception):
    pass


class CircularAliasError(AliasError):
    """when the aliases refer back to each other"""
    pass
