from django.db import models


class ReferencedOnepayObject(models.Model):
    reference = models.CharField(max_length=190, db_index=True, unique=True)
    order = models.ForeignKey('pretixbase.Order')
    transaction = models.CharField(db_index=True, max_length=190, default="None")