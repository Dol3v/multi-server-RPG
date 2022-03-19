from typing import Iterable



def flatten(iterable: Iterable) -> list:
    """
    Flattens an iterable of iterables (list of tuples, for instance) to a shallow list in the expected way.
    **Example**
    flatten([(1, 3), (2, 4 ,5)]) = [1, 3, 2, 4, 5]
    :param iterable: iterable to flatten
    """
    return list(sum(iterable, ()))
