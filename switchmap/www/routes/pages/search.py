"""Module of switchmap.webserver routes.

Contains all routes that switchmap.s Flask webserver uses

"""
# Flask imports
from flask import Blueprint, render_template, request

# Switchmap-NG imports
from switchmap.main.search import Search
from switchmap.www.pages.device import Device
from switchmap.www import CONFIG

# Define the SEARCH global variable
SEARCH = Blueprint('SEARCH', __name__)


@SEARCH.route('/search', methods=['POST'])
def index():
    """Function for creating search results.

    Args:
        None

    Returns:
        HTML

    """
    # Initialize key variables
    devices_tables = {'Not Found': '<h3>&nbsp;Please try again ...</h3>'}
    devices = {}

    # Get search form data
    items = request.form

    for key, value in items.items():
        # (key, value) = item
        if key == 'search_term':
            search_term = value.strip()

            # Create the search list
            search = Search(search_term)
            result = search.find()

            # Create result dict
            for item in result:
                # Create a list of devices for port table generation
                for hostname, ifindex in item.items():
                    if hostname in devices:
                        devices[hostname].append(ifindex)
                    else:
                        devices[hostname] = [ifindex]

            if bool(devices) is True:
                devices_tables = {}

                for hostname, ifindexes in sorted(devices.items()):
                    # Create data table dict
                    device_object = Device(
                        CONFIG, hostname, ifindexes=ifindexes)
                    port_table = device_object.ports()
                    devices_tables[hostname] = port_table

    # Present results
    return render_template(
        'search.html',
        results_dict=devices_tables)
