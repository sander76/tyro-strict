from dataclasses import dataclass


def test_invalid_argument_type__tyro__fails():
    @dataclass
    class Model:
        a: int

    pass
