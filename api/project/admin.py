from django.contrib import admin
from .models import *
from import_export.admin import ImportExportModelAdmin


@admin.register(projectType)
class ProjectTypeAdmin(ImportExportModelAdmin):
    list_display = ['id', 'name'] 
    list_display_links = ['id', 'name'] 

    class Meta:
        model = projectType

@admin.register(Project)
class ProjectAdmin(ImportExportModelAdmin):
    list_display = ['id','project_code','name','project_type','sample','clients','cpi','other_cost','operation_select',
            'finance_select','upload_document','tentative_start_date','tentative_end_date','estimated_time','status','remark',
            'assigned_to'] 

    search_fields = ["id","project_code","name","status"]
    list_filter = ['status']

# @admin.register(ProjectCode)
# class ProjectCodeAdmin(ImportExportModelAdmin):
#     list_display = ('project_code',)
    
    
@admin.register(Client)
class ClientAdmin(ImportExportModelAdmin):
    list_display = ('id','name','project_code','client_purchase_order_no','email_id_for_cc','additional_survey','total_survey_to_be_billed_to_client','other_specific_billing_instruction')
    
admin.site.register(ProjectUpdatedData)


@admin.register(ProjectSample)
class ProjectSampleAdmin(admin.ModelAdmin):
    list_display = ['project','sample','cpi','updated_at','is_rejected']
    search_fields = ('sample','cpi')

@admin.register(ProjectDocument)
class ProjectDocumentAdmin(admin.ModelAdmin):
    list_display = ['id','project','upload_document','uploaded_at']




from django.contrib import admin
from .models import Notification

class NotificationAdmin(admin.ModelAdmin):
    list_display = ('id','user', 'project_sample','project', 'message', 'subject', 'is_read', 'is_approved', 'created_at', 'updated_at')
    list_filter = ('is_read', 'is_approved', 'created_at')
    search_fields = ('message', 'subject', 'user__username')  # Search by message, subject, or user
    list_editable = ('is_read', 'is_approved')  # Allow editing of read/approved status directly in the list view

    # Action to bulk mark notifications as approved
    actions = ['mark_as_approved']

    def mark_as_approved(self, request, queryset):
        """
        Mark selected notifications as approved.
        """
        count = queryset.update(is_approved=True)
        self.message_user(request, f"{count} notification(s) marked as approved.")
    
    mark_as_approved.short_description = 'Mark selected notifications as approved'

# Register the Notification model with the custom admin class
admin.site.register(Notification, NotificationAdmin)    



from django.contrib import admin
from django import forms
from dal import autocomplete
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views import View
from django.urls import reverse_lazy
from .models import ProjectAssignment, Project, UserRole

# Custom Form for ProjectAssignmentAdmin
class ProjectAssignmentForm(forms.ModelForm):
    class Meta:
        model = ProjectAssignment
        fields = '__all__'
        widgets = {
            'project_id': autocomplete.ModelSelect2(url=reverse_lazy('project-autocomplete'))
        }

@admin.register(ProjectAssignment)
class ProjectAssignmentAdmin(admin.ModelAdmin):
    form = ProjectAssignmentForm
    list_display = ('project_id', 'assigned_by', 'assigned_to', 'assigned_at')
    search_fields = ('project_id__name', 'assigned_by__user__username', 'assigned_to__user__username')

# Custom Autocomplete View
@method_decorator(csrf_exempt, name='dispatch')
class ProjectAutocompleteView(View):
    def get(self, request, *args, **kwargs):
        query = request.GET.get('q', '').strip()

        # Fetch all projects
        projects = Project.objects.all()

        # Separate matches vs. other results
        exact_matches = []
        other_results = []

        for project in projects:
            project_data = {"id": project.id, "text": project.name}

            if query and project.name.lower().startswith(query.lower()):
                exact_matches.append(project_data)  # Prioritize matches
            else:
                other_results.append(project_data)

        # Final response: matches first, then others
        return JsonResponse({"results": exact_matches + other_results}, safe=False)

# Assign View Function to Variable
project_autocomplete = ProjectAutocompleteView.as_view()
