from django.contrib import admin

# Register your models here.
from django.contrib import admin

from .models import Profile, Stuff, Exchange


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('id', 'external_id', 'username', 'first_name',
                    'last_name', 'contact')


@admin.register(Stuff)
class StuffAdmin(admin.ModelAdmin):
    list_display = ('description', 'profile', 'image_url')


@admin.register(Exchange)
class ExchangeAdmin(admin.ModelAdmin):
    list_display = ('first_user_id', 'second_user_id', 'first_stuff_descr',
                    'second_stuff_descr', 'created',)
