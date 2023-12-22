import uuid

from django.db import models


# Create your models here.
class Customer(models.Model):
    first_name = models.CharField(max_length=32, null=False)
    last_name = models.CharField(max_length=32, null=False)
    email = models.EmailField(null=False)
    date_of_birth = models.DateField(null=False)
    exported = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class CustomerAddress(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, null=False)
    address_line_one = models.CharField(max_length=32, null=False)
    address_line_two = models.CharField(max_length=32, null=True)
    suburb = models.CharField(max_length=32, null=False)
    postal_code = models.CharField(max_length=12, null=False)
    exported = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.address_line_one}, {self.address_line_two}"


class BankAccountType(models.Model):
    account_type = models.CharField(max_length=15, verbose_name='Bank account type')
    transactional = models.BooleanField(default=0, verbose_name='Transactional field')

    def __str__(self):
        return self.account_type


class BankAccount(models.Model):
    account_type = models.ForeignKey(BankAccountType, on_delete=models.CASCADE, null=False)
    account_number = models.CharField(max_length=21, verbose_name='Bank account number')
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, null=False)
    exported = models.BooleanField(default=False)

    def __str__(self):
        return self.account_number


class AccountTransactionType(models.Model):
    transaction_type = models.CharField(max_length=12, null=False)
    transaction_operator = models.CharField(max_length=1, null=False)

    def __str__(self):
        return self.transaction_type


class TransactionCategory(models.Model):
    category_name = models.CharField(max_length=32, null=False)
    weight = models.CharField(max_length=12, null=True)

    def __str__(self):
        return self.category_name


class AccountTransaction(models.Model):
    bank_account = models.ForeignKey(BankAccount, on_delete=models.CASCADE, null=False)
    transaction_type = models.ForeignKey(AccountTransactionType, on_delete=models.CASCADE, null=False)
    timestamp = models.DateTimeField(auto_now=True)
    opening_balance = models.FloatField(null=False, default=0)
    transaction_value = models.FloatField(null=False, default=0)
    closing_balance = models.FloatField(null=False, default=0)
    reference = models.UUIDField(null=False, default=uuid.uuid4)
    description = models.CharField(max_length=512, null=False)
    transaction_category = models.ForeignKey(TransactionCategory, on_delete=models.CASCADE, null=False, default=1)
    transaction_date = models.DateField(null=True)
    exported = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.timestamp} - {self.transaction_value}"


class Retailer(models.Model):
    name = models.CharField(null=False, max_length=256)
    dominant_operational_format = models.CharField(null=True, max_length=256)
