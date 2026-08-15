from django.urls import reverse
from django.core.management import call_command
from rest_framework.test import APITestCase
from core.models import *
class FlowTests(APITestCase):
    def setUp(self):
        self.u=User.objects.create_user('worker','w@test.com','pass',role='EMPLOYEE'); self.s=Store.objects.create(name='Romford',store_code='ROM'); UserStore.objects.create(user=self.u,store=self.s); self.other=Store.objects.create(name='Ilford',store_code='ILF'); self.f1=Fridge.objects.create(store=self.s,name='One',fridge_number='1'); self.f2=Fridge.objects.create(store=self.s,name='Two',fridge_number='2'); self.p=Product.objects.create(name='Coca-Cola',sku='COKE'); self.session=RefillSession.objects.create(store=self.s,employee=self.u); self.client.force_authenticate(self.u)
    def test_store_separation(self):
        ids=[x['id'] for x in self.client.get('/api/stores/').json()['results']]; self.assertEqual(ids,[self.s.id])
    def test_pick_list_aggregates_and_preserves_breakdown(self):
        RefillRequirement.objects.create(refill_session=self.session,fridge=self.f1,product=self.p,required_quantity=4); RefillRequirement.objects.create(refill_session=self.session,fridge=self.f2,product=self.p,required_quantity=6)
        row=self.client.get(f'/api/refill-sessions/{self.session.id}/pick-list/').json()[0]; self.assertEqual(row['total_required'],10); self.assertEqual(sorted(x['required_quantity'] for x in row['breakdown']),[4,6])
    def test_stale_quantity_update_is_rejected(self):
        r=RefillRequirement.objects.create(refill_session=self.session,fridge=self.f1,product=self.p,required_quantity=4)
        self.client.patch(f'/api/requirements/{r.id}/',{'required_quantity':5,'version':1},format='json'); response=self.client.patch(f'/api/requirements/{r.id}/',{'required_quantity':9,'version':1},format='json'); self.assertEqual(response.status_code,409)
    def test_fridge_products_are_in_physical_order(self):
        a=Product.objects.create(name='Product A',sku='A'); b=Product.objects.create(name='Product B',sku='B'); c=Product.objects.create(name='Product C',sku='C')
        FridgeProduct.objects.create(fridge=self.f1,product=b,shelf_number=2,position=1)
        FridgeProduct.objects.create(fridge=self.f1,product=a,shelf_number=1,position=2)
        FridgeProduct.objects.create(fridge=self.f1,product=c,shelf_number=1,position=1)
        names=[x['product_detail']['name'] for x in self.client.get(f'/api/fridges/{self.f1.id}/products/').json()]
        self.assertEqual(names,['Product C','Product A','Product B'])
    def test_refill_requirements_are_in_physical_order(self):
        a=Product.objects.create(name='Product A',sku='RA'); b=Product.objects.create(name='Product B',sku='RB'); c=Product.objects.create(name='Product C',sku='RC')
        for product,shelf,position in [(b,2,1),(a,1,2),(c,1,1)]:
            FridgeProduct.objects.create(fridge=self.f1,product=product,shelf_number=shelf,position=position)
            RefillRequirement.objects.create(refill_session=self.session,fridge=self.f1,product=product,required_quantity=1)
        rows=self.client.get(f'/api/requirements/?refill_session={self.session.id}').json()['results']
        self.assertEqual([x['product_detail']['name'] for x in rows],['Product C','Product A','Product B'])

class HornchurchSeedTests(APITestCase):
    def test_seed_is_idempotent_and_store_isolated(self):
        call_command('seed_hornchurch'); first=(Store.objects.count(),Fridge.objects.count(),Product.objects.count(),FridgeProduct.objects.count())
        call_command('seed_hornchurch'); second=(Store.objects.count(),Fridge.objects.count(),Product.objects.count(),FridgeProduct.objects.count())
        self.assertEqual(first,second)
        hornchurch=Store.objects.get(store_code='HORNCHURCH_ESSO'); self.assertEqual(hornchurch.fridges.count(),6)
        other=Store.objects.create(name='Other',store_code='OTHER'); self.assertFalse(FridgeProduct.objects.filter(fridge__store=other).exists())
