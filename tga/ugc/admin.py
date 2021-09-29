from django.contrib import admin

# Register your models here.
from django.contrib import admin

from .models import Profile, Stuff

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('id', 'external_id', 'username', 'first_name',
        'last_name', 'contact')

@admin.register(Stuff)
class StuffAdmin(admin.ModelAdmin):
    list_display = ('description', 'profile', 'image_url')