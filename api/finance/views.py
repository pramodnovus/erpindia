from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from api.project.models import Project
from drf_yasg.utils import swagger_auto_schema
from rest_framework import viewsets, permissions, status
from django.core import signing
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework import status as http_status
from rest_framework.permissions import IsAuthenticated
from .models import *
from drf_yasg.utils import swagger_auto_schema
from api.operation.models import ProjectUpdate
from .serializers import *
from drf_yasg import openapi
from api.project.notifications import send_notification
from django.core.mail import send_mail
from api.project.models import ProjectSample
from django.db.models import Q
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from django.utils.timezone import now
from datetime import timedelta
from .auth import get_user_role
from rest_framework.generics import UpdateAPIView
import logging
from django.shortcuts import get_object_or_404
class ProjectCbrRaisedAPIView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    #@swagger_auto_schema(request_body=ProjectCbrRaisedSerializer)
    def patch(self, request, project_id):
        try:
            project = Project.objects.get(id=project_id)
        except Project.DoesNotExist:
            return Response({"message": "Project not found."}, status=status.HTTP_404_NOT_FOUND)

        if project.status == "CBR Raised":
            return Response(
                {"message": "CBR has already been raised for this project."},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = ProjectCbrRaisedSerializer(data=request.data)
        if serializer.is_valid():
            remarks = serializer.validated_data.get("remarks")
            samples_cpi_data = serializer.validated_data.get("samples")  # List of dicts
            final_status = serializer.validated_data.get("status")

            # Update project status
            ProjectUpdate.objects.filter(project_id=project.id).update(status=final_status)
            project.status = final_status
            project.save()

            # Create or update FinanceRequest
            finance_request, created = FinanceRequest.objects.get_or_create(
                project=project,
                defaults={
                    'final_samples': samples_cpi_data,
                    'cbr_raised_remarks': remarks,
                    'cbr_raised_by_user': request.user.userrole,
                    'status': 'Invoice to be Raised'
                }
            )

            if not created:
                finance_request.final_samples = samples_cpi_data
                finance_request.cbr_raised_remarks = remarks
                finance_request.cbr_raised_by_user = request.user.userrole 
                finance_request.cbr_raised_status = True
                finance_request.status = 'Invoice to be Raised'
                finance_request.save()

            return Response(
                {
                    "message": "Project status updated to 'CBR Raised' and Finance Request handled.",
                    "finance_request_status": "Created" if created else "Updated",
                    "project_id": project.id,
                    "status": project.status
                },
                status=status.HTTP_200_OK
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(request_body=FinanceCbrCreateSerializer)
    def post(self, request):
        data = request.data.copy()

        # Fetch and assign Sales Owner
        sales_owner_id = request.data.get('sales_owner')
        try:
            sales_owner = UserRole.objects.get(id=int(sales_owner_id))
            data['sales_owner'] = str(sales_owner)  # Ensuring it's saved as a string
        except (UserRole.DoesNotExist, ValueError, TypeError):
            return Response({"error": "Invalid sales_owner ID"}, status=status.HTTP_400_BAD_REQUEST)

        # Fetch and assign Project Manager
        project_manager_name = request.data.get('project_manager_name')
        project_manager_role = get_user_role(project_manager_name)
        data['project_manager'] = project_manager_role.id if project_manager_role else None

        # Serialize and save FinanceCBR data
        serializer = FinanceCbrCreateSerializer(data=data, context={"request": request})
        if serializer.is_valid():
            finance_request = serializer.save()
            return Response(
                {"message": "Finance request created successfully", "data": serializer.data},
                status=status.HTTP_201_CREATED
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


###################################################################################################### FINANCE PROJECT API  ##############################################################################

class FinanceProjectAPIView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    
    def get(self, request, project_id=None):
        if project_id:
            # Fetch FinanceRequest for a specific project ID
            finance_requests = FinanceRequest.objects.filter(project_id=project_id).select_related('project')
        else:
            # Fetch all FinanceRequest objects
            finance_requests = FinanceRequest.objects.select_related('project').all()

        if not finance_requests.exists():
            return Response({"error": "No finance requests found."}, status=status.HTTP_404_NOT_FOUND)

        # Serialize the data
        serializer = FinanceRequestSerializer(finance_requests, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

############################################################################################### CBR RELATED FINANCE  #######################################################################################

class FinanceCbrAPIView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
 
    @swagger_auto_schema(responses={200: CbrSerializer(many=True)})
    def get(self, request, project_id=None):
        try:
            # Fetch all FinanceRequest objects
            finance_requests = FinanceRequest.objects.all()
 
            if project_id:
                # Filter finance requests for a specific project
                finance_requests = finance_requests.filter(project__id=project_id)
                if not finance_requests.exists():
                    return Response({"message": "No finance requests found for this project."}, status=status.HTTP_404_NOT_FOUND)
 
            # Serialize the data
            serializer = CbrSerializer(finance_requests, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
 
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

###############################################################################################  VPR API VIEW ########################################################################################
class VPRCreateView(APIView):
    def post(self, request, *args, **kwargs):
        # Step 1: Serialize the data and create the VPR instance
        serializer = VPRSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            vpr_instance = serializer.save()  # Create the VPR object
            
            # Step 2: Send notification to the senior
            self.notify_senior(vpr_instance)  # Notify senior after creation
            
            # Return success response with the created VPR data
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    
    
    def notify_senior(self, vpr):
        """
        Notify the reporting manager or senior when a VPR is created.
        """
        # Get the current user's role
        user_role = self.request.user.userrole
        def get_hod(role):
            """
            Recursively traverse the 'reports_to' hierarchy until HOD is found.
            """
            if role:
                if role.role.name == "HOD":
                    return role  # Return the HOD UserRole object
                elif role.reports_to:
                    return get_hod(role.reports_to) 
                
            return None 
        
        # Get the senior or HOD by traversing the reporting structure
        senior_role = get_hod(user_role)
        # Handle the case where no HOD is found
        if not senior_role:
            return Response(
                {"error": "No HOD found in the reporting hierarchy. Please check the reporting structure."},
                status=status.HTTP_400_BAD_REQUEST
            )
        notification_type = "VPR"
        # Create the notification message
        message = f"A new {notification_type} has been created by {self.request.user.username} for project {vpr.project.name}."
        subject = f"New {notification_type} Created for Project {vpr.project.name}"
        email = senior_role.user.email  # Assuming `user` has an `email` field
        # email = "pramod.kumar@novusinsights.com"
        project_sample_instance = ProjectSample.objects.filter(project=vpr.project).last()  # Fetch the instance
        send_notification(senior_role, message, subject, email, project_id=vpr.project,project_sample=project_sample_instance,notification_type=notification_type)


############### VPR UPDATE #######################

class VPRUpdateView(UpdateAPIView):
    queryset = VPR.objects.all()
    serializer_class = VPRUpdateSerializer
    lookup_field = "id"
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def patch(self, request, *args, **kwargs):
        vpr_obj = self.get_object()
        serializer = self.get_serializer(vpr_obj, data=request.data, partial=True, context={"request": request})
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"message": "VPR updated successfully", "data": serializer.data}, 
                status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


########################################################################################### Finance Project List API ###############################################################################


class FinanceRequestList(APIView):
    permission_classes = [IsAuthenticated]  # Adjust permissions as needed

    def get(self, request, *args, **kwargs):
        # Get the project_id from query parameters
        project_id = request.query_params.get('project_id', None)

        if project_id:
            # Filter FinanceRequests by the specified project_id
            finance_requests = FinanceRequest.objects.filter(project__id=project_id).select_related('project')
        else:
            # If no project_id is provided, return the first project
            finance_requests = FinanceRequest.objects.first()
            if finance_requests:
                finance_requests = [finance_requests]  # Convert the single object to a list

        # Serialize the result
        serializer = FinanceRequestSerializer(finance_requests, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        serializer = FinanceRequestSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class FinanceRequestDetail(APIView):
    permission_classes = [IsAuthenticated]  # Adjust permissions as needed

    def get_object(self, pk):
        try:
            return FinanceRequest.objects.get(pk=pk)
        except FinanceRequest.DoesNotExist:
            return None

    def get(self, request, pk, *args, **kwargs):
        finance_request = self.get_object(pk)
        if finance_request is not None:
            serializer = FinanceRequestSerializer(finance_request)
            return Response(serializer.data)
        return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

    def put(self, request, pk, *args, **kwargs):
        finance_request = self.get_object(pk)
        if finance_request is not None:
            serializer = FinanceRequestSerializer(finance_request, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

    def delete(self, request, pk, *args, **kwargs):
        finance_request = self.get_object(pk)
        if finance_request is not None:
            finance_request.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)



############################ Advance billing post api #################################################

class AdvanceBillingRequisitionCreateView(APIView):
    permission_classes = [IsAuthenticated]  # Restrict to authenticated users

    @swagger_auto_schema(request_body=AdvanceBillingRequisitionCreateSerializer)
    def post(self, request):
        project_id = request.data.get('project')  # Extract project ID
        
        # Prevent duplicate entries for the same project
        if AdvanceBillingRequisition.objects.filter(project_id=project_id).exists():
            return Response(
                {"error": "Advance Billing Requisition already exists for this project."},
                status=status.HTTP_400_BAD_REQUEST
            )
        # Extract user IDs from request data
        project_manager = request.data.get('project_manager')
        created_by = request.data.get('created_by')
        sales_owner = request.data.get('sales_owner')

        # Retrieve corresponding UserRole instances
        project_manager_role = get_user_role(project_manager)

        # If roles exist, add them to request data
        data = request.data.copy()
        data['project_manager'] = project_manager_role.id if project_manager_role else None
        data['created_by'] = int(created_by)
        data['sales_owner'] = int(sales_owner)

        serializer = AdvanceBillingRequisitionCreateSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"message": "Advance Billing Requisition created successfully", "data": serializer.data}, 
                status=status.HTTP_201_CREATED
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

############################# Advance billing  GET API #################################

#class AdvanceBillingRequisitionAPIView(APIView):
    #authentication_classes = [JWTAuthentication]
    #permission_classes = [IsAuthenticated]

    #def get(self, request, project_id=None):
        """
        Retrieve all Advance Billing Requisition (ABR) records or filter by project_id.
        """
        #if project_id:
            #queryset = AdvanceBillingRequisition.objects.filter(project_id=project_id)
            #if not queryset.exists():
                #return Response({"error": "No Advance Billing Requisition found for this project."}, status=status.HTTP_404_NOT_FOUND)
        #else:
            #queryset = AdvanceBillingRequisition.objects.all()

        #serializer = AdvanceBillingRequisitionSerializer(queryset, many=True)
        #return Response(serializer.data, status=status.HTTP_200_OK)


class AdvanceBillingRequisitionAPIView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, project_id=None):
        """
        Retrieve all Advance Billing Requisition (ABR) records or filter by project_id.
        Uses optimized query with select_related for better performance.
        """
        if project_id:
            # Optimize query using select_related
            queryset = AdvanceBillingRequisition.objects.filter(project_id=project_id).select_related(
                'project', 'sales_owner', 'project_manager', 'created_by'
            )
        else:
            queryset = AdvanceBillingRequisition.objects.select_related(
                'project', 'sales_owner', 'project_manager', 'created_by'
            ).all()

        if not queryset.exists():
            return Response({"error": "No Advance Billing Requisition found."}, status=status.HTTP_404_NOT_FOUND)

        # Serialize the data
        serializer = AdvanceBillingRequisitionSingleProjectSerializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

###############################################################################################################################################





##########################################################   INvoice API ############################################################################
# Pagination class for GET requests
class InvoicePagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

# View for creating a new invoice (POST request)
class GenerateInvoiceAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        # Deserialize the incoming data
        serializer = InvoiceSerializer(data=request.data)

        if serializer.is_valid():
            # Save the invoice to the database
            invoice = serializer.save()
            return Response(InvoiceSerializer(invoice).data, status=status.HTTP_201_CREATED)

        # If validation fails, return errors
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class InvoicePagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

class InvoiceListAPIView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    pagination_class = InvoicePagination
    queryset = Invoice.objects.all()
    serializer_class = InvoiceSerializer

    def get_queryset(self):
        queryset = super().get_queryset()

        # Filter by issue_date
        issue_date_filter = self.request.query_params.get('issue_date', None)
        if issue_date_filter:
            today = now().date()

            if issue_date_filter == 'today':
                queryset = queryset.filter(issue_date=today)
            elif issue_date_filter == 'past_7_days':
                start_date = today - timedelta(days=7)
                queryset = queryset.filter(issue_date__gte=start_date)
            elif issue_date_filter == 'this_month':
                queryset = queryset.filter(issue_date__month=today.month, issue_date__year=today.year)
            elif issue_date_filter == 'this_year':
                queryset = queryset.filter(issue_date__year=today.year)

        # Filter by due_date
        due_date_filter = self.request.query_params.get('due_date', None)
        if due_date_filter:
            today = now().date()

            if due_date_filter == 'today':
                queryset = queryset.filter(due_date=today)
            elif due_date_filter == 'past_7_days':
                start_date = today - timedelta(days=7)
                queryset = queryset.filter(due_date__gte=start_date)
            elif due_date_filter == 'this_month':
                queryset = queryset.filter(due_date__month=today.month, due_date__year=today.year)
            elif due_date_filter == 'this_year':
                queryset = queryset.filter(due_date__year=today.year)

        # Filter by services
        services_filter = self.request.query_params.get('services', None)
        if services_filter and services_filter != 'All':
            queryset = queryset.filter(services__icontains=services_filter)

        # Filter by entity
        entity_filter = self.request.query_params.get('entity', None)
        if entity_filter:
            queryset = queryset.filter(entity__id=entity_filter)

        return queryset



########################################################################## Invoice Generated #############################################################

from api.finance.utils.invoice_utils import *

class GenerateInvoiceAPIView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def post(self, request, *args, **kwargs):
        # Deserialize the incoming data
        serializer = InvoiceSerializer(data=request.data, context={'request': request})
        user = request.user

        if serializer.is_valid():
            entity = serializer.validated_data.get('entity')
            project = serializer.validated_data.get('project')
            invoice_type = serializer.validated_data.get('type')
            cbr = serializer.validated_data.get('cbr')
            abr = serializer.validated_data.get('abr')
            #cbr_obj = FinanceRequest.objects.get(id=cbr)
            #abr_id = get_object_or_404(AdvanceBillingRequisition,id=abr)

            if not project or not invoice_type:
                return Response({"error": "Project and Invoice Type are required."}, status=status.HTTP_400_BAD_REQUEST)

            if invoice_type == "CBR" and not cbr:
                return Response({"error": "CBR ID is mandatory for CBR invoices."}, status=status.HTTP_400_BAD_REQUEST)

            if invoice_type == "ABR" and not abr:
                return Response({"error": "ABR ID is mandatory for ABR invoices."}, status=status.HTTP_400_BAD_REQUEST)

            try:
                pr = Project.objects.get(id=project.id)
            except Project.DoesNotExist:
                return Response({"error": "Project not found."}, status=status.HTTP_404_NOT_FOUND)

            # Generate unique invoice number
            invoice_number = generate_invoice_number(pr, invoice_type)

            # Update serializer data with invoice number
            serializer.validated_data['invoice_number'] = invoice_number

            if invoice_type == "CBR":
                finance_request = FinanceRequest.objects.filter(project=pr).first()
                if finance_request:
                    finance_request.status = "Invoice Generated"
                    finance_request.save()

            elif invoice_type == "ABR":
                abr_instance = get_object_or_404(AdvanceBillingRequisition, project=pr)
                abr_instance.status = "Advanced Invoice Generated"
                abr_instance.save()



            if entity:
                company = entity
                serializer.validated_data.update({
                    'account_title': company.account_title,
                    'account_number': company.account_number,
                    'swift_code': company.swift_code,
                    'wire_aba_number': company.wire_aba_number,
                    'wire_ach_number': company.wire_ach_number,
                    'sort_code': company.sort_code,
                    'iban_number': company.iban_number,
                    'bank_name': company.bank_name,
                    'ifsc': company.ifsc,
                    'bank_address': company.bank_address,
                })

            # Save the invoice to the database with generated invoice number
            invoice = serializer.save()

            # Optionally, trigger an invoice notification
            #send_invoice_notification(user=user, project=pr)

            return Response(InvoiceSerializer(invoice).data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



########################################################################### Invoice Payment API View ################################################################
logger = logging.getLogger(__name__)

class InvoicePaymentAPIView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def post(self, request, *args, **kwargs):
        """Handles payments against an invoice"""
        serializer = InvoicePaymentSerializer(data=request.data)

        if serializer.is_valid():
            try:
                with transaction.atomic():
                    payment = serializer.save()
                return Response(InvoicePaymentSerializer(payment).data, status=status.HTTP_201_CREATED)
            except Exception as e:
                logger.error(f"Error processing payment: {str(e)}")
                return Response({"error": "Failed to process payment. Please try again."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request, invoice_id, *args, **kwargs):
        """Retrieve all payments for a specific invoice"""
        try:
            invoice = Invoice.objects.get(id=invoice_id)
            payments = InvoicePayment.objects.filter(invoice=invoice)
            serializer = InvoicePaymentSerializer(payments, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Invoice.DoesNotExist:
            logger.warning(f"Invoice with ID {invoice_id} not found")
            return Response({"error": "Invoice not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Unexpected error retrieving payments: {str(e)}")
            return Response({"error": "Internal server error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
