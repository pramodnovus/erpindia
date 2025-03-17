from rest_framework import serializers
from .models import *
from datetime import datetime, date
from api.user.models import *
from django.contrib.auth import get_user_model
from rest_framework.views import APIView
from drf_yasg.utils import swagger_auto_schema
import logging
from rest_framework.exceptions import ValidationError
from api.operation.models import ProjectUpdate
# Configure logger
logger = logging.getLogger(__name__)

class ProjectEmailSerializer(serializers.ModelSerializer):
    project_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = Project
        fields = ['id','project_id','project_code','name', 'sample', 'tentative_end_date', 'reason_for_adjustment']

class ProjectSampledSerializer(serializers.ModelSerializer):
    project = ProjectEmailSerializer(read_only=True)
    class Meta:
        model = ProjectSample
        fields = ['id','project','sample', 'cpi', 'target_group','pending_changes','updated_at']


class ProjectDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectDocument
        fields = ('id', 'upload_document', 'uploaded_at')

class ProjectUpdateDateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectUpdate
        fields = ["update_date"]  # Include all relevant fields

class ProjectSerializer(serializers.ModelSerializer):
    documents = ProjectDocumentSerializer(many=True, required=False)
    project_samples = ProjectSampledSerializer(many=True, required=False)  # Allows multiple samples
    project_actual_start_date = serializers.SerializerMethodField()  # Use a method field
    project_actual_end_date = serializers.SerializerMethodField()
    class Meta:
        model = Project
        fields = (
            'id', 'project_code', 'name', 'project_type', 'initial_sample_size', 'sample', 
            'project_samples', 'clients', 'cpi', 'set_up_fee', 'transaction_fee', 'status', 
            'other_cost','label_cost', 'operation_select', 'finance_select', 
            'tentative_start_date', 'tentative_end_date', 'estimated_time', 'man_days', 
            'total_achievement', 'remaining_interview', 'status', 'remark', 'assigned_to', 
            'created_by', 'send_email_manager', 'created_at', 'updated_at', 'documents','project_client_pm','purchase_order_no','project_actual_start_date','project_actual_end_date'
        )
        read_only_fields = ['is_multiple_sample_cpi']

    def get_project_actual_start_date(self, obj):
        """Fetch the earliest update_date from ProjectUpdate table for this project."""
        first_update = ProjectUpdate.objects.filter(project_id=obj.id).order_by('update_date').first()
        return first_update.update_date if first_update else None  # Return earliest update_date or None

    def get_project_actual_end_date(self, obj):
        if obj.status == 'Completed':
            # Find the latest update with the status 'Completed' for this project
            latest_update = ProjectUpdate.objects.filter(project_id=obj).filter(status='Completed').order_by('-trck_updated_at').first()
            if latest_update:
                return latest_update.trck_updated_at
        return None  # Return None if the project is not completed
    

    def to_representation(self, instance):
        data = super().to_representation(instance)

        # Clients representation with id and name
        data['clients'] = {
            'id': instance.clients.id,
            'name': instance.clients.name,
        } if instance.clients else None

        # Project type representation
        data['project_type'] = {
            'id': instance.project_type.id,
            'name': instance.project_type.name
        } if instance.project_type else None

        # Assigned to and created by representation
        data['assigned_to'] = {
            'id': instance.assigned_to.id,
            'name': instance.assigned_to.user.username
        } if instance.assigned_to else None

        data['created_by'] = {
            'id': instance.created_by.id,
            'name': instance.created_by.user.username
        } if instance.created_by else None

        # Remove null project samples
        filtered_samples = [
            sample for sample in data['project_samples']
            if sample['sample'] is not None or sample['cpi'] is not None or sample['target_group'] is not None
        ]
        data['project_samples'] = filtered_samples

        # Project assignment details representation
        #assignments = ProjectAssignment.objects.filter(project_id=instance)
        assignments = ProjectAssignment.objects.filter(project_id=instance).select_related('assigned_by__user', 'assigned_to__user')
        if assignments.exists():
            first_assignment = assignments.first()
            data['project_assigned_by_manager'] = {
                    'id': first_assignment.assigned_by.id,
                    'name': first_assignment.assigned_by.user.username
                }
            data['project_assigned_to_teamlead'] = [
                        {
                        'id': assignment.assigned_to.id,
                        'name': assignment.assigned_to.user.username
                    } for assignment in assignments
                ]
        else:
            data['project_assigned_by_manager'] = []
            data['project_assigned_to_teamlead'] = []
        # Include all project assignments

        return data

    def create(self, validated_data):
        # Fetch request from context to get access to uploaded files
        request = self.context.get('request')
        documents_data = request.FILES.getlist('upload_document[]')  # Fetch list of uploaded documents

        samples_data = validated_data.pop('project_samples', [])
        validated_data['created_by'] = self.get_user_role(request.user)

        # Create the project instance
        project = super().create(validated_data)

        # Save uploaded documents associated with the project
        for document in documents_data:
            ProjectDocument.objects.create(project=project, upload_document=document)

        # Save project samples if provided
        for sample_data in samples_data:
            if sample_data.get('sample') or sample_data.get('cpi') or sample_data.get('target_group'):
                ProjectSample.objects.create(project=project, **sample_data)
                
        #try:
            # Assign the first document from the list to the upload_document field
            #project.upload_document = documents_data[0]
            #project.save(update_fields=['upload_document'])
        #except IndexError:
            # Handle the case where documents_data is empty
            #pass  # No document available to save in upload_document

        return project

    def get_user_role(self, user):
        try:
            return UserRole.objects.get(user=user)
        except UserRole.DoesNotExist:
            raise serializers.ValidationError("No UserRole associated with this user.")

    def get_advance_billing_amount(self, obj):
        """Returns the latest advance billing amount for the project."""
        advance_billing = AdvanceBillingRequest.objects.filter(project=obj).order_by('-request_date').first()
        return advance_billing.advanced_billing if advance_billing else None

        
        
class ProjectDocumentUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectDocument
        fields = ['upload_document', 'updated_at']
        read_only_fields = ['updated_at']    
    

        


class ClientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Client
        fields = [
            'id', 'name', 'email', 'contact_person_email', 'project_code', 'address',
            'city', 'country', 'phone_number', 'contact_person', 'client_purchase_order_no',
            'email_id_for_cc', 'additional_survey', 'total_survey_to_be_billed_to_client',
            'other_specific_billing_instruction', 'is_active', 'created_at', 'updated_at'
        ]

class ProjectTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = projectType
        fields = ['id', 'name', 'is_active']

    def validate_name(self, value):
        if not value:
            raise serializers.ValidationError("Name field cannot be empty.")
        return value

    def to_representation(self, instance):
        try:
            data = super().to_representation(instance)
        except Exception as e:
            raise serializers.ValidationError(f"Error serializing ProjectType: {str(e)}")
        return data


############################################### USER ROLE SERILIZER AS MANAGER SHOW INTO DROPDOWN #######################################


class UserRoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserRole
        fields = ['id', 'user', 'role', 'department', 'reports_to']
        
    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['user'] = {
            'id': instance.user.id,
            'name': instance.user.username,
            'email': instance.user.email
        }
        data['role'] = {
            'id': instance.role.id,
            'name': instance.role.name
        }

        data['user_role'] = {
                'id':instance.id,
                'name':instance.user.username
        }
        data['department'] = {
            'id': instance.department.id,
            'name': instance.department.name
        } if instance.department else None
        data['reports_to'] = {
            'id': instance.reports_to.id,
            'name': instance.reports_to.user.username
        } if instance.reports_to else None
        return data
        
        

############################################## USER SERIALIZERS MODIFICATION ###############################################################
# class UserRoleSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = CustomUser
#         fields = ['id','email','username']
        
############################################ PROJECT ASSIGNMENT BY OPERATION MANAGER  TO OPERATION TL ############################################


