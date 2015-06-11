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

import mock
import os
import six

from ironic_python_agent import errors
from ironic_python_agent import hardware
from ironic_python_agent import utils
from oslotest import base as test_base

import onmetal_ironic_hardware_manager as onmetal_hardware_manager

if six.PY2:
    OPEN_FUNCTION_NAME = '__builtin__.open'
else:
    OPEN_FUNCTION_NAME = 'builtins.open'


def _read_file(test_data):
    filename = os.path.join(os.path.dirname(__file__), test_data)
    with open(filename, 'r') as data:
        return data.read()


DDOEMCLI_FORMAT_OUT = _read_file('data/ddoemcli_format_out.txt')
DDOEMCLI_LISTALL_OUT = _read_file('data/ddoemcli_listall_out.txt')
DDOEMCLI_HEALTH_OUT = _read_file('data/ddoemcli_health_out.txt')
SMARTCTL_ATTRIBUTES_OUT = _read_file('data/smartctl_attributes_out.txt')

WARPDRIVE_ATTRIBUTES = {
    '4_FL00AV2L': {
        'DevicePowerCycleCount': '49',
        'EraseFailCount1': '0',
        'GigabytesErased': '329',
        'I_OErrorDetectionCodeRate': '0',
        'MaximumLifetimeTemperature': '82',
        'Power-OnHours': '957.6',
        'ProgramFailCount': '0',
        'ReservedBlocksRemaining': '100',
        'Reserved_over-provisioned_Blocks': '32128',
        'RetiredBlockCount': '0',
        'SSDLifeLeft_PECycles_': '100',
        'TotalReadsToHost': '0',
        'TotalWritesFromHost': '7',
        'TrimCount': '0',
        'UncorrectableRAISEErrors': '0',
        'UnexpectedPowerLossCount': '56',
        'WriteAmplification': '1.29'
    },
    '5_FL00AV3L': {
        'DevicePowerCycleCount': '47',
        'EraseFailCount1': '0',
        'GigabytesErased': '289',
        'I_OErrorDetectionCodeRate': '0',
        'MaximumLifetimeTemperature': '82',
        'Power-OnHours': '957.5',
        'ProgramFailCount': '0',
        'ReservedBlocksRemaining': '100',
        'Reserved_over-provisioned_Blocks': '31232',
        'RetiredBlockCount': '0',
        'SSDLifeLeft_PECycles_': '100',
        'TotalReadsToHost': '0',
        'TotalWritesFromHost': '7',
        'TrimCount': '0',
        'UncorrectableRAISEErrors': '0',
        'UnexpectedPowerLossCount': '52',
        'WriteAmplification': '1.29'
     },
     '6_FL00AVPL': {
         'DevicePowerCycleCount': '45',
         'EraseFailCount1': '0',
         'GigabytesErased': '262',
         'I_OErrorDetectionCodeRate': '0',
         'MaximumLifetimeTemperature': '79',
         'Power-OnHours': '957.5',
         'ProgramFailCount': '0',
         'ReservedBlocksRemaining': '100',
         'Reserved_over-provisioned_Blocks': '30848',
         'RetiredBlockCount': '0',
         'SSDLifeLeft_PECycles_': '100',
         'TotalReadsToHost': '0',
         'TotalWritesFromHost': '7',
         'TrimCount': '0',
         'UncorrectableRAISEErrors': '0',
         'UnexpectedPowerLossCount': '48',
         'WriteAmplification': '1.29'
     },
     '7_FL00ATTV': {
         'DevicePowerCycleCount': '74',
         'EraseFailCount1': '0',
         'GigabytesErased': '9125',
         'I_OErrorDetectionCodeRate': '0',
         'MaximumLifetimeTemperature': '79',
         'Power-OnHours': '975.8',
         'ProgramFailCount': '0',
         'ReservedBlocksRemaining': '100',
         'Reserved_over-provisioned_Blocks': '31488',
         'RetiredBlockCount': '0',
         'SSDLifeLeft_PECycles_': '100',
         'TotalReadsToHost': '1228',
         'TotalWritesFromHost': '7936',
         'TrimCount': '0',
         'UncorrectableRAISEErrors': '0',
         'UnexpectedPowerLossCount': '89',
         'WriteAmplification': '1.02'
    }
}

