from rest_framework import viewsets
from django.shortcuts import render
from django.http import HttpResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import generics
from rest_framework import status
from .models import *
from .serializers import *
from drf_yasg.utils import swagger_auto_schema
from rest_framework import permissions
from django.contrib.auth import get_user_model
from rest_framework import serializers
from django.shortcuts import get_object_or_404
from django.core.mail import send_mail
from rest_framework.exceptions import NotFound
from django.utils.html import strip_tags
from django.template.loader import render_to_string
from django.template.defaultfilters import linebreaksbr
from rest_framework import viewsets, permissions, status
from django.core import signing
from django.shortcuts import render
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.permissions import IsAuthenticated,AllowAny
from rest_framework.decorators import action
from django.db import transaction
from rest_framework.pagination import PageNumberPagination
from rest_framework.exceptions import NotFound
from django.http import HttpResponse, HttpResponseNotFound, Http404
from api.user.serializers import *
from api.operation.models import *
import logging
from django.views.decorators.cache import cache_page
from django.core.cache import cache
from django.conf import settings
from django.utils.decorators import method_decorator
from api.project.notifications import *
from django.db.models import Q
from api.finance.models import FinanceRequest,AdvanceBillingRequisition
from django.db.utils import IntegrityError
from rest_framework.generics import UpdateAPIView
logger = logging.getLogger(__name__)
############################################# USER ROLE AS MANAGER IN PROJECT VIEWS ######################################


class UserRoleViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = UserRole.objects.all()
    serializer_class = UserRoleSerializer  # This will be used for other actions

    @action(detail=False, methods=['get'])
    def managers(self, request):
        manager_role_name = ['Manager','Ass.Manager','Sr.Manager','HOD']
        managers = UserRole.objects.filter(role__name__in=manager_role_name, department__name='Operation')
        serializer = UserRoleSerializer(managers, many=True)
        return Response(serializer.data)
    
################################################## TL Under Manager ############################################################


class TeamLeadsUnderManagerView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    def get_subordinates(self, manager_role):
        """Recursively fetch all subordinates of a given manager role."""
        subordinates = UserRole.objects.filter(reports_to=manager_role)
        all_subordinates = list(subordinates)
 
        for subordinate in subordinates:
            # Recursively fetch subordinates of each subordinate
            all_subordinates.extend(self.get_subordinates(subordinate))
        
        return all_subordinates
    
    def get(self, request, manager_id, format=None):
        try:
            print(manager_id,'manager manager id manager id id did')
            # Fetch the UserRole of the Manager
            manager_role = UserRole.objects.get(id=manager_id)
 
            # Check if the manager's role is 'Director'
            if manager_role.role.name == 'Director':
                # If the manager is a Director, get all Team Leads
                team_leads = UserRole.objects.filter(role__name__in=[role.name for role in Role.objects.all()],department__name='Operation')
                # unique_assignments = {assignment.project_id.id: assignment for assignment in assignments}.values()
            elif manager_role.role.name in [role.name for role in Role.objects.all()]:
                # If the manager is a Manager, get only the Team Leads reporting to this Manager
                team_leads = UserRole.objects.filter(
                    reports_to=manager_role,
                    role__name__in=[role.name for role in Role.objects.all()],
                    department__name='Operation'
                )
            else:
                return Response(
                    {'error': 'The specified user is neither a Manager nor a Director'},
                    status=status.HTTP_400_BAD_REQUEST
                )
 
            all_subordinates = self.get_subordinates(manager_role)
            
            
            # Serialize the manager details
            manager_serializer = UserRoleSerializer(manager_role) 
            # Serialize the user information of the Team Leads
            team_leads_serializer = UserRoleSerializer(team_leads, many=True)
            
            subordinates_serializer = UserRoleSerializer(all_subordinates, many=True)
            
            response_data = {
                'manager': manager_serializer.data,
                'team_leads': team_leads_serializer.data,
                'subordinates': subordinates_serializer.data
            }
 
            return Response(response_data, status=status.HTTP_200_OK)
 
        except UserRole.DoesNotExist:
            return Response(
                {'error': 'Manager not found'},
                status=status.HTTP_404_NOT_FOUND
            )



####################################################### Project API View #######################################################
#class ProjectPagination(PageNumberPagination):
#    page_size = 10  # Customize as needed


#class ProjectListAPIView(APIView):
#    authentication_classes = [JWTAuthentication]
#    permission_classes = [IsAuthenticated]

    
#    def get(self, request):
#        try:
            # Check if data is cached
            #projects = cache.get('projects')
            

            #if not projects:
                # Fetch data from the database
#                projects = Project.objects.filter(is_active=True).order_by("-created_at").select_related(
#                    'project_type', 'clients', 'created_by', 'assigned_to'
#                ).prefetch_related(
#                    'project_samples', 'documents'
#                )

#                # Serialize the data
#                serializer = ProjectSerializer(projects, many=True)
#                
#                # Manipulate the project_samples and sample fields in the serializer data
#                for project_data in serializer.data:
#                    # Custom logic for project_samples
#                    project_samples = project_data.get('project_samples', [])
#                    if project_samples:
#                        project_data['project_samples'] = [
#                            {   
#                                'id': sample.get('id'),
#                                'sample': sample.get('sample'),
#                                'cpi': sample.get('cpi'),
#                                'target_group': sample.get('target_group')
#                            } for sample in project_samples
#                        ]
#                    else:
#                        pass
#                        # If no project_samples exist, use the default sample and cpi
                        #project_data['project_samples'] = [{
                            #'sample': project_data.get('sample'),
                            #'cpi': project_data.get('cpi'),
                            #'project_id': project_data.get('id'),
                        #}]

