import os
import googlemaps
from elasticsearch import Elasticsearch
from onlinebanking.models import BankAccount, BankAccountType, AccountTransactionType, AccountTransaction, Customer, \
    CustomerAddress, Retailer
from envmanager.models import ClusterDetail
from django.core.management.base import BaseCommand
import json
import re
from config.settings import GOOGLE_MAPS_API_KEY
index_name = "search-bank-project-transactions_v1"

cluster_details = ClusterDetail.objects.all().first()
es = Elasticsearch(
    cloud_id=cluster_details.cloud_id,
    http_auth=(cluster_details.elastic_user, cluster_details.elastic_password)
)

def build_record(transaction_id):
    payload = {}
    transaction_details = AccountTransaction.objects.filter(id=transaction_id).first()
    bank_account_details = BankAccount.objects.filter(id=transaction_details.bank_account_id).first()
    customer_details = Customer.objects.filter(id=bank_account_details.customer_id).first()

    payload = {
        "transaction_date": transaction_details.transaction_date.strftime("%Y-%m-%d"),
        "bank_account_number": str(transaction_details.bank_account),
        "bank_account_type": str(bank_account_details.account_type),
        "transaction_category": transaction_details.transaction_category.category_name,
        "transaction_type": transaction_details.transaction_type.transaction_type,
        "opening_balance": transaction_details.opening_balance,
        "transaction_value": transaction_details.transaction_value,
        "closing_balance": transaction_details.closing_balance,
        "description": transaction_details.description,
        "customer_name": f'{customer_details.first_name} {customer_details.last_name}',
        "customer_email": customer_details.email
    }
    pattern = r"merchant: (.+?), location: (.+)$"
    match = re.search(pattern, transaction_details.description)
    if match:
        merchant = match.group(1)
        retailer_format = Retailer.objects.filter(name=merchant).first()
        payload['description'] = f"{transaction_details.description} - category: { retailer_format.dominant_operational_format }"
        payload['merchant_name'] = match.group(1)
        payload['location'] = match.group(2)

        gmaps = googlemaps.Client(key=GOOGLE_MAPS_API_KEY)
        geocode_result = gmaps.geocode(payload['location'])
        location = geocode_result[0]['geometry']['location']
        latitude = location['lat']
        longitude = location['lng']
        payload['geometry'] = {
            "lat": latitude,
            "lon": longitude
        }
    payload = json.dumps(payload)
    print(payload)
    return payload

class Command(BaseCommand):
    help = 'Export un-exported records to Elasticsearch'

    def handle(self, *args, **kwargs):
        records_to_import = AccountTransaction.objects.filter(exported=0)
        for r in records_to_import:
            payload = build_record(r.id)
            index_response = es.index(index=index_name, id=r.id, document=payload)
            self.stdout.write(
                self.style.SUCCESS('Successfully indexed record "%s"' % r.id)
            )