SMARTCTL_ATTRIBUTES = {
    '1-Raw_Read_Error_Rate': {
        'FLAG': '0x000a',
        'RAW_VALUE': '0',
        'THRESH': '000',
        'TYPE': 'Old_age',
        'UPDATED': 'Always',
        'VALUE': '100',
        'WHEN_FAILED': '-',
        'WORST': '100'
    },
    '10-Unknown_SSD_Attribute': {
        'FLAG': '0x0013',
        'RAW_VALUE': '0',
        'THRESH': '050',
        'TYPE': 'Pre-fail',
        'UPDATED': 'Always',
        'VALUE': '100',
        'WHEN_FAILED': '-',
        'WORST': '100'
    },
    '12-Power_Cycle_Count': {
        'FLAG': '0x0012',
        'RAW_VALUE': '68',
        'THRESH': '000',
        'TYPE': 'Old_age',
        'UPDATED': 'Always',
        'VALUE': '100',
        'WHEN_FAILED': '-',
        'WORST': '100'
    },
    '167-Unknown_Attribute': {
        'FLAG': '0x0022',
        'RAW_VALUE': '0',
        'THRESH': '000',
        'TYPE': 'Old_age',
        'UPDATED': 'Always',
        'VALUE': '100',
        'WHEN_FAILED': '-',
        'WORST': '100'
    },
    '168-Unknown_Attribute': {
        'FLAG': '0x0012',
        'RAW_VALUE': '0',
        'THRESH': '000',
        'TYPE': 'Old_age',
        'UPDATED': 'Always',
        'VALUE': '100',
        'WHEN_FAILED': '-',
        'WORST': '100'
    },
    '169-Unknown_Attribute': {
        'FLAG': '0x0013',
        'RAW_VALUE': '262144',
        'THRESH': '010',
        'TYPE': 'Pre-fail',
        'UPDATED': 'Always',
        'VALUE': '100',
        'WHEN_FAILED': '-',
        'WORST': '100'
    },
    '170-Unknown_Attribute': {
        'FLAG': '0x0013',
        'RAW_VALUE': '0',
        'THRESH': '010',
        'TYPE': 'Pre-fail',
        'UPDATED': 'Always',
        'VALUE': '100',
        'WHEN_FAILED': '-',
        'WORST': '100'
    },
    '173-Unknown_Attribute': {
        'FLAG': '0x0012',
        'RAW_VALUE': '262146',
        'THRESH': '000',
        'TYPE': 'Old_age',
        'UPDATED': 'Always',
        'VALUE': '199',
        'WHEN_FAILED': '-',
        'WORST': '199'
    },
    '175-Program_Fail_Count_Chip': {
        'FLAG': '0x0013',
        'RAW_VALUE': '0',
        'THRESH': '010',
        'TYPE': 'Pre-fail',
        'UPDATED': 'Always',
        'VALUE': '100',
        'WHEN_FAILED': '-',
        'WORST': '100'
    },
    '192-Power-Off_Retract_Count': {
        'FLAG': '0x0012',
        'RAW_VALUE': '0',
        'THRESH': '000',
        'TYPE': 'Old_age',
        'UPDATED': 'Always',
        'VALUE': '100',
        'WHEN_FAILED': '-',
        'WORST': '100'
    },
    '194-Temperature_Celsius': {
        'FLAG': '0x0023',
        'RAW_VALUE': '40',
        'THRESH': '030',
        'TYPE': 'Pre-fail',
        'UPDATED': 'Always',
        'VALUE': '100',
        'WHEN_FAILED': '-',
        'WORST': '100'
    },
    '197-Current_Pending_Sector': {
        'FLAG': '0x0012',
        'RAW_VALUE': '0',
        'THRESH': '000',
        'TYPE': 'Old_age',
        'UPDATED': 'Always',
        'VALUE': '100',
        'WHEN_FAILED': '-',
        'WORST': '100'
    },
    '2-Throughput_Performance': {
        'FLAG': '0x0005',
        'RAW_VALUE': '0',
        'THRESH': '050',
        'TYPE': 'Pre-fail',
        'UPDATED': 'Offline',
        'VALUE': '100',
        'WHEN_FAILED': '-',
        'WORST': '100'
    },
    '240-Unknown_SSD_Attribute': {
        'FLAG': '0x0013',
        'RAW_VALUE': '0',
        'THRESH': '050',
        'TYPE': 'Pre-fail',
        'UPDATED': 'Always',
        'VALUE': '100',
        'WHEN_FAILED': '-',
        'WORST': '100'
    },
    '3-Spin_Up_Time': {
        'FLAG': '0x0007',
        'RAW_VALUE': '0',
        'THRESH': '050',
        'TYPE': 'Pre-fail',
        'UPDATED': 'Always',
        'VALUE': '100',
        'WHEN_FAILED': '-',
        'WORST': '100'
    },
    '5-Reallocated_Sector_Ct': {
        'FLAG': '0x0013',
        'RAW_VALUE': '0',
        'THRESH': '050',
        'TYPE': 'Pre-fail',
        'UPDATED': 'Always',
        'VALUE': '100',
        'WHEN_FAILED': '-',
        'WORST': '100'
    },
    '7-Unknown_SSD_Attribute': {
        'FLAG': '0x000b',
        'RAW_VALUE': '0',
        'THRESH': '050',
        'TYPE': 'Pre-fail',
        'UPDATED': 'Always',
        'VALUE': '100',
        'WHEN_FAILED': '-',
        'WORST': '100'
    },
    '8-Unknown_SSD_Attribute': {
        'FLAG': '0x0005',
        'RAW_VALUE': '0',
        'THRESH': '050',
        'TYPE': 'Pre-fail',
        'UPDATED': 'Offline',
        'VALUE': '100',
        'WHEN_FAILED': '-',
        'WORST': '100'
    },
    '9-Power_On_Hours': {
        'FLAG': '0x0012',
        'RAW_VALUE': '1673',
        'THRESH': '000',
        'TYPE': 'Old_age',
        'UPDATED': 'Always',
        'VALUE': '100',
        'WHEN_FAILED': '-',
        'WORST': '100'
    }
}