#                    # Add Project Assignment details
#                    assignments = ProjectAssignment.objects.filter(project_id=project_data['id']).select_related(
#                        'assigned_by__user', 'assigned_to__user'
#                    )
#
#                    if assignments.exists():
#                        first_assignment = assignments.first()
#                        project_data['project_assigned_by_manager'] = {
#                            'id': first_assignment.assigned_by.id,
#                            'name': first_assignment.assigned_by.user.username
#                        }
#                        project_data['project_assigned_to_teamlead'] = [
#                            {
#                                'id': assignment.assigned_to.id,
#                                'name': assignment.assigned_to.user.username
#                            } for assignment in assignments
#                        ]
#                    else:
#                        project_data['project_assigned_by_manager'] = None
#                        project_data['project_assigned_to_teamlead'] = []
#                    
#                    # Fetch and add project documents
#                    documents = ProjectDocument.objects.filter(project_id=project_data['id'])
#                    project_data['documents'] = [
#                        {
#                            'id': doc.id,
#                            'upload_document': doc.upload_document.url if doc.upload_document else None,
#                            'uploaded_at': doc.uploaded_at,
#                            'updated_at': doc.updated_at
#                        } for doc in documents
#                    ]
#                # Cache the serialized and modified data
#                #cache.set('projects', serializer.data, timeout=settings.CACHE_TTL)
#                return Response(serializer.data, status=status.HTTP_200_OK)
#            #else:
#                # Return cached data
#                #return Response(projects, status=status.HTTP_200_OK)
#        except Exception as e:
#            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class ProjectPagination(PageNumberPagination):
    page_size = 10  # Number of items per page
    page_size_query_param = 'page_size'  # Allow clients to override `page_size`
    max_page_size = 100  # Maximum limit for `page_size`

from django.db.models import Q
from datetime import datetime


