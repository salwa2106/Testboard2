import pytest

def test_passes():
    assert 1 == 1

@pytest.mark.xfail(reason="intentional demo fail", strict=True)
def test_fails():
    assert 2 == 1