class TestOnMetalHardwareManager(test_base.BaseTestCase):
    def setUp(self):
        super(TestOnMetalHardwareManager, self).setUp()
        self.hardware = onmetal_hardware_manager.OnMetalHardwareManager()
        self.block_device = hardware.BlockDevice('/dev/sda', 'NWD-BLP4-1600',
                                                 1073741824, False)

        self.FAKE_DEVICES = [
            {
                'id': '1',
                'model': 'NWD-BLP4-1600',
                'pci_address': '00:02:00',
                'version': '12.22.00.00'
            },
            {
                'id': '2',
                'model': 'NWD-BLP4-1600',
                'pci_address': '00:04:00',
                'version': '12.22.00.00'
            }
        ]

    def _mock_file(self, mocked_open, contents):
        mocked_open.return_value.__enter__ = lambda s: s
        mocked_open.return_value.__exit__ = mock.Mock()
        read_mock = mocked_open.return_value.read
        read_mock.return_value = contents

    @mock.patch.object(utils, 'execute')
    def test__list_lsi_devices(self, mocked_execute):
        mocked_execute.side_effect = [
            (DDOEMCLI_LISTALL_OUT, '')
        ]
        devices = self.hardware._list_lsi_devices()
        self.assertEqual(self.FAKE_DEVICES, devices)

    @mock.patch.object(os.path, 'realpath')
    @mock.patch.object(utils, 'execute')
    def test_erase_block_device_lsi_success(self,
                                            mocked_execute,
                                            mocked_realpath):
        self.hardware._list_lsi_devices = mock.Mock()
        self.hardware._list_lsi_devices.return_value = self.FAKE_DEVICES

        # Mock the PCI address lookup
        mocked_realpath.return_value = ('/sys/devices/pci0000:00/0000:00:02.0'
            '/0000:02:00.0/host3/target3:1:0/3:1:0:0/block/sdb')

        mocked_execute.return_value = (DDOEMCLI_FORMAT_OUT, '')

        self.hardware.erase_block_device(self.block_device)

        mocked_execute.assert_called_once_with(
                onmetal_hardware_manager.DDOEMCLI,
                '-c', '1', '-format', '-op', '-level', 'nom', '-s')

    @mock.patch.object(os.path, 'realpath')
    @mock.patch.object(utils, 'execute')
    def test_erase_block_device_lsi_notfound(self,
                                             mocked_execute,
                                             mocked_realpath):
        self.hardware._list_lsi_devices = mock.Mock()
        self.hardware._list_lsi_devices.return_value = self.FAKE_DEVICES

        # The '0000:06:00.0' does not map to an address in the ddcli output
        mocked_realpath.return_value = ('/sys/devices/pci0000:00/0000:00:02.0'
            '/0000:06:00.0/host3/target3:1:0/3:1:0:0/block/sdb')

        # A CleaningError is raised instead of a BlockDeviceEraseError because
        # the error was with the cleaning finding the block device rather than
        # actually erasing an existing block device.
        self.assertRaises(errors.CleaningError,
                          self.hardware.erase_block_device,
                          self.block_device)

        self.assertEqual(0, mocked_execute.call_count)

    @mock.patch.object(os.path, 'realpath')
    @mock.patch.object(utils, 'execute')
    def test_erase_block_device_lsi_multiple(self,
                                             mocked_execute,
                                             mocked_realpath):
        self.hardware._list_lsi_devices = mock.Mock()
        dupes = self.FAKE_DEVICES
        dupes[1]['pci_address'] = '00:02:00'
        self.hardware._list_lsi_devices.return_value = dupes

        mocked_realpath.return_value = ('/sys/devices/pci0000:00/0000:00:02.0'
            '/0000:02:00.0/host3/target3:1:0/3:1:0:0/block/sdb')

        # A CleaningError is raised instead of a BlockDeviceEraseError because
        # the error was with the cleaning finding the block device rather than
        # actually erasing an existing block device.
        self.assertRaises(errors.CleaningError,
                          self.hardware.erase_block_device,
                          self.block_device)

        self.assertEqual(0, mocked_execute.call_count)

    @mock.patch.object(os.path, 'realpath')
    @mock.patch.object(utils, 'execute')
    def test_erase_block_device_lsi_error(self,
                                          mocked_execute,
                                          mocked_realpath):
        self.hardware._list_lsi_devices = mock.Mock()
        self.hardware._list_lsi_devices.return_value = self.FAKE_DEVICES

        mocked_realpath.return_value = ('/sys/devices/pci0000:00/0000:00:02.0'
            '/0000:02:00.0/host3/target3:1:0/3:1:0:0/block/sdb')

        # Presumably it doesn't print success on an error
        error_output = DDOEMCLI_LISTALL_OUT.replace(
            'WarpDrive format successfully completed.',
            'Something went terribly, terribly wrong.')

        mocked_execute.return_value = (error_output, '')
        self.assertRaises(errors.BlockDeviceEraseError,
                          self.hardware.erase_block_device,
                          self.block_device)

        mocked_execute.assert_called_once_with(
            onmetal_hardware_manager.DDOEMCLI,
            '-c', '1', '-format', '-op', '-level', 'nom', '-s'),

    @mock.patch('ironic_python_agent.hardware.GenericHardwareManager'
                '.erase_block_device')
    @mock.patch.object(utils, 'execute')
    def test_erase_block_device_defer_to_generic(self,
                                                 mocked_execute,
                                                 mocked_generic):

        self.block_device.model = 'NormalSSD'
        self.hardware.erase_block_device(self.block_device)

        self.assertEqual(0, mocked_execute.call_count)
        mocked_generic.assert_called_once_with(self.block_device)

    @mock.patch.object(utils, 'execute')
    def test_update_warpdrive_firmware_upgrade_both(self, mocked_execute):
        self.FAKE_DEVICES[0]['version'] = '11.00.00.00'
        self.FAKE_DEVICES[1]['version'] = '11.00.00.00'

        self.hardware._list_lsi_devices = mock.Mock()
        self.hardware._list_lsi_devices.return_value = self.FAKE_DEVICES
        self.hardware.update_warpdrive_firmware({}, [])
        mocked_execute.assert_has_calls([
            mock.call(
                onmetal_hardware_manager.DDOEMCLI, '-c', '1', '-f',
                os.path.join(onmetal_hardware_manager.LSI_WARPDRIVE_DIR,
                             onmetal_hardware_manager.LSI_FIRMWARE_PREFLASH),
                check_exit_code=[0]),
            mock.call(
                onmetal_hardware_manager.DDOEMCLI, '-c', '1', '-updatepkg',
                os.path.join(onmetal_hardware_manager.LSI_WARPDRIVE_DIR,
                             onmetal_hardware_manager.LSI_FIRMWARE_PACKAGE),
                check_exit_code=[0]),
            mock.call(
                onmetal_hardware_manager.DDOEMCLI, '-c', '2', '-f',
                os.path.join(onmetal_hardware_manager.LSI_WARPDRIVE_DIR,
                             onmetal_hardware_manager.LSI_FIRMWARE_PREFLASH),
                check_exit_code=[0]),
            mock.call(
                onmetal_hardware_manager.DDOEMCLI, '-c', '2', '-updatepkg',
                os.path.join(onmetal_hardware_manager.LSI_WARPDRIVE_DIR,
                             onmetal_hardware_manager.LSI_FIRMWARE_PACKAGE),
                check_exit_code=[0]),
        ])

    @mock.patch.object(utils, 'execute')
    def test_update_warpdrive_firmware_upgrade_one(self, mocked_execute):
        self.FAKE_DEVICES[1]['version'] = '11.00.00.00'

        self.hardware._list_lsi_devices = mock.Mock()
        self.hardware._list_lsi_devices.return_value = self.FAKE_DEVICES
        self.hardware.update_warpdrive_firmware({}, [])
        mocked_execute.assert_has_calls([
            mock.call(
                onmetal_hardware_manager.DDOEMCLI, '-c', '2', '-f',
                os.path.join(onmetal_hardware_manager.LSI_WARPDRIVE_DIR,
                             onmetal_hardware_manager.LSI_FIRMWARE_PREFLASH),
                check_exit_code=[0]),
            mock.call(
                onmetal_hardware_manager.DDOEMCLI, '-c', '2', '-updatepkg',
                os.path.join(onmetal_hardware_manager.LSI_WARPDRIVE_DIR,
                             onmetal_hardware_manager.LSI_FIRMWARE_PACKAGE),
                check_exit_code=[0])
        ])

    @mock.patch.object(utils, 'execute')
    def test_update_warpdrive_firmware_same_version(self, mocked_execute):
        self.hardware._list_lsi_devices = mock.Mock()
        self.hardware._list_lsi_devices.return_value = self.FAKE_DEVICES
        self.hardware.update_warpdrive_firmware({}, [])
        self.assertEqual(0, mocked_execute.call_count)

    @mock.patch.object(utils, 'execute')
    def test_remove_bootloader(self, mocked_execute):
        self.hardware.get_os_install_device = mock.Mock()
        self.hardware.get_os_install_device.return_value = '/dev/hdz'
        self.hardware.remove_bootloader({}, [])

        mocked_execute.assert_called_once_with(
            'dd',
            'if=/dev/zero',
            'of=/dev/hdz',
            'bs=1M',
            'count=1',
            check_exit_code=[0])

    @mock.patch.object(utils, 'execute')
    def test__get_smartctl_attributes(self, mocked_execute):
        expected = SMARTCTL_ATTRIBUTES

        mocked_execute.return_value = (SMARTCTL_ATTRIBUTES_OUT, '')
        self.block_device = hardware.BlockDevice('/dev/sda', '32G MLC SATADOM',
                                                 31016853504, False)
        actual = self.hardware._get_smartctl_attributes(self.block_device)

        mocked_execute.assert_called_once_with(
            'smartctl',
            '--attributes',
            '/dev/sda')

        self.assertEqual(expected, actual)

    @mock.patch.object(utils, 'execute')
    def test__get_warpdrive_attributes(self, mocked_execute):
        expected = WARPDRIVE_ATTRIBUTES

        self.hardware._get_warpdrive_card = mock.Mock()
        self.hardware._get_warpdrive_card.return_value = {'id': '1'}

        mocked_execute.return_value = (DDOEMCLI_HEALTH_OUT, '')
        actual = self.hardware._get_warpdrive_attributes(self.block_device)

        mocked_execute.assert_called_once_with(
                onmetal_hardware_manager.DDOEMCLI,
                '-c', '1', '-health')

        self.assertEqual(expected, actual)

    def test_get_disk_metrics(self):
        self.hardware._send_gauges = mock.Mock()
        self.hardware.list_block_devices = mock.Mock()
        self.hardware.list_block_devices.return_value = [
                hardware.BlockDevice(
                    '/dev/sdb', '32G MLC SATADOM', 31016853504, False),
                self.block_device]

        self.hardware._get_warpdrive_attributes = mock.Mock()
        self.hardware._get_warpdrive_attributes.return_value = (
                WARPDRIVE_ATTRIBUTES)

        self.hardware._get_smartctl_attributes = mock.Mock()
        self.hardware._get_smartctl_attributes.return_value = (
                SMARTCTL_ATTRIBUTES)

        # get_disk_metrics is forced to take 2 additional arguments for node
        # and ports by IPA
        node = mock.Mock()
        ports = mock.Mock()
        self.hardware.get_disk_metrics(node, ports)

        self.hardware._send_gauges.assert_has_calls([
            mock.call('smartdata_sdb_32GMLCSATADOM', {
                '9-Power_On_Hours.VALUE': '100',
                '9-Power_On_Hours.WORST': '100',
                '9-Power_On_Hours.RAW_VALUE': '1673',
                '12-Power_Cycle_Count.VALUE': '100',
                '12-Power_Cycle_Count.WORST': '100',
                '12-Power_Cycle_Count.RAW_VALUE': '68',
                '169-Unknown_Attribute.VALUE': '100',
                '169-Unknown_Attribute.WORST': '100',
                '169-Unknown_Attribute.RAW_VALUE': '262144',
                '173-Unknown_Attribute.VALUE': '199',
                '173-Unknown_Attribute.WORST': '199',
                '173-Unknown_Attribute.RAW_VALUE': '262146',
                '194-Temperature_Celsius.VALUE': '100',
                '194-Temperature_Celsius.WORST': '100',
                '194-Temperature_Celsius.RAW_VALUE': '40',
            }),
            mock.call('smartdata_sda_NWD-BLP4-1600', {
                '6_FL00AVPL.Power-OnHours': '957.5',
                '5_FL00AV3L.UncorrectableRAISEErrors': '0',
                '4_FL00AV2L.TotalWritesFromHost': '7',
                '7_FL00ATTV.EraseFailCount1': '0',
                '5_FL00AV3L.MaximumLifetimeTemperature': '82',
                '4_FL00AV2L.RetiredBlockCount': '0',
                '5_FL00AV3L.ProgramFailCount': '0',
                '5_FL00AV3L.TotalWritesFromHost': '7',
                '6_FL00AVPL.MaximumLifetimeTemperature': '79',
                '6_FL00AVPL.WriteAmplification': '1.29',
                '4_FL00AV2L.GigabytesErased': '329',
                '4_FL00AV2L.MaximumLifetimeTemperature': '82',
                '7_FL00ATTV.ReservedBlocksRemaining': '100',
                '7_FL00ATTV.I_OErrorDetectionCodeRate': '0',
                '6_FL00AVPL.DevicePowerCycleCount': '45',
                '7_FL00ATTV.TotalWritesFromHost': '7936',
                '5_FL00AV3L.Power-OnHours': '957.5',
                '7_FL00ATTV.Power-OnHours': '975.8',
                '7_FL00ATTV.GigabytesErased': '9125',
                '4_FL00AV2L.ProgramFailCount': '0',
                '6_FL00AVPL.EraseFailCount1': '0',
                '6_FL00AVPL.TotalWritesFromHost': '7',
                '5_FL00AV3L.I_OErrorDetectionCodeRate': '0',
                '7_FL00ATTV.MaximumLifetimeTemperature': '79',
                '6_FL00AVPL.I_OErrorDetectionCodeRate': '0',
                '4_FL00AV2L.TrimCount': '0',
                '6_FL00AVPL.TrimCount': '0',
                '4_FL00AV2L.UnexpectedPowerLossCount': '56',
                '4_FL00AV2L.Power-OnHours': '957.6',
                '6_FL00AVPL.RetiredBlockCount': '0',
                '7_FL00ATTV.TrimCount': '0',
                '5_FL00AV3L.GigabytesErased': '289',
                '6_FL00AVPL.TotalReadsToHost': '0',
                '4_FL00AV2L.ReservedBlocksRemaining': '100',
                '7_FL00ATTV.UncorrectableRAISEErrors': '0',
                '7_FL00ATTV.RetiredBlockCount': '0',
                '7_FL00ATTV.Reserved_over-provisioned_Blocks': '31488',
                '6_FL00AVPL.ProgramFailCount': '0',
                '5_FL00AV3L.SSDLifeLeft_PECycles_': '100',
                '7_FL00ATTV.WriteAmplification': '1.02',
                '6_FL00AVPL.ReservedBlocksRemaining': '100',
                '5_FL00AV3L.TotalReadsToHost': '0',
                '4_FL00AV2L.WriteAmplification': '1.29',
                '6_FL00AVPL.Reserved_over-provisioned_Blocks': '30848',
                '6_FL00AVPL.UnexpectedPowerLossCount': '48',
                '5_FL00AV3L.WriteAmplification': '1.29',
                '6_FL00AVPL.UncorrectableRAISEErrors': '0',
                '5_FL00AV3L.Reserved_over-provisioned_Blocks': '31232',
                '5_FL00AV3L.DevicePowerCycleCount': '47',
                '7_FL00ATTV.DevicePowerCycleCount': '74',
                '6_FL00AVPL.SSDLifeLeft_PECycles_': '100',
                '4_FL00AV2L.Reserved_over-provisioned_Blocks': '32128',
                '5_FL00AV3L.TrimCount': '0',
                '5_FL00AV3L.RetiredBlockCount': '0',
                '7_FL00ATTV.UnexpectedPowerLossCount': '89',
                '4_FL00AV2L.I_OErrorDetectionCodeRate': '0',
                '4_FL00AV2L.UncorrectableRAISEErrors': '0',
                '5_FL00AV3L.EraseFailCount1': '0',
                '7_FL00ATTV.ProgramFailCount': '0',
                '6_FL00AVPL.GigabytesErased': '262',
                '4_FL00AV2L.EraseFailCount1': '0',
                '4_FL00AV2L.SSDLifeLeft_PECycles_': '100',
                '5_FL00AV3L.ReservedBlocksRemaining': '100',
                '7_FL00ATTV.SSDLifeLeft_PECycles_': '100',
                '4_FL00AV2L.DevicePowerCycleCount': '49',
                '4_FL00AV2L.TotalReadsToHost': '0',
                '7_FL00ATTV.TotalReadsToHost': '1228',
                '5_FL00AV3L.UnexpectedPowerLossCount': '52'})
            ])

    def test_verify_blockdevice_count_io_pass(self):
        self.hardware._get_flavor_from_node = mock.Mock()
        self.hardware._get_flavor_from_node.return_value = 'onmetal-io1'
        self.hardware.list_block_devices = mock.Mock()
        self.hardware.list_block_devices.return_value = [
            hardware.BlockDevice('/dev/sda', 'NWD-BLP4-1600', 1073741824,
                                 False),
            hardware.BlockDevice('/dev/sdb', 'NWD-BLP4-1600', 1073741824,
                                 False),
            hardware.BlockDevice('/dev/sdc', '32G MLC SATADOM', 33554432,
                                 False)]

        self.hardware.verify_hardware({}, [])

    def test_verify_blockdevice_count_io_missing_warpdrive(self):
        self.hardware._get_flavor_from_node = mock.Mock()
        self.hardware._get_flavor_from_node.return_value = 'onmetal-io1'
        self.hardware.list_block_devices = mock.Mock()
        self.hardware.list_block_devices.return_value = [
            hardware.BlockDevice('/dev/sda', 'NWD-BLP4-1600', 1073741824,
                                 False),
            hardware.BlockDevice('/dev/sdb', '32G MLC SATADOM', 33554432,
                                 False)]

        self.assertRaises(errors.CleaningError,
                          self.hardware.verify_hardware, {}, [])

    def test_verify_blockdevice_count_io_missing_satadom(self):
        self.hardware._get_flavor_from_node = mock.Mock()
        self.hardware._get_flavor_from_node.return_value = 'onmetal-io1'
        self.hardware.list_block_devices = mock.Mock()
        self.hardware.list_block_devices.return_value = [
            hardware.BlockDevice('/dev/sda', 'NWD-BLP4-1600', 1073741824,
                                 False),
            hardware.BlockDevice('/dev/sdb', 'NWD-BLP4-1600', 1073741824,
                                 False)]

        self.assertRaises(errors.CleaningError,
                          self.hardware.verify_hardware, {}, [])

    def test_verify_blockdevice_count_missing_satadom(self):
        self.hardware._get_flavor_from_node = mock.Mock()
        self.hardware._get_flavor_from_node.return_value = 'onmetal-compute1'
        self.hardware.list_block_devices = mock.Mock()
        self.hardware.list_block_devices.return_value = []

        self.assertRaises(errors.CleaningError,
                          self.hardware.verify_hardware, {}, [])

    def test_verify_blockdevice_count_pass(self):
        self.hardware._get_flavor_from_node = mock.Mock()
        self.hardware._get_flavor_from_node.return_value = 'onmetal-compute1'
        self.hardware.list_block_devices = mock.Mock()
        self.hardware.list_block_devices.return_value = [
                hardware.BlockDevice('/dev/sda', '32G MLC SATADOM', 33554432,
                                     False)]

        self.hardware.verify_hardware({}, [])