class ProjectListAPIView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def get(self, request):

        try:
            user_role = request.user.userrole
            print("user_role.id", user_role.id)
        except UserRole.DoesNotExist:
            return Response({"error": "User role not assigned"}, status=400)
        

        page = request.query_params.get('page', 1)
        page_size = request.query_params.get('page_size', 10)
        status = request.query_params.get('status', None)  # Add status filter
        cache_key = f"projects_{request.user.userrole.id}_page_{page}_size_{page_size}_status_{status}"

        # Generate a cache key unique to the user
        # cache_key = f"projects_{request.user.userrole.id}"
        cached_projects = cache.get(cache_key)

        if cached_projects:
            # Return cached response if available
            return Response(cached_projects)
        


        current_year = datetime.now().year

        # Define modular conditions
        filter_tentative_end_in_current_year = Q(tentative_end_date__year=current_year)  # End date in current year
        filter_created_in_current_year = Q(tentative_start_date__year=current_year)  # Created in current year

        # Combine filtering conditions
        filters = filter_tentative_end_in_current_year | filter_created_in_current_year

        # Prefetch related data for optimization
        projects_qs = Project.objects.filter(is_active=True).filter(filters).prefetch_related(
            'assigned_to',  # Prefetch assigned users
            'created_by',   # Prefetch creators
        ).select_related(
            'assigned_to__role',  # Fetch related role for the assigned user
            'created_by__role',   # Fetch related role for the creator
        ).order_by('-created_at')


        if status and status.lower() != "all":
            projects_qs = projects_qs.filter(status=status)
            print("Filtered project_qs count:", projects_qs.count())
        else:
            projects_qs = projects_qs 
        # Initialize the projects queryset
        projects = projects_qs.none()

        if user_role.role.name == 'Director':
            # Case 1: Director - Show all projects
            projects = projects_qs

        elif user_role.role.name == 'HOD' and user_role.department.name == 'Operation':
            # Case 2: HOD (Operations) - Show projects assigned to subordinates
            subordinates = self.get_subordinates(user_role, ['Sr.Manager', 'Ass.Manager', 'Manager'])
              # Ensure subordinates include all relevant users
            print("Subordinates for HOD:", subordinates)
            projects = projects_qs.filter(
                Q(assigned_to=user_role) | Q(assigned_to__in=subordinates)
            )
            print("projects", projects)

        elif user_role.role.name == 'Sr.Manager' and user_role.department.name == 'Operation':
            # Case 3: Sr.Manager - Show projects directly assigned and to reporting managers
            subordinates = self.get_subordinates(user_role, ['Manager', 'Ass.Manager'])
            projects = projects_qs.filter(
                Q(assigned_to=user_role) | Q(assigned_to__in=subordinates)
            )

        elif user_role.role.name == 'Manager':
            # Case 4: Manager - Include projects assigned to them and their subordinates
            subordinates = self.get_subordinates(user_role, ['Ass.Manager', 'Team Lead'])
            projects = self.get_projects_for_user_and_subordinates(user_role, subordinates, projects_qs)

        elif user_role.role.name == 'Ass.Manager' and user_role.department.name == 'Operation':
            # Case 5: Assistant Manager - Similar to Manager logic
            subordinates = self.get_subordinates(user_role, ['Team Lead'])
            projects = self.get_projects_for_user_and_subordinates(user_role, subordinates, projects_qs)

        elif user_role.role.name == 'Team Lead':
            if user_role.department.name == 'Sales':
                # Case 6: Team Lead (Sales) - Projects created by them
                projects = projects_qs.filter(created_by=user_role)
                print("MANAGER SALES PROJECT", projects.count())
            elif user_role.department.name == 'Operation':
                # Case 7: Team Lead (Operations) - Projects assigned via ProjectAssignment
                project_ids = ProjectAssignment.objects.filter(assigned_to=user_role).values_list('project_id', flat=True) 
                projects = projects_qs.filter(id__in=project_ids)

        elif user_role.role.name == 'Manager' and user_role.department.name =='Sales':
            projects = projects_qs.filter(created_by=user_role)


        elif user_role.role.name == 'HOD' and user_role.department.name == 'Sales':
            subordinates = self.get_subordinates(user_role, ['Sr.Manager', 'Ass.Manager', 'Manager', 'Team Lead'])
            #projects = projects_qs.filter(Q(created_by__in=subordinates))
            projects = projects_qs.filter(Q(created_by__in=subordinates) | Q(created_by=user_role)).distinct()
    

        elif user_role.role.name == 'HOD' and user_role.department.name == 'Finance':
            projects = projects_qs
               #Q(status='CBR Raised'
            #print("Projects with CBR Raised for Finance HOD:", projects.count())
     

        # Paginate the queryset
        paginator =  ProjectPagination()
        paginated_projects = paginator.paginate_queryset(projects, request)      
        paginator.page_size = page_size
        # Serialize and return the data
        serializer = ProjectSerializer(paginated_projects, many=True)
        serializer_data = serializer.data
     
        #cache.set(cache_key, serializer_data, timeout=settings.CACHE_TTL)
        cache.set(cache_key, {
                "count": projects.count(),
                "next": paginator.get_next_link(),
                "previous": paginator.get_previous_link(),
                "results": serializer_data
            }, timeout=settings.CACHE_TTL)

        # return Response(serializer_data)
        return paginator.get_paginated_response(serializer_data)


    def get_subordinates(self, user_role, roles=None):
        """
        Fetch all subordinates recursively for a given user_role.
        """
        all_subordinates = set()
        queue = [user_role]

        while queue:
            current_role = queue.pop(0)
            subordinates = UserRole.objects.filter(reports_to=current_role)
            if roles:
                subordinates = subordinates.filter(role__name__in=roles)

            all_subordinates.update(subordinates)
            queue.extend(subordinates)

        return list(all_subordinates)

    

    def get_projects_for_user_and_subordinates(self, user_role, subordinates, projects_qs):
        """
        Fetch projects assigned to the user or their subordinates.
        """
        project_ids = ProjectAssignment.objects.filter(assigned_to=user_role).values_list('project_id', flat=True)
        return projects_qs.filter(
            Q(assigned_to=user_role) |
            Q(assigned_to__in=subordinates) |
            Q(id__in=project_ids)
        ).distinct()




    def post(self, request, *args, **kwargs):
        data = request.data.copy()
        
        manager = self.get_user_role(data.get('project_manager'))
        project_type = self.get_project_type(data.get('project_type'))
        data['created_by'] = self.get_user_role(request.user.id).id
        data['assigned_to'] = manager.id
        data['project_type'] = project_type.id


        serializer = ProjectSerializer(
            data=data,
            context={
                'request': request,
                'is_multiple_sample_cpi': data.get('is_multiple_sample_cpi')
            }
        )
        
        if serializer.is_valid():
            project = serializer.save()
            #advanced_billing_raised = request.data.get('advanced_billing_raised', None)
            #if advanced_billing_raised:
                    #FinanceRequest.objects.create(
                        #project=project,
                        #requested_by=request.user.userrole,
                        #remarks=request.data.get('remark', ''),
                        #advanced_billing_raised=advanced_billing_raised,
                       # advance_billing_amount = request.data.get('advance_billing_amount',None)
                    #)
            if data.get('is_multiple_sample_cpi') == 'True':
                self.create_project_samples(data, project)
            else:
                self.create_single_sample(data, project)

            # Invalidate cache
            cache.delete_pattern('projects_*')
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def create_project_samples(self, data, project):
        index = 0
        sample_count = 0  # Counter for created samples
        samples_exist = True
        max_samples = sum(1 for key in data if key.startswith('project_samples[') and 'target_group' in key)
        while samples_exist and sample_count < max_samples:
            target_group_key = f'project_samples[{index}][target_group]'
            sample_key = f'project_samples[{index}][sample]'
            cpi_key = f'project_samples[{index}][cpi]'

            target_group = data.get(target_group_key)
            sample = data.get(sample_key)
            cpi = data.get(cpi_key)

            # Check if all fields for the sample are present and non-empty
            if target_group and sample and cpi:
                ProjectSample.objects.create(
                    project=project,
                    target_group=target_group,
                    sample=sample,
                    cpi=cpi
                )
                sample_count += 1  # Increment the sample count
                index += 1  # Move to the next index
            else:
                # Stop the loop if any of the fields are missing or empty
                samples_exist = False

    def create_single_sample(self, data, project):
        #target_group = data.get('project_samples[0][target_group]')
        target_group = None
        sample = data.get('project_samples[0][sample]')
        cpi = data.get('project_samples[0][cpi]')
        print('$$$$$$$$$$$$$$',target_group)
        
        # Only create if all necessary fields are provided
        if sample and cpi:
            ProjectSample.objects.create(
                project=project,
                target_group=target_group,
                sample=sample,
                cpi=cpi
            )

    def get_user_role(self, user_id):
        try:
            return UserRole.objects.get(user__id=user_id)
        except UserRole.DoesNotExist:
            raise ValidationError("Manager or user role does not exist.")

    def get_project_type(self, project_type_id):
        try:
            return projectType.objects.get(id=project_type_id)
        except projectType.DoesNotExist:
            raise ValidationError("Project Type does not exist.")

