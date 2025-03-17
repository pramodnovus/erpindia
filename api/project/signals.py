from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from api.project.tasks import update_estimated_time_task
from .models import *
from django.db import IntegrityError
from django.utils import timezone
from datetime import timedelta
from django.utils.timezone import now, timedelta
from django.db.models import Sum
from django.utils.text import slugify
from django.db import transaction
from django.db.models.functions import Cast
from django.db.models import IntegerField, FloatField
from django.db.models import F, Value
from django.core.exceptions import ValidationError
from datetime import datetime
import logging
from api.operation.models import *
logger = logging.getLogger(__name__)

updating_project_update = False


@receiver(post_save, sender=Client)
def create_project_code(sender, instance, created, **kwargs):
    if created:  # Only execute when a new Client instance is created
        
        # Generate project code pattern using client instance ID prefix, client name, and a suffix in ascending order
        #client_prefix = str(instance.pk).zfill(3)  # Pad client instance ID with leading zeros
        client_prefix = str(datetime.now().year)[-2:]  # Extract last two digits of the year
        client_name_medium = instance.name[:3].lower()  # First three characters of client name in lowercase
        
        suffix = str(instance.pk + 1).zfill(3)  # Generate suffix in ascending order
        
        # Construct the project code using the pattern
        project_code = f"{client_prefix}{client_name_medium}{suffix}"
        
        # Update the Client instance with the generated project code
        instance.project_code = project_code
        instance.save()
        
###################  signal change ##########################        
#@receiver(post_save, sender=Project)
#def update_project_code(sender, instance, created, **kwargs):
#    if created:
#        try:
#            # Ensure this operation is within a transaction
#            with transaction.atomic():
#                project_code = instance.clients.project_code
#                new_project_code = project_code

                # Check if the project code exists in the Project table
#                while Project.objects.filter(project_code=new_project_code).exists():
                    # Extract the last three digits of the project code
#                    last_three_digits = int(new_project_code[-3:])
                    # Increment the last three digits by 1
#                    new_suffix = last_three_digits + 1
                    # Form the new project code by replacing the last three digits
#                    new_project_code = project_code[:-3] + str(new_suffix).zfill(3)

                # Update the project code and initial sample size
#                Project.objects.filter(id=instance.id).update(project_code=new_project_code, initial_sample_size=instance.sample)
#        except Exception as e:
#            print(f'Error: {e}')



@receiver(post_save, sender=Project)
def update_project_code(sender, instance, created, **kwargs):
    if created:
        try:
            with transaction.atomic():
                project_code = instance.clients.project_code
                new_project_code = project_code
                print('New project code generation in progress:', new_project_code)

                # Check for existing project codes and adjust the suffix
                while Project.objects.filter(project_code=new_project_code).exists():
                    last_three_digits = int(new_project_code[-3:])
                    new_suffix = last_three_digits + 1
                    new_project_code = project_code[:-3] + str(new_suffix).zfill(3)

                # Update instance fields
                instance.project_code = new_project_code
                instance.initial_sample_size = instance.sample
                instance.save(update_fields=['project_code', 'initial_sample_size'])

                print(f"Updated Project Code: {instance.project_code}")
        except Exception as e:
            print(f"Error updating project code: {e}")



##################################################################################
                
            

@receiver(post_save, sender=Project)
def update_related_fields(sender, instance, **kwargs):
    global updating_project_update
    if kwargs.get('raw', False) or updating_project_update:
        return

    updating_project_update = True

    try:
        project_update_objects = ProjectUpdate.objects.filter(project_id=instance)
        
        if project_update_objects.exists():
            first_project_update = project_update_objects.first()

            if instance.sample:
                sample_increment = int(instance.sample) - (int(first_project_update.remaining_interview) + int(first_project_update.total_achievement))
                for project_update in project_update_objects:
                    project_update.remaining_interview = int(project_update.remaining_interview) + sample_increment
                    project_update.save(update_fields=['remaining_interview'])

            last_project_update = project_update_objects.last()
            instance.remaining_interview = int(last_project_update.remaining_interview)

            aggregation_result = project_update_objects.aggregate(
                total_man_days=Sum(Cast('total_man_days', FloatField())),
                total_achievement=Sum(Cast('total_achievement', IntegerField()))
            )

            # Update instance fields
            instance.man_days = aggregation_result['total_man_days'] or 0
            instance.total_achievement = aggregation_result['total_achievement'] or 0

            # Save only the necessary fields
            instance.save(update_fields=['remaining_interview', 'man_days', 'total_achievement'])

    except Exception as e:
        logger.error(f"An error occurred while updating project update: {e}")

    finally:
        updating_project_update = False
        

