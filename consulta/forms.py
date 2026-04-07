from datetime import timedelta

from django import forms
from django.utils import timezone


class PeriodoConsultaForm(forms.Form):
    data_inicio = forms.DateField(
        label='Data de início',
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        initial=lambda: (timezone.now() - timedelta(days=7)).date()
    )

    data_fim = forms.DateField(
        label='Data de fim',
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        initial=lambda: timezone.now().date()
    )

    def clean(self):
        cleaned_data = super().clean()
        data_inicio = cleaned_data.get('data_inicio')
        data_fim = cleaned_data.get('data_fim')

        if data_inicio and data_fim and data_inicio > data_fim:
            raise forms.ValidationError('A data de início deve ser anterior à data de fim.')

        return cleaned_data
