from rest_framework import serializers
from .models import Category, Product, Review

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug']

class ReviewSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = Review
        fields = ['id', 'user', 'user_name', 'product', 'rating', 'comment', 'created_at']
        read_only_fields = ['user']

class ProductSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(), source='category', required=False, allow_null=True
    )
    reviews = ReviewSerializer(many=True, read_only=True)
    average_rating = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            'id', 'category', 'category_id', 'name', 'slug', 'description',
            'purchase_price', 'selling_price', 'offer_price', 'price',
            'image_1', 'image_2', 'image_3', 'stock', 'sold_quantity',
            'expire_date', 'created_at', 'updated_at', 'reviews', 'average_rating'
        ]
        read_only_fields = ['price']

    def get_average_rating(self, obj):
        reviews = obj.reviews.all()
        if reviews.exists():
            return sum([r.rating for r in reviews]) / reviews.count()
        return 0
