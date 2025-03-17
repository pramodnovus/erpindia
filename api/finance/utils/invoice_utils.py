from datetime import datetime
from django.db.models import Max
from api.finance.models import Invoice  # Adjust import based on your project structure

def generate_invoice_number(project, invoice_type):
    """
    Generates a structured invoice number:
    Format:
    - ADV-YY-PROJECTCODE-SEQ (e.g., ADV-25-027nov192-0001)
    - INV-YY-PROJECTCODE-SEQ (e.g., INV-25-027nov192-0002)
    """
    current_year = datetime.now().year % 100  # Get last two digits of year
    invoice_prefix = "FIN-INV" if invoice_type == 'CBR' else "ADV-INV"

    latest_invoice = Invoice.objects.filter(project=project).aggregate(Max('invoice_number'))
    latest_number = latest_invoice['invoice_number__max']

    if latest_number:
        try:
            last_seq = int(latest_number.split("-")[-1])  # Extract last sequence number
            next_seq = str(last_seq + 1).zfill(4)
        except (ValueError, IndexError):
            next_seq = "0001"
    else:
        next_seq = "0001"

    return f"{invoice_prefix}-{current_year}-{project.project_code}-{next_seq}"
