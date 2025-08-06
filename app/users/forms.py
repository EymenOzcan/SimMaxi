from django import forms


class JoinDealerForm(forms.Form):
    secure_id = forms.CharField(label="Bayi Kodu", max_length=12)
