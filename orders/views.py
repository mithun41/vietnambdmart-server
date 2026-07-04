from rest_framework import viewsets, permissions
from .models import Order
from .serializers import OrderSerializer

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from rest_framework.pagination import PageNumberPagination
from django.utils import timezone
from django.utils.dateparse import parse_date

class OrderPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100

class OrderViewSet(viewsets.ModelViewSet):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = OrderPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'payment_method']
    search_fields = ['first_name', 'last_name', 'email', 'phone', 'id']
    ordering_fields = ['created_at', 'total_amount']

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            queryset = Order.objects.all().order_by('-created_at')
        else:
            queryset = Order.objects.filter(user=user).order_by('-created_at')

        period = self.request.query_params.get('period')
        
        if period == 'today':
            today = timezone.localtime().date()
            queryset = queryset.filter(created_at__date=today)
        elif period == 'this_month':
            today = timezone.localtime().date()
            queryset = queryset.filter(created_at__year=today.year, created_at__month=today.month)
        else:
            start_date = self.request.query_params.get('start_date')
            end_date = self.request.query_params.get('end_date')

            if start_date:
                parsed_start = parse_date(start_date)
                if parsed_start:
                    queryset = queryset.filter(created_at__date__gte=parsed_start)
            
            if end_date:
                parsed_end = parse_date(end_date)
                if parsed_end:
                    queryset = queryset.filter(created_at__date__lte=parsed_end)

        return queryset

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from .models import Cart, CartItem
from .serializers import CartSerializer, CartItemSerializer

class CartView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        cart, created = Cart.objects.get_or_create(user=request.user)
        serializer = CartSerializer(cart)
        return Response(serializer.data)

class CartItemViewSet(viewsets.ModelViewSet):
    serializer_class = CartItemSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return CartItem.objects.filter(cart__user=self.request.user)

    def perform_create(self, serializer):
        cart, created = Cart.objects.get_or_create(user=self.request.user)
        
        product = serializer.validated_data['product']
        quantity = serializer.validated_data['quantity']
        
        # If product already in cart, just increase quantity
        existing_item = CartItem.objects.filter(cart=cart, product=product).first()
        if existing_item:
            existing_item.quantity += quantity
            existing_item.save()
            serializer.instance = existing_item
        else:
            serializer.save(cart=cart)

from django.db.models import Sum, Count, F
from django.contrib.auth import get_user_model
from products.models import Product
from .models import Order, OrderItem

User = get_user_model()

from django.utils import timezone

class DashboardStatsView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        period = request.query_params.get('period')
        order_qs = Order.objects.all()
        order_item_qs = OrderItem.objects.all()

        # Time Filters
        if period == 'today':
            today = timezone.localtime().date()
            order_qs = order_qs.filter(created_at__date=today)
            order_item_qs = order_item_qs.filter(order__created_at__date=today)
        elif period == 'this_month':
            today = timezone.localtime().date()
            order_qs = order_qs.filter(created_at__year=today.year, created_at__month=today.month)
            order_item_qs = order_item_qs.filter(order__created_at__year=today.year, order__created_at__month=today.month)
        else:
            start_date = request.query_params.get('start_date')
            end_date = request.query_params.get('end_date')

            if start_date:
                parsed_start = parse_date(start_date)
                if parsed_start:
                    order_qs = order_qs.filter(created_at__date__gte=parsed_start)
                    order_item_qs = order_item_qs.filter(order__created_at__date__gte=parsed_start)
            
            if end_date:
                parsed_end = parse_date(end_date)
                if parsed_end:
                    order_qs = order_qs.filter(created_at__date__lte=parsed_end)
                    order_item_qs = order_item_qs.filter(order__created_at__date__lte=parsed_end)


        # 1. Total Revenue (only Delivered orders)
        revenue_data = order_qs.filter(status='Delivered').aggregate(total_revenue=Sum('total_amount'))
        total_revenue = revenue_data['total_revenue'] or 0

        # Calculate Total Profit
        profit_data = order_item_qs.filter(order__status='Delivered').aggregate(
            total_profit=Sum((F('price') - F('purchase_price')) * F('quantity'))
        )
        total_profit = profit_data['total_profit'] or 0

        # 2. Counts
        total_orders = order_qs.count()
        total_products = Product.objects.count()
        total_customers = User.objects.filter(is_superuser=False, is_staff=False).count()

        # 3. Order Status Breakdown
        status_counts = order_qs.values('status').annotate(count=Count('id'))
        order_status_summary = {item['status']: item['count'] for item in status_counts}

        # 4. Recent Orders
        recent_orders = order_qs.order_by('-created_at')[:5]
        recent_orders_data = [
            {
                "id": o.id,
                "customer": f"{o.first_name} {o.last_name}",
                "total_amount": o.total_amount,
                "status": o.status,
                "date": o.created_at
            } for o in recent_orders
        ]

        # 5. Top Products
        top_products = Product.objects.all().order_by('-sold_quantity')[:5]
        top_products_data = [
            {
                "id": p.id,
                "name": p.name,
                "sold_quantity": p.sold_quantity,
                "stock": p.stock,
                "price": p.price
            } for p in top_products
        ]

        return Response({
            "total_revenue": total_revenue,
            "total_profit": total_profit,
            "total_orders": total_orders,
            "total_products": total_products,
            "total_customers": total_customers,
            "order_status_summary": order_status_summary,
            "recent_orders": recent_orders_data,
            "top_products": top_products_data
        })

