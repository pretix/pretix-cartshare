from django import forms
from django.forms import BaseFormSet, formset_factory
from django.utils.translation import ugettext_lazy as _
from pretix_cartshare.models import SharedCart


class SharedCartForm(forms.ModelForm):
    class Meta:
        model = SharedCart
        fields = [
            'expires'
        ]


class CartPositionForm(forms.Form):
    count = forms.IntegerField(
        label=_("Count"),
        initial=1
    )
    itemvar = forms.ChoiceField(
        label=_("Product")
    )
    price = forms.DecimalField(
        required=False,
        max_digits=10, decimal_places=2,
        label=_('Price per item (empty for default)'),

    )

    def __init__(self, *args, event=None, **kwargs):
        super().__init__(*args, **kwargs)
        choices = []
        for i in event.items.prefetch_related('variations').filter(active=True):
            pname = i.name
            variations = list(i.variations.all())
            if variations:
                for v in variations:
                    if v.active:
                        choices.append(('%d-%d' % (i.pk, v.pk), '%s – %s' % (pname, v.value)))
            else:
                choices.append((str(i.pk), pname))
        self.fields['itemvar'].choices = choices


class FormSet(BaseFormSet):
    """
    This is equivalent to a normal BaseModelFormset, but cares for the special needs
    of I18nForms (see there for more information).
    """

    def __init__(self, *args, **kwargs):
        self.event = kwargs.pop('event', None)
        super().__init__(*args, **kwargs)

    def _construct_form(self, i, **kwargs):
        kwargs['event'] = self.event
        return super()._construct_form(i, **kwargs)

    @property
    def empty_form(self):
        form = self.form(
            auto_id=self.auto_id,
            prefix=self.add_prefix('__prefix__'),
            empty_permitted=True,
            event=self.event
        )
        self.add_fields(form, None)
        return form


CartPositionFormSet = formset_factory(CartPositionForm, formset=FormSet, extra=1, can_order=False, can_delete=True)
