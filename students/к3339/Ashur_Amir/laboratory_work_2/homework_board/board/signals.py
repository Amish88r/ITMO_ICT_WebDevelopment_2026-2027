from django.contrib.auth.models import Group
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import User

TEACHERS_GROUP = 'Преподаватели'


@receiver(post_save, sender=User)
def sync_teacher_group(sender, instance, **kwargs):
    """Пользователь с is_staff автоматически получает права преподавателя (и теряет их без is_staff)."""
    group = Group.objects.filter(name=TEACHERS_GROUP).first()
    if group is None:
        return
    if instance.is_staff:
        instance.groups.add(group)
    else:
        instance.groups.remove(group)
