from django.urls import include,path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView,TokenRefreshView
from .views import *
r=DefaultRouter(); r.register('me',MeViewSet,basename='me'); r.register('stores',StoreViewSet,basename='stores'); r.register('fridges',FridgeViewSet,basename='fridges'); r.register('products',ProductViewSet); r.register('fridge-products',FridgeProductViewSet,basename='fridge-products'); r.register('refill-sessions',SessionViewSet,basename='sessions'); r.register('fridge-checks',CheckViewSet,basename='checks'); r.register('requirements',RequirementViewSet,basename='requirements'); r.register('shortages',ShortageViewSet,basename='shortages')
urlpatterns=[path('auth/token/',TokenObtainPairView.as_view()),path('auth/refresh/',TokenRefreshView.as_view()),path('',include(r.urls)),path('history/',SessionViewSet.as_view({'get':'list'}))]
