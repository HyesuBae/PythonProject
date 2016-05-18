from django.db import models

# Create your models here.
class Expenditure(models.Model):
    user = models.ForeignKey('auth.User')
    date = models.DateField()
    contents = models.CharField(max_length=200)
    expenditure = models.IntegerField()
    expend_from = models.CharField(max_length=100)
    category = models.CharField(max_length=200)

    def set_expenditure(self):
        self.save()

class Income(models.Model):
    user = models.ForeignKey('auth.User')
    date = models.DateField()
    contents = models.CharField(max_length=200)
    income = models.IntegerField()
    income_to = models.CharField(max_length=100)
    category = models.CharField(max_length=200)

    def set_income(self):
        self.save()