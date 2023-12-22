from django.http import StreamingHttpResponse
from django.shortcuts import render
from django.conf import settings
from onlinebanking.models import BankAccount, BankAccountType, AccountTransactionType, AccountTransaction, Customer, \
    CustomerAddress, Retailer
from envmanager.models import ClusterDetail
from django.core.management import call_command
from elasticsearch import Elasticsearch
import subprocess
from io import StringIO

customer_id = getattr(settings, 'DEMO_USER_ID', None)
index_name = getattr(settings, 'TRANSACTION_INDEX_NAME', None)


# Create your views here.
def manager(request):
    return render(request, 'envmanager/index.html')


def cluster(request):
    cluster_details = ClusterDetail.objects.all().first()
    if ClusterDetail.objects.count():
        if request.method == 'POST':
            cluster_details.cloud_id = request.POST.get('cloud_id')
            cluster_details.elastic_user = request.POST.get('elastic_user')
            cluster_details.elastic_password = request.POST.get('elastic_password')
            cluster_details.save()
        es = Elasticsearch(
            cloud_id=cluster_details.cloud_id,
            http_auth=(cluster_details.elastic_user, cluster_details.elastic_password)
        )
        context = {
            'id': cluster_details.id,
            'cloud_id': cluster_details.cloud_id,
            'elastic_user': cluster_details.elastic_user,
            'elastic_password': cluster_details.elastic_password,
            'es': es.info,
            'ping': es.ping
        }
    else:
        if request.method == 'POST':
            cloud_id = request.POST.get('cloud_id')
            elastic_user = request.POST.get('elastic_user')
            elastic_password = request.POST.get('elastic_password')
            cluster_details = ClusterDetail(cloud_id=cloud_id, elastic_user=elastic_user,
                                            elastic_password=elastic_password)
            cluster_details.save()
            cluster_details = ClusterDetail.objects.all().first()
            es = Elasticsearch(
                cloud_id=cluster_details.cloud_id,
                http_auth=(cluster_details.elastic_user, cluster_details.elastic_password)
            )
            context = {
                'id': cluster_details.id,
                'cloud_id': cluster_details.cloud_id,
                'elastic_user': cluster_details.elastic_user,
                'elastic_password': cluster_details.elastic_password,
                'es': es.info,
                'ping': es.ping
            }
        else:
            context = {
                'cloud_id': 'Add-your-cloud-id-here',
                'elastic_user': 'Add-your-user-here',
                'elastic_password': 'Add-your-password-here',
            }
    return render(request, 'envmanager/cluster.html', context)


def generate_data(request):
    context = {
        'view_name': 'generate_data'
    }
    return render(request, 'envmanager/index.html', context)


def execute_backend_command(request):
    if request.POST.get('command_name') == 'generate_data':
        message = 'The data generation command has been called and will execute asynchronously in the background.'
        number_of_customers = request.POST.get('number_of_customers')
        number_of_months = request.POST.get('number_of_months')
        transaction_minimum = request.POST.get('transaction_minimum')
        transaction_maximum = request.POST.get('transaction_maximum')
        # Check if arguments are not None or empty before calling call_command
        args = [
            arg for arg in [number_of_customers, number_of_months, transaction_minimum, transaction_maximum]
            if arg is not None and arg != ''
        ]
        call_command('generate_dataset', *args)
        context = {
            'view_name': 'generate_data'
        }
    return render(request, 'envmanager/command_handler.html', context)


def process_data_action(request):
    if request.method == 'POST':
        context = {
            'view_name': 'create',
            'form_data': {
                'number_of_customers': request.POST.get('number_of_customers'),
                'number_of_months': request.POST.get('number_of_months'),
                'transaction_minimum': request.POST.get('transaction_minimum'),
                'transaction_maximum': request.POST.get('transaction_maximum'),
            }
        }
    return render(request, 'envmanager/action.html', context)


def clear_data(request):
    cluster_details = ClusterDetail.objects.all().first()
    es = Elasticsearch(
        cloud_id=cluster_details.cloud_id,
        http_auth=(cluster_details.elastic_user, cluster_details.elastic_password))
    query = {
        "match_all": {}
    }
    if request.method == 'POST':
        if request.POST.get('delete'):
            es.delete_by_query(index=index_name, query=query)
            Customer.objects.exclude(id=customer_id).delete()
            CustomerAddress.objects.all().delete()
            BankAccount.objects.all().delete()
            Retailer.objects.all().delete()

    es_record_count = es.count(index=index_name, query=query)
    bank_account_count = BankAccount.objects.count()
    customer_count = Customer.objects.exclude(id=customer_id).count()
    customer_address_count = CustomerAddress.objects.count()
    account_transactions_count = AccountTransaction.objects.count()
    retailer_count = Retailer.objects.count()

    context = {
        'view_name': 'clear_data',
        'bank_account_count': bank_account_count,
        'customer_count': customer_count,
        'customer_address_count': customer_address_count,
        'account_transactions_count': account_transactions_count,
        'retailer_count': retailer_count,
        'es_record_count': es_record_count['count']
    }
    return render(request, 'envmanager/index.html', context)


def run_command():
    # Use subprocess.Popen to run the command and capture output in real-time
    process = subprocess.Popen(
        ['python', 'manage.py', 'elastic_export'],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,  # Use line buffering
        universal_newlines=True,
    )

    # Iterate over the command's output in real-time
    for line in iter(process.stdout.readline, ''):
        yield line

    # Ensure the process has completed
    process.stdout.close()
    process.wait()


def export_data(request):
    if request.POST.get('command_name') == 'elastic_export':
        # Create a StreamingHttpResponse with the generator function
        response = StreamingHttpResponse(run_command(), content_type="text/plain")

    else:
        response = 0

    account_transactions_count = AccountTransaction.objects.filter(exported=0).count()
    context = {
        'record_count': account_transactions_count,
        'view_name': 'export',
        'streaming_content': response
    }
    return render(request, 'envmanager/export.html', context)
