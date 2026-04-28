from django.shortcuts import render, redirect, get_object_or_404
from .models import Product
from .forms import ProductForm
from django.db.models import ProtectedError


# VIEW PRODUCTS (ALL USERS)
def product_list(request):
    products = Product.objects.filter(is_active=True)
    return render(request, 'products/product_list.html',
                  {'products': products})


# ADMIN PANEL
def manage_products(request):
    products = Product.objects.all()
    return render(request, 'products/manage_products.html',
                  {'products': products})


# CREATE
def add_product(request):
    form = ProductForm(request.POST or None, request.FILES or None)

    if form.is_valid():
        form.save()
        return redirect('product_list')

    return render(request, 'products/product_form.html', {'form': form})


# UPDATE
def update_product(request, pk):
    product = get_object_or_404(Product, pk=pk)
    form = ProductForm(request.POST or None,
                       request.FILES or None, instance=product)

    if form.is_valid():
        form.save()
        return redirect('manage_products')

    return render(request, 'products/product_form.html', {'form': form})


# DELETE
def delete_product(request, pk):
    product = get_object_or_404(Product, pk=pk)

    try:
        product.delete()
        # image deletion handled by signal in products/signals.py
    except ProtectedError:
        # Product has sales history — deactivate instead of delete
        product.is_active = False
        product.save()

    return redirect('manage_products')
