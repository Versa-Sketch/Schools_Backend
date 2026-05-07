from django.db.models.signals import post_save
from django.dispatch import receiver


@receiver(post_save, sender='core.School')
def create_school_configuration(sender, instance, created, **kwargs):
    if created:
        from core.models import SchoolConfiguration
        SchoolConfiguration.objects.get_or_create(school=instance)
