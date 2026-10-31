"""Группа «Преподаватели» с правами, достаточными для работы в Django Admin."""
from django.contrib.auth.management import create_permissions
from django.db import migrations

TEACHER_PERMS = {
    'homework': ('add', 'change', 'delete', 'view'),
    'submission': ('change', 'view'),
    'subject': ('add', 'change', 'view'),
    'studygroup': ('view',),
    'user': ('view',),
}


def forwards(apps, schema_editor):
    # права создаются после миграций, поэтому создаём их явно
    for app_config in apps.get_app_configs():
        app_config.models_module = True
        create_permissions(app_config, apps=apps, verbosity=0)
        app_config.models_module = None
    Group = apps.get_model('auth', 'Group')
    Permission = apps.get_model('auth', 'Permission')
    group, _ = Group.objects.get_or_create(name='Преподаватели')
    codenames = [f'{a}_{m}' for m, actions in TEACHER_PERMS.items() for a in actions]
    group.permissions.set(Permission.objects.filter(content_type__app_label='board', codename__in=codenames))


def backwards(apps, schema_editor):
    apps.get_model('auth', 'Group').objects.filter(name='Преподаватели').delete()


class Migration(migrations.Migration):
    dependencies = [('board', '0001_initial'), ('auth', '0012_alter_user_first_name_max_length')]
    operations = [migrations.RunPython(forwards, backwards)]
