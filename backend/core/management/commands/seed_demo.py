from django.core.management.base import BaseCommand
from core.models import *
class Command(BaseCommand):
    help='Create repeatable demo data'
    def handle(self,*args,**kwargs):
        admin,_=User.objects.get_or_create(username='admin',defaults={'email':'admin@fridgerefill.test','first_name':'Alex','role':'ADMIN','is_staff':True,'is_superuser':True}); admin.set_password('AdminDemo123!'); admin.save()
        employee,_=User.objects.get_or_create(username='employee',defaults={'email':'employee@fridgerefill.test','first_name':'Jamie','role':'EMPLOYEE'}); employee.set_password('EmployeeDemo123!'); employee.save()
        stores=[]
        for name,code,address in [('Romford Store','ROM','Romford, London'),('Ilford Store','ILF','Ilford, London')]:
            s,_=Store.objects.get_or_create(store_code=code,defaults={'name':name,'address':address}); UserStore.objects.get_or_create(user=employee,store=s); stores.append(s)
        products=[]
        for i,(name,brand,cat) in enumerate([('Starbucks Frappuccino','Starbucks','Coffee'),("Jimmy's Iced Coffee","Jimmy's",'Coffee'),('Huel Chocolate','Huel','Protein'),('Huel Vanilla','Huel','Protein'),('Yazoo Strawberry','Yazoo','Milk')],1):
            p,_=Product.objects.get_or_create(sku=f'DEMO-{i:03}',defaults={'name':name,'brand':brand,'category':cat,'barcode':f'50000000000{i}'}); products.append(p)
        for store in stores:
            for n,name in enumerate(['Coffee & Protein Drinks','Milk & Dairy'],1):
                f,_=Fridge.objects.get_or_create(store=store,fridge_number=str(n),defaults={'name':name,'location_description':'Front chilled aisle','display_order':n})
                chosen=products[:4] if n==1 else products[3:]
                for order,p in enumerate(chosen): FridgeProduct.objects.get_or_create(fridge=f,product=p,defaults={'display_order':order})
        self.stdout.write(self.style.SUCCESS('Demo ready: admin/AdminDemo123! and employee/EmployeeDemo123!'))
