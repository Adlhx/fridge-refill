from django.core.management.base import BaseCommand
from core.models import Store, Fridge, Product, FridgeProduct, User, UserStore

FRIDGES = {
1: ('Front Soft Drinks / Water', [
['Diet Coke Multipack','Coca-Cola Original Multipack','Red Bull Sugarfree Multipack','Red Bull Original Multipack','Monster Energy Multipack','Lucozade Sport Orange Multipack','Apple Juice 1L','Orange Juice 1L'],
['Lucozade Energy Original','Lucozade Energy Orange','Rubicon Spring Black Cherry Raspberry','Rubicon Spring Orange Mango','Robinsons Blackcurrant','Robinsons Orange','Royal Still Water','Schweppes Slimline Tonic Water','Schweppes Tonic Water','Fever-Tree Tonic Water'],
['Pepsi Max','Pepsi','Coca-Cola Zero Sugar','Diet Coke','Fanta Fruit Twist','Fanta Orange','7UP','Schweppes Lemonade'],['Still Water','Volvic Flavoured Water']]),
2: ('Sports / Hydration Drinks', [
['Lucozade Sport','Lucozade Sport Raspberry or dark variant','Lucozade Sport Orange','Lucozade Zero Pink Lemonade','Lucozade Zero Lemonade variant','Lucozade Grapefruit variant','Lucozade Energy Orange','Lucozade Energy Original'],
['Rubicon Raw variant 1','Rubicon Raw variant 2','Powerade Blue','Mountain Dew Original','Rubicon Black Cherry Raspberry','Rubicon Orange Mango','Juice Burst Orange','Juice Burst Apple','San Pellegrino Lemon','San Pellegrino Orange'],
['Celsius variant 1','Celsius variant 2','Celsius variant 3','Huel Ready-to-Drink variant','Functional Drink Can - Verify 1','Functional Drink Can - Verify 2','Trip Pink','Trip Yellow'],
['Vit-Hit variant 1','Vit-Hit variant 2','Vitamin Well Hydrate','Vitamin Well Recover','Vitamin Well Peach','Vitamin Well Raspberry','Volvic Touch of Fruit variant 1','Volvic Touch of Fruit variant 2','Volvic Touch of Fruit variant 3'],
['Highland Spring','Buxton','Volvic','San Pellegrino Sparkling Water']]),
3: ('Energy Drinks', [
['Red Bull Original','Red Bull Sugarfree','Red Bull Zero','Red Bull Large Can','Red Bull Multipack','Red Bull Edition - Verify'],
['Red Bull Edition 1 - Verify','Red Bull Edition 2 - Verify','Red Bull Edition 3 - Verify','Red Bull Edition 4 - Verify','Red Bull Edition 5 - Verify'],
['Red Bull Pink Edition','Red Bull Purple Edition - Verify','Red Bull Yellow Edition - Verify','Red Bull Blue Edition - Verify','Red Bull Peach Edition - Verify','Red Bull White Edition - Verify','Red Bull Cherry Edition - Verify','Red Bull Summer Edition Multipack - Verify'],
['Carabao variant 1','Carabao variant 2','Relentless variant 1','Relentless variant 2','C4 Energy variant 1','C4 Energy variant 2','NOCCO BCAA','NOCCO Focus','Reign Storm variant 1','Reign Storm variant 2'],
['Monster Energy Original','Monster Ultra White','Monster Mango Loco','Monster Pipeline Punch','Monster Pacific Punch','Monster Juiced variant','Monster Ultra variant','Monster variant - Verify']]),
4: ('Cola / Soft Drinks', [
['Pepsi Max','Pepsi','Pepsi Max Cherry','Pepsi Max Lime','Pepsi Flavoured Variant - Verify'],
['Coca-Cola Original Taste','Coca-Cola Zero Sugar','Diet Coke','Coca-Cola Cherry','Coca-Cola Multipack','Diet Coke Multipack'],
['Coca-Cola Cherry','Coca-Cola Zero Cherry','Coca-Cola Original Taste','Dr Pepper','Dr Pepper Zero','Dr Pepper Cherry or flavoured variant'],
['Tango Orange','7UP','7UP Zero','Fanta Fruit Twist','Fanta Orange','Fanta Lemon or light variant - Verify','IRN-BRU','IRN-BRU Xtra or Zero'],
['Ribena Blackcurrant','Ribena variant - Verify','Robinsons Ready-to-Drink variant 1','Robinsons Ready-to-Drink variant 2','Lipton Lemon Ice Tea','Lipton Peach Ice Tea','Lipton Tropical Ice Tea','Oasis variant 1','Oasis variant 2']]),
5: ('Coffee / Protein / Dairy', [
['Naked Blue Machine','Copella Cloudy Apple','Arctic Coffee Café Latte','Arctic Coffee variant - Verify',"Jimmy's Iced Coffee Original","Jimmy's Iced Coffee Caramel",'Starbucks Frappuccino','Starbucks Frappuccino variant - Verify','Starbucks Caramel Macchiato','Starbucks Caffè Latte','Starbucks Grande Caramel Macchiato','Starbucks Protein Drink variant - Verify'],
['Huel Strawberries & Cream','Huel Chocolate','Huel Banana','Huel Iced Coffee Caramel','Huel Vanilla','Huel Ready-to-Drink variant - Verify','YFood Classic Choco','YFood Smooth Vanilla','YFood Fresh Berry'],
['UFIT Protein Chocolate','UFIT Protein variant - Verify','Grenade Protein Shake Strawberry','Grenade Protein Shake Chocolate','Grenade Protein Shake variant - Verify','Barebells Strawberry','Barebells Chocolate','Barebells Vanilla','Shaken Udder Chocolate','Shaken Udder Vanillalicious','Shaken Udder Raspberry','Yazoo Chocolate','Yazoo Strawberry','Delamere Flavoured Milk variant'],
['Freshways Whole Milk','Freshways Semi-Skimmed Milk','Freshways Skimmed Milk','Elmlea','Onken Yogurt','Lurpak','Anchor Butter','Cathedral City Mature Cheddar','Arla Cravendale Whole Milk','Arla Cravendale Semi-Skimmed Milk']]),
6: ('Food To Go / Meal Deal', [['Starbucks Caffè Latte','Red Bull Original','Monster Ultra White','Monster Mango Loco','Monster Juiced Variant','Pepsi Max','Coca-Cola Original Taste','Diet Coke','Coca-Cola Zero Sugar','Fanta Orange','7UP','Oasis Summer Fruits','Still Water','San Pellegrino Sparkling Water']]),
}

