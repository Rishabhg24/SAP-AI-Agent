import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.models.extraction import MasterDataType
from app.services.validation_service import validation_service
from app.services.missing_fields import missing_field_engine

rec1 = {
    'CardCode': 'CUST001',
    'CardName': 'ABC Pvt Ltd',
    'CardType': 'cCustomer',
    'EmailAddress': 'rishabh@example.com',
    'Phone1': '9876543210',
    'Address': '123 Main St, Delhi, Delhi 110001, India',
    'City': 'Delhi',
    'State': 'DL',
    'ZipCode': '110001',
    'Country': 'India',
    'Currency': 'INR',
    'ControlAccount': '132000',
    'PaymentTerms': 'Net 30',
    'TaxDetails': 'GST 18%',
    'GSTNo': 'UNREGISTERED',
    'PANNo': 'NA',
    'GSTRegStatus': 'Unregistered'
}

val_res = validation_service.validate(MasterDataType.BUSINESS_PARTNER, rec1)
print("Valid:", val_res.valid)
print("Missing:", [m.field for m in val_res.missing_fields])
print("Invalid:", [(e.field, e.message) for e in val_res.invalid_fields])
print("Warnings:", val_res.warnings)
