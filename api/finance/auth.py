from api.user.models import UserRole
from rest_framework import serializers
def get_user_role(user):
        try:
            return UserRole.objects.get(user__id=user)
        except UserRole.DoesNotExist:
            raise serializers.ValidationError("No UserRole associated with this user.")
