from django.contrib import admin
from .models import Expenditure, Income

# Register your models here.
admin.site.register(Expenditure)
admin.site.register(Income)