def brand_for(name):
    brands=['Coca-Cola','Diet Coke','Red Bull','Monster','Lucozade','Rubicon','Robinsons','Schweppes','Pepsi','Fanta','Volvic','San Pellegrino','Huel','Starbucks',"Jimmy's",'YFood','Yazoo','Dr Pepper','IRN-BRU','Ribena','Lipton','Oasis','Barebells','Freshways','Arla']
    return next((b for b in brands if name.lower().startswith(b.lower())), '')

class Command(BaseCommand):
    help='Idempotently create Hornchurch Esso, its six fridges, and physical shelf layouts.'
    def handle(self,*args,**kwargs):
        store,_=Store.objects.update_or_create(store_code='HORNCHURCH_ESSO',defaults={'name':'Hornchurch Esso','active':True})
        for user in User.objects.filter(role__in=[User.Role.ADMIN,User.Role.MANAGER,User.Role.EMPLOYEE],is_active=True): UserStore.objects.get_or_create(user=user,store=store)
        product_ids=set(); assignment_count=0
        for number,(name,shelves) in FRIDGES.items():
            fridge,_=Fridge.objects.update_or_create(store=store,fridge_number=str(number),defaults={'name':name,'display_order':number,'active':True})
            seen=set(); overall=0
            for shelf_number,products in enumerate(shelves,1):
                for position,product_name in enumerate(products,1):
                    if product_name in seen: continue
                    seen.add(product_name); overall+=1
                    product,_=Product.objects.get_or_create(name=product_name,defaults={'brand':brand_for(product_name),'needs_verification':'verify' in product_name.lower(),'active':True})
                    if 'verify' in product_name.lower() and not product.needs_verification: product.needs_verification=True; product.save(update_fields=['needs_verification','updated_at'])
                    product_ids.add(product.id)
                    FridgeProduct.objects.update_or_create(fridge=fridge,product=product,defaults={'shelf_number':shelf_number,'position':position,'display_order':overall,'active':True})
                    assignment_count+=1
        self.stdout.write(self.style.SUCCESS(f'Hornchurch ready: 6 fridges, {len(product_ids)} unique products, {assignment_count} assignments.'))
