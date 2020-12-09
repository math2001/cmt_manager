import yaml
from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseBadRequest, JsonResponse
from django.template import loader
from django.views.decorators.http import require_GET, require_POST
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
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
    response = HttpResponse(content_type="text/plain")
    if "node" not in request.GET or "group" not in request.GET:
        response.status_code = 400
        response.write("required parameters: node, group")
        return response

    group = request.GET["group"]
    node = request.GET["node"]
    if group not in state:
        response.status_code = 404
        response.write("unknown group: {}".format(group))
        return response

    if node not in state[group]:
        response.status_code = 404
        response.write("unknown_node: {}".format(node))
        return response

    response.status_code = 200
    yaml.dump(state[group][node], response)
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


def parse_name(name):
    """Retrieves (group, node, identifier) from "group-node-identifier" """
    bits = name.split(sep="-", maxsplit=2)
    if len(bits) != 3:
        print(bits)
        raise ValueError("invalid name {!r}, can't split in three parts".format(name))
    return bits[0], bits[1], bits[2]
