from django import forms
from django.contrib.auth.forms import UserCreationForm

from .models import Car, CarOwner


class CarOwnerForm(UserCreationForm):
    """Создание пользователя-автовладельца с новыми атрибутами (практики 2.2 и 2.3)."""
    class Meta:
        model = CarOwner
        fields = ('username', 'first_name', 'last_name', 'birth_date',
                  'passport_number', 'home_address', 'nationality')
        widgets = {'birth_date': forms.DateInput(attrs={'type': 'date'})}


class CarForm(forms.ModelForm):
    class Meta:
        model = Car
        fields = ('state_number', 'brand', 'model_name', 'color')
