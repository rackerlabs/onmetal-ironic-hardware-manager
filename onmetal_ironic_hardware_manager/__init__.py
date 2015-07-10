# Copyright 2014 Rackspace, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import re

import six

from ironic_python_agent.common import metrics
from ironic_python_agent import errors
from ironic_python_agent import hardware
from ironic_python_agent import netutils
from ironic_python_agent import utils

from oslo_log import log


# Directory that all BIOS utilities are located in
BIOS_DIR = '/mnt/bios/quanta_A14'
LSI_MODELS = ['NWD-BLP4-1600']
SATADOM_MODELS = ['32G MLC SATADOM', '7 PIN  SATA FDM', 'Fastable SD131 7',
                  'SATADOM-SH TYPE C 3SE']
# Directory that all the LSI utilities/firmware are located in
LSI_FIRMWARE_VERSION = '12.22.00.00'
LSI_FIRMWARE_PREFLASH = 'NWD-BLP4-1600_ConcatSigned.fw'
LSI_FIRMWARE_PACKAGE = 'NWD-BLP4-1600_12.22.00.00.bin'
LSI_WARPDRIVE_DIR = os.path.join('/mnt/LSI', LSI_FIRMWARE_VERSION)
DDOEMCLI = os.path.join(LSI_WARPDRIVE_DIR, 'ddoemcli')

LOG = log.getLogger()

LLDP_PORT_TYPE = 2
LLDP_CHASSIS_TYPE = 5


