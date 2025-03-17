# tasks.py
from celery import shared_task
from datetime import timedelta
from django.utils import timezone
from .models import Project

from django.core.cache import cache
from datetime import date

@shared_task(bind=True)
def update_estimated_time_task(self):
    # Check if the task has already run today
    last_run_date = cache.get('last_run_date')
    if last_run_date == date.today():
        print("Task already ran today. Skipping.")
        return "Task already ran today. Skipping."

    try:
        """
        Retrieves all Project objects from the database.
        """
        projects = Project.objects.all()
        for project in projects:
            if project.tentative_start_date and project.tentative_end_date:
                current_date = timezone.now().date()
                end_date = project.tentative_end_date.date()
                days_difference = (end_date - current_date).days
                print('days_difference',days_difference)
                project.estimated_time = max(timedelta(days=days_difference), timedelta(0))
                project.save()
    except Project.DoesNotExist:
        print(f"Project with ID {project} does not exist.")
        return f"Project with ID {project} does not exist."

    # Update the last run date to today
    cache.set('last_run_date', date.today())

    return f"Estimated time updated for project."


