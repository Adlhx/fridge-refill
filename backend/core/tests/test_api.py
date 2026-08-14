from django.urls import reverse
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
