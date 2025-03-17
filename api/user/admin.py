from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from api.user.forms import CustomUserCreationForm
from import_export import resources
from import_export.admin import ImportExportModelAdmin
# Register your models here.
from api.user.models import *



# Unregister the CustomUser model first
admin.site.unregister(CustomUser)

class UserResource(resources.ModelResource):
    class Meta:
        model = CustomUser

# Define the custom user admin class
class CustomUserAdmin(UserAdmin):
    add_form = CustomUserCreationForm
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('username','phone','gender','token')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'username', 'password1', 'password2', 'is_active', 'is_staff', 'is_superuser'),
        }),
    )
    list_display = ('id','email', 'username', 'is_active', 'is_staff', 'is_superuser')
    search_fields = ('email', 'username')
    ordering = ('email',)

    resource_class = UserResource

# Register the CustomUser model with the custom user admin class
admin.site.register(CustomUser, CustomUserAdmin)

@admin.register(Country)
class CountryAdmin(ImportExportModelAdmin):
    list_display = ("name","sub_branch","is_active","created_at","updated_at")
    
@admin.register(Lang)
class LangAdmin(ImportExportModelAdmin):
    list_display = ("lang_type",)

admin.site.register(Company)
    

@admin.register(Menu)
class MenuAdmin(ImportExportModelAdmin):
    list_display = ("menu_name","page_link")
    
@admin.register(Submenu)
class SubmenuAdmin(ImportExportModelAdmin):
    list_display = ("submenu_name","page_link")
    
    
@admin.register(UserRole)
class UserRoleAdmin(ImportExportModelAdmin):
    list_display = ('id', 'user','role','department', 'reports_to')    
    
@admin.register(Department)
class UserDepartmentAdmin(ImportExportModelAdmin):
    list_display = ('id', 'name')        
    
admin.site.register(Role)