class TestOnMetalVerifyPorts(test_base.BaseTestCase):
    def setUp(self):
        super(TestOnMetalVerifyPorts, self).setUp()
        self.hardware = onmetal_hardware_manager.OnMetalHardwareManager()
        self.interfaces = [
            hardware.NetworkInterface('eth0', 'aa:bb:cc:dd:ee:ff'),
            hardware.NetworkInterface('eth1', 'ff:ee:dd:cc:bb:aa')]
        self.lldp_info = {
            'eth0': [
                # Chassis ID
                (1, 'switch1'),
                # Port ID
                (2, '\x05Ethernet1/1'),
                # TTL
                (3, '\x00x'),
                # Port Description
                (4, 'port1'),
                # System Name
                (5, 'switch1'),
            ],
            'eth1': [
                (1, 'switch2'),
                (2, '\x05Ethernet2/1'),
                (3, '\x00x'),
                (4, 'port2'),
                (5, 'switch2'),
            ]
        }

        self.node = {
            'extra': {
                'hardware/interfaces/0/mac_address': 'aa:bb:cc:dd:ee:ff',
                'hardware/interfaces/0/name': 'eth0',
                'hardware/interfaces/0/switch_chassis_id': 'switch1',
                'hardware/interfaces/0/switch_port_id': 'Eth1/1',
                'hardware/interfaces/1/mac_address': 'ff:ee:dd:cc:bb:aa',
                'hardware/interfaces/1/name': 'eth1',
                'hardware/interfaces/1/switch_chassis_id': 'switch2',
                'hardware/interfaces/1/switch_port_id': 'Eth2/1',
            }
        }

        self.ports = [
            {
                'address': 'aa:bb:cc:dd:ee:ff',
                'extra': {
                    'chassis': 'switch1',
                    'port': 'Eth1/1'
                }
            },
            {
                'address': 'ff:ee:dd:cc:bb:aa',
                'extra': {
                    'chassis': 'switch2',
                    'port': 'Eth2/1'
                }
            }
        ]

        self.netiface = {
            17: [{'broadcast': 'ff:ff:ff:ff:ff:ff',
                  'addr': 'aa:bb:cc:dd:ee:ff'}],
            2: [{'broadcast': '10.0.0.255',
                 'netmask': '255.255.255.0',
                 'addr': '10.0.0.2'}],
            10: [{'netmask': 'ffff:ffff:ffff:ffff::',
                  'addr': '2001:4802:7801:102:be76:4eff:fe20:67ae'},
                 {'netmask': 'ffff:ffff:ffff:ffff::',
                  'addr': 'fe80::be76:4eff:fe20:67ae%eth0'}]
        }

        self.port_tuples = set([('switch2', 'eth2/1'), ('switch1', 'eth1/1')])

    @mock.patch('onmetal_ironic_hardware_manager.OnMetalHardwareManager.'
                '_get_node_switchports')
    @mock.patch('onmetal_ironic_hardware_manager.OnMetalHardwareManager.'
                '_get_port_from_lldp')
    @mock.patch('ironic_python_agent.netutils.get_lldp_info')
    @mock.patch('onmetal_ironic_hardware_manager.OnMetalHardwareManager.'
                'list_network_interfaces')
    def test_verify_ports(self, list_mock, lldp_mock,
                          lldp_ports_mock, node_ports_mock):
        list_mock.return_value = self.interfaces
        lldp_mock.return_value = {
            'eth0': self.lldp_info['eth0'],
            'eth1': self.lldp_info['eth1']
        }

        node_ports_mock.return_value = self.port_tuples
        lldp_ports_mock.side_effect = [
            ('switch1', 'eth1/1'),
            ('switch2', 'eth2/1')
        ]

        self.hardware.verify_ports(self.node, self.ports)

    @mock.patch('onmetal_ironic_hardware_manager.OnMetalHardwareManager.'
                '_get_node_switchports')
    @mock.patch('onmetal_ironic_hardware_manager.OnMetalHardwareManager.'
                '_get_port_from_lldp')
    @mock.patch('ironic_python_agent.netutils.get_lldp_info')
    @mock.patch('onmetal_ironic_hardware_manager.OnMetalHardwareManager.'
                'list_network_interfaces')
    def test_verify_ports_mismatch(self, list_mock, lldp_mock,
                                   lldp_ports_mock, node_ports_mock):
        list_mock.return_value = self.interfaces
        lldp_mock.return_value = {
            'eth0': self.lldp_info['eth0'],
            'eth1': self.lldp_info['eth1']
        }

        node_ports_mock.return_value = self.port_tuples
        lldp_ports_mock.side_effect = [
            ('switch1', 'Eth1/2'),  # mismatch port
            ('switch2', 'Eth2/1')
        ]

        self.assertRaises(errors.CleaningError,
                          self.hardware.verify_ports,
                          self.node,
                          self.ports)

    @mock.patch('onmetal_ironic_hardware_manager.OnMetalHardwareManager.'
                '_get_node_switchports')
    @mock.patch('onmetal_ironic_hardware_manager.OnMetalHardwareManager.'
                '_get_port_from_lldp')
    @mock.patch('ironic_python_agent.netutils.get_lldp_info')
    @mock.patch('onmetal_ironic_hardware_manager.OnMetalHardwareManager.'
                'list_network_interfaces')
    def test_verify_ports_unmatched(self, list_mock, lldp_mock,
                                    lldp_ports_mock, node_ports_mock):
        list_mock.return_value = self.interfaces
        # Node has more ports than detected
        lldp_mock.return_value = {
            'eth0': self.lldp_info['eth0'],
        }

        node_ports_mock.return_value = self.port_tuples
        lldp_ports_mock.side_effect = [
            ('switch1', 'Eth1/1'),
        ]

        self.assertRaises(errors.CleaningError,
                          self.hardware.verify_ports,
                          self.node,
                          self.ports)

    def test__get_tlv_malformed(self):
        self.lldp_info['eth0'][0] = ('bad tlv',)
        self.assertRaises(errors.CleaningError,
                          self.hardware._get_tlv,
                          1,
                          self.lldp_info['eth0'])

    def test__get_port_from_lldp(self):
        expected_ports = ('switch1', 'eth1/1')
        ports = self.hardware._get_port_from_lldp(self.lldp_info['eth0'])
        self.assertEqual(expected_ports, ports)

    def test__get_node_switchports(self):
        expected_ports = set([('switch2', 'eth2/1'), ('switch1', 'eth1/1')])
        ports = self.hardware._get_node_switchports(self.node, self.ports)
        self.assertEqual(expected_ports, ports)
