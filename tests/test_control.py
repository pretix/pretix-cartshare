import pytest
from datetime import timedelta

from decimal import Decimal
from django.utils.timezone import now
from pretix.base.models import CartPosition
from pretix.base.models import Event
from pretix.base.models import EventPermission
from pretix.base.models import Organizer
from pretix.base.models import User
from pretix_cartshare.models import SharedCart
from pretix_cartshare.signals import clean_cart_positions


@pytest.fixture
def env():
    o = Organizer.objects.create(name='Dummy', slug='dummy')
    event = Event.objects.create(
        organizer=o, name='Dummy', slug='dummy',
        date_from=now(), plugins='pretix_cartshare'
    )
    user = User.objects.create_user('dummy@dummy.dummy', 'dummy')
    EventPermission.objects.create(user=user, event=event)

    ticket = event.items.create(default_price=Decimal('12'))

    return event, user, ticket


@pytest.mark.django_db
def test_create_sharedcart_defaultprice(client, env):
    event, user, ticket = env
    client.login(email='dummy@dummy.dummy', password='dummy')
    q = event.quotas.create(size=5, name='Test')
    q.items.add(ticket)
    r = client.post('/control/event/%s/%s/cartshare/create/' % (event.slug, event.organizer.slug), {
        'expires': (now() + timedelta(days=14)).strftime("%Y-%m-%d %H:%M:%S"),
        'form-TOTAL_FORMS': '1',
        'form-INITIAL_FORMS': '0',
        'form-MIN_NUM_FORMS': '1',
        'form-MAX_NUM_FORMS': '1000',
        'form-0-count': '3',
        'form-0-itemvar': ticket.id,
        'form-0-price': ''
    }, follow=True)
    assert 'alert-success' in r.rendered_content
    cps = CartPosition.objects.all()
    assert len(cps) == 3
    assert all(cp.item == ticket for cp in cps)
    assert all(cp.price == ticket.default_price for cp in cps)


@pytest.mark.django_db
def test_create_sharedcart_customprice(client, env):
    event, user, ticket = env
    client.login(email='dummy@dummy.dummy', password='dummy')
    r = client.post('/control/event/%s/%s/cartshare/create/' % (event.slug, event.organizer.slug), {
        'expires': (now() + timedelta(days=14)).strftime("%Y-%m-%d %H:%M:%S"),
        'form-TOTAL_FORMS': '1',
        'form-INITIAL_FORMS': '0',
        'form-MIN_NUM_FORMS': '1',
        'form-MAX_NUM_FORMS': '1000',
        'form-0-count': '3',
        'form-0-itemvar': ticket.id,
        'form-0-price': '14'
    }, follow=True)
    assert 'alert-success' in r.rendered_content
    cps = CartPosition.objects.all()
    assert len(cps) == 3
    assert all(cp.item == ticket for cp in cps)
    assert all(cp.price == Decimal('14') for cp in cps)


@pytest.mark.django_db
def test_create_sharedcart_variation(client, env):
    event, user, ticket = env
    shirt = event.items.create(name='T-Shirt')
    shirt_red = shirt.variations.create(value='Red')
    client.login(email='dummy@dummy.dummy', password='dummy')
    r = client.post('/control/event/%s/%s/cartshare/create/' % (event.slug, event.organizer.slug), {
        'expires': (now() + timedelta(days=14)).strftime("%Y-%m-%d %H:%M:%S"),
        'form-TOTAL_FORMS': '1',
        'form-INITIAL_FORMS': '0',
        'form-MIN_NUM_FORMS': '1',
        'form-MAX_NUM_FORMS': '1000',
        'form-0-count': '3',
        'form-0-itemvar': '%s-%s' % (shirt.id, shirt_red.id),
        'form-0-price': '14'
    }, follow=True)
    assert 'alert-success' in r.rendered_content
    cps = CartPosition.objects.all()
    assert len(cps) == 3
    assert all(cp.item == shirt for cp in cps)
    assert all(cp.price == Decimal('14') for cp in cps)


