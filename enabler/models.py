from django.db import models


class Probe(models.Model):
    class Meta:
        unique_together = [["group", "node"]]

    NOTICE_LEVELS = ["alert", "warn", "notice"]

    group = models.CharField(max_length=200)
    node = models.CharField(max_length=200)

    probe_enabled = models.BooleanField()
    pager_enabled = models.BooleanField()
    notice_level = models.CharField(max_length=50)


class Check(models.Model):
    class Meta:
        unique_together = [["probe", "name"]]

    probe = models.ForeignKey(Probe, on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    time_switch = models.CharField(max_length=200)
