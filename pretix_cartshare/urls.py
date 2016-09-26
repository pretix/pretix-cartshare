from django.conf.urls import url

from .views import (
    CartShareCreateView, CartShareDeleteView, CartShareListView, RedeemView,
)

urlpatterns = [
    url(r'^control/event/(?P<organizer>[^/]+)/(?P<event>[^/]+)/cartshare/$',
        CartShareListView.as_view(), name='list'),
    url(r'^control/event/(?P<organizer>[^/]+)/(?P<event>[^/]+)/cartshare/create/$',
        CartShareCreateView.as_view(), name='create'),
    url(r'^control/event/(?P<organizer>[^/]+)/(?P<event>[^/]+)/cartshare/(?P<id>[^/]+)/delete$',
        CartShareDeleteView.as_view(), name='delete'),
]

event_patterns = [
    url(r'^sharedcart/(?P<id>[^/]+)/', RedeemView.as_view(), name='redeem'),
]
