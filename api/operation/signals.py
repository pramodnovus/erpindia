from django.db.models.signals import post_save,post_delete
from django.dispatch import receiver
from .models import *
from api.project.models import Project
from django.db.models import Sum
from datetime import timedelta
from django.db.models.functions import Cast
from django.db.models import IntegerField, FloatField
from django.db.models import F, Value
import logging
from rest_framework import status

# Set up logging
logger = logging.getLogger(__name__)

# Global flags to control signal handling
updating_project = False

@receiver(post_save, sender=ProjectUpdate)
def update_project_instance(sender, instance, created, **kwargs):
    project_id = instance.project_id.id
    logger.info(f"Project ID received: {project_id}")
    update_project(project_id)

def update_project(project_id):
    global updating_project
    updating_project = True

    try:
        project_instance = Project.objects.filter(id=project_id).first()
        if not project_instance:
            logger.error(f"Project with id {project_id} not found.")
            return

        # Check if the fields exist in ProjectUpdate
        project_update_fields = [field.name for field in ProjectUpdate._meta.get_fields()]
        if 'total_man_days' not in project_update_fields or 'total_achievement' not in project_update_fields:
            logger.error(f"Fields total_man_days or total_achievement not found in ProjectUpdate model.")
            return

        aggregation_result = ProjectUpdate.objects.filter(project_id=project_id).aggregate(
            total_man_days=Sum(Cast('total_man_days', FloatField())),
            total_achievement=Sum(Cast('total_achievement', FloatField()))  # Assuming total_achievement needs to be summed as float
        )
        total_man_days = aggregation_result['total_man_days'] or 0
        total_achievement = aggregation_result['total_achievement'] or 0
        logger.info(f"Total man days: {total_man_days}, Total achievement: {total_achievement}")

        project_instance.man_days = total_man_days
        project_instance.total_achievement = total_achievement

        last_operation_team = ProjectUpdate.objects.filter(project_id=project_id).last()
        logger.info(f"Last operation team: {last_operation_team}")

        if last_operation_team:
            remaining_interview = last_operation_team.remaining_interview
            remaining_interview = int(remaining_interview) if remaining_interview is not None else 0

            if remaining_interview < 0:
                logger.warning(
                    f"Remaining interviews is negative ({remaining_interview}). Updating it to 0 and marking as 'Completed'."
                )
                #last_operation_team.remaining_interview = 0
                #last_operation_team.status = 'Completed'
                #last_operation_team.save(update_fields=['remaining_interview', 'status'])

                #project_instance.status = 'Completed'
                raise ValueError("Interviews completed. Cannot create another entry.")
            else:
                project_instance.remaining_interview = remaining_interview
                project_instance.remaining_time = last_operation_team.remaining_time
                project_instance.status = last_operation_team.status

                #if remaining_interview == 0:
                #    project_instance.status = 'Completed'

        project_instance.save()
    except Exception as e:
        logger.error(f"An error occurred while updating project: {e}")
        raise
    finally:
        updating_project = False



