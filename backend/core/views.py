from django.db import transaction
from django.db.models import Count, Sum, Prefetch, OuterRef, Subquery
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from .models import *
from .serializers import *
from .permissions import *
from .planogram import PlanogramError, parse_planogram

def allowed_stores(user): return Store.objects.all() if user.role==User.Role.ADMIN else user.stores.all()
class MeViewSet(viewsets.ViewSet):
    def list(self,request): return Response(UserSerializer(request.user).data)
class StoreViewSet(viewsets.ModelViewSet):
    serializer_class=StoreSerializer; permission_classes=[AdminWritePermission]
    def get_queryset(self):
        q=allowed_stores(self.request.user)
        if not (self.request.user.role==User.Role.ADMIN and self.request.query_params.get('all')=='true'): q=q.filter(active=True)
        return q.annotate(fridge_count=Count('fridges',filter=models.Q(fridges__active=True))).order_by('name')
    @action(detail=True)
    def fridges(self,request,pk=None):
        store=self.get_object(); qs=store.fridges.filter(active=True).annotate(product_count=Count('assignments',filter=models.Q(assignments__active=True)))
        return Response(FridgeSerializer(qs,many=True,context={'request':request}).data)
class ProductViewSet(viewsets.ModelViewSet):
    queryset=Product.objects.all(); serializer_class=ProductSerializer; permission_classes=[AdminWritePermission]; filterset_fields=['barcode','sku']
    def get_queryset(self):
        q=super().get_queryset(); s=self.request.query_params.get('search'); verification=self.request.query_params.get('verification')
        if s: q=q.filter(models.Q(name__icontains=s)|models.Q(barcode__icontains=s)|models.Q(sku__icontains=s))
        if verification=='needs': q=q.filter(needs_verification=True)
        if verification=='verified': q=q.filter(needs_verification=False)
        return q
class FridgeViewSet(viewsets.ModelViewSet):
    serializer_class=FridgeSerializer; permission_classes=[AdminWritePermission,AssignedStorePermission]
    def get_queryset(self): return Fridge.objects.filter(store__in=allowed_stores(self.request.user)).select_related('store').prefetch_related('assignments__product').annotate(product_count=Count('assignments',filter=models.Q(assignments__active=True)))
    def perform_create(self,s):
        if not allowed_stores(self.request.user).filter(pk=s.validated_data['store'].pk).exists(): raise PermissionDenied()
        s.save()
    @action(detail=True)
    def products(self,request,pk=None): return Response(FridgeProductSerializer(self.get_object().assignments.filter(active=True).select_related('product'),many=True,context={'request':request}).data)
    @action(detail=True,methods=['post'],url_path='import-layout-preview')
    def import_layout_preview(self,request,pk=None):
        self.get_object()
        upload=request.FILES.get('file')
        if not upload: raise ValidationError({'file':'Choose a PDF to import.'})
        if upload.size>15*1024*1024: raise ValidationError({'file':'The PDF must be 15 MB or smaller.'})
        if not upload.name.lower().endswith('.pdf'): raise ValidationError({'file':'Only PDF files are supported.'})
        try: rows=parse_planogram(upload)
        except PlanogramError as exc: raise ValidationError({'file':str(exc)})
        barcodes=[row['barcode'] for row in rows if row['barcode']]; skus=[row['londis_code'] for row in rows if row['londis_code']]
        products=Product.objects.filter(models.Q(barcode__in=barcodes)|models.Q(sku__in=skus))
        by_barcode={p.barcode:p for p in products if p.barcode}; by_sku={p.sku:p for p in products if p.sku}
        matched=0
        for row in rows:
            product=by_barcode.get(row['barcode']) or by_sku.get(row['londis_code'])
            row['product_id']=product.id if product else None; row['match']='existing' if product else 'new'
            matched+=bool(product)
        return Response({'rows':rows,'summary':{'products':len(rows),'shelves':len({r['shelf_number'] for r in rows}),'matched':matched,'new':len(rows)-matched}})
    @action(detail=True,methods=['post'],url_path='apply-layout-import')
    def apply_layout_import(self,request,pk=None):
        fridge=self.get_object(); rows=request.data.get('rows') or []
        if not rows: raise ValidationError({'rows':'Preview a PDF before applying the layout.'})
        seen=set()
        with transaction.atomic():
            fridge.assignments.select_for_update().update(active=False)
            for index,row in enumerate(sorted(rows,key=lambda r:(int(r['shelf_number']),int(r['position'])))):
                product=Product.objects.filter(pk=row.get('product_id')).first() if row.get('product_id') else None
                if not product and row.get('barcode'): product=Product.objects.filter(barcode=row['barcode']).first()
                if not product and row.get('londis_code'): product=Product.objects.filter(sku=row['londis_code']).first()
                if not product:
                    product=Product.objects.create(name=row['name'],barcode=row.get('barcode',''),sku=row.get('londis_code',''),size=row.get('pack_size',''),pack_size=row.get('pack_size',''),category='Alcohol',needs_verification=True)
                if product.id in seen: raise ValidationError({'rows':f"{product.name} appears more than once; duplicate fridge assignments are not supported."})
                seen.add(product.id)
                notes=f"Planogram {row.get('m_code','')} · {row.get('facings',1)} facing(s)".strip()
                FridgeProduct.objects.update_or_create(fridge=fridge,product=product,defaults={'shelf_number':max(1,int(row['shelf_number'])),'position':max(1,int(row['position'])),'display_order':index,'notes':notes,'active':True})
        return Response({'detail':'Layout imported','products':len(seen),'shelves':len({int(r['shelf_number']) for r in rows})})
