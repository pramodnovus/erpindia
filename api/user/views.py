# # views.py
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import viewsets, permissions, status
from .models import *
from rest_framework.authtoken.models import Token
from .serializers import *
from django.contrib.auth.hashers import check_password
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.contrib.auth.models import update_last_login
from drf_yasg.utils import swagger_auto_schema
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.http import JsonResponse
from rest_framework.reverse import reverse
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.contrib.auth import authenticate



User = get_user_model()


@api_view(['GET'])
def api_root(request, format=None):
    return Response({
        'snippets': reverse('snippet-list', request=request, format=format)
    })


#Country ViewSet
class CountryViewSet(viewsets.ModelViewSet):
    queryset = Country.objects.all()
    serializer_class = CountrySerializer
    permission_classes = (permissions.AllowAny,)
    




    

# User RegistrationViewset  
class UserRegistrationViewSet(viewsets.ModelViewSet):
    queryset = CustomUser.objects.all()
    serializer_class = CustomUserSerializer
    permission_classes = (permissions.AllowAny,)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        ''' perform create method is used to add extra information when creating a new object. 
         perform_create() method will not execute if you override create() method.'''
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

class UpdateUserStatusAPIView(APIView):
    serializer_class = UserStatusSerializer
    authentication_classes = [JWTAuthentication]
    # permission_classes = (permissions.AllowAny,)
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(request_body=UserStatusSerializer)
    def post(self, request, *args, **kwargs):
        serializer = UserStatusSerializer(data=request.data)
        if serializer.is_valid():
            user_id = serializer.validated_data['id']
            is_active = serializer.validated_data['is_active'].capitalize()
            
            try:
                user = CustomUser.objects.get(pk=user_id)
                user.is_active = is_active
                user.save()

                if is_active == 'True':
                    return Response({"message": "User activated successfully."}, status=status.HTTP_200_OK)
                else:
                    return Response({"message": "User deactivated successfully."}, status=status.HTTP_200_OK)
                    
            except CustomUser.DoesNotExist:
                return Response({"message": "User with the given ID does not exist."}, status=status.HTTP_404_NOT_FOUND)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    
    
class UpdateProfileAPIView(generics.RetrieveUpdateAPIView):
    queryset = CustomUser.objects.all()
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        return self.request.user

    def get_queryset(self):
        if self.request.user.is_authenticated:
            return self.queryset.filter(email=self.request.user.email)
        else:
            return CustomUser.objects.none()
        
        
    
class UserLists(APIView):
    permission_classes = (permissions.AllowAny,)
    serializer_class = UserSerializers
    queryset = CustomUser.objects.all()

    @swagger_auto_schema(
        operation_description="Return a list of all users.",
        responses={200: UserSerializers(many=True)},
        )
    def get(self, request, format=None):
        """
        Return a list of all users.
        """
        users = CustomUser.objects.all()
        serialized_users = UserSerializers(users, many=True).data
        return JsonResponse({'users': serialized_users}, safe=False)
   

class UserLoginViewSet(viewsets.ModelViewSet):
    serializer_class = UserLoginSerializer
    permission_classes = (permissions.AllowAny,)
    queryset = CustomUser.objects.all()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data['email']
        password = serializer.validated_data['password']
        
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            user = None
            
        if user is None:
            return Response({
                'status': 400,
                'message': 'Invalid email Address.'
            }, status=status.HTTP_400_BAD_REQUEST)
            
        if not user.is_active:
            return Response({
                'status': 400,
                'message': 'User does not exists.'
            }, status=status.HTTP_400_BAD_REQUEST)

        user = authenticate(request, email=email, password=password)
        
        print(user)
        
        if user is None:
            return Response({
                'status': 400,
                'message': 'The password you entered is incorrect. Please try again.'
            }, status=status.HTTP_400_BAD_REQUEST)
            
        # refresh = RefreshToken.for_user(user)
        # access_token = str(refresh.access_token)
        
        # # Generate custom token
        custom_token_serializer = MyTokenObtainPairSerializer()
        refresh = custom_token_serializer.get_token(user)
        access_token = str(refresh.access_token)
        return Response({
            'refresh': str(refresh),
            'access': access_token,
            # Add other data you want to return with the token
            'success': 'Login successful.'
        }, status=status.HTTP_200_OK)





