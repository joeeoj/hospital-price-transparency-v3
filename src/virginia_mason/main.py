#!/usr/bin/env python3
"""
The Hospital Chargemaster is a list of all billable services charged by the hospital for services rendered
Our hospital license covers our downtown Seattle Medical Center and our Federal Way Outpatient Surgery Center
The Professional Chargemaster is a list of all billable services charged by physicians for services rendered.
"""
import csv
from itertools import chain
from pathlib import Path

from src.config import USERNAME


DATA_DIR = Path.cwd() / 'data'
COL_MAPPING = {
    'Chargecode': 'internal_revenue_code',
    'Description': 'description',
    'CPT/HCPCS': 'code',
    'Fee': 'price',
}
CMS_CODE = '500005'
HOMEPAGE_URL = 'https://www.vmfh.org/our-hospitals/virginia-mason-medical-center.html'
CHARGEMASTER_URL = 'https://www.vmfh.org/billing-insurance/vm-billing-insurance/fees-by-location/virginia-mason-standard-charges'


def dict_to_csv(fname: str, data: list[dict]) -> None:
    with open(fname, 'wt') as f:
        csvwriter = csv.DictWriter(f, fieldnames=data[0].keys())
        csvwriter.writeheader()
        csvwriter.writerows(data)


def csv_to_dict(fname: str, code_disambiguator: str) -> list[dict]:
    data = []
    with open(fname) as f:
        csvreader = csv.DictReader(f)
        for row in csvreader:
            d = {v: row[k] or 'NONE' for k,v in COL_MAPPING.items()}
            d['code_disambiguator'] = code_disambiguator
            data.append(d)
    return data


def convert_price(price: str) -> float:
    if price == 'N/A':
        return 0.0

    try:
        return float(price.replace('$', '').replace(',', ''))
    except:
        return 0.0


def parse_row(d: dict) -> dict:
    d['price'] = convert_price(d['price'])
    if d['price'] == 0.0:
        return None

    d['cms_certification_num'] = CMS_CODE
    d['payer'] = 'GROSS CHARGE'
    d['inpatient_outpatient'] = 'UNSPECIFIED'
    return d


def main():
    hosp = csv_to_dict(DATA_DIR / 'hospital-chargemaster.csv', 'H')
    prof = csv_to_dict(DATA_DIR / 'professional-chargemaster.csv', 'P')
    rev_code_overlap = set([d['internal_revenue_code'] for d in hosp]) & set([d['internal_revenue_code'] for d in prof])
    code_overlap = set([d['code'] for d in hosp]) & set([d['code'] for d in prof])

    results = []
    for row in hosp + prof:
        d = parse_row(row)

        if d is None:
            continue
        elif d['internal_revenue_code'] not in rev_code_overlap and d['code'] not in code_overlap:
            # remove code disambiguator if only one internal rev code and one code exists
            d['code_disambiguator'] = 'NONE'
        results.append(d)

    # create prices.csv
    dict_to_csv('prices.csv', results)

    # write hospitals.csv
    dict_to_csv('hospitals.csv', [{
        'cms_certification_num': CMS_CODE,
        'name': 'VIRGINIA MASON MEDICAL CENTER',
        'address': '925 SENECA ST',
        'city': 'SEATTLE',
        'state': 'WA',
        'zip5': '98101',
        'beds': 336,
        'phone_number': '2062236600',
        'homepage_url': HOMEPAGE_URL,
        'chargemaster_url': CHARGEMASTER_URL,
        'last_edited_by_username': USERNAME,
    }])


if __name__ == '__main__':
    main()
