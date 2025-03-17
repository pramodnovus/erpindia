from django.db import models
from api.user.models import *
from api.project.models import *

class FinanceRequest(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, null=True, blank=True)
    po_number = models.CharField(max_length=50, null=True, blank=True)  # New field
    requested_by = models.ForeignKey(UserRole, on_delete=models.CASCADE,null=True,blank=True)
    final_samples = models.JSONField(null=True, blank=True)
    client = models.ForeignKey(Client, on_delete=models.CASCADE, null=True, blank=True)
    client_contact_person = models.CharField(max_length=255,null=True,blank=True)
    client_email_address = models.EmailField(null=True,blank=True)
    client_rejected_sample = models.PositiveIntegerField(default=0,null=True, blank=True)
    remarks = models.TextField(null=True, blank=True)
    advanced_billing_raised = models.BooleanField(default=False)
    cbr_raised_status = models.BooleanField(default=False)
    advance_billing_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)  # Added field for advance billing amount
    cbr_raised_by_user = models.ForeignKey(UserRole, on_delete=models.CASCADE, null=True, blank=True, related_name="cbr_finance_requests")

    # Client information
    #client = models.ForeignKey(Client, on_delete=models.CASCADE, null=True, blank=True)  # Client: Name of the client
    client_name = models.CharField(max_length=255,null=True,blank=True)  # Client: Name of the client
    client_contact_person = models.CharField(max_length=255, null=True, blank=True)  # Client: Contact Person (e.g. John Doe)
    client_email_address = models.EmailField(max_length=255, null=True, blank=True)  # Client: Email Address
    client_cc_emails = models.TextField(null=True, blank=True)  # Cc: Email IDs (if any), stored as comma-separated emails

    # Project details
    project_name = models.CharField(max_length=255, null=True, blank=True)  # Project Name
    client_purchase_order_no = models.CharField(max_length=255, null=True, blank=True)  # Client Purchase order no.
    project_code = models.CharField(max_length=255, null=True, blank=True)  # Project Code
    number_of_surveys_initial_sow = models.PositiveIntegerField(null=True, blank=True)  # # of Surveys as per Initial SOW
    number_of_additional_surveys = models.IntegerField(null=True, blank=True)  # # of Additional Surveys as per client confirmation
    total_surveys_to_be_billed = models.PositiveIntegerField(null=True, blank=True)  # # of Total Surveys to be billed to client
    other_billing_instruction = models.TextField(null=True, blank=True)  # Other Specific billing instructions (if any)

    # Personnel information
    sales_owner = models.CharField(max_length=255, null=True, blank=True)  # Sales Owner
    project_manager = models.ForeignKey(UserRole, on_delete=models.SET_NULL, null=True, related_name="project_manager_cbr")
    #project_manager_name = models.CharField(max_length=255,null=True, blank=True)  # Name of Project Manager

    #final_samples = models.JSONField(null=True, blank=True)
    #client_rejected_sample = models.PositiveIntegerField(null=True, blank=True)
    #remarks = models.TextField(null=True, blank=True)
    #advanced_billing_raised = models.BooleanField(default=False)  #
    #advance_billing_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)  # Added field for advance billing amount
    cbr_raised_remarks = models.TextField(null=True, blank=True)
    status = models.CharField(max_length=50, choices=[
          ('Invoice to be Raised', 'Invoice to be Raised'),
            ('Invoice Generated', 'Invoice Generated'),
            ('Payment Received', 'Payment Received'), # Project Completed 
            ('Advanced Billing Raised', 'Advanced Billing Raised'),  #
            ('Advanced Invoice Generated', 'Advanced Invoice Generated'),
            ('Advance Payment Received', 'Advance Payment Received'),
            ('CBR Raised', 'CBR Raised'),
    ], default='Invoice to be Raised')
    request_date = models.DateTimeField(auto_now_add=True)

    #def save(self, *args, **kwargs):
        # Set status to 'Advanced Billing Raised' if advanced_billing_raised is True
        #if self.advanced_billing_raised:
            #self.status = 'Advanced Billing Raised'
        #else:
            # Default to 'Invoice to be Raised' if no advanced billing
            #self.status = 'Invoice to be Raised'
        #super().save(*args, **kwargs)

    # def __str__(self):
    #     return f"Finance request for {self.project.name} by {self.requested_by.user.username}"
     

