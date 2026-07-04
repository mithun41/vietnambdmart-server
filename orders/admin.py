from django.contrib import admin
from .models import Order, OrderItem, Cart, CartItem

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['price']

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'first_name', 'last_name', 'status', 'total_amount', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['first_name', 'last_name', 'email', 'phone', 'user__username']
    inlines = [OrderItemInline]
    readonly_fields = ['total_amount']

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        # Calculate total amount after items are saved
        total = sum([item.price * item.quantity for item in form.instance.items.all() if item.price])
        form.instance.total_amount = total
        form.instance.save()

class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0

@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'created_at', 'updated_at']
    search_fields = ['user__username', 'user__email']
    inlines = [CartItemInline]
