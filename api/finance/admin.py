from import_export.admin import ImportExportModelAdmin
from django.contrib import admin
from .models import *

@admin.register(FinanceRequest)
class FinanceRequestAdmin(admin.ModelAdmin):
    # Fields to display in the list view
    list_display = (
        'id',
        'project',
        'project_code',
        'requested_by',
        'sales_owner',
        'project_manager',
        'client',
        'client_contact_person',
        'client_email_address',
        'client_purchase_order_no',
        'status',
        'cbr_raised_status',
        'request_date',
    )

    # Fields to filter the list by
    list_filter = (
        'status',
        'advanced_billing_raised',
        'request_date',
    )

    # Fields to search by
    search_fields = (
        'project__name',  # Assuming Project has a 'name' field
        'requested_by__role',  # Assuming UserRole has a 'role' field
        'remarks',
    )

    # Fields to edit inline
    list_editable = (
        'status',
        
    )

    # Read-only fields for specific details
    readonly_fields = (
        'request_date',
    )

    # Ordering of records
    ordering = ('-request_date',)  # Show newest requests first

    # Customizing the admin for
    fieldsets = (
        ("Project Information", {
            'fields': ('project', 'project_name', 'project_code', 'requested_by', 'sales_owner', 'project_manager')
        }),
        ("Client Details", {
            'fields': ('client', 'client_contact_person', 'client_email_address', 'client_purchase_order_no')
        }),
        ("Finance Details", {
            'fields': ('final_samples', 'client_rejected_sample', 'remarks', 'cbr_raised_remarks', 'cbr_raised_status', 'status')
        }),
        ("Survey & Billing Information", {
            'fields': (
                'number_of_surveys_initial_sow',
                'number_of_additional_surveys',
                'total_surveys_to_be_billed',
                'other_billing_instruction'
            )
        }),
        ("Timestamps", {
            'fields': ('request_date',)
        }),
    )



class VPRAdmin(admin.ModelAdmin):
    # Display the following fields in the list view
    list_display = ('id', 'project', 'created_by', 'approved_by', 'status', 'name_of_client', 
                    'project_code', 'project_name', 'vendor_name', 'invoice_amount', 'approved_amount','created_at','approved_at')
    
    # Add search functionality to search by project, client name, and project code
    search_fields = ('project__name', 'name_of_client', 'project_code')
    
    # Add filters to filter by project, status, and created/approved by
    list_filter = ('status', 'created_by', 'approved_by', 'approved_at', 'project')
    
    # Set default ordering by created_at, showing the latest VPRs first
    ordering = ('-created_at',)
    
    # Make created_at and approved_at readonly to prevent editing
    readonly_fields = ('created_at', 'approved_at')

    # Customize the fields displayed when editing a VPR
    fieldsets = (
        (None, {
            'fields': ('project', 'approved_by', 'status', 'name_of_client', 'project_code', 
                       'project_name', 'vendor_name', 'type_of_services', 'invoice_amount', 
                       'approved_amount', 'name_of_project_manager', 'data','other_cost')
        }),
        ('Timestamps', {  # New Section to include readonly fields
            'fields': ('created_at', 'approved_at'),
        }),
    )

# Register the model with the admin panel
admin.site.register(VPR, VPRAdmin)



@admin.register(AdvanceBillingRequisition)
class AdvanceBillingRequisitionAdmin(admin.ModelAdmin):
    list_display = ('id', 'client_name', 'project', 'total_project_cost', 'advance_invoice_amount', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('client_name__name', 'project__name', 'contact_person_name', 'contact_person_email')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at')

    fieldsets = (
        ("Client Details", {
            'fields': ('client_name', 'client_address')
        }),
        ("Project Information", {
            'fields': ('project', 'contact_person_name', 'contact_person_email', 'cc_emails')
        }),
        ("Billing Details", {
            'fields': ('specific_billing_instruction', 'total_project_cost', 'advance_invoice_percentage', 'advance_invoice_amount')
        }),
        ("Assigned Persons", {
            'fields': ('sales_owner', 'project_manager','created_by')
        }),
        ("Status & Metadata", {
            'fields': ('status', 'created_at', 'updated_at')
        }),
    )


from django.contrib import admin
from .models import Invoice

@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ("invoice_number", "entity", "project", "issue_date", "due_date", "total_cost_usd", "advance_paid", "final_payment",'created_by')
    list_filter = ("issue_date", "entity", "project")
    search_fields = ("invoice_number", "entity__name", "project__project_code", "buyer_name")
    ordering = ("-issue_date",)

    fieldsets = (
        ("Invoice Details", {
            "fields": ("entity", "project", "invoice_number", "po_number", "issue_date", "due_date")
        }),
        ("Billing Information", {
            "fields": ("buyer_name", "services", "description", "cost_components", "total_cost_usd", "advance_paid", "final_payment", "payment_terms")
        }),
        ("Bank Details", {
            "fields": ("account_title", "account_number", "swift_code", "wire_aba_number", "wire_ach_number",
                       "sort_code", "iban_number", "bank_name", "ifsc", "bank_address")
        }),
    )

    readonly_fields = ("invoice_number",)




class InvoicePaymentInline(admin.TabularInline):
    model = InvoicePayment
    extra = 1  # Allows adding new payments inline in Invoice admin

from django.contrib import admin
from .models import InvoicePayment

@admin.register(InvoicePayment)
class InvoicePaymentAdmin(admin.ModelAdmin):
    list_display = ('invoice', 'payment_date', 'amount_paid')
    list_filter = ('payment_date', 'invoice')
    search_fields = ('invoice__invoice_number',)
    readonly_fields = ('payment_date',)  # Payment date is auto-set

    fieldsets = (
        ("Invoice Payment Details", {
            'fields': ('invoice', 'payment_date', 'amount_paid')
        }),
    )

    ordering = ('-payment_date',)  # Show latest payments first