class VPR(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    project = models.ForeignKey(Project,on_delete=models.CASCADE,null=True,blank=True,related_name="vpr_projects")
    created_by = models.ForeignKey(UserRole, on_delete=models.CASCADE, related_name='vpr_created',null=True)
    approved_by = models.ForeignKey(UserRole, on_delete=models.CASCADE, related_name='vpr_approved', null=True, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    
    data = models.JSONField(null=True,blank=True)
    other_cost = models.JSONField(null=True,blank=True)
    
    name_of_client = models.CharField(max_length=255, blank=True, null=True)
    project_code = models.CharField(max_length=100, blank=True, null=True)
    project_name = models.CharField(max_length=255, blank=True, null=True)
    vendor_name = models.CharField(max_length=255, blank=True, null=True)
    type_of_services = models.CharField(max_length=255, blank=True, null=True)
    invoice_amount = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    approved_amount = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    name_of_project_manager = models.CharField(max_length=255, blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    
    
    def __str__(self):
        return str(self.id)


class AdvanceBillingRequisition(models.Model):
    ABR_CODE = "Unimrkt/PR/ABR/1.1"

    STATUS_CHOICES = [
        ('Advanced Billing Raised', 'Advanced Billing Raised'),
        ('Advanced Invoice Generated', 'Advanced Invoice Generated'),
        ('Advance Payment Received', 'Advance Payment Received'),
    ]

    # Client Information
    client_name = models.ForeignKey(Client, on_delete=models.SET_NULL, null=True, blank=True)
    client_address = models.TextField(blank=True, null=True)  # Optional for new clients
    client_city = models.CharField(max_length=100, blank=True, null=True)
    client_country = models.CharField(max_length=100, blank=True, null=True)
    clientname = models.CharField(max_length=100, blank=True, null=True)

    # Project Relation (Prevent automatic deletion)
    project = models.ForeignKey(
        Project,
        on_delete=models.SET_NULL,  # Use PROTECT to prevent deletion
        null=True,
        blank=True
    )
    contact_person_name = models.CharField(max_length=255,null=True,blank=True)
    contact_person_email = models.EmailField(null=True,blank=True)
    cc_emails = models.TextField(blank=True, null=True, help_text="Comma-separated emails")  # If any

    # Billing Details
    specific_billing_instruction = models.TextField(blank=True, null=True)  # Optional
    total_project_cost = models.DecimalField(max_digits=12, decimal_places=2,null=True,blank=True)  # Amount as per SOW
    advance_invoice_percentage = models.DecimalField(max_digits=5, decimal_places=2, help_text="Percentage",null=True,blank=True)
    advance_invoice_amount = models.DecimalField(max_digits=12, decimal_places=2,null=True,blank=True)  # Amount as per SOW

    # Assigned Persons
    sales_owner = models.ForeignKey(UserRole, on_delete=models.SET_NULL, null=True, related_name="sales_owner")
    project_manager = models.ForeignKey(UserRole, on_delete=models.SET_NULL, null=True, related_name="project_manager")
    created_by = models.ForeignKey(UserRole, on_delete=models.SET_NULL, null=True, related_name="created_by")
    # Status
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='Advanced Billing Raised')

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"ABR {self.project} ({self.status})"
        # return f"ABR {self.pk} - {self.client_name} - {self.project_name} ({self.status})"


class Invoice(models.Model):
    INVOICE_TYPE_CHOICES = [
        ('CBR', 'Client Billing Request'),
        ('ABR', 'Advance Billing Requisition'),
    ]
    STATUS_CHOICES = [
        ('Invoice to be Raised', 'Invoice to be Raised'),
        ('Invoice Generated', 'Invoice Generated'),
        ('Partially Paid', 'Partially Paid'),
        ('Payment Received', 'Payment Received'),
        ('Advanced Billing Raised', 'Advanced Billing Raised'),
        ('Advanced Invoice Generated', 'Advanced Invoice Generated'),
        ('Advance Payment Received', 'Advance Payment Received'),
    ]
    #Fields to distinguish between ABR and CBR invoices
    type = models.CharField(max_length=3, choices=INVOICE_TYPE_CHOICES, default='CBR')
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='Invoice to be Raised')
    project = models.ForeignKey(Project, on_delete=models.SET_NULL, related_name="invoices", null=True, blank=True)  # New field
    cbr = models.ForeignKey(FinanceRequest, on_delete=models.SET_NULL, null=True, blank=True, related_name='cbrinvoices')
    abr = models.ForeignKey(AdvanceBillingRequisition, on_delete=models.SET_NULL, null=True, blank=True,related_name='abrinvoices')
    po_number = models.CharField(max_length=50, null=True, blank=True)  # New field
    entity = models.ForeignKey(Company, on_delete=models.CASCADE)
    invoice_number = models.CharField(max_length=50, unique=True)
    issue_date = models.DateField()
    due_date = models.DateField()
    buyer_name = models.CharField(max_length=255)
    services = models.CharField(max_length=255)
    description = models.TextField()
    cost_components = models.JSONField()  # Store detailed cost breakdown
    total_cost_usd = models.DecimalField(max_digits=10, decimal_places=2)
    advance_paid = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    final_payment = models.DecimalField(max_digits=10, decimal_places=2)
    payment_terms = models.TextField(default="Payment to be released within 30 days from the date of invoice.")
    # **Snapshot of bank details (from Company) at the time of invoice generation**
    account_title = models.CharField(max_length=200, null=True, blank=True)
    account_number = models.CharField(max_length=50, null=True, blank=True)
    swift_code = models.CharField(max_length=50, null=True, blank=True)
    wire_aba_number = models.CharField(max_length=50, null=True, blank=True)
    wire_ach_number = models.CharField(max_length=50, null=True, blank=True)
    sort_code = models.CharField(max_length=50, null=True, blank=True)
    iban_number = models.CharField(max_length=50, null=True, blank=True)
    bank_name = models.CharField(max_length=200, null=True, blank=True)
    ifsc = models.CharField(max_length=50, null=True, blank=True)
    bank_address = models.TextField(null=True, blank=True)

    # Issued By Invoice 
    created_by = models.ForeignKey(UserRole, on_delete=models.CASCADE, related_name='invoice_created_by',null=True)

    def __str__(self):
        return f"Invoice {self.invoice_number} - {self.entity.name}"

    def __str__(self):
        return f"Invoice {self.invoice_number} - {self.entity.name}"
    

    def calculate_total_cost(self):
        """
        Calculate total cost from cost_components JSON field.
        """
        total = 0
        if isinstance(self.cost_components, list):  # Ensure it's a list
            for component in self.cost_components:
                sample = component.get("sample", 0)
                cpi = component.get("cpi", 0)
                total += sample * cpi
        return total

    

    def update_payment_terms(self):
        """ Update payment terms based on advance payment """
        if self.advance_paid and self.advance_paid > 0:
            self.payment_terms = "Payment to be released within 7 days from the date of invoice."
        else:
            self.payment_terms = "Payment to be released within 30 days from the date of invoice."

    def update_bank_details(self):
        """Update bank details from the related company."""
        try:
            company = self.entity
            self.account_title = company.account_title
            self.account_number = company.account_number
            self.swift_code = company.swift_code
            self.wire_aba_number = company.wire_aba_number
            self.wire_ach_number = company.wire_ach_number
            self.sort_code = company.sort_code
            self.iban_number = company.iban_number
            self.bank_name = company.bank_name
            self.ifsc = company.ifsc
            self.bank_address = company.bank_address
        except Company.DoesNotExist:
            pass  #        



    def calculate_final_invoice(self):
        """
        Calculate the final invoice amount by considering ABR and CBR.
        """
        if self.type == 'ABR':
            # For ABR, the total cost is the advance amount
            self.total_cost_usd = self.abr.advance_invoice_amount
            self.advance_paid = 0  # No advance payment for ABR
        elif self.type == 'CBR':
            # For CBR, the total cost is the final amount minus any advance payment
            if self.abr:
                self.advance_paid = self.abr.advance_invoice_amount
                self.total_cost_usd = self.cbr.total_surveys_to_be_billed * self.cbr.cost_per_survey  # Example calculation
            else:
                self.advance_paid = 0
                self.total_cost_usd = self.cbr.total_surveys_to_be_billed * self.cbr.cost_per_survey  # Example calculation

        self.final_payment = self.get_total_due()


    # @property
    # def balance_due(self):
    #     """Dynamically calculate balance due"""
    #     return self.final_payment - self.amount_paid

    # def update_status(self):
    #     """Automatically updates the invoice status based on payments"""
    #     if self.balance_due == 0:
    #         self.status = 'Payment Received'
    #     elif self.paid_amount > 0:
    #         self.status = 'Partially Paid'
    #     else:
    #         self.status = 'Invoice Generated'
    #     self.save()





class InvoicePayment(models.Model):
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name="payments")
    payment_date = models.DateTimeField(default=timezone.now)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2)
    amount_due = models.DecimalField(max_digits=10, decimal_places=2)

    def save(self, *args, **kwargs):
            """Ensure atomic transaction and update invoice status"""
            with transaction.atomic():
                # Calculate remaining balance before saving
                total_paid = InvoicePayment.objects.filter(invoice=self.invoice).aggregate(models.Sum('amount_paid'))['amount_paid__sum'] or 0
                total_paid += self.amount_paid
                self.amount_due = max(self.invoice.final_payment - total_paid, 0)

                super().save(*args, **kwargs)

                # Update invoice status
                if self.amount_due == 0:
                    self.invoice.status = "Payment Received"
                else:
                    self.invoice.status = "Partially Paid"
                self.invoice.save()

    def __str__(self):
        return f"Payment of {self.amount_paid} for Invoice {self.invoice.invoice_number}" 
