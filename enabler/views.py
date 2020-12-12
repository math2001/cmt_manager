import yaml
import requests
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, HttpResponseBadRequest, JsonResponse
from django.template import loader
from django.views.decorators.http import require_GET, require_POST
from django.core.exceptions import (
    ObjectDoesNotExist,
    MultipleObjectsReturned,
)
from django.db import IntegrityError
from .models import Probe, Check


@require_GET
def index(request):
    state = {
        # groupname: {
        #   nodename: {
        #     probe_enabled: bool,
        #     pager_enabled: bool,
        #     notice_level: "alert" | "warning" | "notice",
        #     checks: {
        #       checkname: timeswitch (string)
        #     }
        #   }
        # }
    }
    probes = Probe.objects.all()
    for probe in probes:

        if probe.group not in state:
            state[probe.group] = {}

        assert probe.node not in state[probe.group]
        state[probe.group][probe.node] = {
            "probe_enabled": probe.probe_enabled,
            "pager_enabled": probe.pager_enabled,
            "notice_level": probe.notice_level,
            "checks": {},
        }

        for check in Check.objects.filter(probe=probe):
            state[probe.group][probe.node]["checks"][check.name] = check.time_switch

    context = {"groups": state, "levels": Probe.NOTICE_LEVELS}
    return render(request, "enabler/index.html", context)


@require_GET
def conf(request):
    if "node" not in request.GET or "group" not in request.GET:
        return HttpResponseBadRequest("required parameters: node, group")

    group = request.GET["group"]
    node = request.GET["node"]

    obj = get_object_or_404(Probe, group=group, node=node)

    response = HttpResponse(content_type="text/plain")
    yaml.dump(
        {
            "global": {
                "enable": obj.probe_enabled,
                "enable_pager": obj.pager_enabled,
                "alert_max_level": obj.notice_level,
            }
        },
        response,
    )
    return response


@require_POST
def update_probes_conf(request):
    if "group" not in request.GET or "node" not in request.GET:
        return HttpResponseBadRequest("missing parameters 'group' and/or 'node'")

    required_fields = ["notice-level"]
    for fields in required_fields:
        if fields not in request.POST:
            return HttpResponseBadRequest("missing field {!r}".format(fields))

    try:
        probe = Probe.objects.get(group=request.GET["group"], node=request.GET["node"])
    except ObjectDoesNotExist:
        return HttpResponseBadRequest("unknown group/node pair")
    except MultipleObjectsReturned:
        return HttpResponseBadRequest(
            "corrupted state: multiple probes for the given group/node pair"
        )

    if request.POST["notice-level"] not in Probe.NOTICE_LEVELS:
        return HttpResponseBadRequest("invalid notice level")

    probe.probe_enabled = "probe-enabled" in request.POST
    probe.pager_enabled = "pager-enabled" in request.POST
    probe.notice_level = request.POST["notice-level"]
    probe.save()

    for name in request.POST:
        if not name.startswith("time-switch-"):
            continue

        checkname = name[len("time-switch-") :]

        try:
            check = Check.objects.get(probe=probe, name=checkname)
        except ObjectDoesNotExists:
            return HttpResponseBadRequest("unknown check for given group/node pair")
        except MultipleObjectsReturned:
            return HttpResponseBadRequest(
                "corrupted state: multiple checks for the given group/node/check triple"
            )

        check.time_switch = request.POST[name]
        check.save()

    return redirect("enabler:index")


@require_GET
def fetch_probes_checks(request):
    hostname = "192.168.122.118"
    port = "9200"
    index = "graylog_0"
    response = requests.get(
        "http://{}:{}/{}/_search".format(hostname, port, index),
        json={
            "collapse": {
                "field": "cmt_id",
            },
            "_source": [""],
        },
    )
    if response.status_code != 200:
        return HttpResponseBadRequest(
            "invalid response from the server. status_code: {} body: {}".format(
                response.status_code,
                response.text,
            )
        )
    result = response.json()

    checks_added = []
    for hit in result["hits"]["hits"]:
        check_id = hit["fields"]["cmt_id"][0]
        group, node, module, checkname = check_id.split(".")
        probe = Probe(
            group=group,
            node=node,
            probe_enabled=True,
            pager_enabled=True,
            notice_level=Probe.NOTICE_LEVELS[0],
        )

        try:
            probe.save()
        except IntegrityError:
            probe = Probe.objects.get(group=group, node=node)

        check = Check(probe=probe, name=checkname)

        try:
            check.save()
            checks_added.append(check_id)
        except IntegrityError:
            pass

    return JsonResponse({"checks_added": checks_added})


def parse_name(name):
    """Retrieves (group, node, identifier) from "group-node-identifier" """
    bits = name.split(sep="-", maxsplit=2)
    if len(bits) != 3:
        print(bits)
        raise ValueError("invalid name {!r}, can't split in three parts".format(name))
    return bits[0], bits[1], bits[2]
