from django.db.models import Sum
from rest_framework import serializers
from .models import *

class UserSerializer(serializers.ModelSerializer):
    class Meta: model=User; fields=['id','username','email','first_name','last_name','role']
class StoreSerializer(serializers.ModelSerializer):
    fridge_count=serializers.IntegerField(read_only=True)
    class Meta: model=Store; fields='__all__'; read_only_fields=['employees']
class ProductSerializer(serializers.ModelSerializer):
    class Meta: model=Product; fields='__all__'
    def validate_product_photo(self,v):
        if v and (v.size>5*1024*1024 or getattr(v,'content_type','').split('/')[0]!='image'): raise serializers.ValidationError('Upload a valid image no larger than 5 MB.')
        return v
class FridgeProductSerializer(serializers.ModelSerializer):
    product_detail=ProductSerializer(source='product',read_only=True)
    class Meta: model=FridgeProduct; fields='__all__'
class FridgeSerializer(serializers.ModelSerializer):
    product_count=serializers.IntegerField(read_only=True); assignments=FridgeProductSerializer(many=True,read_only=True)
    class Meta: model=Fridge; fields='__all__'
class FridgeListSerializer(serializers.ModelSerializer):
    product_count=serializers.IntegerField(read_only=True)
    class Meta: model=Fridge; fields=['id','store','name','fridge_number','location_description','photo','display_order','active','product_count']
class RequirementSerializer(serializers.ModelSerializer):
    product_detail=ProductSerializer(source='product',read_only=True); fridge_name=serializers.CharField(source='fridge.name',read_only=True); shelf_number=serializers.IntegerField(read_only=True); position=serializers.IntegerField(read_only=True)
    class Meta: model=RefillRequirement; fields='__all__'; read_only_fields=['status']
class FridgeCheckSerializer(serializers.ModelSerializer):
    class Meta: model=FridgeCheck; fields='__all__'; read_only_fields=['checked_by']
class ShortageSerializer(serializers.ModelSerializer):
    product_detail=ProductSerializer(source='product',read_only=True)
    class Meta: model=StockShortage; fields='__all__'; read_only_fields=['reported_by','short_quantity']
class SessionSerializer(serializers.ModelSerializer):
    store_detail=StoreSerializer(source='store',read_only=True); employee_detail=UserSerializer(source='employee',read_only=True); checked_count=serializers.IntegerField(read_only=True); total_units=serializers.IntegerField(read_only=True)
    class Meta: model=RefillSession; fields='__all__'; read_only_fields=['employee','completed_at','status']
