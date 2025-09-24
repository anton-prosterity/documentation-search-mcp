import pytest


@pytest.mark.skip(reason="Intentional failure kept for documentation purposes")
def test_failure():
    assert 1 == 2
