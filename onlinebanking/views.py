import json

import elasticsearch
from django.shortcuts import render
from django.conf import settings
from .models import BankAccount, BankAccountType, AccountTransactionType, AccountTransaction, Customer
from envmanager.models import ClusterDetail
from .forms import AccountTransactionForm, AccountTransferForm
from elasticsearch import Elasticsearch
import boto3
from langchain.llms import Bedrock, AzureOpenAI
from langchain_core.output_parsers import StrOutputParser
from langchain.prompts import ChatPromptTemplate
from dotenv import load_dotenv
import os
load_dotenv()

from langchain.schema import (
    SystemMessage,
    HumanMessage,
    AIMessage
)

customer_id = getattr(settings, 'DEMO_USER_ID', None)
index_name = getattr(settings, 'TRANSACTION_INDEX_NAME', None)
aws_region = getattr(settings, 'AWS_REGION', None)
aws_access_key = getattr(settings, 'AWS_ACCESS_KEY', None)
aws_secret_key = getattr(settings, 'AWS_SECRET_KEY', None)
default_model_id = "amazon.titan-text-express-v1"
openai_api_key = os.environ['openai_api_key']
openai_api_type = os.environ['openai_api_type']
openai_api_base = os.environ['openai_api_base']
openai_api_version = os.environ['openai_api_version']


def connect_to_bedrock():
    bedrock_client = boto3.client(
        service_name="bedrock-runtime",
        region_name=aws_region,
        aws_access_key_id=aws_access_key,
        aws_secret_access_key=aws_secret_key
    )

    AWS_MODEL_ID = default_model_id
    llm = Bedrock(
        client=bedrock_client,
        model_id=AWS_MODEL_ID
    )
    return llm


def connect_to_azureopenai():
    BASE_URL = openai_api_base
    API_KEY = openai_api_key
    DEPLOYMENT_NAME = "timb-davinci"
    llm = AzureOpenAI(
        openai_api_base=BASE_URL,
        openai_api_version=openai_api_version,
        deployment_name=DEPLOYMENT_NAME,
        openai_api_key=API_KEY,
        openai_api_type="azure",
        temperature=0.1
    )
    return llm


# Create your views here.
def search(request):
    if request.method == 'POST':
        question = request.POST.get('question')
        demo_user = Customer.objects.filter(id=customer_id).first()
        # handle the es connection for the map and conversational search components
        cluster_details = ClusterDetail.objects.all().first()
        es = Elasticsearch(
            cloud_id=cluster_details.cloud_id,
            http_auth=(cluster_details.elastic_user, cluster_details.elastic_password)
        )
        query = {
            "query": {
                "bool": {
                    "filter": [
                        {
                            "term": {"customer_email.keyword": demo_user.email}
                        }
                    ],
                    "should": [
                        {
                            "match": {
                                "description": question
                            }
                        },
                        {
                            "text_expansion": {
                                "description": {
                                    "model_id": ".elser_model_2_linux-x86_64",
                                    "model_text": question,
                                    "boost": 1
                                }
                            }
                        }
                    ]
                }
            }
        }
        fields = ["transaction_date", "description", "transaction_value", "closing_balance", "bank_account_type",
                  "transaction_category"]
        response = es.search(index=index_name, body=query, size=100, fields=fields)
        transaction_results = []
        context = []
        for hit in response['hits']['hits']:
            if hit['_score'] > 0:
                hit_data = hit['_source']
                hit_data['score'] = hit['_score']
                transaction_results.append(hit_data)
                context.append(hit['_source']['description'])

        string_results = json.dumps(context)
        # interact with the LLM

        augmented_prompt = f"""Using only the contexts below, answer the query.
        Contexts: {string_results}

        Query: {question}"""
        messages = [
            SystemMessage(
                content="You are a helpful financial analyst using transaction search results to give advice to customers. "
                        "If you can asnwer a question, attempt to answer it fully. Assume the context provided provides an accurate response to the query."),
            # HumanMessage(content="Hi AI, how are you today?"),
            # AIMessage(content="I am great thank you. How can I help you today?"),
            HumanMessage(content=augmented_prompt)
        ]
        print(messages)
        model = connect_to_azureopenai()
        answer = model.invoke(messages)
    else:
        question = 'no question'
        answer = 'no answer'
        transaction_results = []
    context = {
        'question': question,
        'results': transaction_results,
        'answer': answer
    }
    return render(request, "onlinebanking/search.html", context)


def transactions(request, bank_account_id):
    transaction_list = AccountTransaction.objects.filter(bank_account=bank_account_id).order_by(
        '-transaction_date')
    context = {
        'transaction_list': transaction_list
    }
    return render(request, "onlinebanking/transactions.html", context)


