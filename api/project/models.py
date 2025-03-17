from django.db import models
from api.user.models import CustomUser
from django.core.exceptions import ValidationError
from datetime import date , datetime
from datetime import timedelta
from api.user.models import *
from django.core.mail import send_mail
from api.project.notifications import send_notification
from django.urls import reverse
from django.conf import settings

# Create your models here.


# CustomProjectManager Table
class CustomProjectManager(models.Manager):
    def create(self, validated_data):
        # Perform custom validation here
        if validated_data['tentative_end_date'] < date.today():
            raise ValidationError("Tentative end date cannot be in the past.")
        
        if self.duration and self.duration.total_seconds() <= 0:
            raise ValidationError({'duration': ['Duration must be greater than 0.']})

        return super().create(validated_data)
    
    
    
# Client Master Table
class Client(models.Model):
    name = models.CharField(max_length=100, unique=True)
    email = models.CharField(max_length=100,null=True,blank=True)
    contact_person_email = models.CharField(max_length=100,null=True,blank=True)
    project_code = models.CharField(max_length=50,null=True,blank=True, unique=True)
    address = models.CharField(max_length=100,null=True,blank=True)
    city = models.CharField(max_length=100,null=True,blank=True)
    country = models.CharField(max_length=100,null=True,blank=True)
    phone_number = models.CharField(max_length=15, null=True, blank=True)
    contact_person = models.CharField(max_length=100,null=True,blank=True)
    client_purchase_order_no = models.CharField(max_length=100,null=True,blank=True)
    email_id_for_cc = models.CharField(max_length=100,null=True,blank=True)
    additional_survey = models.CharField(max_length=100,null=True,blank=True)
    total_survey_to_be_billed_to_client = models.CharField(max_length=100,null=True,blank=True)
    other_specific_billing_instruction = models.CharField(max_length=255,null=True,blank=True)
    is_active = models.BooleanField(default=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name
    
    
class projectType(models.Model):
    name = models.CharField(max_length=50, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


    
# Project/Sales model
class Project(models.Model):
    project_id = models.CharField(max_length=100, null=True, blank=True)
    project_code = models.CharField(max_length=255, null=True, blank=True, unique=True)
    name = models.CharField(max_length=250)
    project_type = models.ForeignKey(projectType, on_delete=models.CASCADE, null=True, blank=True)
    initial_sample_size = models.CharField(max_length=50, null=True, blank=True)
    sample = models.CharField(max_length=50, null=True, blank=True)
    clients = models.ForeignKey(Client, on_delete=models.CASCADE, null=True, blank=True)
    cpi = models.CharField(max_length=50, null=True, blank=True)
    set_up_fee = models.IntegerField(null=True, blank=True)
    transaction_fee = models.IntegerField(null=True, blank=True)
    other_cost = models.CharField(max_length=50, null=True, blank=True)
    label_cost = models.JSONField(blank=True, null=True)
    operation_select = models.BooleanField(default=False)
    finance_select = models.BooleanField(default=False)
    upload_document = models.FileField(upload_to="File Upload", null=True, blank=True)
    tentative_start_date = models.DateTimeField(null=True, blank=True)
    tentative_end_date = models.DateTimeField(null=True, blank=True)
    estimated_time = models.DurationField(null=True, blank=True)
    remark = models.CharField(max_length=255, null=True, blank=True)
    man_days = models.FloatField(null=True, blank=True)
    reason_for_adjustment = models.TextField(null=True, blank=True, default=None)
    send_email_manager = models.BooleanField(default=False, blank=True)
    total_achievement = models.CharField(max_length=255, null=True, blank=True, default=None)
    remaining_time = models.DurationField(default=timedelta(), null=True, blank=True)
    remaining_interview = models.CharField(max_length=255, null=True, blank=True, default=None)
    project_client_pm = models.CharField(max_length=255, null=True, blank=True)
    purchase_order_no = models.CharField(max_length=150, null=True, blank=True)
    project_unimrkt_pm = models.CharField(max_length=255, null=True, blank=True)
    created_by = models.ForeignKey(UserRole, on_delete=models.CASCADE, related_name='created_projects')
    assigned_to = models.ForeignKey(UserRole, null=True, blank=True, on_delete=models.SET_NULL, related_name='assigned_projects')
    advance_billing_raised = models.BooleanField(default=False)
    status = models.CharField(max_length=20, choices=[
        ('Project Initiated', 'Project Initiated'),
        ('To Be Started', 'To Be Started'),
        ('In Progress', 'In Progress'),
        ('Completed', 'Completed'),
        ('On Hold', 'On Hold'),
        ('CBR Raised', 'CBR Raised'),
    ], default='Project Initiated')
    is_active = models.BooleanField(default=True, blank=True)
    is_multiple_sample_cpi = models.BooleanField(default=False, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if self.tentative_start_date and self.tentative_end_date:
            self.estimated_time = self.tentative_end_date - self.tentative_start_date
        super().save(*args, **kwargs)
        # if self.status == 'Completed':
        #     self.raise_cbr_to_finance()

    # def raise_cbr_to_finance(self):
    #     # Logic to raise CBR to finance team
    #     FinanceRequest.objects.create(
    #         project=self,
    #         requested_by=self.assigned_to
    #     )


class ProjectSample(models.Model):
    project = models.ForeignKey(Project, related_name="project_samples", on_delete=models.CASCADE,null=True,blank=True)
    sample = models.CharField(max_length=50, null=True, blank=True)
    cpi = models.CharField(max_length=50, null=True, blank=True)
    target_group = models.CharField(max_length=50, null=True, blank=True)
    remark = models.TextField(null=True, blank=True)  # Add remark field
    date = models.DateTimeField(null=True, blank=True)  # Add date field
    updated_by = models.ForeignKey(UserRole, null=True, blank=True, on_delete=models.SET_NULL)  # Track last user who updated
    is_approved = models.BooleanField(default=False)  # Approval status
    is_rejected = models.BooleanField(default=False)  # Approval status
    pending_changes = models.JSONField(null=True, blank=True)  # Store pending updates temporarily
    updated_at = models.DateTimeField(auto_now_add=True)


    def notify_assign_by(self):
        assign_by_user = self.project.assigned_to
        if assign_by_user:
            message = f"A sample edit request has been made for project {self.project.name}."
            subject = f"Sample Edit Request for {self.project.name}"
            #action_url = reverse('approve_sample_revision', kwargs={'pk': self.project.id})  # Action link
            action_url = f"http://{settings.DOMAIN}{reverse('approve_sample_revision', kwargs={'pk': self.project.id})}"
            # email = assign_by_user.email  # Replace with correct email field
            email = "pramod.kumar@novusinsights.com"
            send_notification(
                user = assign_by_user, 
                message = message,
                subject = subject,
                email = email,
                action_url=action_url)




    #def __str__(self):
        #return self.sample

class ProjectDocument(models.Model):
    project = models.ForeignKey(Project, related_name='documents', on_delete=models.CASCADE,null=True,blank=True)
    upload_document = models.FileField(upload_to='project_documents/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)



class ProjectAssignment(models.Model):
    project_id = models.ForeignKey(Project, on_delete=models.CASCADE)
    assigned_by = models.ForeignKey(UserRole, on_delete=models.CASCADE, related_name='assigned_projects_by')
    assigned_to = models.ForeignKey(UserRole, on_delete=models.CASCADE, related_name='assigned_projects_to')
    assigned_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.project_id.name} assigned to {self.assigned_to.user.username} by {self.assigned_by.user.username}"


class ProjectUpdatedData(models.Model):
    project_id = models.IntegerField(unique=True)
    sample = models.CharField(max_length=50, null=True, blank=True)
    tentative_end_date = models.DateTimeField(null=True, blank=True)
    reason_for_adjustment = models.TextField(null=True, blank=True, default=None)
    updated_by = models.ForeignKey(UserRole, on_delete=models.CASCADE, related_name='updated_projects_by')
    updated_at = models.DateTimeField(auto_now_add=True)
    

class Notification(models.Model):
    NOTIFICATION_CHOICES = [
        ('VPR', 'VPR'),
        ('CBR', 'CBR'),
    ]
    user = models.ForeignKey(
        UserRole,  # Replace with your custom user model if necessary
        on_delete=models.CASCADE,
        related_name='notifications'
    )
    project_sample = models.ForeignKey(
        ProjectSample, 
        on_delete=models.CASCADE,
        null=True, blank=True,
        related_name='notifications'
    )
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        null=True, blank=True,
        related_name='project_notifications'
    )
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    subject = models.CharField(max_length=255, null=True, blank=True)
    is_read = models.BooleanField(default=False)  # Track read status
    is_approved = models.BooleanField(default=False)  # Tracks approval of related project_sample
    is_rejected = models.BooleanField(default=False)  # Approval status
    notification_type = models.CharField(max_length=20,choices=NOTIFICATION_CHOICES,null=True,blank=True)
    action_url = models.URLField(null=True, blank=True)  # Optional link for 
    updated_at = models.DateTimeField(auto_now=True)

    def mark_as_approved(self):
            """
            Mark notification as approved and remove from pending list.
            """
            self.is_approved = True
            self.save(update_fields=['is_approved'])     