@pytest.mark.django_db
def test_create_sharedcart_quota_full(client, env):
    event, user, ticket = env
    q = event.quotas.create(size=2, name='Test')
    q.items.add(ticket)
    client.login(email='dummy@dummy.dummy', password='dummy')
    r = client.post('/control/event/%s/%s/cartshare/create/' % (event.slug, event.organizer.slug), {
        'expires': (now() + timedelta(days=14)).strftime("%Y-%m-%d %H:%M:%S"),
        'form-TOTAL_FORMS': '1',
        'form-INITIAL_FORMS': '0',
        'form-MIN_NUM_FORMS': '1',
        'form-MAX_NUM_FORMS': '1000',
        'form-0-count': '3',
        'form-0-itemvar': ticket.id,
        'form-0-price': '14'
    }, follow=True)
    assert 'alert-danger' in r.rendered_content
    assert not CartPosition.objects.exists()


@pytest.mark.django_db
def test_create_sharedcart_invalid(client, env):
    event, user, ticket = env
    client.login(email='dummy@dummy.dummy', password='dummy')
    r = client.post('/control/event/%s/%s/cartshare/create/' % (event.slug, event.organizer.slug), {
        'expires': (now() + timedelta(days=14)).strftime("%Y-%m-%d %H:%M:%S"),
        'form-TOTAL_FORMS': '1',
        'form-INITIAL_FORMS': '0',
        'form-MIN_NUM_FORMS': '1',
        'form-MAX_NUM_FORMS': '1000',
        'form-0-count': '3',
        'form-0-itemvar': ticket.id,
        'form-0-price': 'abc'
    }, follow=True)
    assert 'alert-danger' in r.rendered_content
    assert not CartPosition.objects.exists()


@pytest.mark.django_db
def test_list_sharedcart(client, env):
    event, user, ticket = env
    client.login(email='dummy@dummy.dummy', password='dummy')
    sc = SharedCart.objects.create(total=Decimal('13'), expires=now() + timedelta(days=3), event=event)
    sc2 = SharedCart.objects.create(total=Decimal('13'), expires=now() - timedelta(days=3), event=event)
    r = client.get('/control/event/%s/%s/cartshare/' % (event.slug, event.organizer.slug))
    assert sc.cart_id in r.rendered_content
    assert sc2.cart_id not in r.rendered_content


@pytest.mark.django_db
def test_delete_sharedcart(client, env):
    event, user, ticket = env
    client.login(email='dummy@dummy.dummy', password='dummy')
    sc = SharedCart.objects.create(total=Decimal('13'), expires=now() + timedelta(days=3), event=event)
    CartPosition.objects.create(cart_id=sc.cart_id, event=event, price=Decimal('13'), item=ticket,
                                expires=now() + timedelta(days=3))
    r = client.post('/control/event/%s/%s/cartshare/%s/delete' % (event.slug, event.organizer.slug, sc.cart_id), {},
                    follow=True)
    assert not SharedCart.objects.exists()
    assert not CartPosition.objects.exists()
    assert 'FOOBAR' not in r.rendered_content


@pytest.mark.django_db
def test_delete_unknown(client, env):
    event, user, ticket = env
    client.login(email='dummy@dummy.dummy', password='dummy')
    r = client.get('/control/event/%s/%s/cartshare/ASD/delete' % (event.slug, event.organizer.slug))
    assert r.status_code == 404


@pytest.mark.django_db
def test_require_permission(client, env):
    event, user, ticket = env
    client.login(email='dummy@dummy.dummy', password='dummy')
    ep = EventPermission.objects.get(user=user, event=event)
    ep.can_change_orders = False
    ep.save()
    r = client.get('/control/event/%s/%s/cartshare/' % (event.slug, event.organizer.slug))
    assert r.status_code == 403
    r = client.get('/control/event/%s/%s/' % (event.slug, event.organizer.slug))
    assert b'cartshare' not in r.content


@pytest.mark.django_db
def test_cleanup(env):
    event, user, ticket = env
    sc = SharedCart.objects.create(total=Decimal('13'), expires=now() + timedelta(days=3), event=event)
    sc2 = SharedCart.objects.create(total=Decimal('13'), expires=now() - timedelta(days=3), event=event)
    CartPosition.objects.create(cart_id=sc2.cart_id, event=event, price=Decimal('13'), item=ticket,
                                expires=now() - timedelta(days=3))
    clean_cart_positions(event)
    assert SharedCart.objects.filter(id=sc.id).exists()
    assert not SharedCart.objects.filter(id=sc2.id).exists()
    assert not CartPosition.objects.exists()
