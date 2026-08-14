from rest_framework.permissions import BasePermission, SAFE_METHODS
from .models import User
class AssignedStorePermission(BasePermission):
    def has_object_permission(self,request,view,obj):
        if request.user.role==User.Role.ADMIN: return True
        store=getattr(obj,'store',obj if obj.__class__.__name__=='Store' else None)
        if hasattr(store,'store'): store=store.store
        return bool(store and request.user.stores.filter(pk=store.pk).exists())
class AdminWritePermission(BasePermission):
    def has_permission(self,request,view):
        if request.method in SAFE_METHODS: return True
        if getattr(view,'basename','') in ['stores','product']: return request.user.role==User.Role.ADMIN
        return request.user.role in [User.Role.ADMIN,User.Role.MANAGER]
