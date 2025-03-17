from rest_framework import serializers
from .models import *
from api.project.models import Project,projectType,Client,ProjectSample
from api.operation.models import ProjectUpdate
from django.utils.timezone import now
 
######################### Sample and Cpi Serializer #############################

class SampleCpiSerializer(serializers.Serializer):
    sample = serializers.CharField(max_length=50)
    cpi = serializers.CharField(max_length=50)

################## Project CBR Serializer #####################################

class ProjectCbrRaisedSerializer(serializers.ModelSerializer):
    samples = serializers.ListField(child=SampleCpiSerializer()) 
    remarks = serializers.CharField(required=True)

    class Meta:
        model = Project
        fields = ('id', 'status', 'samples', 'remarks')
 
####################### Finance CBR Create Serializer #############################

class FinanceCbrCreateSerializer(serializers.ModelSerializer):
    samples = serializers.ListField(child=serializers.DictField(), source='final_samples')
    #po_number = serializers.CharField(required=True)

    class Meta:
        model = FinanceRequest
        fields = ['project','project_code','project_name','client','client_contact_person','client_email_address','client_purchase_order_no','number_of_surveys_initial_sow','number_of_additional_surveys','total_surveys_to_be_billed','other_billing_instruction','status', 'samples', 'remarks','sales_owner','project_manager']

    def validate(self, attrs):
        project = attrs.get('project')
        if FinanceRequest.objects.filter(project=project).exists():
            raise serializers.ValidationError({"project": "CBR already Created for this project."})
        return attrs

    def create(self, validated_data):
        request = self.context.get("request")
        user_role = request.user.userrole if request else None

        if not user_role:
            raise serializers.ValidationError({"requested_by": "User role is required."})

        project = validated_data.get("project")
        if not project:
            raise serializers.ValidationError({"project": "Project is required."})

        # Compute samples and rejected samples safely
        samples_data = validated_data.pop('final_samples', [])
        total_sample = int(project.sample or 0)  # Ensure total_sample is an integer
        actual_sample = sum(
            int(item.get("sample", 0)) for item in samples_data if isinstance(item, dict) and str(item.get("sample", "0")).isdigit()
        )

        # 🚨 Ensure actual_sample does not exceed total_sample
        if actual_sample > total_sample:
            raise serializers.ValidationError(
                {"samples": "Actual sample count exceeds total project sample. Please increase the project sample first."}
            )


        rejected_sample = max(0, total_sample - actual_sample)  # Ensure it's non-negative

        # Create and return FinanceRequest
        # Create and return FinanceRequest
        finance_request = FinanceRequest.objects.create(
            requested_by=user_role,
            final_samples=samples_data,
            client_rejected_sample=rejected_sample,
            **validated_data
        )
        
        # ✅ Update status using serializer to maintain consistency
        self.update_project_status(finance_request)

        return finance_request

    def update_project_status(self, finance_request):
        """Update the latest ProjectUpdate status."""
        final_status = finance_request.status
        last_project_update = ProjectUpdate.objects.filter(project_id=finance_request.project).last()

        if last_project_update:
            last_project_update.status = final_status
            last_project_update.save()

################################################# CBR #########################################################

# Nested Serializer for UserRole (to include user's name)
class UserRoleIdNameSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source='user.username')  # Get the username from the related CustomUser model

    class Meta:
        model = UserRole
        fields = ['id', 'name']  # Include both id and name

# Nested Serializer for Project
class ProjectIdNameSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = ['id', 'name']  # Include both id and name

# Main Serializer for FinanceRequest
class CbrSerializer(serializers.ModelSerializer):
    project = ProjectIdNameSerializer()  # Use the nested ProjectIdNameSerializer
    requested_by = UserRoleIdNameSerializer()  # Use the nested UserRoleSerializer
    cbr_raised_by_user = UserRoleIdNameSerializer()  # Use the nested UserRoleSerializer

    class Meta:
        model = FinanceRequest
        fields = '__all__'  # Include all fields from the FinanceRequest model



''' *************************  Start Serializer ******************************* '''

############################# Project Serializer ############################

# Nested Serializer for ForeignKey fields with ID & Name
class ProjectTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = projectType
        fields = ['id', 'name']

############################ Client Serializer ###############################

class ClientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Client
        fields = ['id', 'name']

################## Project sample and cpi multiple ###########################

class ProjectSampleCpiSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectSample
        fields = ['id','sample', 'cpi', 'target_group','pending_changes','updated_at']

################################################################################
################# Finance Project Serializer with Nested Serializer ###########

