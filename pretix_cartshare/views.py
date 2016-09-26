from collections import Counter
from datetime import timedelta

from django.contrib import messages
from django.core.urlresolvers import reverse
from django.db import transaction
from django.http import Http404, HttpResponseRedirect
from django.shortcuts import redirect
from django.utils.decorators import method_decorator
from django.utils.functional import cached_property
from django.utils.timezone import now
from django.utils.translation import ugettext_lazy as _
from django.views.generic import DeleteView, FormView, ListView, TemplateView
from pretix.base.models import CartPosition, Item, ItemVariation, Quota
from pretix.base.services.cart import CartError
from pretix.control.permissions import EventPermissionRequiredMixin
from pretix.multidomain.urlreverse import build_absolute_uri, eventreverse
from pretix.presale.utils import event_view
from pretix.presale.views import CartMixin

from .forms import CartPositionFormSet, SharedCartForm
from .models import SharedCart


class CartShareListView(EventPermissionRequiredMixin, ListView):
    model = SharedCart
    context_object_name = 'carts'
    paginate_by = 25
    template_name = 'pretixplugins/cartshare/list.html'
    permission = 'can_change_orders'

    def get_queryset(self):
        qs = SharedCart.objects.filter(event=self.request.event, expires__gte=now()).order_by('-datetime')
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
            url = build_absolute_uri(self.request.event, 'plugins:pretix_cartshare:redeem', kwargs={
                'id': form.instance.cart_id
            })
            messages.success(self.request, _('The cart has been saved. You can now share the following URL: '
                                             '{url}').format(url=url))
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
                    if avail[0] != Quota.AVAILABILITY_OK or (avail[1] is not None and avail[1] < diff):
                        raise CartError(self.error_messages['quota'].format(name=quota.name))

                sc.expires = expires
                sc.event = self.request.event
                sc.total = sum([p.price for p in positions])
                sc.save()
                CartPosition.objects.bulk_create(positions)


class CartShareDeleteView(EventPermissionRequiredMixin, DeleteView):
    model = SharedCart
    template_name = 'pretixplugins/cartshare/delete.html'
    permission = 'can_change_orders'
    context_object_name = 'cart'

    def get_object(self, queryset=None) -> SharedCart:
        try:
            return SharedCart.objects.get(
                event=self.request.event,
                cart_id=self.kwargs['id']
            )
        except SharedCart.DoesNotExist:
            raise Http404(_("The requested shared cart does not exist."))

    @transaction.atomic
    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        success_url = self.get_success_url()
        self.object.positions.delete()
        self.object.delete()
        messages.success(request, _('The selected cart has been deleted.'))
        return HttpResponseRedirect(success_url)

    def get_success_url(self):
        return reverse('plugins:pretix_cartshare:list', kwargs={
            'event': self.request.event.slug,
            'organizer': self.request.organizer.slug,
        })


@method_decorator(event_view, name='dispatch')
class RedeemView(CartMixin, TemplateView):
    template_name = 'pretixplugins/cartshare/redeem.html'

    @cached_property
    def object(self):
        try:
            return SharedCart.objects.get(
                event=self.request.event,
                cart_id=self.kwargs['id'],
                expires__gte=now()
            )
        except SharedCart.DoesNotExist:
            raise Http404()

    def get_cart(self, answers=False, queryset=None, payment_fee=None, payment_fee_tax_rate=None):
        queryset = self.object.positions
        return super().get_cart(answers, queryset, 0, 0)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data()
        ctx['event'] = self.request.event
        ctx['cart'] = self.get_cart()
        return ctx

    def post(self, request, *args, **kwargs):
        now_dt = now()
        expiry = now_dt + timedelta(minutes=request.event.settings.get('reservation_time', as_type=int))
        with transaction.atomic():
            self.object.positions.update(expires=expiry, cart_id=request.session.session_key)
            self.object.delete()
        return redirect(eventreverse(request.event, 'presale:event.checkout.start'))
