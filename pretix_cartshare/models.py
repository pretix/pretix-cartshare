from django.db import models
from django.utils.crypto import get_random_string
from django.utils.translation import ugettext_lazy as _
from pretix.base.models import CartPosition, Event


def generate_cart_id():
    return get_random_string(32)


class SharedCart(models.Model):
    event = models.ForeignKey(
        Event,
        verbose_name=_("Event")
    )
    cart_id = models.CharField(
        max_length=255, default=generate_cart_id,
        verbose_name=_("Cart ID"),
        db_index=True,
    )
    datetime = models.DateTimeField(
        verbose_name=_("Date"),
        auto_now_add=True
    )
    expires = models.DateTimeField(
        verbose_name=_("Expiration date")
    )
    total = models.DecimalField(
        verbose_name=_("Total"),
        decimal_places=2, max_digits=10
    )

    @property
    def positions(self):
        return CartPosition.objects.filter(cart_id=self.cart_id, event=self.event)