class FinanceProjectSerializer(serializers.ModelSerializer):
    project_type = ProjectTypeSerializer()  # Correct ForeignKey representation
    clients = ClientSerializer()
    created_by = UserRoleIdNameSerializer()
    assigned_to = UserRoleIdNameSerializer()
    project_samples = ProjectSampleCpiSerializer(many=True, read_only=True)  # Use correct related_name
    class Meta:
        model = Project
        fields = [
            'id','project_code', 'name', 'project_type', 'clients', 'cpi',
            'set_up_fee', 'transaction_fee', 'other_cost', 'label_cost',
            'tentative_start_date', 'tentative_end_date', 'estimated_time', 
            'remaining_time', 'created_by', 'assigned_to','status','project_client_pm','project_samples','sample'
        ]        
        

##########  Finance Request Serializer with Nested Project and UserRole ###########################

class FinanceRequestSerializer(serializers.ModelSerializer):
    project = FinanceProjectSerializer(read_only=True)  # Nested ProjectSerializer
    requested_by = UserRoleIdNameSerializer()  # Include requested_by with ID and name
    cpi = serializers.SerializerMethodField()
    sample = serializers.SerializerMethodField()
    class Meta:
        model = FinanceRequest
        fields = [
            'id', 'requested_by', 'client', 'client_contact_person',
            'client_email_address', 'number_of_surveys_initial_sow',
            'number_of_additional_surveys', 'total_surveys_to_be_billed', 
            'other_billing_instruction', 'sales_owner', 'project_name', 
            'project_code', 'project_manager', 'final_samples', 
            'client_rejected_sample', 'remarks', 
            'status', 'request_date', 'project','cpi','sample','po_number'
        ]
    def to_representation(self, instance):
        data = super().to_representation(instance)
        if instance.client:  # Ensure client exists
            data['client'] = {
                "id": instance.client.id,
                "name": instance.client.name  # Assuming `name` field exists in Client model
            }
        else:
            data['client'] = None  # If client is missing

        return data
    
    def get_cpi(self, obj):
        final_samples = obj.final_samples or []
        return int(final_samples[0]["cpi"]) if len(final_samples) == 1 else 0 if final_samples else None

    def get_sample(self, obj):
        final_samples = obj.final_samples or []
        if not final_samples:
            return None

        sample_values = [fs["sample"] for fs in final_samples]
        if all(isinstance(s, int) or s.isdigit() for s in sample_values):
            return sum(map(int, sample_values))  
        
        return "+".join(map(str, sample_values))

''' *********************************  End Serializer ******************************************* '''

################### VPR Create Serializer ###########################################################################

class VPRSerializer(serializers.ModelSerializer):
    notification_type = serializers.SerializerMethodField()

    class Meta:
        model = VPR
        fields = ['project','status','name_of_client','project_code','project_name','vendor_name','type_of_services','invoice_amount','approved_amount','name_of_project_manager','notification_type','other_cost']

    def get_notification_type(self, obj):
        return "VPR" # You can customize this as needed
    
    def create(self, validated_data):
        # Access the request and get the UserRole instance
        user_role = self.context['request'].user.userrole
        validated_data['created_by'] = user_role  # Assign the UserRole instance, not just the ID
        
        return super().create(validated_data)

class VPRUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = VPR
        fields = ['status']

    def update(self, instance, validated_data):
        request = self.context.get('request')
        if request and request.user:
            instance.approved_by = request.user.userrole  # Assuming UserRole is related to User
        if validated_data.get('status') == 'approved':
            notification_obj = Notification.objects.filter(project_id=instance.project,notification_type="VPR").update(is_approved=True,is_rejected=False)
            instance.approved_at = now()  
            instance.is_rejected = False  
        elif validated_data.get('status') == 'rejected':
            Notification.objects.filter(project_id=instance.project,notification_type="VPR").update(is_rejected=True,is_approved=False)
            instance.is_rejected = True  
            instance.is_approved = None  
            
        return super().update(instance, validated_data)

