from django import forms
from django.conf import settings

from .models import AccountTransaction, AccountTransactionType, BankAccountType, BankAccount, TransactionCategory

customer_id = getattr(settings, 'DEMO_USER_ID', None)


class TargetAccountSelectField(forms.ModelChoiceField):
    def __init__(self, *args, **kwargs):
        queryset = kwargs.pop('queryset', None)
        super().__init__(queryset=queryset, *args, **kwargs)


class AccountTransactionForm(forms.ModelForm):
    target_account = forms.CharField(max_length=100, required=True)
    target_bank = forms.CharField(max_length=100, required=True)

    class Meta:
        model = AccountTransaction
        fields = ['bank_account', 'transaction_type', 'opening_balance', 'transaction_value',
                  'closing_balance', 'reference', 'description', 'transaction_category']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Field style
        self.fields['bank_account'].widget = forms.Select(attrs={'class': 'form-select'})
        self.fields['transaction_value'].widget = forms.TextInput(attrs={'class': 'form-control'})
        self.fields['description'].widget = forms.TextInput(attrs={'class': 'form-control'})
        self.fields['target_bank'].widget = forms.TextInput(attrs={'class': 'form-control'})
        self.fields['target_account'].widget = forms.TextInput(attrs={'class': 'form-control'})

        # Lookup fields
        self.fields['bank_account'].queryset = BankAccount.objects.filter(customer=customer_id)
        self.fields['transaction_type'].initial = AccountTransactionType.objects.get(id=2)
        self.fields['transaction_category'].initial = TransactionCategory.objects.get(id=1)

        # hidden fields
        self.fields['transaction_type'].widget = forms.HiddenInput()
        self.fields['reference'].widget = forms.HiddenInput()
        self.fields['closing_balance'].widget = forms.HiddenInput()
        self.fields['opening_balance'].widget = forms.HiddenInput()
        self.fields['transaction_category'].widget = forms.HiddenInput()


class AccountTransferForm(forms.ModelForm):
    target_account = TargetAccountSelectField(queryset=BankAccount.objects.filter(customer=customer_id))

    class Meta:
        model = AccountTransaction
        fields = ['bank_account', 'transaction_type', 'opening_balance', 'transaction_value',
                  'closing_balance', 'reference', 'description', 'transaction_category']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Field style
        self.fields['bank_account'].widget = forms.Select(attrs={'class': 'form-select'})
        self.fields['transaction_value'].widget = forms.TextInput(attrs={'class': 'form-control'})
        self.fields['description'].widget = forms.TextInput(attrs={'class': 'form-control'})
        self.fields['target_account'].widget = forms.Select(attrs={'class': 'form-select'})

        # Lookup fields
        self.fields['bank_account'].queryset = BankAccount.objects.filter(customer=customer_id)
        self.fields['transaction_type'].initial = AccountTransactionType.objects.get(id=2)
        self.fields['transaction_category'].initial = TransactionCategory.objects.get(id=3)
        self.fields['target_account'].queryset = BankAccount.objects.filter(customer=customer_id)


        # hidden fields
        self.fields['transaction_type'].widget = forms.HiddenInput()
        self.fields['reference'].widget = forms.HiddenInput()
        self.fields['closing_balance'].widget = forms.HiddenInput()
        self.fields['opening_balance'].widget = forms.HiddenInput()
        self.fields['transaction_category'].widget = forms.HiddenInput()
