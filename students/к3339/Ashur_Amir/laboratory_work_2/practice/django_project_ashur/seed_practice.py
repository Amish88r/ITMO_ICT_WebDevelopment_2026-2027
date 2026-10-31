# Тестовые данные для практик: python manage.py shell < seed_practice.py
from datetime import date
from project_first_app.models import CarOwner, Car, Ownership, DriverLicense
if not CarOwner.objects.filter(is_superuser=True).exists():
    CarOwner.objects.create_superuser('admin', '', 'admin')
people = [('ivanov','Иван','Иванов','4510 123456','Москва, ул. Ленина, 1','русский'),
          ('petrov','Пётр','Петров','4011 654321','СПб, Невский пр., 10','русский'),
          ('aliev','Руслан','Алиев','8212 111222','Казань, ул. Баумана, 5','татарин')]
owners=[]
for u,f,l,p,a,n in people:
    o,_=CarOwner.objects.get_or_create(username=u, defaults=dict(first_name=f,last_name=l,passport_number=p,home_address=a,nationality=n,birth_date=date(1990,1,1)))
    o.set_password('pass12345'); o.save(); owners.append(o)
cars=[Car.objects.get_or_create(state_number=s, defaults=dict(brand=b,model_name=m,color=c))[0] for s,b,m,c in
      [('А001АА77','Lada','Vesta','белый'),('В777ВВ78','Kia','Rio','синий'),('С123СС16','Toyota','Camry','чёрный'),('Е555ЕЕ99','BMW','X5',None)]]
Ownership.objects.all().delete()
# два владельца, у каждого >=3 автомобиля, периоды не пересекаются (машины переходили из рук в руки)
plan=[(0,0,date(2015,1,1),date(2017,1,1)),(0,1,date(2017,2,1),date(2019,1,1)),(0,2,date(2019,2,1),None),
      (1,1,date(2019,3,1),None),(1,0,date(2017,3,1),date(2018,1,1)),(1,3,date(2018,2,1),date(2019,2,1)),
      (2,3,date(2019,3,1),None)]
for oi,ci,s,e in plan: Ownership.objects.create(owner=owners[oi],car=cars[ci],start_date=s,end_date=e)
for i,o in enumerate(owners):
    DriverLicense.objects.get_or_create(owner=o, number=f'77AB{i}0000', defaults=dict(type='B', issue_date=date(2012,5,1)))
print('seeded')
