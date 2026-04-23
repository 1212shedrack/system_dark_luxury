from django import forms
from .models import Product, Category


class ProductForm(forms.ModelForm):
    # keep text input
    category = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )

    class Meta:
        model = Product
        fields = ['name', 'category', 'price',
                  'quantity', 'description', 'image']

        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'price': forms.NumberInput(attrs={'class': 'form-control'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control'}),
        }

    # ✅ FIX 1: convert BEFORE saving (important)
    def clean_category(self):
        category_name = self.cleaned_data['category']

        category, created = Category.objects.get_or_create(name=category_name)

        return category  # ✅ return object, not string

    # ✅ FIX 2: ensure correct assignment
    def save(self, commit=True):
        product = super().save(commit=False)

        product.category = self.cleaned_data['category']  # now it's object

        if commit:
            product.save()

        return product
