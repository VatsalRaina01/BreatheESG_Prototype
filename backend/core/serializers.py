from rest_framework import serializers
from .models import Tenant, User


class UserSerializer(serializers.ModelSerializer):
    tenant_name = serializers.CharField(source='tenant.name', read_only=True, default='')

    class Meta:
        model = User
        fields = ['id', 'email', 'username', 'role', 'tenant_name']
        read_only_fields = fields


class TenantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tenant
        fields = ['id', 'name', 'slug', 'is_active', 'created_at']
        read_only_fields = ['id', 'created_at']
