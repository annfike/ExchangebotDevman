from django.db import models

# Create your models here.
class Profile(models.Model):
    external_id = models.PositiveIntegerField(
        verbose_name='ID пользователя в Телеграме',
        unique=True,
    )

    username = models.CharField('Имя пользователя в Телеграме',
                                   max_length=50, blank=True, default='')
    first_name = models.CharField('Имя',
                                  max_length=256, blank=True, default='')
    last_name = models.CharField('Фамилия',
                                 max_length=256, blank=True, default='')
    contact = models.CharField('Контакт для связи', max_length=256,
                               blank=True, default='')

    lat = models.FloatField('Широта', blank=True, null=True)
    lon = models.FloatField('Долгота', blank=True, null=True)
    )

    def __str__(self):
        return f'{self.first_name} ({self.external_id})'

    class Meta:
        verbose_name = 'Профиль'
        verbose_name_plural = 'Профили'


class Stuff(models.Model):
    profile = models.ForeignKey(
        to='Profile',
        verbose_name='Профиль',
        on_delete=models.CASCADE,
    )
    description = models.CharField(max_length=256)

    image_url = models.CharField(max_length=256)

    class Meta:
        verbose_name = 'Вещь'
        verbose_name_plural = 'Вещи'
