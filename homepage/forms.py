from django import forms
from .models import Customer

class CustomerRegisterForm(
forms.ModelForm):
    password1 = forms.CharField(label='Password', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Confirm Password', widget=forms.PasswordInput)

    class Meta:
        model = Customer
        fields = ('email', 'username')

    def clean_password2(self):
        p1 = self.cleaned_data.get('password1')
        p2 = self.cleaned_data.get('password2')
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError("Passwords don't match")
        return p2

    def save(self, commit=True):
        customer = super().save(commit=False)
        customer.set_password(self.cleaned_data['password1'])
        if commit:
            customer.save()
        return customer


class CustomerLoginForm(forms.Form):
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput)


class CheckoutForm(forms.Form):
    # Address Information
    division = forms.ModelChoiceField(
        queryset=None,
        empty_label="Select Division",
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'id_division'})
    )
    district = forms.ModelChoiceField(
        queryset=None,
        empty_label="Select District",
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'id_district'})
    )
    thana = forms.ModelChoiceField(
        queryset=None,
        empty_label="Select Thana",
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'id_thana'})
    )
    area = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'id': 'id_area',
            'placeholder': 'Enter your area name (e.g., Dhanmondi 32, Gulshan 1, etc.)'
        }),
        label="Area"
    )
    detailed_address = forms.CharField(
        max_length=500,
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'House/Flat number, Road, Building name (Optional)'
        }),
        label="Detailed Address (Optional)"
    )
    phone_number = forms.CharField(
        max_length=15,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '01XXXXXXXXX'
        }),
        label="Your Phone Number"
    )
    
    # Payment Information
    PAYMENT_CHOICES = [
        ('bkash', 'bKash'),
        ('rocket', 'Rocket'),
        ('upay', 'Upay'),
        ('nagad', 'Nagad'),
    ]
    
    payment_method = forms.ChoiceField(
        choices=PAYMENT_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'payment-method'}),
        label="Select Payment Method"
    )
    payment_phone = forms.CharField(
        max_length=15,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '01XXXXXXXXX'
        }),
        label="Payment Account Number"
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from .models import Division, District, Thana, Area
        
        self.fields['division'].queryset = Division.objects.all()
        self.fields['district'].queryset = District.objects.none()
        self.fields['thana'].queryset = Thana.objects.none()
        
        if 'division' in self.data:
            try:
                division_id = int(self.data.get('division'))
                self.fields['district'].queryset = District.objects.filter(division_id=division_id).order_by('name')
            except (ValueError, TypeError):
                pass
        
        if 'district' in self.data:
            try:
                district_id = int(self.data.get('district'))
                self.fields['thana'].queryset = Thana.objects.filter(district_id=district_id).order_by('name')
            except (ValueError, TypeError):
                pass
