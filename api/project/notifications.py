from django.core.mail import send_mail
from django.conf import settings
#from channels.layers import get_channel_layer
#from asgiref.sync import async_to_sync
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.contrib.sites.shortcuts import get_current_site
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
#from channels.layers import get_channel_layer
#from asgiref.sync import async_to_sync
import logging
logger = logging.getLogger(__name__)
DEFAULT_SENDER_EMAIL = "noreply.erp@unimrkt.com"

def send_notification(user, message, subject, email=None, action_url=None,project_sample=None, project_id=None,notification_type=None):
    """
    Utility to send in-app notifications and email.
    """
    # Create in-app notification
    from .models import Notification
    if user and project_id and project_sample:
        notification = Notification.objects.create(
            user=user,
            message=message,
            subject=subject,
            action_url=action_url,
              project_sample=project_sample,  # Store the related ProjectSample
              project = project_id,
              notification_type=notification_type
        
        )
        #channel_layer = get_channel_layer()
        #group_name = f"user_{user.id}"

        #async_to_sync(channel_layer.group_send)(
        #    group_name,
        #    {
        #        'type': 'send_notification',
        #        'data': {
        #            'message': message,
        #            'subject': subject,
        #            'notification_id': notification.id,  # Optionally send notification ID
        #            'action_url': action_url
        #        }
        #    }
        #)
        #print("Notification sent to group:", group_name)

    # Send email if an email address is provided
    if email:
        send_mail(
            subject=subject,
            message=f"{message} \n\nAction Required: {action_url if action_url else 'N/A'}",
            from_email="noreply.erp@unimrkt.com",
            recipient_list=[email],
        )


def mark_notification_as_approved(notification_id):
    """
    Marks a notification as approved and updates the database.
    """
    from .models import Notification
    try:
        notification = Notification.objects.get(id=notification_id)
        notification.is_approved = True
        notification.save(update_fields=["is_approved"])
        print(f"Notification {notification_id} marked as approved.")
    except Notification.DoesNotExist:
        print(f"Notification {notification_id} does not exist.")
        return False
    return True


def send_approval_notification(project_sample):
    """
    Sends a notification to the assigned user when a sample edit request is created.
    """
    assign_by_user = project_sample.project.assigned_to
    if assign_by_user:
        message = f"New sample edit request for project {project_sample.project.name}."
        subject = f"Sample Edit Request for {project_sample.project.name}"
        action_url = f"https://{settings.DOMAIN}/projects/samples/{project_sample.id}/approve"  # Example URL
        send_notification(
            user=assign_by_user,
            message=message,
            subject=subject,
            action_url=action_url,
            project_sample=project_sample,  # Pass project_sample to the notification
        )



def send_invoice_notification(user, project):
    """
    Sends a notification when an invoice is generated.
    """
    message = f"Invoice generated successfully against project {project}."
    subject = f"Invoice Generated: {project}"
    action_url = f"https://{settings.DOMAIN}/projects/{project.id}/invoices"

    send_mail(
       
        message=message,
        subject=subject,
        from_email=DEFAULT_SENDER_EMAIL,
        recipient_list=['pramod.kumar@novusinsights.com',],
    )        