class FridgeProductViewSet(viewsets.ModelViewSet):
    serializer_class=FridgeProductSerializer; permission_classes=[AdminWritePermission]
    def get_queryset(self): return FridgeProduct.objects.filter(fridge__store__in=allowed_stores(self.request.user)).select_related('fridge','product')
    def perform_create(self,s):
        if not allowed_stores(self.request.user).filter(pk=s.validated_data['fridge'].store_id).exists(): raise PermissionDenied()
        s.save()
    @action(detail=False,methods=['post'],url_path='save-layout')
    def save_layout(self,request):
        rows=request.data.get('assignments',[])
        with transaction.atomic():
            allowed={x.id:x for x in self.get_queryset().select_for_update().filter(id__in=[r.get('id') for r in rows])}
            if len(allowed)!=len(rows): raise PermissionDenied('One or more assignments are outside your stores.')
            for index,row in enumerate(rows):
                item=allowed[row['id']]; item.shelf_number=max(1,int(row['shelf_number'])); item.position=max(1,int(row['position'])); item.display_order=index; item.save(update_fields=['shelf_number','position','display_order','updated_at'])
        return Response(FridgeProductSerializer(sorted(allowed.values(),key=lambda x:(x.shelf_number,x.position)),many=True,context={'request':request}).data)
    @action(detail=False,methods=['post'],url_path='bulk-add')
    def bulk_add(self,request):
        fridge=Fridge.objects.get(pk=request.data.get('fridge'))
        if not allowed_stores(request.user).filter(pk=fridge.store_id).exists(): raise PermissionDenied()
        shelf=max(1,int(request.data.get('shelf_number',1))); existing=fridge.assignments.filter(shelf_number=shelf).aggregate(v=models.Max('position'))['v'] or 0; made=[]
        for offset,product_id in enumerate(request.data.get('products',[]),1):
            obj,created=FridgeProduct.objects.get_or_create(fridge=fridge,product_id=product_id,defaults={'shelf_number':shelf,'position':existing+offset,'display_order':existing+offset})
            if created: made.append(obj)
        return Response(FridgeProductSerializer(made,many=True,context={'request':request}).data,status=201)