################################################# Advance billing Requisition ##################################################
#class AdvanceBillingRequisitionSerializer(serializers.ModelSerializer):
    #advance_invoice_number = serializers.SerializerMethodField()
    #class Meta:
        #model = AdvanceBillingRequisition
        #fields = [
            #'id', 'client_name','client_city','client_country', 'client_address', 'project', 'contact_person_name',
            #'contact_person_email', 'cc_emails', 'specific_billing_instruction',
            #'total_project_cost', 'advance_invoice_percentage', 'advance_invoice_amount',
            #'sales_owner', 'project_manager','created_by','status', 'created_at', 'updated_at','advance_invoice_number'
        #]
        #read_only_fields = ['id', 'created_at', 'updated_at']

    #def get_advance_invoice_number(self, obj):
    #    invoice = Invoice.objects.filter(abr=obj, type='ABR').first()
    #    return invoice.invoice_number if invoice else None

    #def get_advance_invoice_number(self, obj):
        #invoice = Invoice.objects.filter(project=obj.project, type='ABR').first()
        #return invoice.invoice_number if invoice else None

class AdvanceBillingRequisitionSerializer(serializers.ModelSerializer):
    #project = serializers.PrimaryKeyRelatedField(queryset=Project.objects.all())  # Allow Project creation
    project = FinanceProjectSerializer(read_only=True)
    sales_owner = UserRoleIdNameSerializer(read_only=True)
    project_manager = UserRoleIdNameSerializer(read_only=True)
    created_by = UserRoleIdNameSerializer(read_only=True)
    advance_invoice_number = serializers.SerializerMethodField()

    class Meta:
        model = AdvanceBillingRequisition
        fields = [
            'id', 'client_name','clientname', 'client_address', 'client_city', 'client_country',
            'contact_person_name', 'contact_person_email', 'cc_emails',
            'specific_billing_instruction', 'total_project_cost',
            'advance_invoice_percentage', 'advance_invoice_amount',
            'sales_owner', 'project_manager', 'created_by',
            'status', 'created_at', 'updated_at', 'project','advance_invoice_number'
        ]

    def get_advance_invoice_number(self, obj):
        invoice = Invoice.objects.filter(project=obj.project, type='ABR').first()
        return invoice.invoice_number if invoice else None

    def to_representation(self, instance):
        """Modify the representation to match the required structure."""
        data = super().to_representation(instance)

        # Format client data properly
        if instance.client_name:  # Ensure client exists
            data['client'] = {
                "id": instance.client_name.id,
                "name": instance.client_name.name  # Assuming `name` field exists in Client model
            }
        else:
            data['client'] = None  # If client is missing

        return data


class AdvanceBillingRequisitionSingleProjectSerializer(serializers.ModelSerializer):
    project = FinanceProjectSerializer(read_only=True)  # Nested ProjectSerializer
    sales_owner = UserRoleIdNameSerializer(read_only=True)
    project_manager = UserRoleIdNameSerializer(read_only=True)

    class Meta:
        model = AdvanceBillingRequisition
        fields = [
            'id', 'client_name', 'contact_person_name', 'contact_person_email', 'cc_emails',
            'specific_billing_instruction', 'advance_invoice_amount',
            'sales_owner', 'project_manager', 'status', 'project'
        ]

    def to_representation(self, instance):
        """Modify the representation to match the required structure."""
        data = super().to_representation(instance)

        # Format client data properly
        if instance.client_name:  # Ensure client exists
            data['client'] = {
                "id": instance.client_name.id,
                "name": instance.client_name.name  # Assuming `name` field exists in Client model
            }
        else:
            data['client'] = None  # If client is missing

        return data



class AdvanceBillingRequisitionCreateSerializer(serializers.ModelSerializer):
    project = serializers.PrimaryKeyRelatedField(queryset=Project.objects.all())
    created_by = serializers.PrimaryKeyRelatedField(queryset=UserRole.objects.all(), required=False, allow_null=True)
    project_manager = serializers.PrimaryKeyRelatedField(queryset=UserRole.objects.all(), required=False, allow_null=True)
    sales_owner = serializers.PrimaryKeyRelatedField(queryset=UserRole.objects.all(), required=False, allow_null=True)

    class Meta:
        model = AdvanceBillingRequisition
        fields = [
            'id', 'client_name','clientname','client_address', 'client_city', 'client_country',
            'contact_person_name', 'contact_person_email', 'cc_emails',
            'specific_billing_instruction', 'total_project_cost',
            'advance_invoice_percentage', 'advance_invoice_amount',
            'sales_owner', 'project_manager','created_by', 'status','created_at', 'updated_at','project'
        ]
#################################################################################################################################





########################################################### INvoice Serilizers #####################################################################
########################################################### INvoice Serilizers #####################################################################

from rest_framework import serializers
from .models import Invoice, Company

class InvoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Invoice
        fields = '__all__'  # Include all fields
        read_only_fields = ['id', 'invoice_number']  # Ensure 'id' is read-only

    def validate(self, data):
        """
        Ensure that an invoice (either ABR or CBR) is only created once per project.
        If the project has an ABR, multiple invoices can exist.
        If the project only has a CBR, only one invoice is allowed.
        """
        project = data.get('project')
        invoice_type = data.get('type')

        if project:
            existing_invoices = Invoice.objects.filter(project=project)

            has_abr = existing_invoices.filter(type="ABR").exists()
            print("has_abr", has_abr)
            has_cbr = existing_invoices.filter(type="CBR").exists()

            # If an invoice of type CBR already exists and the new one is also CBR, prevent duplication
            if has_cbr and invoice_type == "CBR":
                raise serializers.ValidationError({
                    "error": f"A Client Billing Request (CBR) invoice has already been raised against project {project}. No additional CBR invoices are allowed."
                })
            if has_abr and invoice_type == 'ABR':
                raise serializers.ValidationError({
                    "error": f"A Client Billing Request (ABR) invoice has already been raised against project {project}. No additional ABR invoices are allowed."
                })

        return data



    def create(self, validated_data):
        """
        Auto-fill bank details from the selected entity when creating an invoice.
        """
        entity = validated_data.get('entity')
        print("entity", entity)
        request = self.context.get('request')  # Use .get() to avoid KeyError
        user_role = request.user.userrole if request else None  # Handle missing request gracefully
        validated_data['created_by'] = user_role  # Assign UserRole if availabl
        
        # Fetch and set bank details from the associated Company entity
        if entity:
            validated_data.update({
                'account_title': entity.account_title or '',
                'account_number': entity.account_number or '',
                'swift_code': entity.swift_code or '',
                'wire_aba_number': entity.wire_aba_number or '',
                'wire_ach_number': entity.wire_ach_number or '',
                'sort_code': entity.sort_code or '',
                'iban_number': entity.iban_number or '',
                'bank_name': entity.bank_name or '',
                'ifsc': entity.ifsc or '',
                'bank_address': entity.bank_address or '',
            })

            print("validated_data",validated_data)

        invoice = super().create(validated_data)
        invoice.total_cost_usd = invoice.calculate_total_cost()
        invoice.save()
        
        return invoice



    def update(self, instance, validated_data):
        instance.cost_components = validated_data.get("cost_components", instance.cost_components)
        instance.total_cost_usd = instance.calculate_total_cost()
        instance.save()
        return instance


#################################################################################### Invoice Payment Received History ###################################################################


from rest_framework import serializers
from django.db.models import Sum
from api.finance.models import InvoicePayment, Invoice

class InvoicePaymentSerializer(serializers.ModelSerializer):
    invoice_number = serializers.CharField(source='invoice.invoice_number', read_only=True)
    final_payment = serializers.DecimalField(source='invoice.final_payment', max_digits=10, decimal_places=2, read_only=True)
    
    class Meta:
        model = InvoicePayment
        fields = ['id', 'invoice', 'invoice_number', 'payment_date', 'amount_paid', 'amount_due', 'final_payment']
        read_only_fields = ['amount_due', 'invoice_number', 'final_payment']

    def validate(self, data):
        """Validate payment to ensure it does not exceed the remaining balance."""
        invoice = data.get('invoice')
        amount_paid = data.get('amount_paid')

        if not invoice:
            raise serializers.ValidationError({"invoice": "Invoice is required."})

        # Get the total amount paid so far
        total_paid = InvoicePayment.objects.filter(invoice=invoice).aggregate(Sum('amount_paid'))['amount_paid__sum'] or 0

        # Calculate the remaining balance
        remaining_balance = invoice.final_payment - total_paid

        if amount_paid > remaining_balance:
            raise serializers.ValidationError({"amount_paid": f"Amount paid cannot exceed the remaining balance of {remaining_balance}."})

        return data

    def create(self, validated_data):
        """Create a payment entry and update the invoice status."""
        invoice = validated_data.get('invoice')
        amount_paid = validated_data.get('amount_paid')

        # Get total paid so far
        total_paid = InvoicePayment.objects.filter(invoice=invoice).aggregate(Sum('amount_paid'))['amount_paid__sum'] or 0
        total_paid += amount_paid

        # Calculate remaining balance
        validated_data['amount_due'] = max(invoice.final_payment - total_paid, 0)

        # Save the payment
        payment = super().create(validated_data)

        # Update invoice status based on remaining amount
        if validated_data['amount_due'] == 0:
            invoice.status = "Payment Received"
        else:
            invoice.status = "Partially Paid"
        invoice.save()

        return payment

