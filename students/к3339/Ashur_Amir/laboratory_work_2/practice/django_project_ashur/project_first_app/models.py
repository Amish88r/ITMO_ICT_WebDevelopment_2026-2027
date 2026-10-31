from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models


class CarOwner(AbstractUser):
    """Автовладелец (практика 2.1) — расширен до пользователя (практика 2.3)."""
    birth_date = models.DateField('Дата рождения', null=True, blank=True)
    passport_number = models.CharField('Номер паспорта', max_length=20, blank=True)
    home_address = models.CharField('Домашний адрес', max_length=255, blank=True)
    nationality = models.CharField('Национальность', max_length=50, blank=True)

    class Meta:
        verbose_name = 'Автовладелец'
        verbose_name_plural = 'Автовладельцы'

    def __str__(self):
        return f'{self.last_name} {self.first_name}'.strip() or self.username


class Car(models.Model):
    state_number = models.CharField('Гос. номер', max_length=15)
    brand = models.CharField('Марка', max_length=20)
    model_name = models.CharField('Модель', max_length=20)
    color = models.CharField('Цвет', max_length=30, null=True, blank=True)
    owners = models.ManyToManyField(settings.AUTH_USER_MODEL, through='Ownership',
                                    related_name='cars', verbose_name='Владельцы')

    class Meta:
        verbose_name = 'Автомобиль'
        verbose_name_plural = 'Автомобили'

    def __str__(self):
        return f'{self.brand} {self.model_name} ({self.state_number})'


class Ownership(models.Model):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                              related_name='ownerships', verbose_name='Владелец')
    car = models.ForeignKey(Car, on_delete=models.CASCADE, related_name='ownerships',
                            verbose_name='Автомобиль')
    start_date = models.DateField('Дата начала')
    end_date = models.DateField('Дата окончания', null=True, blank=True)

    class Meta:
        verbose_name = 'Владение'
        verbose_name_plural = 'Владения'

    def __str__(self):
        return f'{self.owner} — {self.car}'


class DriverLicense(models.Model):
    TYPES = (('A', 'A — мотоциклы'), ('B', 'B — легковые'), ('C', 'C — грузовые'),
             ('D', 'D — автобусы'), ('M', 'M — мопеды'))
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                              related_name='licenses', verbose_name='Владелец')
    number = models.CharField('Номер удостоверения', max_length=10)
    type = models.CharField('Тип', max_length=10, choices=TYPES)
    issue_date = models.DateField('Дата выдачи')

    class Meta:
        verbose_name = 'Водительское удостоверение'
        verbose_name_plural = 'Водительские удостоверения'

    def __str__(self):
        return f'{self.number} ({self.type})'
