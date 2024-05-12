import math


# http://szudzik.com/ElegantPairing.pdf
def elegant_pair(x: int, y: int) -> int:
    return x * x + x + y if x >= y else y * y + x


def elegant_unpair(z: int) -> tuple[int, int]:
    sqrtz: int = math.floor(math.sqrt(z))
    sqz: int = sqrtz * sqrtz
    return (sqrtz, z - sqz - sqrtz) if (z - sqz) >= sqrtz else (z - sqz, sqrtz)