class ChangePasswordViewSet(viewsets.GenericViewSet):
    serializer_class = ChangePasswordSerializer
    permission_classes = (permissions.AllowAny,)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data['user']
        new_password = serializer.validated_data['new_password']

        user.set_password(new_password)
        user.save()

        return Response({'detail': 'Password changed successfully.'}, status=status.HTTP_200_OK)
    



class CustomPasswordResetTokenGenerator(PasswordResetTokenGenerator):
    def _make_hash_value(self, user, timestamp):
        return str(user.pk) + str(timestamp) + str(user.token)

class SendPasswordResetEmailView(viewsets.ViewSet):
    serializer_class = SendPasswordResetEmailSerializer
    permission_classes = (permissions.AllowAny,)

    @swagger_auto_schema(request_body=SendPasswordResetEmailSerializer)
    def create(self, request):
        serializer = SendPasswordResetEmailSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data['email']
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({'detail': 'User with this email does not exist.'}, status=status.HTTP_404_NOT_FOUND)

        # Generate a password reset token
        token_generator = CustomPasswordResetTokenGenerator()
        token = token_generator.make_token(user)
        user.token = token
        user.save()

        # Render the HTML email content
        ctx = {
            'uid': urlsafe_base64_encode(force_bytes(user.pk)),
            'token': token
        }

        msg_html = render_to_string('password_reset_form.html', ctx)
        plain_message = strip_tags(msg_html)
        recipient_list = [user.email] 
        # Send the password reset email
        subject = 'Your Novuscrm password request'
        to_email = user.email
        frm_email = "noreply.erp@unimrkt.com"
        send_mail(
            subject,
            plain_message,
            frm_email,
            [to_email],
            recipient_list,
            html_message=msg_html,
        )

        return Response({'detail': 'Password reset link sent successfully.'}, status=status.HTTP_200_OK)
    

class UserPasswordResetView(APIView):
  permission_classes = (permissions.AllowAny,)
  @swagger_auto_schema(request_body=UserPasswordResetSerializer)
  def post(self, request, uid, token, format=None):
    serializer = UserPasswordResetSerializer(data=request.data, context={'uid':uid, 'token':token})
    serializer.is_valid(raise_exception=True)
    return Response({'msg':'Password Reset Successfully'}, status=status.HTTP_200_OK)


# class UserReportsView(generics.ListAPIView):
#     serializer_class = UserRoleSerializer
#     permission_classes = [IsAuthenticated]

#     def get_queryset(self):
#         user_id = self.kwargs['user_id']
#         return UserRole.objects.filter(reports_to_id=user_id)
    

class ZoneViewSet(viewsets.ModelViewSet):
    queryset = ZoneMaster.objects.all()
    serializer_class = ZoneMasterSerializer
    permission_classes = (permissions.AllowAny,)  
    

class RegionViewSet(viewsets.ModelViewSet):
    queryset = RegionMaster.objects.all()
    serializer_class = RegionMasterSerializer
    permission_classes = (permissions.AllowAny,)      
    
    
class CityViewSet(viewsets.ModelViewSet):
    queryset = CityMaster.objects.all()
    serializer_class = CityMasterSerializer
    permission_classes = (permissions.AllowAny,)    
    


#################################################################  ENTITY API VIEW ########################################################################################


class CompanyDetailAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]  # Restrict access to authenticated users
    authentication_classes = [JWTAuthentication]
    

    def get(self, request, pk):
            try:
                company = Company.objects.get(id=pk, is_active=True)  # Fetch only active company
                serializer = CompanySerializer(company)
                return Response({
                    "status": 200,
                    "message": "Company data fetched successfully.",
                    "data": serializer.data
                }, status=status.HTTP_200_OK)
            except Company.DoesNotExist:
                return Response({
                    "status": 404,
                    "message": "Company not found or inactive."
                }, status=status.HTTP_404_NOT_FOUND)



######################################################## All COmapany ##############################################################################
class AllCompaniesAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        companies = Company.objects.filter(is_active=True)  # Fetch all active companies
        serializer = CompanySerializer(companies, many=True)
        return Response({
            "status": 200,
            "message": "All active companies fetched successfully.",
            "data": serializer.data
        }, status=status.HTTP_200_OK)

