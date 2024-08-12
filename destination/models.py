from django.db import models


class City(models.Model):
    name = models.CharField(max_length=100, primary_key=True)
    adcode = models.CharField(max_length=6, unique=True)

    def __str__(self):
        return self.name


class School(models.Model):
    id = models.CharField(max_length=10, primary_key=True)
    name = models.CharField(max_length=100, unique=True)
    city = models.ForeignKey(City, on_delete=models.CASCADE)

    def __str__(self):
        return self.name
