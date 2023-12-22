import uuid
import csv
from onlinebanking.models import Customer, CustomerAddress, BankAccountType, BankAccount, \
    TransactionCategory, AccountTransaction, AccountTransactionType, Retailer
from django.core.management.base import BaseCommand
import random
from mimesis import Person, Finance
from mimesis.locales import Locale
from time import sleep
from datetime import datetime, timedelta
import string
from config.settings import BASE_DIR
import random_address
from datetime import datetime, timedelta, timezone

person = Person(locale=Locale.EN)
finance = Finance(locale=Locale.EN_GB)


def generate_address():
    address = random_address.real_random_address()
    key = 'city'
    if key not in address:
        address[key] = 'San Francisco'
    return address


def generate_outbound_payment(bank_account, transaction_date, transaction_value):
    description = f"Payment made from {bank_account} to {person.first_name()} {person.last_name()}, " \
                  f"{finance.company()}: {uuid.uuid4()}"
    transaction_type = AccountTransactionType.objects.filter(transaction_type='Debit').first()
    transaction_category = TransactionCategory.objects.filter(category_name='EFT').first()
    latest_transaction = AccountTransaction.objects.filter(
        bank_account=bank_account).order_by('-timestamp').first()
    if latest_transaction:
        closing_balance = latest_transaction.closing_balance
    else:
        closing_balance = 0
    transaction_value = transaction_value
    if transaction_type.transaction_operator == '-':
        new_closing_balance = closing_balance - transaction_value
    elif transaction_type.transaction_operator == '+':
        new_closing_balance = closing_balance + transaction_value

    AccountTransaction.objects.create(
        bank_account=bank_account,
        transaction_type=transaction_type,
        transaction_category=transaction_category,
        opening_balance=closing_balance,
        transaction_value=transaction_value,
        closing_balance=new_closing_balance,
        description=description,
        transaction_date=transaction_date
    )
    return


def generate_transfer(bank_account, transaction_date, transaction_value):
    other_bank_account = BankAccount.objects.exclude(pk=bank_account.pk).first()
    if other_bank_account:
        outbound_transaction_type = AccountTransactionType.objects.filter(transaction_type='Debit').first()
        inbound_transaction_type = AccountTransactionType.objects.filter(transaction_type='Credit').first()
        transaction_category = TransactionCategory.objects.filter(category_name='Transfer').first()
        outbound_latest_transaction = AccountTransaction.objects.filter(
            bank_account=bank_account).order_by('-timestamp').first()
        if outbound_latest_transaction:
            last_outbound_closing_balance = outbound_latest_transaction.closing_balance
        else:
            last_outbound_closing_balance = 0
        transaction_value = transaction_value
        outbound_closing_balance = last_outbound_closing_balance - transaction_value
        inbound_latest_transaction = AccountTransaction.objects.filter(
            bank_account=other_bank_account).order_by('-timestamp').first()
        if inbound_latest_transaction:
            last_inbound_closing_balance = inbound_latest_transaction.closing_balance
        else:
            last_inbound_closing_balance = 0
        inbound_closing_balance = last_inbound_closing_balance + transaction_value
        description = f"Transfer made from {bank_account} to {other_bank_account} - Reason: internal"

        # outbound transaction
        AccountTransaction.objects.create(
            bank_account=bank_account,
            transaction_type=outbound_transaction_type,
            transaction_category=transaction_category,
            opening_balance=last_outbound_closing_balance,
            transaction_value=transaction_value,
            closing_balance=outbound_closing_balance,
            description=description,
            transaction_date=transaction_date
        )

        # inbound transaction
        AccountTransaction.objects.create(
            bank_account=other_bank_account,
            transaction_type=inbound_transaction_type,
            transaction_category=transaction_category,
            opening_balance=last_inbound_closing_balance,
            transaction_value=transaction_value,
            closing_balance=inbound_closing_balance,
            description=description,
            transaction_date=transaction_date
        )
    return


def generate_purchase(bank_account, transaction_date, transaction_value):
    transaction_type = AccountTransactionType.objects.filter(transaction_type='Debit').first()
    transaction_category = TransactionCategory.objects.filter(category_name='Transfer').first()
    latest_transaction = AccountTransaction.objects.filter(
        bank_account=bank_account).order_by('-timestamp').first()
    if latest_transaction:
        opening_balance = latest_transaction.closing_balance
    else:
        opening_balance = random.randint(100, 5000)
    transaction_value = transaction_value
    if transaction_type.transaction_operator == '-':
        closing_balance = opening_balance - transaction_value
    elif transaction_type.transaction_operator == '+':
        closing_balance = opening_balance + transaction_value
    retailers = Retailer.objects.all()
    retailer = random.choice(retailers)
    address = generate_address()
    city = address['city']
    state = address['state']
    description = f"Purchase made at {retailer.name}, {city}, {state}"

    AccountTransaction.objects.create(
        bank_account=bank_account,
        transaction_type=transaction_type,
        transaction_category=transaction_category,
        opening_balance=opening_balance,
        transaction_value=transaction_value,
        closing_balance=closing_balance,
        description=description,
        transaction_date=transaction_date
    )


