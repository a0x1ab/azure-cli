# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=protected-access

from azure.cli.core.util import shell_safe_json_parse
from azure.cli.core.aaz.utils import assign_aaz_list_arg

from ..aaz.latest.network.nat.gateway import Create as _GatewayCreate, Update as _GatewayUpdate


def _extract_ids_from_json(text):
    """Try to parse a legacy JSON array string and return a list of resource IDs, or None on failure."""
    try:
        parsed = shell_safe_json_parse(text)
    except Exception:   # pylint: disable=broad-except
        return None
    if not isinstance(parsed, list):
        return None
    return [item.get('id') for item in parsed if isinstance(item, dict) and item.get('id')]


def _normalize_pipv6_list(ctx, values, resource_type):
    """Normalize v6 public IP address/prefix input to list of {"id": resource_id} objects.

    Supports three input formats:
    - Resource name: 'pipv6-name' -> resolved to full resource ID
    - Resource ID: '/subscriptions/.../publicIPAddresses/pipv6' -> used as-is
    - Legacy JSON: "[{'id': '/subscriptions/...'}]" -> parsed and extracted
    """
    if not values:
        return []
    serialized = values.to_serialized_data()
    if not serialized:
        return []

    result = []
    for val in serialized:
        if not isinstance(val, str):
            continue
        stripped = val.strip()
        # Legacy JSON format: a single element that is a JSON array of objects
        if stripped.startswith('['):
            ids = _extract_ids_from_json(stripped)
            if ids is not None:
                result.extend(ids)
                continue
        # Full resource ID
        if stripped.startswith('/'):
            result.append(stripped)
        else:
            # Resource name -> build full resource ID
            resource_id = (
                f"/subscriptions/{ctx.subscription_id}/resourceGroups/"
                f"{ctx.args.resource_group.to_serialized_data()}/providers/Microsoft.Network/"
                f"{resource_type}/{stripped}"
            )
            result.append(resource_id)
    return result


class GatewayCreate(_GatewayCreate):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        from azure.cli.core.aaz import AAZListArg, AAZStrArg, AAZResourceIdArg, AAZResourceIdArgFormat
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.public_ip_addresses = AAZListArg(
            options=["--public-ip-addresses"],
            help="Space-separated list of public IP addresses (Names or IDs).",
        )
        args_schema.public_ip_addresses.Element = AAZResourceIdArg(
            fmt=AAZResourceIdArgFormat(
                template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network"
                         "/publicIPAddresses/{}",
            ),
        )
        args_schema.public_ip_prefixes = AAZListArg(
            options=["--public-ip-prefixes"],
            help="Space-separated list of public IP prefixes (Names or IDs).",
        )
        args_schema.public_ip_prefixes.Element = AAZResourceIdArg(
            fmt=AAZResourceIdArgFormat(
                template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network"
                         "/publicIPPrefixes/{}",
            ),
        )
        # Hide original v6 args (keep them for content builder) and clear their aliases
        args_schema.pip_addresses_v6._registered = False
        args_schema.pip_prefixes_v6._registered = False
        for opt in ('pip-addresses-v6', '--pip-addresses-v6'):
            args_schema._fields_alias_map.pop(opt, None)
        for opt in ('pip-prefixes-v6', '--pip-prefixes-v6'):
            args_schema._fields_alias_map.pop(opt, None)
        # Create new input args that accept plain names, resource IDs, and legacy JSON
        args_schema.pip_addresses_v6_input = AAZListArg(
            options=["--pip-addresses-v6"],
            help="Space-separated list of public IP addresses V6 (Names or IDs).",
        )
        args_schema.pip_addresses_v6_input.Element = AAZStrArg()
        args_schema.pip_prefixes_v6_input = AAZListArg(
            options=["--pip-prefixes-v6"],
            help="Space-separated list of public IP prefixes V6 (Names or IDs).",
        )
        args_schema.pip_prefixes_v6_input.Element = AAZStrArg()
        args_schema.pip_addresses._registered = False
        args_schema.pip_prefixes._registered = False
        return args_schema

    def pre_operations(self):
        args = self.ctx.args
        args.pip_addresses = assign_aaz_list_arg(
            args.pip_addresses,
            args.public_ip_addresses,
            element_transformer=lambda _, address_id: {"id": address_id}
        )
        args.pip_prefixes = assign_aaz_list_arg(
            args.pip_prefixes,
            args.public_ip_prefixes,
            element_transformer=lambda _, prefix_id: {"id": prefix_id}
        )
        from azure.cli.core.aaz import has_value
        if has_value(args.pip_addresses_v6_input):
            normalized = _normalize_pipv6_list(self.ctx, args.pip_addresses_v6_input, "publicIPAddresses")
            args.pip_addresses_v6 = [{"id": rid} for rid in normalized]
        if has_value(args.pip_prefixes_v6_input):
            normalized = _normalize_pipv6_list(self.ctx, args.pip_prefixes_v6_input, "publicIPPrefixes")
            args.pip_prefixes_v6 = [{"id": rid} for rid in normalized]
        args.sku.name = "Standard"


