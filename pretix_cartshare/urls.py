from django.conf.urls import url

from .views import CartShareCreateView, CartShareListView

urlpatterns = [
    url(r'^control/event/(?P<organizer>[^/]+)/(?P<event>[^/]+)/cartshare/$',
        CartShareListView.as_view(), name='list'),
    url(r'^control/event/(?P<organizer>[^/]+)/(?P<event>[^/]+)/cartshare/create/$',
        CartShareCreateView.as_view(), name='create'),
]
