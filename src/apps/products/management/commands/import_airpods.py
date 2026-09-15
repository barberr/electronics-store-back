"""Import Apple AirPods catalog. Run: python manage.py import_airpods"""
from django.core.management.base import BaseCommand
from django.db import transaction
from ...models import Brand, Category, Attribute, Product, ProductVariant


def ensure_attribute(**d):
    slug, name = d.pop('slug'), d.pop('name')
    a = Attribute.objects.filter(slug=slug).first() or Attribute.objects.filter(name=name).first()
    if a:
        if d.get('type') == 'enum':
            merged = list(dict.fromkeys([*(a.values or []), *(d.get('values') or [])]))
            if a.values != merged:
                a.values = merged; a.save(update_fields=['values'])
        return a
    return Attribute.objects.create(slug=slug, name=name, **d)


def yn(v): return 'Да' if v else 'Нет'

ATTRS = [
 dict(slug='release-year',name='Год выпуска',applies_to='product',type='number',is_required=False,sort_order=10,unit='',group_name='Основные характеристики',values=None),
 dict(slug='processor',name='Процессор',applies_to='product',type='string',is_required=False,sort_order=20,unit='',group_name='Производительность',values=None),
 dict(slug='headphone-type',name='Тип наушников',applies_to='product',type='string',is_required=False,sort_order=30,unit='',group_name='Основные характеристики',values=None),
 dict(slug='noise-cancellation',name='Активное шумоподавление',applies_to='product',type='enum',is_required=False,sort_order=40,unit='',group_name='Звук',values=['Да','Нет']),
 dict(slug='adaptive-audio',name='Адаптивное аудио',applies_to='product',type='enum',is_required=False,sort_order=50,unit='',group_name='Звук',values=['Да','Нет']),
 dict(slug='transparency-mode',name='Режим прозрачности',applies_to='product',type='enum',is_required=False,sort_order=60,unit='',group_name='Звук',values=['Да','Нет']),
 dict(slug='spatial-audio',name='Пространственное аудио',applies_to='product',type='enum',is_required=False,sort_order=70,unit='',group_name='Звук',values=['Да','Нет']),
 dict(slug='battery-life',name='Время работы',applies_to='product',type='number',is_required=False,sort_order=80,unit='ч',group_name='Автономность',values=None),
 dict(slug='charging-case',name='Зарядный футляр',applies_to='product',type='string',is_required=False,sort_order=90,unit='',group_name='Питание',values=None),
 dict(slug='wireless-charging',name='Беспроводная зарядка',applies_to='product',type='enum',is_required=False,sort_order=110,unit='',group_name='Питание',values=['Да','Нет']),
 dict(slug='heart-rate',name='Измерение пульса',applies_to='product',type='enum',is_required=False,sort_order=130,unit='',group_name='Возможности',values=['Да','Нет']),
 dict(slug='hearing-health',name='Функции здоровья слуха',applies_to='product',type='enum',is_required=False,sort_order=140,unit='',group_name='Возможности',values=['Да','Нет']),
 dict(slug='model-numbers',name='Номера моделей',applies_to='product',type='string',is_required=False,sort_order=160,unit='',group_name='Основные характеристики',values=None),
]