class ProjectAssignmentSerializer(serializers.ModelSerializer):
    project_client_pm = serializers.CharField(allow_null=True, required=False)
    purchase_order_no = serializers.CharField(allow_null=True, required=False)

    class Meta:
        model = ProjectAssignment
        fields = '__all__'
 

    def to_representation(self, instance):
        representation = super().to_representation(instance)

        # Get the project associated with this assignment
        project = instance.project_id

        # Fetch all assignments related to the project
        assignments = ProjectAssignment.objects.filter(project_id=project)

        # Create a list of users assigned to the project
        assigned_users = [
            {
                'id': assignment.assigned_to.id,
                'name': assignment.assigned_to.user.username
            }
            for assignment in assignments
        ]

        representation['project_assigned_to'] = assigned_users

        # Show the user who made the assignment for this specific instance
        representation['project_assigned_by'] = {
            'project_id': project.id,
            'id': instance.assigned_by.id,
            'name': instance.assigned_by.user.username
        }

        # Add the new fields in the response, set them to None if not present
        representation['project_client_pm'] = project.project_client_pm if project.project_client_pm else None
        representation['purchase_order_no'] = project.purchase_order_no if project.purchase_order_no else None
        
        # Remove fields that are represented differently
        representation.pop('assigned_by', None)
        representation.pop('assigned_to', None)

        return representation

    #def to_representation(self, instance):
        #representation = super().to_representation(instance)

        # Get the project ID
        #project_id = instance.project_id.id

        # Fetch all assignments related to the project
        #assignments = ProjectAssignment.objects.filter(project_id=instance.project_id)

        # Create a list of users assigned to the project
        #assigned_users = [
            #{
                #'id': assignment.assigned_to.id,
                #'name': assignment.assigned_to.user.username
            #}
            #for assignment in assignments
        #]

        #representation['project_assigned_to'] = assigned_users

        # Show the user who made the assignment for this specific instance
        #representation['project_assigned_by'] = {
            #'project_id': project_id,
            #'id': instance.assigned_by.id,
            #'name': instance.assigned_by.user.username
        #}

        # Add the new fields in the response
        #representation['project_client_pm'] = instance.project_id.project_client_pm
        #representation['purchase_order_no'] = instance.project_id.purchase_order_no
        
        #representation.pop('assigned_by', None)
        #representation.pop('assigned_to', None)

        #return representation

    
    
class ProjectStatusSerializer(serializers.Serializer):
    project_id = serializers.IntegerField()
    status = serializers.CharField(max_length=255)
    


class ProjectUpdatedDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectUpdatedData
        fields = ['project_id', 'sample', 'tentative_end_date', 'reason_for_adjustment']
    
#class ProjectEmailSerializer(serializers.ModelSerializer):
    #project_id = serializers.IntegerField(write_only=True)

    #class Meta:
        #model = Project
        #fields = ['project_id', 'sample', 'tentative_end_date', 'reason_for_adjustment']


class ProjectNotificationOffSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = ['id', 'sample', 'tentative_end_date', 'reason_for_adjustment','send_email_manager']
 
    def validate_tentative_end_date(self, value):
        # Ensure the tentative end date is not in the past
        if value and value.date() < date.today():
            raise serializers.ValidationError("Tentative end date cannot be in the past.")
        return value


####################################### Project Sample Serializers ##############################################

from rest_framework import serializers
from .models import ProjectSample

class ProjectSampleSerializer(serializers.ModelSerializer):
    remark = serializers.CharField(required=True)
    date = serializers.DateField(required=True) 
    class Meta:
        model = ProjectSample
        fields = ['id', 'project', 'sample', 'cpi', 'target_group','remark', 'date']
        read_only_fields = ['id']




################################################################### Project Update Sample Serializer ########################################


class ProjectSampleUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectSample
        fields = ['id', 'is_rejected', 'pending_changes', 'is_approved']

############################################# Project Type Update Serializer #########################

class ProjectTypeUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = ['project_type']


################################################################## notification serializer #################################################



class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ['id', 'message', 'subject', 'is_read', 'created_at', 'action_url']



class ProjectIDSerializer(serializers.Serializer):
    project_id = serializers.IntegerField(required=True, error_messages={
        "required": "Project ID is required.",
        "invalid": "Project ID must be an integer.",
    })