#@receiver(pre_save, sender=Project)
#def update_project_update_end_date(sender, instance, **kwargs):
#    try:
#        # Check if this is an update and not a creation
#        if instance.pk:
#            old_instance = Project.objects.get(pk=instance.pk)
#            print('old_instance', old_instance)
#
#            if instance.tentative_start_date > instance.tentative_end_date:
#                raise ValidationError("Project Start Date must be less than or equal to Project End Date!")
#            # Check if the tentative_end_date has changed
#            if old_instance.tentative_end_date != instance.tentative_end_date:
#                # Calculate the difference in tentative_end_date
#                date_difference = instance.tentative_end_date - old_instance.tentative_end_date
#                print("date_difference", date_difference, type(date_difference))
#                print("instance.tentative_end_date", instance.tentative_end_date)
##
#                # Round or truncate the timedelta to avoid high precision
#                date_difference = timedelta(days=date_difference.days, seconds=date_difference.seconds)
#                print('##########3')
#
#                # Update all related ProjectUpdate objects
#                project_updates = ProjectUpdate.objects.filter(project_id=instance.id)
#                for project_update in project_updates:
#                    # Update remaining_time by adding the difference
#                    if project_update.remaining_time is not None:
#                        project_update.remaining_time += date_difference
#                    else:
#                        project_update.remaining_time = date_difference
#                    project_update.save()
                    
           
                
#    except Project.DoesNotExist:
#        pass  # If the project does not exist, it is being created, so no need to update ProjectUpdate here



####################################################### Project Real time Cache ############################################
# signals.py
import logging
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.cache import cache
from .models import Project

logger = logging.getLogger(__name__)

@receiver(post_save, sender=Project)
@receiver(post_delete, sender=Project)
def invalidate_project_cache(sender, instance, **kwargs):
    try:
        # Check if the project is being deactivated or deleted
        if not instance.is_active or kwargs.get('created', False) == False:
            cache.delete_pattern('projects_*')
            logger.info(f"Cache invalidated for projects due to update on Project ID: {instance.id}")
    except Exception as e:
        # Log any exceptions that occur during signal processing
        logger.error(f"Error invalidating project cache for Project ID: {instance.id}. Error: {str(e)}")

# Signal for cache invalidation on save (modification)
@receiver(post_save, sender=Project)
def invalidate_project_cache_on_save(sender, instance, **kwargs):
    try:
        # Invalidate cache when a project is modified
        if instance.pk and not kwargs.get('created', False):  # Not a new instance, so it's an update
            cache.delete_pattern('projects_*')
            logger.info(f"Cache invalidated for projects due to UPDATE of Project ID: {instance.id}")
    except Exception as e:
        logger.error(f"Error invalidating project cache for Project ID: {instance.id}. Error: {str(e)}")
###################################################### Notification On Request Creation #######################################

from .notifications import send_approval_notification,mark_notification_as_approved

from django.db.models import Sum, F

 
@receiver(post_save, sender=ProjectSample)
def handle_sample_edit_request(sender, instance, created, **kwargs):
    if not created:
        send_approval_notification(instance)
 
 
@receiver(post_save, sender=ProjectSample)
def handle_sample_changes(sender, instance, **kwargs):
    """
    Handle approvals, rejections, and updates for project samples, and update notifications.
    """
    if instance.is_approved:
        # Update notifications as approved
        Notification.objects.filter(
            project_sample=instance, user=instance.project.assigned_to
        ).update(is_approved=True)
 
    elif instance.is_rejected:
        # Update notifications as rejected
        Notification.objects.filter(
            project_sample=instance, user=instance.project.assigned_to
        ).update(is_rejected=True)
 
 
 
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from .models import ProjectSample, Project
 
@receiver(post_save, sender=ProjectSample)
def update_project_based_on_samples(sender, instance, created, **kwargs):
    """
    Update the associated project based on changes in ProjectSample.
    """
    if not created:
        project = instance.project

        # Ensure a project is associated with the sample
        if not project:
            return

        # Fetch all approved samples for the project
        approved_samples = ProjectSample.objects.filter(project=project, is_approved=True)
        # Get the total sum of the sample field for all samples in the project
        without_approved_sample = ProjectSample.objects.filter(project=project)
        ws = 0
        for dm in without_approved_sample:
            try:
                ws += int(dm.sample)
            except ValueError:
                print(f"Invalid sample value: {dm.sample}")
        retain_sample = ws

        if approved_samples:
            # Update the total sample count in the project
            total_sample_count = sum(
                [int(sample.sample or retain_sample) for sample in approved_samples]
            )
            print(total_sample_count,"test total sample")
            
        else:
            total_sample_count = retain_sample

        project.sample = str(total_sample_count)

        # Update tentative_end_date to the latest date among all approved samples
        latest_date = max(
            (sample.date for sample in approved_samples if sample.date), default=None
        )

        if latest_date:
            project.tentative_end_date = latest_date

        # Save the updated project
        project.save()



 
 
@receiver(pre_save, sender=ProjectSample)
def handle_date_change(sender, instance, **kwargs):
    """
    Track changes in the `date` field of ProjectSample and update the associated project.
    """
    # Only proceed if the instance exists in the database (not a new record)
    if not instance.pk:
        return
 
    # Get the previous state of the instance
    previous_instance = ProjectSample.objects.get(pk=instance.pk)
    Project.objects.filter(id=instance.pk).update(sample=previous_instance.sample) 
    # Check if the `date` has changed
    if previous_instance.date != instance.date:
        # Update the associated project's tentative_end_date if necessary
        project = instance.project
        if project:
            approved_samples = ProjectSample.objects.filter(project=project, is_approved=True)
            latest_date = max(
                [sample.date for sample in approved_samples if sample.date], default=None
            )
            if latest_date:
                project.tentative_end_date = latest_date
                project.save()
