import random
import string
from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseBadRequest
from django.template import loader
from django.views.decorators.http import require_GET, require_POST

random.seed(2)

ALERT_LEVELS = ("alert", "warning", "notice")
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

state = {}

j = 0
for name in ("group1", "group2", "group3", "group4"):
    state[name] = {}
    for i in range(random.randint(1, 5)):
        node = "node" + string.ascii_uppercase[j]
        j += 1
        state[name][node] = {
            "enabled": bool(random.randint(0, 1)),
            "level": random.choice(ALERT_LEVELS),
            "checks": {},
        }
        for check in random.sample(CHECKS, random.randint(2, len(CHECKS) // 2)):
            state[name][node]["checks"][check] = ""


@require_GET
def index(request):
    context = {"groups": state, "levels": ALERT_LEVELS}
    return render(request, "enabler/index.html", context)


@require_POST
def update_probes_conf(request):
    for name in request.POST:
        # hard-coded, but the documentation hard codes it too in the documentation
        # https://docs.djangoproject.com/en/dev/ref/csrf/#acquiring-the-token-if-csrf-use-sessions-or-csrf-cookie-httponly-is-true
        if name == "csrfmiddlewaretoken":
            continue

        try:
            group, node, identifer = parse_name(name)
        except ValueError as e:
            print(e)  # FIXME: proper logging?
            return HttpResponseBadRequest("invalid name {!r}".format(name))

        if identifer == "enabled":
            state[group][node][identifer] = request.POST[name] == "true"
        elif identifer == "level":
            assert request.POST[name] in ALERT_LEVELS, request.POST[name]
            state[group][node][identifer] = request.POST[name]
        else:

            if "-" not in identifer:
                return HttpResponseBadRequest("invalid name {!r}".format(name))

            check, identifer = identifer.split("-", maxsplit=1)
            if identifer != "disabled-time-range":
                return HttpResponseBadRequest("invalid name {!r}".format(name))
            state[group][node][check] = request.POST[name]

    return redirect("enabler:index")


def parse_name(name):
    """Retrieves (group, node, identifier) from "group-node-identifier" """
    bits = name.split(sep="-", maxsplit=2)
    if len(bits) != 3:
        print(bits)
        raise ValueError("invalid name {!r}, can't split in three parts".format(name))
    return bits[0], bits[1], bits[2]