class ProjectDetailAPIView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    def get_object(self, pk):
        try:
            return get_object_or_404(Project, pk=pk)
        except Http404:
            raise Http404("Project does not exist")
        except Exception as e:
            raise e
    
    def get(self, request, pk):
        try:
            project = self.get_object(pk)
            serializer = ProjectSerializer(project)
            return Response(serializer.data)
        except Http404 as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def put(self, request, pk):
        try:
            project = self.get_object(pk)
            serializer = ProjectSerializer(project, data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Http404 as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def delete(self, request, pk):
        try:
            project = self.get_object(pk)
            project.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Http404 as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


    def patch(self, request, pk):
        try:
            project = self.get_object(pk)
            data = request.data

            # Only allow updates to man_days or tentative_end_date
            partial_data = {}
            if 'man_days' in data:
                partial_data['man_days'] = data['man_days']
            if 'tentative_end_date' in data:
                partial_data['tentative_end_date'] = data['tentative_end_date']

            serializer = ProjectSerializer(project, data=partial_data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Http404 as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)        
        

class ProjectCustomActionAPIView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    def get_object(self, pk):
        try:
            return get_object_or_404(Project, pk=pk)
        except Http404:
            raise Http404("Project does not exist")
        except Exception as e:
            raise e
    
    def post(self, request, pk):
        try:
            project = self.get_object(pk)
            # Perform custom action logic here
            return Response({"message": f"Custom action performed for project {pk}"}, status=status.HTTP_200_OK)
        except Http404 as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ProjectDocumentUpdateView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, project_id):
        # Check if project exists with the given project_id
        try:
            project = Project.objects.get(id=project_id)
        except Project.DoesNotExist:
            return Response(
                {"error": "Project with the given ID does not exist."},
                status=status.HTTP_404_NOT_FOUND
            )

        # Ensure that upload_document data is provided
        uploaded_files = request.data.getlist('upload_document')
        if not uploaded_files:
            return Response(
                {"error": "No files provided in upload_document."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # List to store the created document data with project details
        created_data = []

        # Iterate through the uploaded files and create a new ProjectDocument instance for each
        for upload_file in uploaded_files:
            # Create the ProjectDocument instance directly
            project_document = ProjectDocument.objects.create(
                project=project,
                upload_document=upload_file
            )

            # Serialize the created instance and add project_id and project_name to the response
            serializer = ProjectDocumentSerializer(project_document)
            document_data = serializer.data
            document_data['project_id'] = project.id
            document_data['project_name'] = project.name
            created_data.append(document_data)

        # Return the list of created document data, including project_id and project_name
        return Response(created_data, status=status.HTTP_201_CREATED)

    def patch(self, request, project_id):
        # Get all documents associated with the given project_id
        documents = ProjectDocument.objects.filter(project_id=project_id).order_by('id')
        
        if not documents.exists():
            return Response(
                {"error": "No documents found for this project_id."},
                status=status.HTTP_404_NOT_FOUND
            )

        # Ensure that upload_document data is a list of files
        uploaded_files = request.data.getlist('upload_document')
        if not uploaded_files:
            return Response(
                {"error": "No files provided in upload_document."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Iterate through the documents and uploaded files to update each document
        updated_data = []
        for document, upload_file in zip(documents, uploaded_files):
            serializer = ProjectDocumentUpdateSerializer(
                document, data={'upload_document': upload_file}, partial=True
            )
            if serializer.is_valid():
                serializer.save()
                updated_data.append(serializer.data)
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        return Response(updated_data, status=status.HTTP_200_OK)
    
    
    def get(self, request, project_id):
        try:
            # Get the project based on project_id
            project = Project.objects.get(id=project_id, is_active=True)
            
            # Fetch all related documents for the project
            documents = ProjectDocument.objects.filter(project=project).order_by('id')

            if not documents.exists():
                return Response(
                    {"error": "No documents found for this project."},
                    status=status.HTTP_404_NOT_FOUND
                )

            # Serialize the documents
            serializer = ProjectDocumentSerializer(documents, many=True)
            return Response({"project_id": project_id, "upload_document": serializer.data}, status=status.HTTP_200_OK)
        
        except Project.DoesNotExist:
            return Response(
                {"error": "Project with the specified ID does not exist or is inactive."},
                status=status.HTTP_404_NOT_FOUND
            )

########### Project Type Update API ##############################
class ProjectTypeUpdateView(UpdateAPIView):
    queryset = Project.objects.all()
    serializer_class = ProjectTypeUpdateSerializer
    lookup_field = "id"
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def patch(self,request,*args, **kwargs):
        project_obj = self.get_object()
        serializer = self.get_serializer(project_obj, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({"message":"Project type updated successfully","data":serializer.data},status=status.HTTP_200_OK)
        return Response(serializer.errors,status=status.HTTP_400_BAD_REQUEST)
############################################### CLIENT VIEWS #################################################################

# from cacheops import cached_as

class ClientPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

class ClientViewSet(viewsets.ModelViewSet):
    serializer_class = ClientSerializer
    pagination_class = ClientPagination
    # authentication_classes = [JWTAuthentication]
    # permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = Client.objects.all()
        # name = self.request.query_params.get('name', None)
        # print('hello name',name)
        # if name is not None:
        #     queryset = queryset.filter(name__icontains=name)
        #     print('my name',queryset)
        return queryset

    # @cached_as(Client.objects.all())
    #def list(self, request, *args, **kwargs):
        #queryset = self.filter_queryset(self.get_queryset())
        # print('modify name',queryset)
        # page = self.paginate_queryset(queryset)
        # print('page to page',page)
        # if page is not None:
        #     serializer = self.get_serializer(page, many=True)
        #     return self.get_paginated_response(serializer.data)
        #serializer = self.get_serializer(queryset, many=True)
        #return Response(serializer.data)
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def handle_exception(self, exc):
        if isinstance(exc, NotFound):
            return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)
        return super().handle_exception(exc)


###################################### PROJECT TYPE views ###########################################################

class ProjectTypePagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

class ProjectTypeViewSet(viewsets.ModelViewSet):
    queryset = projectType.objects.all()
    serializer_class = ProjectTypeSerializer
    pagination_class = ProjectTypePagination
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = projectType.objects.all()
        name = self.request.query_params.get('name', None)
        if name is not None:
            queryset = queryset.filter(name__icontains=name)
        return queryset

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def handle_exception(self, exc):
        if isinstance(exc, NotFound):
            return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)
        return super().handle_exception(exc)

############################################ PROJECT ASSIGNMENT BY OPERATION MANAGER  TO OPERATION TL ############################################

@swagger_auto_schema(request_body=ProjectAssignmentSerializer(many=True))
class ProjectAssignmentAPIView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            # Fetch all assignments and remove duplicates based on project_id
            assignments = ProjectAssignment.objects.all()
            unique_assignments = {assignment.project_id.id: assignment for assignment in assignments}.values()
            
            serializer = ProjectAssignmentSerializer(unique_assignments, many=True)
            return Response(serializer.data)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


    @swagger_auto_schema(request_body=ProjectAssignmentSerializer(many=True))
    def post(self, request, *args, **kwargs):
        data = request.data
        if isinstance(data, list):
            # Handle bulk creation
            return self.bulk_create(data)
        else:
            # Handle single creation
            return self.single_create(data)

    def single_create(self, data):
        try:
            with transaction.atomic():
                project_id = data.get('project_id')
                assigned_by_id = data.get('assigned_by')
                assigned_to_id = data.get('assigned_to')
                project_client_pm = data.get('project_client_pm')
                purchase_order_no = data.get('purchase_order_no')
                print(assigned_by_id,assigned_to_id)

                if not project_id or not assigned_by_id or not assigned_to_id:
                    return Response({"error": "Project ID, Assigned By ID, and Assigned To ID are required."}, status=status.HTTP_400_BAD_REQUEST)

                project = get_object_or_404(Project, id=project_id)
                assigned_by = get_object_or_404(UserRole, id=assigned_by_id)
                assigned_to = get_object_or_404(UserRole, id=assigned_to_id)
                print(assigned_by,assigned_to,'******')
                assignment = ProjectAssignment(project_id=project, assigned_by=assigned_by, assigned_to=assigned_to)
                assignment.save()
                 
                project.status = "To Be Started"
                project.project_client_pm = project_client_pm
                project.purchase_order_no = purchase_order_no
                project.save()
                print('YYYYYY')
                #subject = f"Project '{project.name}' Assigned"
                #message = f"Hello {assigned_to.user},\n\nYou have been assigned to the project '{project.name}'.\n\nProject Manager: {project_client_pm}\nPurchase Order No: {purchase_order_no}"
                #recipient_email = assigned_to.user.email
                #send_mail(subject, message, settings.EMAIL_HOST_USER, [recipient_email], fail_silently=False)
                serializer = ProjectAssignmentSerializer(assignment)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def bulk_create(self, data):
        try:
            assignments = []
            with transaction.atomic():
                for item in data:
                    project_id = item.get('project_id')
                    assigned_by_id = item.get('assigned_by')
                    assigned_to_id = item.get('assigned_to')
                    project_client_pm = item.get('project_client_pm')
                    purchase_order_no = item.get('purchase_order_no')

                    if not project_id or not assigned_by_id or not assigned_to_id:
                        return Response({"error": "Project ID, Assigned By ID, and Assigned To ID are required for all items."}, status=status.HTTP_400_BAD_REQUEST)

                    project = get_object_or_404(Project, id=project_id)
                    assigned_by = get_object_or_404(UserRole, id=assigned_by_id)
                    assigned_to = get_object_or_404(UserRole, id=assigned_to_id)

                    assignment = ProjectAssignment(project_id=project, assigned_by=assigned_by, assigned_to=assigned_to)
                    assignment.save()
                    assignments.append(assignment)

                    project.status = "To Be Started"
                    project.project_client_pm = project_client_pm
                    project.purchase_order_no = purchase_order_no
                    project.save()
                    #subject = f"Project '{project.name}' Assigned"
                    #message = f"Hello {assigned_to.user},\n\nYou have been assigned to the project '{project.name}'.\n\nProject Manager: {project_client_pm}\nPurchase Order No: {purchase_order_no}"
                    #recipient_email = assigned_to.user.email
                    #send_mail(subject, message, settings.EMAIL_HOST_USER, [recipient_email], fail_silently=False)

                serializer = ProjectAssignmentSerializer(assignments, many=True)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class UpdateProjectStatusAPIView(APIView):
    serializer_class = ProjectStatusSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(request_body=ProjectStatusSerializer)
    def post(self, request, *args, **kwargs):
        serializer = ProjectStatusSerializer(data=request.data)
        if serializer.is_valid():
            project_id = serializer.validated_data['project_id']
            status_value = serializer.validated_data['status']
            
            try:
                project = Project.objects.get(id=project_id)
                last_project_update = ProjectUpdate.objects.filter(project_id=project_id).last()
                
                if last_project_update:
                    last_project_update.status = status_value
                    last_project_update.save()
                
                project.status = status_value
                project.save()
                
                return Response({"message": "Project status updated successfully."}, status=status.HTTP_200_OK)
            except Project.DoesNotExist:
                return Response({"message": "Project with the given ID does not exist."}, status=status.HTTP_404_NOT_FOUND)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



class ProjectEmailView(APIView):
    serializer_class = ProjectEmailSerializer
    # authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    @swagger_auto_schema(request_body=ProjectEmailSerializer)
    def post(self, request):
        logger.info("Received request data: %s", request.data)
        serializer = ProjectEmailSerializer(data=request.data)

        if serializer.is_valid():
            project_id = serializer.validated_data['project_id']
            try:
                project = get_object_or_404(Project, id=project_id)
            except Exception as e:
                logger.error("Error fetching project: %s", e)
                return Response({"error": "Project not found."}, status=status.HTTP_404_NOT_FOUND)

            sample = project.sample if serializer.validated_data.get('sample') == "" else serializer.validated_data.get('sample')
            tentative_end_date = serializer.validated_data.get('tentative_end_date')
            reason_for_adjustment = serializer.validated_data.get('reason_for_adjustment', '')

            user_role = UserRole.objects.get(user=request.user.id)  
            
            #manager_emails = "ankit.sharma@novusinsights.com"
            manager_emails = user_role.reports_to.user.email
            frm_email = "noreply.erp@unimrkt.com"

            subject = f"Project Update: {project.name}"
            message = f"""Dear Manager,

            Here is an update on the project:

            - **Project ID**: {project_id}
            - **Sample**: {sample}
            - **Tentative End Date**: {tentative_end_date}
            - **Reason for Adjustment**: {reason_for_adjustment}

            Please review the project details at your earliest convenience.
            """

            to_email = manager_emails

            try:
                send_mail(
                    subject,
                    message,
                    frm_email,
                    [to_email],
                )
                logger.info("Email sent successfully to: %s", to_email)
            except Exception as e:
                logger.error("Error sending email: %s", e)
                return Response({"error": f"Failed to send email.{e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            try:
                ProjectUpdatedData.objects.update_or_create(
                    project_id=project_id,
                    defaults={
                        'sample': sample,
                        'tentative_end_date': tentative_end_date,
                        'reason_for_adjustment': reason_for_adjustment,
                        'updated_by' : user_role,
                    }
                )
                project.send_email_manager = True
                #project.sample = sample
                #project.tentative_end_date = tentative_end_date
                project.save()
            except Exception as e:
                logger.error("Error updating project data: %s", e)
                return Response({"error": f"Failed to update project data.{e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            context = {
                "message": "Email sent successfully!",
                "project_id": project_id,
                "sample": sample,
                "tentative_end_date": tentative_end_date,
                "reason_for_adjustment": reason_for_adjustment
            }
            return Response(context, status=status.HTTP_200_OK)
        else:
            logger.error("Serializer errors: %s", serializer.errors)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ProjectUpdatedDataView(APIView):
    def get(self, request, project_id):
        # Get the project based on project_id and check if send_email_manager is True
        project = get_object_or_404(Project, id=project_id, send_email_manager=True)

        # Filter data in ProjectUpdatedData based on project_id
        updated_data = ProjectUpdatedData.objects.filter(project_id=project_id)

        if updated_data.exists():
            serializer = ProjectUpdatedDataSerializer(updated_data, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response({"message": "No updated data found for this project ID."}, status=status.HTTP_404_NOT_FOUND)



########################################################################## Project Edit Notification ######################################

class ProjectUpdateView(viewsets.ViewSet):
    @swagger_auto_schema(request_body=ProjectNotificationOffSerializer)
    @action(detail=False, methods=['put'], url_path='with-projectid')  # Updated URL path
    def update_by_id(self, request):
        # Extract project_id from request data
        project_id = request.data.get('id')  # Changed from 'project_code' to 'id'

        # Validate project_id
        if not project_id:
            return Response({'detail': 'Project ID is required.'}, status=status.HTTP_400_BAD_REQUEST)

        # Attempt to retrieve the project by project_id
        try:
            project = Project.objects.get(id=project_id)  # Changed from project_code to id
        except Project.DoesNotExist:
            return Response({'detail': 'Project not found.'}, status=status.HTTP_404_NOT_FOUND)

        # Serialize and update the project with allowed fields
        serializer = ProjectNotificationOffSerializer(project, data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save()  # Save the updated project details

            # Update additional fields from ProjectUpdatedData
            try:
                project_notification_data = ProjectUpdatedData.objects.get(project_id=project_id)
                project.sample = project_notification_data.sample
                project.tentative_end_date = project_notification_data.tentative_end_date
                project.save()
            except ProjectUpdatedData.DoesNotExist:
                return Response({'detail': 'Project notification data not found.'}, status=status.HTTP_404_NOT_FOUND)

            return Response({"message": "Project updated successfully", "data": serializer.data}, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



##################################################################### Project Sample View ######################################################
from .serializers import ProjectSampleSerializer
class ProjectSampleDetailView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]
 
    def get(self, request, pk):
        try:
            # Get project by ID and filter all related samples
            project = get_object_or_404(Project, pk=pk)
            samples = ProjectSample.objects.filter(project=project)  # Filter by project ID
            serializer = ProjectSampledSerializer(samples, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Project.DoesNotExist:
            return Response({"error": "Project not found."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            # Generic exception handling for unexpected errors
            return Response(
                {"error": "An unexpected error occurred.", "details": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
    def put(self, request, pk):
        # Get the sample instance to be updated
        sample = get_object_or_404(ProjectSample, pk=pk)
 
        # Check if there are pending changes
        if sample.pending_changes:
            return Response(
                {"error": "You have already raised a request for sample revision."},
                status=status.HTTP_400_BAD_REQUEST,
            )
 
        # If no pending changes, update the sample data
        serializer = ProjectSampleSerializer(sample, data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
 
    def patch(self, request, pk):
        """
        Handle the update of multiple ProjectSample records based on the project ID.
        """
        project = get_object_or_404(Project, pk=pk)  # Get the project based on the project ID
        # Fetch all project updates for this project
        project_updates = ProjectUpdate.objects.filter(project_id=project)

        # Calculate total remaining samples
        total_achievement = sum(
            int(update.total_achievement) for update in project_updates if update.total_achievement
        )
       
        # Check if the incoming data is a list or a single object
        if isinstance(request.data, list) and len(request.data) > 1:
            # Handle multiple samples
            return self.update_multiple_samples(request.data, project, request,total_achievement)
 
        else:
            # Handle single sample update
            return self.update_single_sample(request.data[0], project, request,total_achievement)
 
 
    def update_multiple_samples(self, samples_data, project, request,total_achievement):
        """
        Handle the update of multiple samples for a given project.
        """
        updated_samples = []
        total_sent_samples = sum(int(sample_data.get('sample')) for sample_data in samples_data if sample_data.get('sample'))
        remaining_sample  = int(project.sample)-int(total_achievement)
        if total_sent_samples < total_achievement:
            return Response(
                {
                    "error": f"Sent samples ({total_sent_samples}) are less than the achieved samples ({total_achievement}). "
                            f"Increase the sample size to match the achievement."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        for sample_data in samples_data:
            # Get the sample instance to be updated based on the project ID
            sample = get_object_or_404(ProjectSample, pk=sample_data.get('id'), project=project)
            # Check if there's already a pending revision request
            if sample.pending_changes:
                return Response(
                    {"error": f"Sample {sample.id} already has a pending revision request."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
 
            # Save the pending changes if manager approval is not given
            sample.pending_changes = {
                "sample": sample_data.get('sample'),
                "cpi": sample_data.get('cpi'),
                "target_group": sample_data.get('target_group'),
                "remark": sample_data.get('remark'),
                "tentative_end_date": sample_data.get('tentative_end_date')
            }
            #sample.date = sample_data.get('tentative_end_date')
            sample.save()
 
            self.notify_manager(sample)
 
            updated_samples.append(sample_data)
 
        return Response(updated_samples, status=status.HTTP_200_OK)
 
    def update_single_sample(self, sample_data, project, request,total_achievement):
       
        """
        Handle the update of a single sample for a given project.
        """
        sample = get_object_or_404(ProjectSample, pk=sample_data.get('id'), project=project)
        sent_sample = int(sample_data.get('sample'))
        remaining_sample  = int(project.sample)-(total_achievement)
            
        if sent_sample < total_achievement:
                return Response(
                    {
                        "error": f"Sent samples ({sent_sample}) are less than the achieved samples ({total_achievement}). "
                                f"Increase the sample size to match the achievement."
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
        # Check if there's already a pending revision request
        if sample.pending_changes:
            return Response(
                {"error": f"Sample {sample.id} already has a pending revision request."},
                status=status.HTTP_400_BAD_REQUEST,
            )
 
        # Save the pending changes if manager approval is not given
        sample.pending_changes = {
            "sample": sample_data.get('sample'),
            "cpi": sample_data.get('cpi'),
            "target_group": sample_data.get('target_group'),
            "remark": sample_data.get('remark'),
            "tentative_end_date": sample_data.get('tentative_end_date')
        }
        #sample.date = sample_data.get('tentative_end_date')
        
        sample.save()
 
        self.notify_manager(sample)
 
        return Response(sample_data, status=status.HTTP_200_OK)
 
    def notify_manager(self, sample):
        assign_by_user = sample.project.assigned_to
        if assign_by_user:
            message = f"Sample {sample.sample} has been updated for project {sample.project.name}."
            subject = f"Sample Update Notification for {sample.project.name}"
            email = assign_by_user.user.email  # Replace with correct email field
            #email = "pramod.kumar@novusinsights.com"
            send_notification(assign_by_user, message, subject, email, project_sample=sample, project_id=sample.project)

############################################ Project Sample Approval View ##################################################################
from dateutil.parser import parse
from datetime import datetime

class ApproveSampleRevisionView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def post(self, request, pk):
        """
        Handle approval or rejection of the revision by the project manager for all samples under a project.
        """
        project = get_object_or_404(Project, pk=pk)

        # Get all samples related to this project
        samples = ProjectSample.objects.filter(project=project)

        # Initialize a response list to track which samples were approved or rejected
        updated_samples = []

        # Default values for approval and rejection
        is_approved = request.data.get('is_approved', False)
        is_rejected = request.data.get('is_rejected', False)

        # Ensure either 'is_approved' or 'is_rejected' is set to True
        if not is_approved and not is_rejected:
            return Response(
                {"message": "Either 'is_approved' or 'is_rejected' must be set to True."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        for sample in samples:
            # Ensure there are pending changes to approve or reject
            if not sample.pending_changes:
                continue  # Skip sample if no pending changes

            # Apply the pending changes to the actual sample fields
            sample.sample = sample.pending_changes.get("sample", sample.sample)
            sample.cpi = sample.pending_changes.get("cpi", sample.cpi)
            sample.target_group = sample.pending_changes.get("target_group", sample.target_group)
            sample.remark = sample.pending_changes.get("remark", sample.remark)
            sample.date = sample.pending_changes.get("tentative_end_date",None)

            # Update the approval/rejection status
            if is_approved:
                sample.is_approved = True
                sample.is_rejected = False  # Reset rejection if approved
            elif is_rejected:
                sample.is_rejected = True
                sample.is_approved = False  # Reset approval if rejected

            sample.pending_changes = None  # Clear the pending changes
            sample.updated_by = request.user.userrole
            sample.save()

            updated_samples.append(sample.id)

        if updated_samples:
            return Response(
                {"message": f"Sample revisions updated successfully for samples: {updated_samples}."},
                status=status.HTTP_200_OK,
            )
        else:
            return Response(
                {"message": "No pending revisions found for approval or rejection."},
                status=status.HTTP_400_BAD_REQUEST,
            )







#####################  Reject Sample ######################################
class ProjectSampleReject(APIView):
    def patch(self, request, project_id):
        """
        Handle rejecting all samples related to a specific project.
        """
        project = get_object_or_404(Project, id=project_id)
        samples = ProjectSample.objects.filter(project=project)

        if not samples.exists():
            return Response(
                {"error": "No samples found for the specified project."},
                status=status.HTTP_404_NOT_FOUND,
            )

        updated_samples = []
        for sample in samples:
            sample.is_rejected = True
            sample.pending_changes = None
            sample.is_approved = False
            sample.save(update_fields=["is_rejected", "pending_changes", "is_approved"])
            updated_samples.append(sample)

        # Serialize the updated samples
        serialized_samples = ProjectSampleUpdateSerializer(updated_samples, many=True)
        return Response(
            {"message": "Samples Rejected successfully", "samples": serialized_samples.data},
            status=status.HTTP_200_OK,
        )




############################################################# Notification API VIew ###########################################


from django.db.models import Q
class NotificationCountAPIView(APIView):
    """
    API view to fetch the count of pending notifications for the logged-in user
    along with the associated project ID.
    """
    permission_classes = [IsAuthenticated]
 
    def get(self, request):
        user_role = request.user.userrole  # Assuming `userrole` is accessible from the request
 
        # Query notifications where approval is pending
        pending_notifications = Notification.objects.filter(
        user=user_role
        ).filter(                    
            Q(is_approved=False) & Q(is_rejected=False) 
        )
        # Extract unique project IDs using distinct() to ensure each project is counted only once
        project_ids = list(
            pending_notifications.values_list('project', flat=True).distinct()
        )
        # Handle single project ID case
        project_id_response = [project_ids[0]] if len(project_ids) == 1 else project_ids
        filtered_list = [x for x in project_id_response if x is not None]
        count = len(filtered_list) 
        return Response({
            "notification_count": count,  # Count of unique project IDs
            "project_id": filtered_list,  # Return single project or list of project IDs
        }, status=200)
        
        
    @swagger_auto_schema(request_body=ProjectIDSerializer)
    def post(self, request):
        serializer = ProjectIDSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        project_id = serializer.validated_data['project_id']

        # Filter notifications by project ID and update `is_rejected` to True
        notifications = Notification.objects.filter(project_id=project_id)

        if not notifications.exists():
            return Response(
                {"error": "No notifications found for the given project ID."},
                status=status.HTTP_404_NOT_FOUND
            )
        # Check if any notification's sample is approved
        project_samples = notifications.values_list('is_approved', flat=True)
        if any(project_samples):
            return Response(
                {"message": "Some notifications have samples that are already approved. Rejection skipped."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        for notification in notifications:
            if hasattr(notification, 'project_sample') and notification.project_sample:
                project_sample = notification.project_sample
 
                # Update `pending_changes` and adjust notification status based on approval/rejection
                if notification.is_approved:
                    project_sample.pending_changes = None
                else:
                    notification.is_rejected = True
                    project_sample.pending_changes = None
 
                project_sample.save()
                notification.save()


######################################################### Dashboard Project API #############################################################################################

class DashboardProjectListAPIView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def get(self, request):
        try:
            user_role = request.user.userrole
            print("user_role.id", user_role.id)
        except UserRole.DoesNotExist:
            return Response({"error": "User role not assigned"}, status=400)

        #status = request.query_params.get('status', None)
        cache_key = f"Dashboard_projects_{request.user.userrole.id}"

        cached_projects = cache.get(cache_key)
        if cached_projects:
            return Response(cached_projects)

        #print("status", status)
        current_year = datetime.now().year
        # Define modular conditions
        filter_tentative_end_in_current_year = Q(tentative_end_date__year=current_year)  # End date in current year
        filter_created_in_current_year = Q(tentative_start_date__year=current_year)  # Created in current year

        # Combine filtering conditions
        filters = filter_tentative_end_in_current_year | filter_created_in_current_year

        # Prefetch related data for optimization
        projects_qs = Project.objects.filter(is_active=True).filter(filters).prefetch_related('assigned_to','created_by',).select_related('assigned_to__role','created_by__role',).order_by('-created_at')


        #if status and status.lower() != "all":
        #    projects_qs = projects_qs.filter(status=status)
        #    print("Filtered project_qs count:", projects_qs.count())

        projects = projects_qs.none()

        if user_role.role.name == 'Director':
            projects = projects_qs

        elif user_role.role.name == 'HOD' and user_role.department.name == 'Operation':
            subordinates = self.get_subordinates(user_role, ['Sr.Manager', 'Ass.Manager', 'Manager'])
            projects = projects_qs.filter(Q(assigned_to=user_role) | Q(assigned_to__in=subordinates))

        elif user_role.role.name == 'Sr.Manager' and user_role.department.name == 'Operation':
            subordinates = self.get_subordinates(user_role, ['Manager', 'Ass.Manager'])
            projects = projects_qs.filter(Q(assigned_to=user_role) | Q(assigned_to__in=subordinates))

        elif user_role.role.name == 'Manager' and user_role.department.name == 'Operation':
            subordinates = self.get_subordinates(user_role, ['Ass.Manager', 'Team Lead'])
            projects = self.get_projects_for_user_and_subordinates(user_role, subordinates, projects_qs)

        elif user_role.role.name == 'Ass.Manager' and user_role.department.name == 'Operation':
            subordinates = self.get_subordinates(user_role, ['Team Lead'])
            projects = self.get_projects_for_user_and_subordinates(user_role, subordinates, projects_qs)

        elif user_role.role.name == 'Team Lead':
            if user_role.department.name == 'Sales':
                projects = projects_qs.filter(created_by=user_role)
            elif user_role.department.name == 'Operation':
                project_ids = ProjectAssignment.objects.filter(assigned_to=user_role).values_list('project_id', flat=True)
                projects = projects_qs.filter(id__in=project_ids)

        elif user_role.role.name == 'HOD' and user_role.department.name == 'Sales':
            subordinates = self.get_subordinates(user_role, ['Sr.Manager', 'Ass.Manager', 'Manager', 'Team Lead'])
            projects = projects_qs.filter(Q(created_by__in=subordinates))

        elif user_role.role.name == 'Sr.Manager' and user_role.department.name == 'Sales':
            reporting_roles = ['Assistant Manager', 'Manager', 'Team Lead']
            reporting_user_roles = UserRole.objects.filter(role__name__in=reporting_roles, reports_to=user_role)
            projects = projects_qs.filter(created_by__in=reporting_user_roles)

        elif user_role.role.name == 'Manager' and user_role.department.name == 'Sales':
            reporting_roles = ['Team Lead']
            reporting_user_roles = UserRole.objects.filter(role__name__in=reporting_roles, reports_to=user_role)
            projects = projects_qs.filter(created_by__in=[user_role] + list(reporting_user_roles))

        elif user_role.role.name == 'HOD' and user_role.department.name == 'Finance':
            projects = projects_qs.filter(Q(status='CBR Raised'))
            print("Projects with CBR Raised for Finance HOD:", projects.count())

        serializer = ProjectSerializer(projects, many=True)
        serializer_data = serializer.data

        cache.set(cache_key, serializer_data, timeout=settings.CACHE_TTL)
        return Response(serializer_data)

    def get_subordinates(self, user_role, roles=None):
        all_subordinates = set()
        queue = [user_role]

        while queue:
            current_role = queue.pop(0)
            subordinates = UserRole.objects.filter(reports_to=current_role)
            if roles:
                subordinates = subordinates.filter(role__name__in=roles)

            all_subordinates.update(subordinates)
            queue.extend(subordinates)

        return list(all_subordinates)

    def get_projects_for_user_and_subordinates(self, user_role, subordinates, projects_qs):
        project_ids = ProjectAssignment.objects.filter(assigned_to=user_role).values_list('project_id', flat=True)
        return projects_qs.filter(
            Q(assigned_to=user_role) |
            Q(assigned_to__in=subordinates) |
            Q(id__in=project_ids)
        ).distinct()

