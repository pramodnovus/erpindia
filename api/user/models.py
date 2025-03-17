from django.db import models
from django.contrib.auth.models import AbstractUser
from api.user.choice import lang_choice,gender_choice
from .managers import CustomUserManager
from django.contrib.auth.hashers import make_password
from django.utils import timezone


# Country model
class Country(models.Model):
    name = models.CharField(max_length=100)
    sub_branch = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


# Language model
class Lang(models.Model):
    lang_type = models.CharField(choices=lang_choice,max_length=100)
    country_id = models.ForeignKey(Country, on_delete=models.CASCADE, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.lang_type
    


# Company model
class Company(models.Model):
    name = models.CharField(max_length=150)
    entity_id = models.CharField(max_length=50)
    entity_name = models.CharField(max_length=50)
    logo = models.ImageField(upload_to='entity_logos/', null=True, blank=True)  # Logo field
    address = models.TextField(null=True, blank=True)
    country_id = models.ForeignKey(Country, on_delete = models.CASCADE, null=True, blank=True)
    email = models.EmailField(max_length=100, null=True,blank=True) 
    is_active = models.BooleanField(default=True)
    # New bank details fields
    account_title = models.CharField(max_length=200, null=True, blank=True)
    account_number = models.CharField(max_length=50, null=True, blank=True)
    swift_code = models.CharField(max_length=50, null=True, blank=True)
    wire_aba_number = models.CharField(max_length=50, null=True, blank=True)  # Wire ABA#
    wire_ach_number = models.CharField(max_length=50, null=True, blank=True)  #
    ifsc = models.CharField(max_length=50, null=True, blank=True)  # Ne
    sort_code = models.CharField(max_length=50, null=True, blank=True)
    iban_number = models.CharField(max_length=50, null=True, blank=True)
    bank_name = models.CharField(max_length=200, null=True, blank=True)
    bank_address = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f'{self.name} - {self.country_id.name}'

    
# Menu Master Table    
class Menu(models.Model):
    menu_name = models.CharField(max_length=255)
    page_link = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

# SubMenu Master table
class Submenu(models.Model):
    menu = models.ForeignKey(Menu, on_delete=models.CASCADE)
    submenu_name = models.CharField(max_length=255)
    page_link = models.CharField(max_length=255)
    permissions = models.ManyToManyField("auth.Permission")   
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True) 
    
    
    

# CustomUser model
class CustomUser(AbstractUser):
    email = models.EmailField(max_length=100, unique=True) 
    username = models.CharField(max_length=150, blank=True, null=True,default='Anonymous')
    phone = models.CharField(max_length=20, blank=True, null=True)
    gender = models.CharField(choices=gender_choice,max_length=20, null=True, blank=True)
    company = models.ForeignKey(Company , on_delete=models.CASCADE, null=True, blank=True)
    token = models.CharField(max_length=255, unique=True, null=True, blank=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', null=True, blank=True)  # Add for profile image
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
     

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']
    
    objects = CustomUserManager()
    
    def __str__(self):
        return self.email
    
    
   
# ZoneMaster model
class ZoneMaster(models.Model):
    name = models.CharField(max_length=50)
    country_id = models.ForeignKey(Country, on_delete=models.CASCADE, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name
    

# RegionMaster model
class RegionMaster(models.Model):
    name = models.CharField(max_length=50)
    zone_id = models.ForeignKey(ZoneMaster, on_delete=models.CASCADE, null=True,blank=True, related_name="regions")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name
    

# StateMaster model
class StateMaster(models.Model):
    name = models.CharField(max_length=50)
    zone_id = models.ForeignKey(ZoneMaster, on_delete=models.CASCADE, null=True,blank=True, related_name='zone_states')
    region_id = models.ForeignKey(RegionMaster, on_delete=models.CASCADE, null=True,blank=True, related_name='region_states')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name
    

# CityMaster model
class CityMaster(models.Model):
    name = models.CharField(max_length=50)
    zone_id = models.ForeignKey(ZoneMaster, on_delete=models.CASCADE, null=True,blank=True, related_name='zone_cities')
    region_id = models.ForeignKey(RegionMaster, on_delete=models.CASCADE, null=True,blank=True,related_name='region_cities')
    state_id = models.ForeignKey(StateMaster, on_delete=models.CASCADE, null=True,blank=True, related_name='state_cities')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name
    

class Role(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name

class Department(models.Model):
    name = models.CharField(max_length=50, unique=True)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, null=True, blank=True, related_name='departments')

    def __str__(self):
        return f'{self.name} - {self.company.name}'

class UserRole(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    role = models.ForeignKey(Role, on_delete=models.CASCADE)
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    reports_to = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL, related_name='subordinates')

    def __str__(self):
        return f"{self.user.username} - {self.role.name} - {self.department.name}"
