from datetime import timedelta
from decimal import Decimal

import pytest
from django.utils.timezone import now
from pretix.base.models import CartPosition, Event, Organizer
from pretix_cartshare.models import SharedCart


@pytest.fixture
def env():
    o = Organizer.objects.create(name='Dummy', slug='dummy')
    event = Event.objects.create(
        organizer=o, name='Dummy', slug='dummy', live=True,
        date_from=now(), plugins='pretix_cartshare'
    )
    ticket = event.items.create(default_price=Decimal('12'), name='Early-bird')
    return event, ticket


@pytest.mark.django_db
def test_redeem_expired(client, env):
    event, ticket = env
    sc = SharedCart.objects.create(total=Decimal('13'), expires=now() - timedelta(days=3), event=event)
    CartPosition.objects.create(cart_id=sc.cart_id, event=event, price=Decimal('13'), item=ticket,
                                expires=now() - timedelta(days=3))
    r = client.post('/%s/%s/sharedcart/%s/' % (event.slug, event.organizer.slug, sc.cart_id), {})
    assert r.status_code == 404


@pytest.mark.django_db
def test_redeem_valid(client, env):
    event, ticket = env
    sc = SharedCart.objects.create(total=Decimal('13'), expires=now() + timedelta(days=3), event=event)
    cp = CartPosition.objects.create(cart_id=sc.cart_id, event=event, price=Decimal('13'), item=ticket,
                                     expires=now() + timedelta(days=3))
    r = client.get('/%s/%s/sharedcart/%s/' % (event.slug, event.organizer.slug, sc.cart_id))
    assert r.status_code == 200
    assert 'Early-bird' in r.rendered_content
    r = client.post('/%s/%s/sharedcart/%s/' % (event.slug, event.organizer.slug, sc.cart_id), {}, follow=True)
    assert r.status_code == 200
    assert not SharedCart.objects.exists()
    cp.refresh_from_db()
    assert cp.cart_id != sc.cart_id
    assert cp.expires < now() + timedelta(days=1)
