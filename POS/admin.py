from django.contrib import admin
from .models import Sale, SaleItem


class SaleItemInline(admin.TabularInline):
    model = SaleItem
    extra = 0
    readonly_fields = ('subtotal',)

    def subtotal(self, obj):
        return f"TZS {obj.subtotal:,.2f}"
    subtotal.short_description = 'Subtotal'


@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = ('sale_number', 'cashier', 'payment_method',
                    'total_amount', 'status', 'created_at')
    list_filter = ('status', 'payment_method', 'created_at')
    search_fields = ('sale_number', 'cashier__username')
    readonly_fields = ('sale_number', 'created_at', 'change_due')
    inlines = [SaleItemInline]


@admin.register(SaleItem)
class SaleItemAdmin(admin.ModelAdmin):
    list_display = ('sale', 'product', 'quantity', 'unit_price', 'subtotal')
    search_fields = ('sale__sale_number', 'product__name')
