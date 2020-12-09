import string
import random
from enabler.models import Probe, Check

Probe.objects.all().delete()

random.seed(2)

CHECKS = [
    "cert_db",
    "cert_mails",
    "files_backup_remote",
    "db1_filer",
    "files_backup_local",
    "savemylife_app_url",
    "ck_test_clevehr",
    "ck_monitor_kheops",
    "ck_www_kheops",
    "ck_jira",
    "ck_imed2_synlab",
    "ck_login_pluus",
    "ck_www_pluus",
    "ck_rdv_justlink",
    "ck_www_justlink",
    "ck_ps_java",
]

j = 0
for group in ("group1", "group2", "group3", "group4"):
    for i in range(random.randint(1, 5)):
        node = "node" + string.ascii_uppercase[j]
        probe = Probe(
            group=group,
            node=node,
            probe_enabled=random.choice((True, False)),
            pager_enabled=random.choice((True, False)),
            notice_level=random.choice(Probe.NOTICE_LEVELS),
        )
        probe.save()
        j += 1
        for checkname in random.sample(CHECKS, random.randint(2, len(CHECKS) // 2)):
            check = Check(probe=probe, name=checkname, time_range="")
            check.save()
