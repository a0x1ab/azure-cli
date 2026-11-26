# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.testsdk import ScenarioTest, ResourceGroupPreparer


class NatGatewayScenarioTests(ScenarioTest):

    @ResourceGroupPreparer(location='eastus2')
    def test_natgateway_basic(self, resource_group, resource_group_location):

        self.kwargs.update({
            'name': "ng1",
            'name2': "ng2",
            'idle_timeout': 4,
            'sku': "Standard",
            'ip_addr': "pip",
            'ip_prefix': "prefix",
            'idle_timeout_updated': 5,
            'zone': 2,
            'location': resource_group_location,
            'resource_type': 'Microsoft.Network/NatGateways',
            'tags': 'foo=bar'
        })

        # create public ip address
        self.cmd('az network public-ip create -g {rg} -n {ip_addr} --location {location} --zone {zone} --sku Standard')

        # create public ip prefix
        self.cmd('az network public-ip prefix create --length 29 --location {location} --name {ip_prefix} --resource-group {rg} --zone {zone}')

        self.cmd('az network nat gateway create --resource-group {rg} --public-ip-prefixes {ip_prefix} --name {name} --location {location} --public-ip-addresses {ip_addr} --idle-timeout {idle_timeout} --zone {zone} --tags {tags}', checks=[
            self.check('resourceGroup', '{rg}'),
            self.check('idleTimeoutInMinutes', '{idle_timeout}'),
            self.check("contains(publicIpAddresses[0].id, '{ip_addr}')", True),
            self.check("contains(publicIpPrefixes[0].id, '{ip_prefix}')", True),
            self.check('sku.name', 'Standard'),
            self.check('location', '{location}'),
            self.check('zones[0]', '{zone}'),
            self.check('tags', {'foo': 'bar'})
        ])
        self.cmd('az network nat gateway update -g {rg} --name {name} --idle-timeout {idle_timeout_updated}',
                 checks=self.check('idleTimeoutInMinutes', 5))
        self.cmd('az network nat gateway list -g {rg}',
                 checks=self.check('length(@)', 1))
        self.cmd('az network nat gateway show --resource-group {rg} --name {name}',
                 checks=self.check('name', '{name}'))

        # delete and verify item is removed
        self.cmd('az network nat gateway delete --resource-group {rg} --name {name}')
        self.cmd('az network nat gateway list -g {rg}',
                 checks=self.check('length(@)', 0))

        # test standardv2 sku
        self.cmd('az network nat gateway create -g {rg} -n {name2} --sku StandardV2', checks=[
            self.check('sku.name', 'StandardV2')
        ])
        self.cmd('az network nat gateway delete -g {rg} -n {name2}')

    @ResourceGroupPreparer(location='eastus2')
    def test_natgateway_pipv6_param_formats(self, resource_group, resource_group_location):
        """Test that --pip-addresses-v6 / --pip-prefixes-v6 accept names, resource IDs, and JSON objects."""
        self.kwargs.update({
            'name': 'ng-v6-formats',
            'location': resource_group_location,
            'ip_by_name': 'pipv6-by-name',
            'ip_by_id': 'pipv6-by-id',
            'ip_by_json': 'pipv6-by-json',
            'prefix_by_name': 'prefixv6-by-name',
            'prefix_by_id': 'prefixv6-by-id',
            'ip_v4': 'pipv4',
        })

        # create resources
        self.cmd('az network public-ip create -g {rg} -n {ip_v4} --location {location} '
                 '--sku StandardV2 --tier Regional --allocation-method Static')
        self.cmd('az network public-ip create -g {rg} -n {ip_by_name} --location {location} '
                 '--sku StandardV2 --version IPv6 --tier Regional --allocation-method Static')
        result = self.cmd('az network public-ip create -g {rg} -n {ip_by_id} --location {location} '
                          '--sku StandardV2 --version IPv6 --tier Regional --allocation-method Static').get_output_in_json()
        self.kwargs['ip_full_id'] = result['publicIp']['id']

        result = self.cmd('az network public-ip create -g {rg} -n {ip_by_json} --location {location} '
                          '--sku StandardV2 --version IPv6 --tier Regional --allocation-method Static').get_output_in_json()
        self.kwargs['ip_json_value'] = '[{{"id": "{}"}}]'.format(result['publicIp']['id'])

        self.cmd('az network public-ip prefix create --length 127 --location {location} '
                 '--name {prefix_by_name} -g {rg} --sku StandardV2 --version IPv6 --tier Regional')
        result = self.cmd('az network public-ip prefix create --length 127 --location {location} '
                          '--name {prefix_by_id} -g {rg} --sku StandardV2 --version IPv6 --tier Regional').get_output_in_json()
        self.kwargs['prefix_full_id'] = result['id']

        # test create with name format
        self.cmd('az network nat gateway create -g {rg} -n {name} --sku StandardV2 '
                 '--public-ip-addresses {ip_v4} '
                 '--pip-addresses-v6 {ip_by_name} '
                 '--pip-prefixes-v6 {prefix_by_name}', checks=[
            self.check('sku.name', 'StandardV2'),
            self.check("contains(publicIpAddressesV6[0].id, '{ip_by_name}')", True),
            self.check("contains(publicIpPrefixesV6[0].id, '{prefix_by_name}')", True),
        ])

        # test update with full resource ID format
        self.cmd('az network nat gateway update -g {rg} -n {name} '
                 '--pip-addresses-v6 {ip_full_id} '
                 '--pip-prefixes-v6 {prefix_full_id}', checks=[
            self.check("contains(publicIpAddressesV6[0].id, '{ip_by_id}')", True),
            self.check("contains(publicIpPrefixesV6[0].id, '{prefix_by_id}')", True),
        ])

        # test update with JSON object format (backward compatibility)
        self.cmd("az network nat gateway update -g {rg} -n {name} "
                 "--pip-addresses-v6 '{ip_json_value}'", checks=[
            self.check("contains(publicIpAddressesV6[0].id, '{ip_by_json}')", True),
        ])

        self.cmd('az network nat gateway delete -g {rg} -n {name}')

    @ResourceGroupPreparer(location='eastus2')
    def test_natgateway_empty_create(self, resource_group, resource_group_location):
        self.kwargs.update({
            'name': "ng1",
            'idle_timeout': 4,
            'sku': "Standard",
            'ip_addr': "pip",
            'ip_prefix': "prefix",
            'idle_timeout_updated': 5,
            'zone': 2,
            'location': resource_group_location,
            'resource_type': 'Microsoft.Network/NatGateways',
            'tags': 'foo=bar'
        })
        self.cmd(
            'az network nat gateway create --resource-group {rg} --name {name} --location {location} --idle-timeout {idle_timeout} --zone {zone} --tags {tags}',
            checks=[
                self.check('resourceGroup', '{rg}'),
                self.check('idleTimeoutInMinutes', '{idle_timeout}'),
                self.check('sku.name', 'Standard'),
                self.check('location', '{location}'),
                self.check('zones[0]', '{zone}'),
                self.check('tags', {'foo': 'bar'})
            ])
