from django.db.models import Q
from django.utils.timezone import now
from django.views.generic import FormView, ListView
from pretix.control.permissions import EventPermissionRequiredMixin

from .models import SharedCart


class CartShareListView(EventPermissionRequiredMixin, ListView):
    model = SharedCart
    context_object_name = 'cart'
    paginate_by = 25
    template_name = 'pretixplugins/cartshare/list.html'
    permission = 'can_change_orders'

    def get_queryset(self):
        qs = SharedCart.objects.filter(event=self.request.event, expires__gte=now())
        return qs


class CartShareCreateView(EventPermissionRequiredMixin, FormView):
    # form_class =
    template_name = 'pretixplugins/cartshare/create.html'
    permission = 'can_change_orders'

    def form_valid(self, form):
        pass
