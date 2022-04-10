import csv
import json


# NONE cols - code, internal_revenue_code, code_disambiguator
# inpatient_outpatient = ('INPATIENT', 'OUTPATIENT', 'BOTH', 'UNSPECIFIED')
# except units
COLS = ['cms_certification_num', 'payer', 'code', 'internal_revenue_code', 'description', 'inpatient_outpatient',
        'price', 'code_disambiguator']
NONE_COLS = ['code', 'internal_revenue_code', 'code_disambiguator']
CMS = '020001'


def create_row(row: list[str], mapping: dict, payer: str, in_out: str, price: float) -> dict:
    d = {
        'cms_certification_num': CMS,
        'payer': payer,
        'inpatient_outpatient': in_out,
        'price': price,
    }

    for k, v in mapping.items():
        d[k] = row.get(v)

    for c in NONE_COLS:
        if c not in d.keys():
            d[c] = 'NONE'

    return d


def add_prices(row: dict, *cols: str) -> float:
    """convert to ints, add, convert back to float"""
    prices = [row[c] for c in cols]
    ints = [int(p) * 100 for p in prices]
    return round(sum(ints) / 100, 2)


with open('020001_Providence-Alaska-Medical-Center_StandardCharges_NC.json') as f:
    data = json.load(f)

results = []
# GROSS CHARGES, BOTH
for row in data['Gross Charges']:
    m = {
        'internal_revenue_code': 'HOSPITAL SYSTEM CHARGE CODE',
        'description': 'CHARGE DESCRIPTION',
        'code': 'CPT/HCPCS CODE',
    }
    price = add_prices(row, 'PAMC LOCATION (Unit Price) [IP/OP]', 'PAMC LOCATION (Base Price) [IP/OP]')
    results.append(create_row(row, m, 'GROSS CHARGE', 'BOTH', price))

# cash price, BOTH
for row in data['Discount Cash Price - Gross']:
    m = {
        'internal_revenue_code': 'HOSPITAL SYSTEM CHARGE CODE',
        'description': 'CHARGE DESCRIPTION',
        'code': 'CPT/HCPCS CODE',
    }
    price = add_prices(row, 'PAMC LOCATION (UNIT PRICE) DISCOUNT CASH PRICE', 'PAMC LOCATION (BASE PRICE) DISCOUNT CASH PRICE')
    results.append(create_row(row, m, 'CASH PRICE', 'BOTH', price))

# inpatient min
for row in data['Inpatient De-identified Minimum Negotiated Charge']:
    m = {
        'code': 'MS-DRG',
        'description': 'Description',
    }
    price = row.get('De-Identified Minimum Negotiated Charge', 0.0)
    results.append(create_row(row, m, 'MIN', 'INPATIENT', price))

# inpatient max
for row in data['Inpatient De-identified Maximum Negotiated Charge']:
    m = {
        'code': 'APC',
        'description': 'Description',
    }
    price = row.get('De-Identified Maximum Negotiated Charge', 0.0)
    results.append(create_row(row, m, 'MAX', 'INPATIENT', price))

# outpatient min
for row in data['Outpatient De-identified Minimum Negotiated Charge']:
    m = {
        'code': 'APC',
        'description': 'Description',
        'price': 'De-Identified Minimum Negotiated Charge'
    }
    price = row.get('De-Identified Minimum Negotiated Charge', 0.0)
    results.append(create_row(row, m, 'MIN', 'OUTPATIENT', price))

# outpatient max
for row in data['Outpatient De-identified Maximum Negotiated Charge']:
    m = {
        'code': 'APC',
        'description': 'Description',
        'price': 'De-Identified Minimum Negotiated Charge'
    }
    price = row.get('De-Identified Maximum Negotiated Charge', 0.0)
    results.append(create_row(row, m, 'MAX', 'OUTPATIENT', price))

# insurance inpatient and outpatient
m = { 'code': 'APC', 'description': 'Description' }
for k in data.keys():
    if k.startswith('Inpatient Payer Specific Charge'):
        for row in data[k]:
            payer = row.get('Payer')
            price = row.get('Payer Specific Negotiated Charge', 0.0)
            results.append(create_row(row, m, payer, 'INPATIENT', price))
    elif k.startswith('Outpatient Payer Specific Charge'):
        for row in data[k]:
            payer = row.get('Payer')
            price = row.get('Payer Specific Negotiated Charge', 0.0)
            results.append(create_row(row, m, payer, 'OUTPATIENT', price))

# write file
with open('firstpass_prices.csv', 'wt') as f:
    csvwriter = csv.DictWriter(f, fieldnames=COLS)
    csvwriter.writeheader()
    for row in results:
        if row['price'] is not None and row['price'] > 0:
            csvwriter.writerow(row)
