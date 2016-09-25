from collections import Counter
from datetime import timedelta

from django.contrib import messages
from django.core.urlresolvers import reverse
from django.db import transaction
from django.utils.functional import cached_property
from django.utils.timezone import now
from django.utils.translation import ugettext_lazy as _
from django.views.generic import ListView, FormView
from pretix.base.models import CartPosition
from pretix.base.models import Item
from pretix.base.models import ItemVariation
from pretix.base.models import Quota
from pretix.base.services.cart import CartError
from pretix.control.permissions import EventPermissionRequiredMixin

from pretix_cartshare.forms import SharedCartForm, CartPositionFormSet
from .models import SharedCart


class CartShareListView(EventPermissionRequiredMixin, ListView):
    model = SharedCart
    context_object_name = 'carts'
    paginate_by = 25
    template_name = 'pretixplugins/cartshare/list.html'
    permission = 'can_change_orders'

    def get_queryset(self):
        qs = SharedCart.objects.filter(event=self.request.event, expires__gte=now())
        return qs


class CartShareCreateView(EventPermissionRequiredMixin, FormView):
    template_name = 'pretixplugins/cartshare/create.html'
    permission = 'can_change_orders'
    form_class = SharedCartForm
    error_messages = {
        'quota': _('The quota {name} does not have enough capacity left to perform the operation.'),
    }

    def get_success_url(self):
        return reverse('plugins:pretix_cartshare:list', kwargs={
            'event': self.request.event.slug,
            'organizer': self.request.organizer.slug,
        })

    def get_initial(self):
        initial = super().get_initial()
        initial['expires'] = now() + timedelta(days=14)
        return initial

    @cached_property
    def formset(self):
        return CartPositionFormSet(self.request.POST if self.request.method == "POST" else None,
                                   event=self.request.event)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data()
        ctx['formset'] = self.formset
        return ctx

    @transaction.atomic
    def form_valid(self, form):
        if not self.formset.is_valid():
            messages.error(self.request, _('Your input was invalid'))
            return self.get(self.request, *self.args, **self.kwargs)


        try:
            self.create_cart(form.instance, form.cleaned_data['expires'])
        except CartError as e:
            messages.error(self.request, str(e))
            return super().get(self.request, *self.args, **self.kwargs)
        else:
            messages.success(self.request, _('The cart has been saved.'))
            return super().form_valid(form)

    def create_cart(self, sc, expires):
        with transaction.atomic():
            with self.request.event.lock():
                positions = []
                quotas = Counter()

                for form in self.formset.forms:
                    if '-' in form.cleaned_data['itemvar']:
                        itemid, varid = form.cleaned_data['itemvar'].split('-')
                    else:
                        itemid, varid = form.cleaned_data['itemvar'], None

                    item = Item.objects.get(pk=itemid, event=self.request.event)
                    variation = ItemVariation.objects.get(pk=varid, item=item) if varid else None
                    price = form.cleaned_data['price']
                    if not price:
                        price = (variation.default_price if variation and variation.default_price is not None
                                 else item.default_price)

                    for quota in item.quotas.all():
                        quotas[quota] += form.cleaned_data['count']

                    for i in range(form.cleaned_data['count']):
                        positions.append(CartPosition(
                            item=item, variation=variation, event=self.request.event, cart_id=sc.cart_id,
                            expires=expires, price=price
                        ))

                for quota, diff in quotas.items():
                    avail = quota.availability()
                    if avail[0] != Quota.AVAILABILITY_OK or avail[1] < diff:
                        raise CartError(self.error_messages['quota'].format(name=quota.name))

                sc.expires = expires
                sc.event = self.request.event
                sc.total = sum([p.price for p in positions])
                sc.save()
                CartPosition.objects.bulk_create(positions)