class OnMetalHardwareManager(hardware.GenericHardwareManager):
    # Overrides superclass's name (generic_hardware_manager).
    HARDWARE_MANAGER_NAME = 'onmetal_hardware_manager'
    # This should be incremented at every upgrade to avoid making the agent
    # change which hardware manager it uses when cleaning in the middle of a
    # hardware manager upgrade.
    HARDWARE_MANAGER_VERSION = '4'

    def evaluate_hardware_support(cls):
        return hardware.HardwareSupport.SERVICE_PROVIDER

    @metrics.instrument(__name__, 'erase_block_device')
    def erase_block_device(self, block_device):
        if self._erase_lsi_warpdrive(block_device):
            return

        super(OnMetalHardwareManager, self).erase_block_device(block_device)

    def get_clean_steps(self, node, ports):
        """Get a list of clean steps with priority.

        Returns a list of dicts of the following form:
        {'step': the HardwareManager function to call.
         'interface': the Ironic interface to use to perform the step. Clean
                      steps use the deploy interface.
         'priority': the order to call. Steps with higher priority are called
                     first.
         'reboot_requested': whether the agent should reboot after the step is
                             complete.
        :return: a default list of decommission steps, as a list of
        dictionaries
        """
        # NOTE(supermari0): GenericHardwareManager is assumed to have an
        # erase_devices step. We implement erase_block_device which is called
        # by erase_devices. We need to be aware of that if IPA changes.
        return [
            {
                'step': 'remove_bootloader',
                'interface': 'deploy',
                'priority': 100,
                'reboot_requested': False,
            },
            {
                'step': 'upgrade_bios',
                'interface': 'deploy',
                'priority': 90,
                'reboot_requested': True,
            },
            {
                'step': 'decom_bios_settings',
                'interface': 'deploy',
                'priority': 80,
                'reboot_requested': True,
            },
            {
                'step': 'update_warpdrive_firmware',
                'interface': 'deploy',
                'priority': 70,
                'reboot_requested': False,
            },
            # This step is a no-op for now.
            {
                'step': 'update_intel_nic_firmware',
                'interface': 'deploy',
                'priority': 60,
                'reboot_requested': True,
            },
            {
                'step': 'erase_devices',
                'interface': 'deploy',
                'priority': 50,
                'reboot_requested': False,
            },
            {
                'step': 'get_disk_metrics',
                'interface': 'deploy',
                'priority': 40,
                'reboot_requested': False
            },
            {
                'step': 'customer_bios_settings',
                'interface': 'deploy',
                'priority': 30,
                'reboot_requested': True,
            },
            {
                'step': 'verify_ports',
                'interface': 'deploy',
                'priority': 20,
                'reboot_requested': False
            },
            {
                'step': 'verify_hardware',
                'interface': 'deploy',
                'priority': 0,
                'reboot_requested': False
            }
        ]

    @metrics.instrument(__name__, 'decom_bios_settings')
    def decom_bios_settings(self, node, ports):
        driver_info = node.get('driver_info', {})
        LOG.info('Decom BIOS Settings called with %s' % driver_info)
        cmd = os.path.join(BIOS_DIR, 'write_bios_settings_decom.sh')
        utils.execute(cmd, check_exit_code=[0])
        return True

    @metrics.instrument(__name__, 'customer_bios_settings')
    def customer_bios_settings(self, node, ports):
        driver_info = node.get('driver_info', {})
        LOG.info('Customer BIOS Settings called with %s' % driver_info)
        cmd = os.path.join(BIOS_DIR, 'write_bios_settings_customer.sh')
        utils.execute(cmd, check_exit_code=[0])
        return True

    @metrics.instrument(__name__, 'remove_bootloader')
    def remove_bootloader(self, node, ports):
        driver_info = node.get('driver_info', {})
        LOG.info('Remove Bootloader called with %s' % driver_info)
        bootdisk = self.get_os_install_device()
        cmd = ['dd', 'if=/dev/zero', 'of=' + bootdisk, 'bs=1M', 'count=1']
        utils.execute(*cmd, check_exit_code=[0])
        return True

    @metrics.instrument(__name__, 'upgrade_bios')
    def upgrade_bios(self, node, ports):
        driver_info = node.get('driver_info', {})
        LOG.info('Update BIOS called with %s' % driver_info)
        cmd = os.path.join(BIOS_DIR, 'flash_bios.sh')
        utils.execute(cmd, check_exit_code=[0])
        return True

    @metrics.instrument(__name__, 'update_warpdrive_firmware')
    def update_warpdrive_firmware(self, node, ports):
        driver_info = node.get('driver_info', {})
        LOG.info('Update Warpdrive called with %s' % driver_info)
        devices = self._list_lsi_devices()
        for device in devices:
            # Don't reflash the same firmware
            if device['version'] != LSI_FIRMWARE_VERSION:
                preflash_path = os.path.join(LSI_WARPDRIVE_DIR,
                                             LSI_FIRMWARE_PREFLASH)
                firmware_path = os.path.join(LSI_WARPDRIVE_DIR,
                                             LSI_FIRMWARE_PACKAGE)

                # note(JayF): New firmware requires us to flash a new firmware
                # flasher before flashing the update package
                precmd = [DDOEMCLI, '-c', device['id'], '-f', preflash_path]
                cmd = [DDOEMCLI, '-c', device['id'],
                       '-updatepkg', firmware_path]
                with metrics.instrument_context(
                        __name__, 'upgrade_warpdrive_firmware_preflash'):
                    utils.execute(*precmd, check_exit_code=[0])
                with metrics.instrument_context(
                        __name__, 'upgrade_warpdrive_firmware_package'):
                    utils.execute(*cmd, check_exit_code=[0])
            else:
                LOG.info('Device %(id)s already version %(version)s, '
                         'not upgrading.' % {
                             'id': device['id'],
                             'version': device['version']
                         })

    def update_intel_nic_firmware(self, node, ports):
        LOG.info('NOOP: Update Intel NIC called with %s' %
                 node.get('driver_info'))

    def _list_lsi_devices(self):
        lines = utils.execute(DDOEMCLI, '-listall')[0].split('\n')
        matching_devices = [line.split() for line in lines for model in
                            LSI_MODELS if model in line]
        devices = []
        for line in matching_devices:
            devices.append({
                'id': line[0].strip(),
                'model': line[1].strip(),
                'version': line[2].strip(),
                # Strip the last :00 to match the /sys/devices filename
                'pci_address': line[3].strip()[:-3]
            })
        return devices

    def _get_warpdrive_card(self, block_device):
        device_name = os.path.basename(block_device.name)
        sys_block_path = '{0}/block/{1}'.format(self.sys_path, device_name)

        # NOTE(russell_h): Trying to map a block device name to an LSI card
        # gets a little weird. It seems like if we follow the
        # /sys/block/<name> symlink, we'll find something that looks like:
        #
        # /sys/devices/pci0000:00/0000:00:02.0/0000:02:00.0/host3/
        #      target3:1:0/3:1:0:0/block/sdb
        #
        # This seems to correspond to the card that ddcli reports has PCI
        # address 00:02:00:00
        real_path = os.path.realpath(sys_block_path)

        # pull out a segment such as 0000:02:00.0 and trim it to 00:02:00
        pci_address = real_path.split('/')[5][2:-2]

        devices = self._list_lsi_devices()

        matching_devices = [device for device in devices if
                            device['pci_address'] == pci_address]

        if len(matching_devices) == 0:
            raise errors.CleaningError(('Unable to locate an LSI '
                'card with a PCI Address matching {0} for block device '
                '{1}').format(pci_address, block_device.name))

        if len(matching_devices) > 1:
            raise errors.CleaningError(('Found multiple LSI '
                'cards with a PCI Address matching {0} for block device '
                '{1}').format(pci_address, block_device.name))

        return matching_devices[0]

    def _is_warpdrive(self, block_device):
        if block_device.model in LSI_MODELS:
            return True

    def _get_smartctl_attributes(self, block_device):
        smartout = utils.execute('smartctl', '--attributes', block_device.name)
        header = None
        it = iter(smartout[0].split('\n'))
        for line in it:
            # note(JayF): skip forward until we get to the header and pull
            # it out
            if line.strip().startswith('ID#'):
                header = line.strip().split()
                break

        attributes = {}
        # note(JayF): All lines at this point contain metrics or are blank.
        for line in it:
            line = line.strip()
            if not line:
                continue
            linelist = line.split()
            # note(JayF): match up headers to values to generate a dict
            key = linelist[0] + '-' + linelist[1]
            value = dict(zip(header[2:], linelist[2:]))
            attributes[key] = value

        return attributes

    def _get_warpdrive_attributes(self, block_device):
        device = self._get_warpdrive_card(block_device)
        result = utils.execute(DDOEMCLI, '-c', device['id'], '-health')
        attributes = {}
        attrkey = None
        # note(JayF): What we really get here is SMART data for the 4 SSDs
        # behind the Warpdrive card. Split them up to parse separately.
        for idx, lines in enumerate(result[0].split('SSD Drive SMART')):
            # note(JayF): The first entry is headers, throw it away
            if idx == 0:
                continue
            it = iter(lines.split('\n'))
            for line in it:
                line = line.strip()
                if not line:
                    continue
                if line.startswith('Data Slot #'):
                    # note(JayF): Get the drive number and serial. The full
                    # line is actually "SSD Drive SMART Data Slot #" but by
                    # splitting on it above we lose the first three words.
                    drivenum = line.split()[3][0]
                    driveserial = line.split()[7]
                    attrkey = drivenum + '_' + driveserial
                    attributes[attrkey] = {}
                # note(JayF): Once we know what drive this is, skip past the
                # current metrics (which are only for a power cycle), to put
                # the iterator in the right place for starting to grab k:v
                # pairs below
                if line.startswith('-------------- Cumulative'):
                    break

            for line in it:
                line = line.strip()
                # note(JayF): It doesn't make sense to store time in graphite
                if not line or line.endswith('(Hours:Minutes:Seconds)'):
                    continue
                # note(JayF): This is the first line of the footer. If we get
                # here, we're done parsing.
                if line.startswith('Warranty Remaining'):
                    break
                # note(JayF): Some of the metrics have units or notes in
                # parens, we look for these and adjust our rsplit accordingly
                if line.endswith('(degree C)'):
                    key = line.rsplit(None, 3)[0].replace(" ", "")
                    value = line.rsplit(None, 3)[1]
                elif (line.endswith('(Gigabytes)')
                       or line.endswith('(%)')):
                    key = line.rsplit(None, 2)[0].replace(" ", "")
                    value = line.rsplit(None, 2)[1]
                else:
                    key = line.rsplit(None, 1)[0].replace(" ", "")
                    value = line.rsplit(None, 1)[1]
                # note(JayF): Ensure all characters are safe for graphite
                key = re.sub(r'[\(\)/\\]', '_', key)
                attributes[attrkey][key] = re.sub(r'[\(\)/\\]', '_', value)

        return attributes

    def _send_gauges(self, prefix, metrics_to_send):
        """Batch-send gauges to MetricsLogger.

        :param prefix: The prefix given to MetricLogger
        :param metrics: Dict in the format {'key': 'value'} where key is the
                        metric name and value is the metric.
        """
        logger = metrics.getLogger(prefix)
        for name, gauge in six.iteritems(metrics_to_send):
            logger.gauge(name, gauge)

    def get_disk_metrics(self, node, ports):
        smart_data_columns = ['VALUE', 'WORST', 'RAW_VALUE']
        block_devices = self.list_block_devices()
        for block_device in block_devices:
            if self._is_warpdrive(block_device):
                wdmetrics = self._get_warpdrive_attributes(block_device)
                prefix = 'smartdata_{0}_{1}'.format(
                        os.path.basename(block_device.name),
                        block_device.model.replace(" ", ""))
                metrics_to_send = {}
                for disk, stats in six.iteritems(wdmetrics):
                    for key, value in six.iteritems(stats):
                        metrickey = disk + '.' + key
                        metrics_to_send[metrickey] = value

            else:
                disk_metrics = self._get_smartctl_attributes(block_device)
                prefix = 'smartdata_{0}_{1}'.format(
                        os.path.basename(block_device.name),
                        block_device.model.replace(" ", ""))
                metrics_to_send = {}
                for k, v in six.iteritems(disk_metrics):
                    if v['RAW_VALUE'] == '0':
                        continue
                    for heading in smart_data_columns:
                        key = k + '.' + heading
                        metrics_to_send[key] = v[heading]

            self._send_gauges(prefix, metrics_to_send)

    def _erase_lsi_warpdrive(self, block_device):
        if not self._is_warpdrive(block_device):
            return False

        # NOTE(JayF): Start timing here, so any devices short circuited
        # don't produce invalidly-short metrics.
        with metrics.instrument_context(__name__, 'erase_lsi_warpdrive'):
            device = self._get_warpdrive_card(block_device)
            result = utils.execute(DDOEMCLI, '-c', device['id'], '-format',
                    '-op', '-level', 'nom', '-s')
            if 'WarpDrive format successfully completed.' not in result[0]:
                raise errors.BlockDeviceEraseError(('Erasing LSI card failed: '
                    '{0}').format(result[0]))

        return True

    @metrics.instrument(__name__, 'verify_ports')
    def verify_ports(self, node, ports):
        """Given Port dicts, verify they match LLDP information

        :param node: a dict representation of a Node object
        :param ports: a dict representation of Ports connected to the node
        :raises CleaningError: if any of the steps determine the node
                does not match the given data
        """
        node_switchports = self._get_node_switchports(node, ports)
        if not node_switchports:
            # Fail gracefully if we cannot find node ports. If call is made
            # with only driver_info, don't fail.
            return

        interface_names = [x.name for x in self.list_network_interfaces()]
        lldp_info = netutils.get_lldp_info(interface_names)

        # Both should be a set of tuples: (chassis, port)
        lldp_ports = set()

        for lldp in lldp_info.values():
            lldp_ports.add(self._get_port_from_lldp(lldp))
        LOG.info('LLDP ports: %s', lldp_ports)
        LOG.info('Node ports: %s', node_switchports)
        # TODO(JoshNang) add check that ports, chassis *and* interface match
        # when port/chassis are stored on Port objects

        # Compare the ports
        if node_switchports != lldp_ports:
            LOG.error('Ports did not match, LLDP: %(lldp)s, Node: %(node)s',
                      {'lldp': lldp_ports, 'node': node_switchports})
            # TODO(supermari0) The old error here - VerificationError - seems
            # not to exist or have existed. It would be good if we had more
            # specific errors that subclass CleaningError.
            raise errors.CleaningError(
                'Detected port mismatches. LLDP detected_ports: %(lldp)s, '
                'Node ports: %(node)s.' %
                {'lldp': lldp_ports, 'node': node_switchports})

        # Return the LLDP info
        LOG.debug('Ports match, returning LLDP info: %s', lldp_info)
        # Ensure the return value is properly encode or JSON throws errors
        return unicode(lldp_info)

    def _get_port_from_lldp(self, lldp_info):
        """Return a set of tuples (chassis, port) from the given LLDP info

        :param lldp_info: the return from netutils.get_lldp_info()
        :return: a Set of tuples (chassis, port)
        """

        tlv_port = self._get_tlv(LLDP_PORT_TYPE, lldp_info)
        tlv_chassis = self._get_tlv(LLDP_CHASSIS_TYPE, lldp_info)

        if len(tlv_port) != 1 or len(tlv_chassis) != 1:
            raise errors.CleaningError(
                'Malformed LLDP info. Received port: %(port)s, '
                'chassis: %(chassis)s' %
                {'port': tlv_port, 'chassis': tlv_chassis})

        port_number = re.search(r'\d{1,2}/\d{1,2}', tlv_port[0])
        lldp_port = 'eth' + port_number.group()
        return tlv_chassis[0].lower(), lldp_port.lower()

    def _get_node_switchports(self, node, ports):
        """Find the chassis and ports the node is attached to

        Return a set of tuples (chassis, port). Supports pulling them
        from node['extra'], with support for pull chassis/port/interface from
        port['extra'] in the future.

        :param node: a dict representation of a Node object
        :param ports: a dict representation of Ports connected to the node
        :return: a Set of tuples (chassis, port)
        """
        if not node.get('extra'):
            return set()
        LOG.info('Matching against node ports: %s', node.get('extra'))
        try:
            return set([
                (node['extra']['hardware/interfaces/0/'
                               'switch_chassis_id'].lower(),
                 node['extra']['hardware/interfaces/0/'
                               'switch_port_id'].lower()),
                (node['extra']['hardware/interfaces/1/'
                               'switch_chassis_id'].lower(),
                 node['extra']['hardware/interfaces/1/'
                               'switch_port_id'].lower())
            ])
        except KeyError:
            raise errors.CleaningError(
                'Node has malformed extra data, could not find chassis'
                ' and port: %s' % node['extra'])

    def _get_tlv(self, tlv_type, lldp_info):
        """Return all LLDP values that match a TLV type (an int) as a list."""
        # Use a list because TLV type 127 may be be used multiple times in LLDP
        values = []
        for tlv in lldp_info:
            if len(tlv) != 2:
                raise errors.CleaningError('Malformed LLDP info %s'
                                               % lldp_info)
            if tlv[0] == tlv_type:
                values.append(tlv[1])
        return values

    def _get_flavor_from_node(self, node):
        ram = node['properties']['memory_mb']
        if ram == (1024 * 32):
            return 'onmetal-compute1'
        if ram == (1024 * 128):
            return 'onmetal-io1'
        if ram == (1024 * 512):
            return 'onmetal-memory1'
        raise errors.CleaningError('unknown flavor')

    def _verify_blockdevice_count(self, block_devices, models, count):
        if len([d for d in block_devices if d.model in models]) != count:
            raise errors.CleaningError('Could not find %(count)s block '
                    'devices with model name "%(model)s"' %
                    {'count': count, 'model': models})

    @metrics.instrument(__name__, 'verify_hardware')
    def verify_hardware(self, node, ports):
        flavor = self._get_flavor_from_node(node)
        block_devices = self.list_block_devices()

        if flavor == 'onmetal-io1':
            # verify it has two IO cards
            self._verify_blockdevice_count(block_devices, LSI_MODELS, 2)

        # note(JayF): Until we verify more than disks, there's no
        # difference between memory and compute nodes.
        self._verify_blockdevice_count(block_devices, SATADOM_MODELS, 1)
