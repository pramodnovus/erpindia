from rest_framework import serializers, generics, viewsets
from rest_framework.response import Response
from rest_framework import status
from .models import *
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.contrib.auth import authenticate,get_user_model,password_validation
from django.contrib.auth.hashers import check_password,make_password
from .models import CustomUser
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.utils import timezone


#Country Serializer Class
class CountrySerializer(serializers.ModelSerializer):
    class Meta:
        model = Country
        fields = ['name','sub_branch','is_active']


#Language Serializer Class
class LngSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lang
        fields = ['lang_type', 'country_id', 'is_active']        
        
# Company Serializer Class
class CompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = ['name','entity_id','entity_name','address','country_id','is_active']

# RoleMaster Serializer Class

 # MenuMaster Serializer Class       
class MenuSerializer(serializers.ModelSerializer):
    role_id = serializers.HyperlinkedRelatedField(many=True, view_name='snippet-detail', read_only=True)
    class Meta:
        model = Menu
        fields = ['menu_name','page_link','role_id','is_active']        
        

# SubMenu Master Serializer Class        
class SubMenuSerializer(serializers.ModelSerializer):
    class Meta:
        model = Submenu
        fields = ['menu', 'submenu_name','page_link','permissions','is_active']        



# Department Serializer Class

class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = ['id','name', 'is_active']
        
        
class UserSerializers(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'email', 'gender','profile_picture','is_active']
        
    def to_representation(self, instance):
        data = super().to_representation(instance)
        
        
        try:
            user_role = instance.userrole  # Assuming 'userrole' is the related_name for UserRole model's user field
            data['user_role'] = {
                'id': user_role.role.id,
                'name': user_role.role.name
            }
            data['user_department'] = {
                'id': user_role.department.id,
                'name': user_role.department.name
            }
        except UserRole.DoesNotExist:
            data['user_role'] = None
            data['user_department'] = None
        
        return data



class CustomUserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)

    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'password', 'confirm_password', 'phone', 'gender']
        extra_kwargs = {'password': {'write_only': True}}

    def validate_email(self, value):
        existing_user = CustomUser.objects.filter(email=value).first()
        if existing_user:
            raise serializers.ValidationError("This email address is already in use.")
        return value

    def validate(self, data):
        if data['password'] != data.pop('confirm_password'):
            raise serializers.ValidationError("Passwords do not match.")
        try:
            validate_password(data['password'])
        except serializers.ValidationError as e:
            raise serializers.ValidationError(str(e))
        return data

    def create(self, validated_data):
        # Hash the password before saving it to the database
        user = CustomUser.objects.create_user(**validated_data)
        return user
    

        
class UserStatusSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    is_active = serializers.CharField(max_length=255)

    
class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['email','phone','gender', 'profile_picture']
        extra_kwargs = {'email': {'read_only': True}}  # Assuming email is not editable

    def update(self, instance, validated_data):
        instance.phone = validated_data.get('phone', instance.phone)
        instance.gender = validated_data.get('gender', instance.gender)
        instance.profile_picture = validated_data.get('profile_picture', instance.profile_picture)
        instance.save()
        return instance
    
class UserLoginSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(max_length=255, min_length=3)
    password = serializers.CharField(max_length=25, min_length=8, required=True)

    class Meta:
        model = CustomUser
        fields = ['email', 'password']

    def validate(self, data):
        email = data.get('email')
        password = data.get('password')

        if not email:
            raise serializers.ValidationError("Email is required.")

        if not password:
            raise serializers.ValidationError("Password is required.")

        # Check if user with this email exists
        user = CustomUser.objects.filter(email=email).first()
        if not user:
            raise serializers.ValidationError("User with this email does not exist.")

        return data
    

class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        # Add custom claims
        token['username'] = user.username
        try:
            token['role'] = user.userrole.role.name
            token['department'] = user.userrole.department.name
            token['userrole'] = user.userrole.id
        except AttributeError as e:
            token['role'] = "role not found"
        # Add any other custom claims you need

        return token


class ChangePasswordSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(write_only=True, required=True)
    confirm_password = serializers.CharField(write_only=True, required=True)

    def validate(self, data):
        email = data.get('email')
        old_password = data.get('old_password')
        new_password = data.get('new_password')
        confirm_password = data.get('confirm_password')

        user = get_user_model().objects.filter(email=email).first()

        if not user:
            raise serializers.ValidationError("User with this email does not exist.")

        if not user.check_password(old_password):
            raise serializers.ValidationError("Incorrect old password.")

        if new_password != confirm_password:
            raise serializers.ValidationError("New password and confirm password do not match.")
        
        if len(new_password) < 8:
            raise serializers.ValidationError("Password length must be 8 characters.")

        try:
            validate_password(new_password, user)
        except serializers.ValidationError as e:
            raise serializers.ValidationError(str(e))

        data['user'] = user
        return data


class SendPasswordResetEmailSerializer(serializers.Serializer):
    email = serializers.EmailField(max_length=255, min_length=3)
    
    def validate_email(self, value):
        user = CustomUser.objects.filter(email=value).first()
        if not user:
            raise serializers.ValidationError("User with this email does not exist.")
        return value



class UserPasswordResetSerializer(serializers.Serializer):
    password = serializers.CharField(max_length=255, style={'input_type':'password'}, write_only=True)
    password2 = serializers.CharField(max_length=255, style={'input_type':'password'}, write_only=True)

    class Meta:
        fields = ['password', 'password2']

    def validate(self, attrs):
        password = attrs.get('password')
        password2 = attrs.get('password2')
        token = self.context.get('token')

        # Retrieve the user using the token
        try:
            user = CustomUser.objects.get(token=token)
        except CustomUser.DoesNotExist:
            raise serializers.ValidationError('Token is not valid or expired')

        # Check if the token is expired (optional)
        if user.updated_at < timezone.now() - timezone.timedelta(minutes=10):
            raise serializers.ValidationError('Token is expired')

        # Validate password match
        if password != password2:
            raise serializers.ValidationError("Passwords do not match.")
        
        if len(password) < 8:
            raise serializers.ValidationError("Password length must be 8 characters.")

        # Set new password and save the user
        user.set_password(password)
        user.token = None  # Clear the token after password reset
        user.save()

        return attrs


#ZoneMaster Serializer Class
class ZoneMasterSerializer(serializers.ModelSerializer):
    zone_cities = serializers.StringRelatedField(many=True)
    regions = serializers.StringRelatedField(many=True)
    class Meta:
        model = ZoneMaster
        fields = ['name','regions', 'zone_cities','is_active']
        
# RegionMaster Serializer Class
class RegionMasterSerializer(serializers.ModelSerializer):
    class Meta:
        model = RegionMaster
        fields = ['name','zone_id','is_active']
        
# StateMaster Serializer Class

class StateMasterSerializer(serializers.ModelSerializer):
    zone_id = serializers.StringRelatedField(many=False, read_only=True)
    region_id = serializers.StringRelatedField(many=False, read_only=True)
    class Meta:
        model = StateMaster
        fields = ['name', 'zone_id','region_id','is_active']
        
        
# CityMaster Serializer Class
class CityMasterSerializer(serializers.ModelSerializer):
    class Meta:
        model = CityMaster
        fields = ['name','region_id','state_id','is_active']
        
        
        


############################################################## ENTITY SERIALIZER ##############################################################################################

from rest_framework import serializers
from .models import Company

class CompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = '__all__'  # Include all fields

