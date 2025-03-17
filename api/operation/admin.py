from django.contrib import admin
from .models import *
from import_export.admin import ImportExportModelAdmin

class ProjectUpdateAdmin(admin.ModelAdmin):
    list_display = (
        'project_id',
        'get_project_code',
        'updated_by',
        'update_date',
        'trck_updated_at',
        'total_man_days',
        'remaining_time',
        'remaining_interview',
        'total_achievement',
        'status',
        'is_active',
    )
    list_filter = (
        'update_date',
        'project_id',
        'updated_by',
        'is_active',
    )
    search_fields = (
        'project_id__name',
        'updated_by__user__username',
        'remaining_interview',
        'total_achievement',
        'status',
    )
    def get_project_code(self, obj):
        return obj.project_id.project_code if obj.project_id else '-'
    get_project_code.short_description = 'Project Code'
    ordering = ('-update_date',)
    readonly_fields = ('update_date',)  # Assuming you don't want this field to be edited

admin.site.register(ProjectUpdate, ProjectUpdateAdmin)


#@admin.register(ProjectAssignment)
#class ProjectAssignment(ImportExportModelAdmin):
#    list_display = ('project_id','assigned_by','assigned_to','assigned_at')
#    search_fields = ('project_id','assigned_by','assigned_to','assigned_at')
