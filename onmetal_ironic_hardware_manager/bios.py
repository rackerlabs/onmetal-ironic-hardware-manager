# Copyright 2015 Rackspace, Inc.
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

from ironic_python_agent.common import metrics
from ironic_python_agent import hardware
from ironic_python_agent import utils

from oslo_log import log


# Directory that all BIOS utilities are located in
BIOS_DIR = '/mnt/f03b_bios/quanta_A14'

LOG = log.getLogger()


class QuantaF03BBIOSHardwareManager(hardware.HardwareManager):
    # This should be incremented at every upgrade to avoid making the agent
    # change which hardware manager it uses when cleaning in the middle of a
    # hardware manager upgrade.
    HARDWARE_MANAGER_VERSION = '1'

    def evaluate_hardware_support(cls):
        # TODO(JoshNang) inspect hardware to ensure this has a BIOS we can
        # flash
        return hardware.HardwareSupport.SERVICE_PROVIDER

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
        return [
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
                'step': 'customer_bios_settings',
                'interface': 'deploy',
                'priority': 30,
                'reboot_requested': True,
            },
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

    @metrics.instrument(__name__, 'upgrade_bios')
    def upgrade_bios(self, node, ports):
        driver_info = node.get('driver_info', {})
        LOG.info('Update BIOS called with %s' % driver_info)
        cmd = os.path.join(BIOS_DIR, 'flash_bios.sh')
        utils.execute(cmd, check_exit_code=[0])
        return True
