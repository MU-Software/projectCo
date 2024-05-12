import typing


def describe_pmmod(pmmod: int) -> list:
    """Permission mode description"""
    pmmod_str: str = str(pmmod)
    pm_length: int = len(pmmod_str)
    result: list[tuple] = []
    for target_pmmod_index in range(pm_length):
        z = int(pmmod_str[target_pmmod_index])
        result.append(tuple(map(bool, (4 & z, 2 & z, 1 & z))))
    return result


def describe_pmmod_with_rwx(pmmod: int) -> str:
    """Permission mode description with RWX"""
    return "".join(y for x, y in zip([4 & pmmod, 2 & pmmod, 1 & pmmod], list("RWX")) if x)


def validate_pmmod_element(z: typing.Sequence[int]) -> bool:
    return (
        not isinstance(z, (str, bytes))
        and isinstance(z, typing.Sequence)
        and all(isinstance(x, int) for x in z)
        and len(z) == 3
    )


def calculate_pmmod(pmmod: typing.Sequence[typing.Sequence[int]]) -> int:
    if not pmmod:
        raise ValueError("Argument 'pmmod' is empty")

    if not all(map(validate_pmmod_element, pmmod)):
        raise ValueError("Length of one of argument 'pmmod' elements is not 3")

    result: str = ""
    for pmmod_element in pmmod:
        result += str(int("".join(map(lambda z: str(int(bool(z))), pmmod_element)), 2))

    return int(result)