def import_retailers():
    from onlinebanking.models import Retailer
    with open(BASE_DIR / "files/cos2019.csv", newline='') as csvfile:
        reader = csv.DictReader(csvfile, delimiter=';')
        for row in reader:
            instance = Retailer(
                name=row['name'],
                dominant_operational_format=row['dominant_operational_format'],
            )
            instance.save()


def generate_customer():
    letters = string.ascii_letters
    prefix_length = random.randint(3, 6)
    suffix_length = random.randint(3, 6)
    prefix = ''.join(random.choice(letters) for _ in range(prefix_length))
    suffix = ''.join(random.choice(letters) for _ in range(suffix_length))

    current_date = datetime.now()
    start_date = current_date - timedelta(days=365 * 100)
    end_date = current_date - timedelta(days=365 * 18)
    random_days = random.randint(0, (end_date - start_date).days)

    first_name = person.first_name()
    last_name = person.last_name()
    email = f"{prefix}{suffix}@demo-domain.org"
    date_of_birth = start_date + timedelta(days=random_days)

    new_customer = Customer.objects.create(first_name=first_name, last_name=last_name, email=email,
                                           date_of_birth=date_of_birth)
    return new_customer


def generate_customer_address(customer):
    address = generate_address()
    CustomerAddress.objects.create(customer=customer, address_line_one=address['address1'],
                                   address_line_two=address['address2'],
                                   suburb=address['city'], postal_code=address['postalCode'])


def random_description():
    payment_topics = ['gifts', 'mobile phone', 'school fees', 'cleaner', 'babysitting', 'contractors', 'gym', 'repairs']
    word = random.choice(payment_topics)
    return word


def generate_bank_account_number():
    number = random.randint(100000, 999999)
    prefix = random.randint(1, 9)
    acc_number = f"EL0{prefix}-{number}"
    return acc_number


def generate_bank_account(customer):
    bank_accounts = BankAccount.objects.filter(customer=customer)
    if not bank_accounts:
        bank_account_type = BankAccountType.objects.filter(account_type='Transmission').first()
    else:
        bank_account_type_list = BankAccountType.objects.all()
        bank_account_type = random.choice(bank_account_type_list)

    account_number = generate_bank_account_number()
    account_number = f"{account_number}-{bank_account_type.account_type}"
    BankAccount.objects.create(account_type=bank_account_type, account_number=account_number, customer=customer,
                               exported=0)
    return


def get_date_x_months_ago(x):
    current_date = datetime.now(tz=timezone.utc)
    months_ago_date = current_date - timedelta(days=30 * x)
    return months_ago_date


class Command(BaseCommand):
    help = 'Generate random users'

    def add_arguments(self, parser):
        parser.add_argument('arg1', type=int, help='Indicates the number of customers to be created')
        parser.add_argument('arg2', type=int,
                            help='Indicates the number of months to create transactions for')
        parser.add_argument('arg3', type=int, help='Indicates the minimum transaction value')
        parser.add_argument('arg4', type=int, help='Indicates the maximum transaction value')

    def handle(self, *args, **kwargs):
        number_of_customers = kwargs['arg1']
        number_of_months = kwargs['arg2']
        transaction_minimum = kwargs['arg3']
        transaction_maximum = kwargs['arg4']

        import_retailers()
        customer_counter = 1
        while customer_counter <= number_of_customers:
            customer = generate_customer()
            print(f"Executed cycle {customer_counter} of {number_of_customers}")
            customer_counter = customer_counter + 1

        all_customers = Customer.objects.all()
        transaction_categories = TransactionCategory.objects.all()
        category_list = []
        weight_list = []
        for t in transaction_categories:
            category_list.append(t.category_name)
            weight_list.append(int(t.weight))
        for customer in all_customers:
            generate_customer_address(customer)
            number_bank_accounts = random.randint(1, 5)
            bank_account_counter = 0
            while bank_account_counter <= number_bank_accounts:
                generate_bank_account(customer)
                bank_account_counter = bank_account_counter + 1

        start_date = get_date_x_months_ago(number_of_months)
        end_date = datetime.now(tz=timezone.utc)
        current_date = start_date
        while current_date <= end_date:
            for customer in all_customers:
                transaction_count = random.randint(transaction_minimum, transaction_maximum)
                print(transaction_count)
                counter = 1
                while counter <= transaction_count:
                    transaction_category = random.choices(category_list, weights=weight_list)[0]
                    if transaction_category != 'Purchase':
                        transaction_type = AccountTransactionType.objects.order_by('?').first()
                        bank_account = BankAccount.objects.filter(customer=customer).order_by('?').first()
                        random_selection = random.randint(1, 10)
                        if random_selection < 4:
                            transaction_value = random.randint(200, 800)
                            generate_transfer(bank_account, current_date, transaction_value)
                        else:
                            transaction_value = random.randint(50, 250)
                            generate_outbound_payment(bank_account, current_date, transaction_value)
                    else:
                        bank_account = BankAccount.objects.filter(customer=customer,
                                                                  account_type__transactional=True).order_by(
                            '?').first()
                        transaction_value = random.randint(10, 200)
                        generate_purchase(bank_account, current_date, transaction_value)
                    counter = counter + 1
                    print(counter, transaction_count)
            current_date += timedelta(days=1)
