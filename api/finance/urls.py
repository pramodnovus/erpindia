from django.urls import path
from .views import *

urlpatterns = [
    path('projects/<int:project_id>/cbr-raised/', ProjectCbrRaisedAPIView.as_view(), name='project-cbr-raised'),
    path('cbr-create/', ProjectCbrRaisedAPIView.as_view(), name='finance-cbr-create'),
    path('vpr-create/', VPRCreateView.as_view(), name='vpr-create'),
    path('vpr/update/<int:id>/',VPRUpdateView.as_view(), name="vpr-update"),
    path('project-cbr-data/', FinanceCbrAPIView.as_view(), name='finance-request-list'),
    path('project-cbr-data/<int:project_id>/', FinanceCbrAPIView.as_view(), name='finance-request-specific'),
    path('cbr/project-list/', FinanceProjectAPIView.as_view(), name='finance-project-list'),
    path('project-list/<int:project_id>/', FinanceProjectAPIView.as_view(), name='finance-project-specific'),
    path('generate-invoice/', GenerateInvoiceAPIView.as_view(), name='generate_invoice'),
    path('invoice-list/', InvoiceListAPIView.as_view(), name='invoice_list'),
    ############### ADVANCE BILLING CREATE / ADVANCE BILLING DATA LIST / ADVANCE BILLING PROJECT SPECIFIC #################
    path('abr/create/', AdvanceBillingRequisitionCreateView.as_view(), name='advance-billing-create'),
    path('abr/project-list/', AdvanceBillingRequisitionAPIView.as_view(), name='all-advance-billing'),
    path('abr/<int:project_id>/', AdvanceBillingRequisitionAPIView.as_view(), name='project-advance-billing'),
    path('generate-invoice/', GenerateInvoiceAPIView.as_view(), name='generate-invoice'),
    path('invoices/', InvoiceListAPIView.as_view(), name='invoice-list'),
    path('invoices/project/<int:project_id>/', InvoiceListAPIView.as_view(), name='invoice-list-project'),

    path('invoice/<int:invoice_id>/payments/', InvoicePaymentAPIView.as_view(), name='invoice-payments'),
    path('invoice/payment/', InvoicePaymentAPIView.as_view(), name='add-payment'),
]