# name, slug, year, chip, type, ANC, adaptive, transparency, spatial, battery, case, connector, wireless, health, models, variants
DATA = [
 ('AirPods 5','airpods-5',2026,'H2','Вкладыши',1,1,1,1,5,'Зарядный футляр USB-C','USB-C',0,0,None,[{'case-type':'USB-C'}]),
 ('AirPods 5 с беспроводным зарядным футляром','airpods-5-wireless-charging-case',2026,'H2','Вкладыши',1,1,1,1,5,'Беспроводной зарядный футляр USB-C','USB-C',1,0,None,[{'case-type':'Беспроводной USB-C'}]),
 ('AirPods Pro 3','airpods-pro-3',2025,'H2','Внутриканальные',1,1,1,1,8,'MagSafe Charging Case (USB-C)','USB-C',1,1,'A3063, A3064, A3065',[{'color':'White'}]),
 ('AirPods Max 2','airpods-max-2',2026,'H2','Полноразмерные',1,1,1,1,None,'Smart Case','USB-C',0,0,'A3454',[{'color':c} for c in ['Midnight','Starlight','Blue','Purple','Orange']]),
 ('AirPods 4','airpods-4',2024,'H2','Вкладыши',0,0,0,1,None,'Зарядный футляр USB-C','USB-C',0,0,'A3053, A3050, A3054',[{'case-type':'USB-C'}]),
 ('AirPods 4 с активным шумоподавлением','airpods-4-anc',2024,'H2','Вкладыши',1,1,1,1,None,'Беспроводной зарядный футляр USB-C','USB-C',1,0,'A3056, A3055, A3057',[{'case-type':'USB-C ANC'}]),
 ('AirPods Pro 2 (USB-C)','airpods-pro-2-usb-c',2023,'H2','Внутриканальные',1,1,1,1,None,'MagSafe Charging Case (USB-C)','USB-C',1,1,'A3047, A3048, A3049',[{'color':'White'}]),
 ('AirPods Pro 2 (Lightning)','airpods-pro-2-lightning',2022,'H2','Внутриканальные',1,1,1,1,None,'MagSafe Charging Case (Lightning)','Lightning',1,0,'A2931, A2699, A2698',[{'color':'White'}]),
 ('AirPods 3','airpods-3',2021,'H1','Вкладыши',0,0,0,1,None,'Lightning / MagSafe','Lightning',1,0,'A2565, A2564',[{'case-type':'Lightning'},{'case-type':'MagSafe'}]),
 ('AirPods Max 1 (USB-C)','airpods-max-1-usb-c',2024,'H1','Полноразмерные',1,0,1,1,None,'Smart Case','USB-C',0,0,'A3184',[{'color':c} for c in ['Midnight','Starlight','Blue','Purple','Orange']]),
 ('AirPods Max 1 (Lightning)','airpods-max-1-lightning',2020,'H1','Полноразмерные',1,0,1,1,None,'Smart Case','Lightning',0,0,'A2096',[{'color':c} for c in ['Space Gray','Silver','Sky Blue','Green','Pink']]),
 ('AirPods Pro 1','airpods-pro-1',2019,'H1','Внутриканальные',1,0,1,1,None,'Wireless Charging Case','Lightning',1,0,'A2084, A2083',[{'color':'White'}]),
 ('AirPods 2','airpods-2',2019,'H1','Вкладыши',0,0,0,0,None,'Charging Case / Wireless Charging Case','Lightning',1,0,'A2032, A2031',[{'case-type':'Charging Case'},{'case-type':'Wireless Charging Case'}]),
 ('AirPods 1','airpods-1',2016,'W1','Вкладыши',0,0,0,0,None,'Charging Case','Lightning',0,0,'A1523, A1722',[{'case-type':'Charging Case'}]),
]

class Command(BaseCommand):
    help = 'Импорт Apple AirPods всех основных поколений'

    @transaction.atomic
    def handle(self,*args,**opts):
        brand,_=Brand.objects.update_or_create(slug='apple',defaults={'name':'Apple'})
        cat,_=Category.objects.update_or_create(slug='airpods',defaults={'name':'AirPods','description':'Наушники Apple AirPods'})
        for d in ATTRS: cat.attributes.add(ensure_attribute(**d))
        # Existing connector is reused.
        connector=ensure_attribute(slug='connector',name='Разъём',applies_to='product',type='string',is_required=False,sort_order=100,unit='',group_name='Питание',values=None); cat.attributes.add(connector)
        color=ensure_attribute(slug='color',name='Цвет',applies_to='variant',type='enum',is_required=True,sort_order=20,unit='',group_name='Внешний вид',values=['White','Midnight','Starlight','Blue','Purple','Orange','Space Gray','Silver','Sky Blue','Green','Pink']); cat.attributes.add(color)
        case=ensure_attribute(slug='case-type',name='Тип зарядного футляра',applies_to='variant',type='enum',is_required=False,sort_order=30,unit='',group_name='Комплектация',values=['USB-C','Беспроводной USB-C','USB-C ANC','Lightning','MagSafe','Charging Case','Wireless Charging Case']); cat.attributes.add(case)
        cp=up=cv=ev=0
        for name,slug,year,chip,typ,anc,adaptive,transparency,spatial,battery,charging,conn,wireless,health,models,variants in DATA:
            specs={'release-year':year,'processor':chip,'headphone-type':typ,'noise-cancellation':yn(anc),'adaptive-audio':yn(adaptive),'transparency-mode':yn(transparency),'spatial-audio':yn(spatial),'charging-case':charging,'connector':conn,'wireless-charging':yn(wireless),'hearing-health':yn(health)}
            if battery is not None: specs['battery-life']=battery
            if models: specs['model-numbers']=models
            p,created=Product.objects.update_or_create(slug=slug,defaults={'name':name,'brand':brand,'category':cat,'short_description':name,'specifications':specs,'is_active':True})
            cp += int(created); up += int(not created)
            for raw in variants:
                attrs={(color.slug if k=='color' else case.slug if k=='case-type' else k):v for k,v in raw.items()}
                if ProductVariant.objects.filter(product=p,attributes=attrs).exists(): ev+=1; continue
                ProductVariant.objects.create(product=p,attributes=attrs,sku=None,price=0,old_price=None,stock=0,is_active=False); cv+=1
        self.stdout.write(self.style.SUCCESS(f'AirPods импортированы. Товары: +{cp}, обновлено {up}; варианты: +{cv}, существовало {ev}.'))
