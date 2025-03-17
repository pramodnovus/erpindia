from django.shortcuts import render
from rest_framework import viewsets
# from .models import operationTeam
from .serializers import *
from rest_framework.response import Response
from rest_framework import viewsets, permissions, status
from drf_yasg.utils import swagger_auto_schema
from rest_framework.views import APIView
from api.project.models import Project  
from rest_framework.decorators import api_view 
import datetime
from django.core import signing
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.core.mail import send_mail
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.permissions import IsAuthenticated
from django.http import JsonResponse
from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
import logging
from django.db.models import Sum
from rest_framework import status
############################################### ADD MAN-DAYS FILLED BY OPERATION TEAM - BULK UPDATE  ##################################################

class ProjectUpdateBulkAPIView(APIView):
    serializer_class = ProjectUpdateSerializer
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(request_body=ProjectUpdateSerializer(many=True))
    def post(self, request):
        data = request.data
        print(data)
        if isinstance(data, dict):  # Single create
            return self.handle_create([data], request)
        elif isinstance(data, list):  # Bulk create
            return self.handle_create(data, request)
        else:
            return Response({"error": "Invalid data format"}, status=status.HTTP_400_BAD_REQUEST)

    def handle_create(self, data, request):
        serializer = ProjectUpdateSerializer(data=data, many=True, context={'request': request})
        if serializer.is_valid():
            try:
                self.perform_create(serializer)
                return Response({"message": "Operation teams created successfully"}, status=status.HTTP_201_CREATED)
            except ValueError as ve:
                return JsonResponse({'error': str(ve)}, status=status.HTTP_400_BAD_REQUEST)
            except Exception as e:
                return JsonResponse({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def perform_create(self, serializer):
        for item in serializer.validated_data:
            ProjectUpdate.objects.create(**item)
            

class OperationTeamListView(APIView):
    permission_classes = (permissions.AllowAny,)
    serializer_class = ProjectPerDaySerializer

    @swagger_auto_schema(request_body=ProjectPerDaySerializer)
    def post(self, request, *args, **kwargs):
        serializer = ProjectPerDaySerializer(data=request.data)
        try:
            if serializer.is_valid():
                project_id = serializer.validated_data['project_id']
                print('@@@@@@@@@@@@@@@')
                if project_id:
                    operation_teams = ProjectUpdate.objects.filter(project_id=project_id).all()
                else:
                    operation_teams = ProjectUpdate.objects.all()
                serializer = OperationTeamSerializer(operation_teams, many=True)
                return Response(serializer.data, status=status.HTTP_200_OK)
        except serializers.ValidationError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)



class OperationTeamProjectListView(APIView):
    permission_classes = (permissions.AllowAny,)
    
    @swagger_auto_schema(responses={200: ProjectListSerializer(many=True)})
    def get(self, request, *args, **kwargs):
        try:
            operation_teams = ProjectUpdate.objects.all()
            serializer = ProjectListSerializer(operation_teams, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class ProjectUpdateBatchEditView(APIView):
    permission_classes = (permissions.AllowAny,)
    @swagger_auto_schema(request_body=ProjectUpdateBatchEditSerializer)
    def post(self, request, *args, **kwargs):
        serializer = ProjectUpdateBatchEditSerializer(data=request.data)
        if serializer.is_valid():
            project_id = serializer.validated_data['project_id']
            updates = serializer.validated_data['updates']

            for update in updates:
                try:
                    # Find the ProjectUpdate instance by id and project_id
                    project_update = ProjectUpdate.objects.get(id=update['id'], project_id=project_id)
                    # Update the total_man_days
                    project_update.total_man_days = update['total_man_days']
                    project_update.save()
                except ProjectUpdate.DoesNotExist:
                    return Response({'error': f'ProjectUpdate with id {update["id"]} and project_id {project_id} does not exist.'}, status=status.HTTP_404_NOT_FOUND)

            return Response({'message': 'Total man days updated successfully.'}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)





################################################################################ AGGREATE TOTAL MAN DAYS WITH UPDATED USER ##########################################################

class OperationTeamProjectListView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = (IsAuthenticated,)  # Allow only authenticated users

    @swagger_auto_schema(responses={200: ProjectListSerializer(many=True)})
    def get(self, request, *args, **kwargs):
        try:
            # Step 1: Get all records ordered by 'updated_by' and '-id'
            project_updates = ProjectUpdate.objects.all().order_by('-id')

            # Step 2: Prepare final data to store results and track unique users
            final_data = []
            processed_users = set()  # To keep track of users that have been processed

            # Step 3: Iterate through each entry, handling one user at a time
            for entry in project_updates:
                if entry.updated_by_id not in processed_users:
                    # Get the last five entries for the new user (different updated_by)
                    last_five_entries = ProjectUpdate.objects.filter(updated_by=entry.updated_by).order_by('-id')[:5]

                    # Aggregate totals for total_man_days, remaining_interview, total_achievement
                    aggregated_data = last_five_entries.aggregate(
                        total_man_days=Sum('total_man_days'),
                        remaining_interview=Sum('remaining_interview'),
                        total_achievement=Sum('total_achievement')
                    )

                    # Prepare individual entries for the last 5 records, keeping their unique fields
                    entries_data = []
                    for sub_entry in last_five_entries:
                        entries_data.append({
                            'id': sub_entry.id,
                            'update_date': sub_entry.update_date,
                            'total_man_days': sub_entry.total_man_days,
                            'sample': sub_entry.project_id.sample,
                            'cpi': sub_entry.project_id.cpi,
                            'remaining_time': sub_entry.remaining_time,
                            'is_active': sub_entry.is_active,
                            'project_id': sub_entry.project_id_id,
                        })

                    # Append the calculated totals and entries to the final data
                    final_data.append({
                        'updated_by': entry.updated_by_id,
                        'total_man_days': aggregated_data['total_man_days'],
                        'remaining_interview': aggregated_data['remaining_interview'],
                        'total_achievement': aggregated_data['total_achievement'],
                        'entries': entries_data  # The last five individual entries for the user
                    })

                    # Add the user to the processed_users set to avoid duplicates
                    processed_users.add(entry.updated_by_id)

            return Response(final_data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
