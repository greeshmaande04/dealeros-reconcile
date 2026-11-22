from django.db import models


class Location(models.Model):
    loc_id = models.CharField(max_length=20, unique=True)
    org_id = models.CharField(max_length=20)   # the ONLY source of tenant mapping
    name = models.CharField(max_length=100, blank=True, default="")


class SystemARecord(models.Model):
    record_id = models.CharField(max_length=30, unique=True)
    loc_id = models.CharField(max_length=20)    # plain text: bad/unknown locations must still import
    event_date = models.DateField(null=True)
    category_code = models.CharField(max_length=30, blank=True, default="")
    actor_id = models.CharField(max_length=30, null=True)   # blank in CSV -> null
    base_value = models.DecimalField(max_digits=14, decimal_places=2, null=True)
    adjustment = models.DecimalField(max_digits=14, decimal_places=2, null=True)
    total_value = models.DecimalField(max_digits=14, decimal_places=2, null=True)
    state = models.CharField(max_length=20, blank=True, default="")


class SystemBEntry(models.Model):
    entry_id = models.CharField(max_length=30, unique=True)
    record_ref_raw = models.CharField(max_length=50, blank=True, default="")  # original text
    record_ref = models.CharField(max_length=30, null=True)                   # cleaned; NOT unique, NOT a FK
    loc_id = models.CharField(max_length=20)
    recorded_on = models.DateField(null=True)
    value_raw = models.CharField(max_length=50, blank=True, default="")
    value = models.DecimalField(max_digits=14, decimal_places=2, null=True)   # null = unknown, never 0
    label = models.CharField(max_length=100, blank=True, default="")