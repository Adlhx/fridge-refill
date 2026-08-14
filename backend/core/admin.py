from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import *
admin.site.register(User,UserAdmin)
for m in [Store,UserStore,Fridge,Product,FridgeProduct,RefillSession,FridgeCheck,RefillRequirement,StockShortage]: admin.site.register(m)