def landing(request):
    demo_user = Customer.objects.filter(id=customer_id).first()
    # handle the es connection for the map and conversational search components
    cluster_details = ClusterDetail.objects.all().first()
    es = Elasticsearch(
        cloud_id=cluster_details.cloud_id,
        http_auth=(cluster_details.elastic_user, cluster_details.elastic_password)
    )
    query = {
        "bool": {
            "filter": [
                {
                    "term": {"customer_email.keyword": demo_user.email}
                },
                {
                    "term": {"transaction_category.keyword": "Purchase"}
                }
            ]
        }
    }
    mapped_results = []
    search_results = es.search(index=index_name, query=query)
    locations = [{'lat': hit.geometry['lat'], 'lon': hit.geometry['lon']} for hit in search_results if
                 'geometry' in hit]

    # handle any form posting
    if request.method == 'POST':
        payment_form = AccountTransactionForm(request.POST)
        transfer_form = AccountTransferForm(request.POST)

        if payment_form.is_valid():
            # get latest balance
            latest_transaction = AccountTransaction.objects.filter(
                bank_account=payment_form.cleaned_data['bank_account']).order_by('-timestamp').first()

            new_transaction = payment_form.save(commit=False)
            new_transaction.opening_balance = latest_transaction.closing_balance
            new_transaction.transaction_value = payment_form.cleaned_data['transaction_value']
            new_transaction.closing_balance = new_transaction.opening_balance - new_transaction.transaction_value
            print(
                f"Our balance was: {new_transaction.opening_balance}. Our transaction value was: {new_transaction.transaction_value}. Which leaves us with {new_transaction.closing_balance}")

            new_description = f"Payment to {payment_form.cleaned_data['target_bank']} | {payment_form.cleaned_data['target_account']}. {new_transaction.description}"
            new_transaction.description = new_description
            new_transaction.save()

        if transfer_form.is_valid():
            # work out the closing balance for the source account and save the record
            latest_transaction_source_account = AccountTransaction.objects.filter(
                bank_account=payment_form.cleaned_data['bank_account']).order_by('-timestamp').first()

            new_outbound_transfer = transfer_form.save(commit=False)
            new_outbound_transfer.opening_balance = latest_transaction_source_account.closing_balance
            new_outbound_transfer.closing_balance = new_outbound_transfer.opening_balance - new_outbound_transfer.transaction_value
            new_outbound_description = f"Outbound transfer to {transfer_form.cleaned_data['target_account']}. {transfer_form.cleaned_data['description']}"
            new_outbound_transfer.description = new_outbound_description
            new_outbound_transfer.save()

            # work out the closing balance for the target account and save the record
            new_inbound_transfer = AccountTransaction()
            latest_transaction_target_account = AccountTransaction.objects.filter(
                bank_account=transfer_form.cleaned_data['target_account']).order_by('-timestamp').first()
            new_inbound_transfer.transaction_value = transfer_form.cleaned_data['transaction_value']
            new_inbound_transfer.opening_balance = latest_transaction_target_account.closing_balance
            new_inbound_transfer.closing_balance = new_inbound_transfer.opening_balance + new_inbound_transfer.transaction_value
            new_inbound_description = f"Inbound transfer from {new_outbound_transfer.bank_account}. {transfer_form.cleaned_data['description']} "
            new_inbound_transfer.description = new_inbound_description
            new_inbound_transfer.bank_account = transfer_form.cleaned_data['target_account']
            new_inbound_transfer.transaction_type = transfer_form.cleaned_data['transaction_type']
            new_inbound_transfer.transaction_category = transfer_form.cleaned_data['transaction_category']
            new_inbound_transfer.save()

    payment_form = AccountTransactionForm()
    transfer_form = AccountTransferForm()
    account_list = BankAccount.objects.filter(customer=customer_id)
    account_dict_list = []
    for a in account_list:
        latest_transaction = AccountTransaction.objects.filter(bank_account=a).order_by(
            '-transaction_date').first()
        account_dict = {
            'id': a.id,
            'account_number': a.account_number,
            'latest_balance': latest_transaction.closing_balance
        }
        account_dict_list.append(account_dict)
    context = {
        'account_dict_list': account_dict_list,
        'payment_form': payment_form,
        'transfer_form': transfer_form,
        'search_results': mapped_results,
        'api_key': getattr(settings, 'GOOGLE_MAPS_API_KEY', None)
    }
    return render(request, "onlinebanking/index.html", context)
