from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password

User = get_user_model()

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])

    class Meta:
        model = User
        fields = ('id', 'name', 'email', 'phone_number', 'password')

    def create(self, validated_data):
        user = User.objects.create(
            email=validated_data['email'],
            name=validated_data['name'],
            phone_number=validated_data.get('phone_number', '')
        )
        user.set_password(validated_data['password'])
        user.save()
        return user

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'name', 'email', 'phone_number', 'address', 'profile_pic')
        read_only_fields = ('id', 'email')
