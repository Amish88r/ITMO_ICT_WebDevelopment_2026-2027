from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Car, CarOwner, DriverLicense, Ownership


class OwnershipInline(admin.TabularInline):
    model = Ownership
    extra = 1


class LicenseInline(admin.TabularInline):
    model = DriverLicense
    extra = 0


@admin.register(CarOwner)
class CarOwnerAdmin(UserAdmin):
    # новые поля пользователя отображаются в Django Admin (практика 2.3)
    fieldsets = UserAdmin.fieldsets + (
        ('Данные автовладельца', {'fields': ('birth_date', 'passport_number',
                                             'home_address', 'nationality')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Данные автовладельца', {'fields': ('first_name', 'last_name', 'birth_date',
                                             'passport_number', 'home_address', 'nationality')}),
    )
    list_display = ('username', 'last_name', 'first_name', 'passport_number', 'nationality')
    inlines = [OwnershipInline, LicenseInline]


@admin.register(Car)
class CarAdmin(admin.ModelAdmin):
    list_display = ('state_number', 'brand', 'model_name', 'color')
    inlines = [OwnershipInline]


admin.site.register(Ownership)
admin.site.register(DriverLicense)
