from rest_framework import serializers
from .models import *
from django.utils import timezone
from datetime import timedelta

class ProjectUpdateSerializer(serializers.ModelSerializer):
    project_id = serializers.PrimaryKeyRelatedField(queryset=Project.objects.all(), source='project')
    
    class Meta:
        model = ProjectUpdate
        fields = ['id', 'project_id', 'updated_by', 'update_date', 'total_man_days', 'total_achievement', 'status', 'is_active']
        read_only_fields = ['id', 'updated_by', 'update_date']

    def validate(self, data):
        project = data['project']
        user = self.context['request'].user
        user_role = UserRole.objects.get(user=user)

        update_date = data.get('update_date', timezone.now())
        try:
            status = data['status']  # Attempt to get the status from the data
            if not status:
                raise serializers.ValidationError("Please select a status. It's mandatory.")
        except KeyError:
            raise serializers.ValidationError("Please select a status. It's mandatory.")

        total_man_days = data['total_man_days']
        total_achievement = data['total_achievement']

        # Fetch the latest project status directly from the database
        project.refresh_from_db()
        project_status = project.status

        if project_status == "To Be Started":
            validated_data = self.validate_to_be_started(project, update_date, total_man_days, total_achievement, status, user_role)
        elif project_status == "In Progress":
            validated_data = self.validate_in_progress(project, update_date, total_man_days, total_achievement, status, user_role)
        else:
            raise serializers.ValidationError(f"Project is already completed or on hold {project_status}")
        
        # Update project status to "In_Progress"
        project.status = "In Progress"
        project.save()

        return validated_data

    def validate_to_be_started(self, project, update_date, total_man_days, total_achievement, status, user_role):
        tentative_end_date = project.tentative_end_date.date()
        date = update_date.date()

        if date > tentative_end_date:
            raise serializers.ValidationError("Project start date is greater than project end date!")

        total_working_days = (tentative_end_date - date).days
        total_working_time = total_working_days * timedelta(hours=24)
        today_working_time = total_man_days * timedelta(hours=8)
        remaining_working_time = total_working_time - today_working_time
        interview_sample_size = int(float(project.sample))
        remaining_achievement = interview_sample_size - int(total_achievement)

        if int(interview_sample_size) < int(total_achievement):
            raise serializers.ValidationError("Achieved target is greater than the sample size.")
        
        if int(interview_sample_size) == int(total_achievement) and status != "Completed":
            raise serializers.ValidationError("Please select the status as completed")

        return {
            'project_id': project,
            'update_date': update_date,
            'updated_by': user_role,
            'total_man_days': total_man_days,
            'total_achievement': total_achievement,
            'remaining_time': remaining_working_time,
            'remaining_interview': remaining_achievement,
            'status': status,
            'is_active': True
        }

    def validate_in_progress(self, project, update_date, total_man_days, total_achievement, status, user_role):
        last_operation_team = ProjectUpdate.objects.filter(project_id=project).last()
        if last_operation_team:
            total_working_time = last_operation_team.remaining_time
            today_working_time = total_man_days * timedelta(hours=8)
            remaining_working_time = total_working_time - today_working_time
            interview_sample_size = int(last_operation_team.remaining_interview)
            remaining_achievement = interview_sample_size - int(total_achievement)

            if int(interview_sample_size) < 1:
                raise serializers.ValidationError("Interviews completed. Cannot create another entry.")
            
            if int(interview_sample_size) < int(total_achievement):
                raise serializers.ValidationError("Achieved target is greater than remaining interviews.")
            
            #if int(total_achievement) == int(interview_sample_size) and status != "Completed":
            #    raise serializers.ValidationError("Please select the status as completed")
            
            #if total_working_time < today_working_time:
                #raise serializers.ValidationError(f"Our overall time target is {total_working_time} hours. Please ensure man days are always less than the total working time.")
        else:
            remaining_working_time = timedelta(hours=0)
            remaining_achievement = 0

        return {
            'project_id': project,
            'update_date': update_date,
            'updated_by': user_role,
            'total_man_days': total_man_days,
            'total_achievement': total_achievement,
            'remaining_time': remaining_working_time,
            'remaining_interview': remaining_achievement,
            'status': status,
            'is_active': True
        }

class OperationTeamSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectUpdate
        fields = ['id', 'project_id', 'updated_by', 'update_date', 'total_man_days', 'total_achievement', 'remaining_time', 'remaining_interview','status', 'is_active']
        read_only_fields = ['id']


    def to_representation(self, instance):
        data = super().to_representation(instance)
        
        data['updated_by'] = {
            'id': instance.updated_by.id,
            'name': instance.updated_by.user.username
         }
        return data
        
        
        
class ProjectPerDaySerializer(serializers.ModelSerializer):
    project_id = serializers.IntegerField(write_only=True, required=True)

    class Meta:
        model = Project
        fields = ['project_id', 'is_active']

    def validate_project_id(self, value):
        # Check if the project id exists
        if not Project.objects.filter(id=value).exists():
            raise serializers.ValidationError("Project with this ID does not exist.")
        return value


class ProjectListSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectUpdate
        fields = "__all__"  # Include all relevant fields

class ProjectUpdateEditSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    total_man_days = serializers.FloatField()

class ProjectUpdateBatchEditSerializer(serializers.Serializer):
    project_id = serializers.IntegerField()
    updates = ProjectUpdateEditSerializer(many=True)


############################################################################### ADD MANDAYS SERIALIZERS ######################################################################
class ProjectListSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectUpdate
        fields = "__all__"  # Include all relevant fields