class GatewayUpdate(_GatewayUpdate):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        from azure.cli.core.aaz import AAZListArg, AAZStrArg, AAZResourceIdArg, AAZResourceIdArgFormat
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.public_ip_addresses = AAZListArg(
            options=["--public-ip-addresses"],
            help="Space-separated list of public IP addresses (Names or IDs).",
            nullable=True,
        )
        args_schema.public_ip_addresses.Element = AAZResourceIdArg(
            fmt=AAZResourceIdArgFormat(
                template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network"
                         "/publicIPAddresses/{}",
            ),
            nullable=True,
        )
        args_schema.public_ip_prefixes = AAZListArg(
            options=["--public-ip-prefixes"],
            help="Space-separated list of public IP prefixes (Names or IDs).",
            nullable=True,
        )
        args_schema.public_ip_prefixes.Element = AAZResourceIdArg(
            fmt=AAZResourceIdArgFormat(
                template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network"
                         "/publicIPPrefixes/{}",
            ),
            nullable=True,
        )
        # Hide original v6 args (keep them for content builder) and clear their aliases
        args_schema.pip_addresses_v6._registered = False
        args_schema.pip_prefixes_v6._registered = False
        for opt in ('pip-addresses-v6', '--pip-addresses-v6'):
            args_schema._fields_alias_map.pop(opt, None)
        for opt in ('pip-prefixes-v6', '--pip-prefixes-v6'):
            args_schema._fields_alias_map.pop(opt, None)
        # Create new input args that accept plain names, resource IDs, and legacy JSON
        args_schema.pip_addresses_v6_input = AAZListArg(
            options=["--pip-addresses-v6"],
            help="Space-separated list of public IP addresses V6 (Names or IDs).",
            nullable=True,
        )
        args_schema.pip_addresses_v6_input.Element = AAZStrArg(nullable=True)
        args_schema.pip_prefixes_v6_input = AAZListArg(
            options=["--pip-prefixes-v6"],
            help="Space-separated list of public IP prefixes V6 (Names or IDs).",
            nullable=True,
        )
        args_schema.pip_prefixes_v6_input.Element = AAZStrArg(nullable=True)
        args_schema.pip_addresses._registered = False
        args_schema.pip_prefixes._registered = False
        return args_schema

    def pre_operations(self):
        args = self.ctx.args
        args.pip_addresses = assign_aaz_list_arg(
            args.pip_addresses,
            args.public_ip_addresses,
            element_transformer=lambda _, address_id: {"id": address_id}
        )
        args.pip_prefixes = assign_aaz_list_arg(
            args.pip_prefixes,
            args.public_ip_prefixes,
            element_transformer=lambda _, prefix_id: {"id": prefix_id}
        )
        from azure.cli.core.aaz import has_value
        if has_value(args.pip_addresses_v6_input):
            normalized = _normalize_pipv6_list(self.ctx, args.pip_addresses_v6_input, "publicIPAddresses")
            args.pip_addresses_v6 = [{"id": rid} for rid in normalized]
        if has_value(args.pip_prefixes_v6_input):
            normalized = _normalize_pipv6_list(self.ctx, args.pip_prefixes_v6_input, "publicIPPrefixes")
            args.pip_prefixes_v6 = [{"id": rid} for rid in normalized]
