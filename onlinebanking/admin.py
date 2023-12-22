from django.contrib import admin
from .models import BankAccountType, BankAccount, Customer, CustomerAddress, AccountTransactionType, AccountTransaction, TransactionCategory, Retailer
from envmanager.models import ClusterDetail
# Register your models here.
admin.site.register(BankAccountType)
admin.site.register(BankAccount)
admin.site.register(Customer)
admin.site.register(CustomerAddress)
admin.site.register(AccountTransactionType)
admin.site.register(AccountTransaction)
admin.site.register(TransactionCategory)
admin.site.register(ClusterDetail)
admin.site.register(Retailer)