from django.utils.dateparse import parse_date
from rest_framework.pagination import PageNumberPagination
from django.utils import timezone

class SalesReportPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100

class SalesReportView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        status_filter = request.query_params.get('status', 'Delivered')
        period = request.query_params.get('period')
        queryset = Order.objects.all().order_by('-created_at')

        # Time Filters
        if period == 'today':
            today = timezone.localtime().date()
            queryset = queryset.filter(created_at__date=today)
        elif period == 'this_month':
            today = timezone.localtime().date()
            queryset = queryset.filter(created_at__year=today.year, created_at__month=today.month)
        else:
            start_date = request.query_params.get('start_date')
            end_date = request.query_params.get('end_date')

            if start_date:
                parsed_start = parse_date(start_date)
                if parsed_start:
                    queryset = queryset.filter(created_at__date__gte=parsed_start)
            
            if end_date:
                parsed_end = parse_date(end_date)
                if parsed_end:
                    queryset = queryset.filter(created_at__date__lte=parsed_end)

        # Status Filter:
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        # Calculate Summary
        total_orders = queryset.count()
        total_revenue = queryset.aggregate(total_revenue=Sum('total_amount'))['total_revenue'] or 0

        # Calculate Profit
        profit_data = OrderItem.objects.filter(order__in=queryset).aggregate(
            total_profit=Sum((F('price') - F('purchase_price')) * F('quantity'))
        )
        total_profit = profit_data['total_profit'] or 0

        # Paginate the queryset
        paginator = SalesReportPagination()
        paginated_queryset = paginator.paginate_queryset(queryset, request, view=self)

        # Detailed Sales Data
        sales_data = []
        for order in paginated_queryset:
            items_data = []
            for item in order.items.all():
                unit_price = item.price or 0
                unit_purchase = item.purchase_price or 0
                qty = item.quantity
                
                total_price = unit_price * qty
                total_purchase = unit_purchase * qty
                item_profit = total_price - total_purchase
                
                items_data.append({
                    "product_name": item.product.name,
                    "quantity": qty,
                    "unit_price": unit_price,
                    "unit_purchase_price": unit_purchase,
                    "total_price": total_price,
                    "total_purchase_price": total_purchase,
                    "profit": item_profit
                })
            
            sales_data.append({
                "order_id": order.id,
                "date": order.created_at,
                "customer_name": f"{order.first_name} {order.last_name}",
                "status": order.status,
                "total_amount": order.total_amount,
                "items": items_data
            })

        return Response({
            "summary": {
                "total_orders": total_orders,
                "total_revenue": total_revenue,
                "total_profit": total_profit
            },
            "pagination": {
                "count": paginator.page.paginator.count,
                "next": paginator.get_next_link(),
                "previous": paginator.get_previous_link()
            },
            "sales_data": sales_data
        })
