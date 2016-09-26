import pytest
from pretix.base.models import CartPosition


@pytest.mark.django_db
def test_foo():
    assert not CartPosition.objects.exists()
