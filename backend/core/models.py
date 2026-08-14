from django.contrib.auth.models import AbstractUser
from django.db import models

class TimeStamped(models.Model):
    created_at=models.DateTimeField(auto_now_add=True,db_index=True); updated_at=models.DateTimeField(auto_now=True)
    class Meta: abstract=True
class User(AbstractUser):
    class Role(models.TextChoices): ADMIN='ADMIN','Admin'; MANAGER='MANAGER','Manager'; EMPLOYEE='EMPLOYEE','Employee'
    role=models.CharField(max_length=10,choices=Role.choices,default=Role.EMPLOYEE); email=models.EmailField(unique=True)
class Store(TimeStamped):
    name=models.CharField(max_length=160); store_code=models.CharField(max_length=30,unique=True); address=models.TextField(blank=True); description=models.TextField(blank=True); active=models.BooleanField(default=True)
    employees=models.ManyToManyField(User,through='UserStore',related_name='stores')
    def __str__(self): return self.name
class UserStore(models.Model):
    user=models.ForeignKey(User,on_delete=models.CASCADE); store=models.ForeignKey(Store,on_delete=models.CASCADE)
    class Meta: constraints=[models.UniqueConstraint(fields=['user','store'],name='unique_user_store')]
class Fridge(TimeStamped):
    store=models.ForeignKey(Store,on_delete=models.PROTECT,related_name='fridges',db_index=True); name=models.CharField(max_length=160); fridge_number=models.CharField(max_length=30); location_description=models.TextField(blank=True); photo=models.ImageField(upload_to='fridges/%Y/%m/',blank=True); display_order=models.PositiveIntegerField(default=0); active=models.BooleanField(default=True)
    class Meta: ordering=['display_order','fridge_number']; constraints=[models.UniqueConstraint(fields=['store','fridge_number'],name='unique_store_fridge_number')]
class Product(TimeStamped):
    name=models.CharField(max_length=180); short_name=models.CharField(max_length=100,blank=True); brand=models.CharField(max_length=100,blank=True); barcode=models.CharField(max_length=64,blank=True,db_index=True); sku=models.CharField(max_length=64,blank=True,db_index=True); category=models.CharField(max_length=100,blank=True); product_photo=models.ImageField(upload_to='products/%Y/%m/',blank=True); pack_size=models.CharField(max_length=80,blank=True); active=models.BooleanField(default=True)
    class Meta: ordering=['name']; constraints=[models.UniqueConstraint(fields=['barcode'],condition=~models.Q(barcode=''),name='unique_nonempty_barcode'),models.UniqueConstraint(fields=['sku'],condition=~models.Q(sku=''),name='unique_nonempty_sku')]
class FridgeProduct(models.Model):
    fridge=models.ForeignKey(Fridge,on_delete=models.CASCADE,related_name='assignments'); product=models.ForeignKey(Product,on_delete=models.PROTECT,related_name='fridge_assignments'); display_order=models.PositiveIntegerField(default=0); shelf_number=models.CharField(max_length=30,blank=True); normal_capacity=models.PositiveIntegerField(null=True,blank=True); minimum_display_quantity=models.PositiveIntegerField(null=True,blank=True); active=models.BooleanField(default=True)
    class Meta: ordering=['display_order','id']; constraints=[models.UniqueConstraint(fields=['fridge','product'],name='unique_fridge_product')]
class RefillSession(TimeStamped):
    class Status(models.TextChoices): IN_PROGRESS='IN_PROGRESS','In progress'; PICKING='PICKING','Picking'; REFILLING='REFILLING','Refilling'; COMPLETED='COMPLETED','Completed'; CANCELLED='CANCELLED','Cancelled'
    store=models.ForeignKey(Store,on_delete=models.PROTECT,related_name='sessions',db_index=True); employee=models.ForeignKey(User,on_delete=models.PROTECT,related_name='refill_sessions',db_index=True); started_at=models.DateTimeField(auto_now_add=True); completed_at=models.DateTimeField(null=True,blank=True); status=models.CharField(max_length=20,choices=Status.choices,default=Status.IN_PROGRESS,db_index=True)
class FridgeCheck(models.Model):
    refill_session=models.ForeignKey(RefillSession,on_delete=models.CASCADE,related_name='fridge_checks'); fridge=models.ForeignKey(Fridge,on_delete=models.PROTECT); checked_by=models.ForeignKey(User,on_delete=models.PROTECT); checked_at=models.DateTimeField(auto_now=True); completed=models.BooleanField(default=False); refilled=models.BooleanField(default=False)
    class Meta: constraints=[models.UniqueConstraint(fields=['refill_session','fridge'],name='unique_session_fridge_check')]
class RefillRequirement(TimeStamped):
    class Status(models.TextChoices): NEEDED='NEEDED','Needed'; PICKED='PICKED','Picked'; SHORT='SHORT','Short'; REFILLED='REFILLED','Refilled'
    refill_session=models.ForeignKey(RefillSession,on_delete=models.CASCADE,related_name='requirements',db_index=True); fridge=models.ForeignKey(Fridge,on_delete=models.PROTECT,db_index=True); product=models.ForeignKey(Product,on_delete=models.PROTECT,db_index=True); required_quantity=models.PositiveIntegerField(default=0); picked_quantity=models.PositiveIntegerField(default=0); refilled_quantity=models.PositiveIntegerField(default=0); status=models.CharField(max_length=12,choices=Status.choices,default=Status.NEEDED); version=models.PositiveIntegerField(default=1)
    class Meta: constraints=[models.UniqueConstraint(fields=['refill_session','fridge','product'],name='unique_session_fridge_product')]
class StockShortage(TimeStamped):
    refill_session=models.ForeignKey(RefillSession,on_delete=models.CASCADE,related_name='shortages',db_index=True); product=models.ForeignKey(Product,on_delete=models.PROTECT,db_index=True); required_quantity=models.PositiveIntegerField(); found_quantity=models.PositiveIntegerField(); short_quantity=models.PositiveIntegerField(); reported_by=models.ForeignKey(User,on_delete=models.PROTECT); note=models.TextField(blank=True)
    class Meta: constraints=[models.UniqueConstraint(fields=['refill_session','product'],name='unique_session_product_shortage')]
