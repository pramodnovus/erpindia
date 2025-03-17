# # In signals.py
# from django.db.models.signals import post_save
# from django.dispatch import receiver
# from .models import CustomUser, TeamLead, Manager, Hod, Director
# from django.db import transaction

# @receiver(post_save, sender=CustomUser)
# def update_master_data(sender, instance, created, **kwargs):
#     if instance.user_role:
#         role_name = instance.user_role.name
#         with transaction.atomic():
#             if role_name == 'Team Lead':
#                 teamlead_obj, created = TeamLead.objects.get_or_create(
#                     name = instance.username,
#                     email=instance.email,
#                     defaults={'teamlead_dep': instance.user_department}
#                 )
#                 if not created:
#                     teamlead_obj.name = instance.username if instance.username else ""
#                     teamlead_obj.teamlead_dep = instance.user_department
#                     teamlead_obj.save()
#             elif role_name == 'AM/Manager':
#                 manager_obj, created = Manager.objects.get_or_create(
#                     name = instance.username,
#                     email=instance.email,
#                     defaults={'manager_dep': instance.user_department}
#                 )
#                 if not created:
#                     manager_obj.name = instance.username if instance.username else ""
#                     manager_obj.manager_dep = instance.user_department
#                     manager_obj.save()
#             elif role_name == 'HOD':
#                 hod_obj, created = Hod.objects.get_or_create(
#                     name = instance.username,
#                     email=instance.email,
#                     defaults={'hod_dep': instance.user_department}
#                 )
#                 if not created:
#                     hod_obj.name = instance.username if instance.username else ""
#                     hod_obj.hod_dep = instance.user_department
#                     hod_obj.save()
#             elif role_name == 'Director':
#                 director_obj, created = Director.objects.get_or_create(
#                     name = instance.username,
#                     email=instance.email,
#                     defaults={'director_dep': instance.user_department}
#                 )
#                 if not created:
#                     director_obj.name = instance.username if instance.username else "None"
#                     director_obj.director_dep = instance.user_department
#                     director_obj.save()
#     else:
#         pass
