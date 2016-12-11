#!/usr/bin/env python3
"""Infoset ingest cache daemon.

Extracts agent data from cache directory files.

"""

# Standard libraries
import sys
import os
import tempfile
from multiprocessing import Pool


# switchmap.libraries
try:
    from switchmap.agents import agent as Agent
except:
    print('You need to set your PYTHONPATH to include the switchmap.library')
    sys.exit(2)
from switchmap.utils import configuration
from switchmap.utils import general
from switchmap.utils import log
from switchmap.snmp import snmp_info
from switchmap.snmp import snmp_manager


class PollingAgent(object):
    """Infoset agent that gathers data.

    Args:
        None

    Returns:
        None

    Functions:
        __init__:
        populate:
        post:
    """

    def __init__(self):
        """Method initializing the class.

        Args:
            config_dir: Configuration directory

        Returns:
            None

        """
        # Initialize key variables
        self.agent_name = 'topology'

        # Get configuration
        self.server_config = configuration.Config()
        self.snmp_config = configuration.ConfigSNMP()

        # Cleanup, move temporary files to clean permanent directory.
        # Delete temporary directory
        cache_directory = self.server_config.cache_directory()
        if os.path.isdir(cache_directory):
            general.delete_files(cache_directory)
        else:
            os.makedirs(cache_directory, 0o755)

    def name(self):
        """Return agent name.

        Args:
            None

        Returns:
            value: Name of agent

        """
        # Return
        value = self.agent_name
        return value

    def query(self):
        """Query all remote hosts for data.

        Args:
            None

        Returns:
            None

        """
        # Initialize key variables
        delay = 3600

        # Post data to the remote server
        while True:
            # Poll after sleeping
            poll_devices()

            # Sleep for "delay" seconds
            Agent.agent_sleep(self.name(), delay)


class Poller(object):
    """Infoset agent that gathers data.

    Args:
        None

    Returns:
        None

    Functions:
        __init__:
        populate:
        post:
    """

    def __init__(self, hostname):
        """Method initializing the class.

        Args:
            hostname: Hostname to poll
            perm_dir: Directory where permanent YAML files should reside.

        Returns:
            None

        """
        # Initialize key variables
        self.server_config = configuration.Config()
        snmp_config = configuration.ConfigSNMP()
        self.hostname = hostname

        # Get snmp configuration information from infoset
        validate = snmp_manager.Validate(hostname, snmp_config.snmp_auth())
        self.snmp_params = validate.credentials()
        self.snmp_object = snmp_manager.Interact(self.snmp_params)

    def query(self):
        """Query all remote hosts for data.

        Args:
            None

        Returns:
            None

        """
        # Check SNMP supported
        if bool(self.snmp_params) is True:
            # Get datapoints
            self._create_yaml()
        else:
            log_message = (
                'Uncontactable host %s or no valid SNMP '
                'credentials found for it.') % (self.hostname)
            log.log2info(1021, log_message)

    def _create_yaml(self):
        """Create the master dictionary for the host.

        Args:
            None
        Returns:
            value: Index value

        """
        # Initialize key variables
        temp_dir = tempfile.mkdtemp()
        temp_file = ('%s/%s.yaml') % (temp_dir, self.hostname)
        perm_file = self.server_config.topology_device_file(self.hostname)

        # Get data
        log_message = (
            'Querying topology data from host %s.'
            '') % (self.hostname)
        log.log2info(1125, log_message)

        # Create YAML file by polling device
        status = snmp_info.Query(self.snmp_object)
        data = status.everything()
        yaml_string = general.dict2yaml(data)

        # Dump data
        with open(temp_file, 'w') as file_handle:
            file_handle.write(yaml_string)

        # Get data
        log_message = (
            'Completed topology query from host %s.'
            '') % (self.hostname)
        log.log2info(1019, log_message)

        # Clean up files
        os.rename(temp_file, perm_file)
        os.rmdir(temp_dir)


def poll_devices():
    """Poll all devices for data using subprocesses and create YAML files.

    Args:
        None

    Returns:
        None

    """
    # Get configuration
    config = configuration.Config()

    # Get the number of threads to use in the pool
    threads_in_pool = config.agent_threads()

    # Create a list of polling objects
    hostnames = config.hostnames()

    # Create a pool of sub process resources
    with Pool(processes=threads_in_pool) as pool:

        # Create sub processes from the pool
        pool.map(poll_single_device, hostnames)


def poll_single_device(hostname):
    """Poll single device for data and create YAML files.

    Args:
        None

    Returns:
        None

    """
    # Get configuration
    poller = Poller(hostname)
    poller.query()


def main():
    """Start the switchmap.agent.

    Args:
        None

    Returns:
        None

    """
    # Get configuration
    cli = Agent.AgentCLI()
    poller = PollingAgent()

    # Do control
    cli.control(poller)

if __name__ == "__main__":
    main()