class SessionViewSet(viewsets.ModelViewSet):
    serializer_class=SessionSerializer
    def get_queryset(self):
        q=RefillSession.objects.filter(store__in=allowed_stores(self.request.user)).select_related('store','employee').annotate(checked_count=Count('fridge_checks',filter=models.Q(fridge_checks__completed=True)),total_units=Sum('requirements__required_quantity'))
        q=q if self.request.user.role!=User.Role.EMPLOYEE else q.filter(employee=self.request.user)
        store=self.request.query_params.get('store'); return q.filter(store_id=store) if store else q
    def perform_create(self,s):
        store=s.validated_data['store']
        if not allowed_stores(self.request.user).filter(pk=store.pk).exists(): raise PermissionDenied()
        active=self.get_queryset().filter(store=store,employee=self.request.user,status__in=[RefillSession.Status.IN_PROGRESS,RefillSession.Status.PICKING,RefillSession.Status.REFILLING]).first()
        if active: raise ValidationError({'existing_session':active.id})
        s.save(employee=self.request.user)
    @action(detail=True,methods=['post'])
    def generate_pick_list(self,request,pk=None):
        obj=self.get_object(); obj.status=RefillSession.Status.PICKING; obj.save(update_fields=['status','updated_at']); return self.pick_list(request,pk)
    @action(detail=True,url_path='pick-list')
    def pick_list(self,request,pk=None):
        rows=self.get_object().requirements.filter(required_quantity__gt=0).values('product','product__name','product__barcode','product__sku','product__product_photo').annotate(total_required=Sum('required_quantity'),total_picked=Sum('picked_quantity')).order_by('product__name')
        out=[]
        for row in rows:
            row['breakdown']=list(self.get_object().requirements.filter(product_id=row['product'],required_quantity__gt=0).values('fridge','fridge__name','required_quantity','picked_quantity'))
            out.append(row)
        return Response(out)
    @action(detail=True,methods=['post'])
    def start_refilling(self,request,pk=None):
        obj=self.get_object(); obj.status=RefillSession.Status.REFILLING; obj.save(update_fields=['status','updated_at']); return Response(SessionSerializer(obj,context={'request':request}).data)
    @action(detail=True,methods=['post'])
    def complete(self,request,pk=None):
        obj=self.get_object(); obj.status=RefillSession.Status.COMPLETED; obj.completed_at=timezone.now(); obj.save(update_fields=['status','completed_at','updated_at']); return Response(SessionSerializer(obj,context={'request':request}).data)
class RequirementViewSet(viewsets.ModelViewSet):
    serializer_class=RequirementSerializer
    def get_queryset(self):
        layout=FridgeProduct.objects.filter(fridge_id=OuterRef('fridge_id'),product_id=OuterRef('product_id'),active=True)
        q=RefillRequirement.objects.filter(refill_session__store__in=allowed_stores(self.request.user)).select_related('product','fridge','refill_session').annotate(shelf_number=Subquery(layout.values('shelf_number')[:1]),position=Subquery(layout.values('position')[:1])).order_by('fridge__display_order','shelf_number','position','id')
        for key in ['refill_session','fridge','product']:
            if self.request.query_params.get(key): q=q.filter(**{f'{key}_id':self.request.query_params[key]})
        return q
    def perform_create(self,s):
        session=s.validated_data.get('refill_session') or RefillSession.objects.get(pk=self.request.data['refill_session'])
        s.save(refill_session=session)
    def update(self,request,*args,**kwargs):
        with transaction.atomic():
            obj=RefillRequirement.objects.select_for_update().get(pk=kwargs['pk'])
            supplied=request.data.get('version')
            if supplied is not None and int(supplied)!=obj.version: return Response({'detail':'Stale update','current':RequirementSerializer(obj).data},status=409)
            request.data['version']=obj.version+1
            return super().update(request,*args,**kwargs)
class CheckViewSet(viewsets.ModelViewSet):
    serializer_class=FridgeCheckSerializer
    def get_queryset(self):
        q=FridgeCheck.objects.filter(refill_session__store__in=allowed_stores(self.request.user)).select_related('fridge','refill_session')
        for key in ['refill_session','fridge']:
            if self.request.query_params.get(key): q=q.filter(**{f'{key}_id':self.request.query_params[key]})
        return q
    def perform_create(self,s): s.save(checked_by=self.request.user)
class ShortageViewSet(viewsets.ModelViewSet):
    serializer_class=ShortageSerializer
    def get_queryset(self): return StockShortage.objects.filter(refill_session__store__in=allowed_stores(self.request.user)).select_related('product','refill_session')
    def perform_create(self,s):
        required=s.validated_data['required_quantity']; found=s.validated_data['found_quantity']; s.save(reported_by=self.request.user,short_quantity=max(0,required-found))
