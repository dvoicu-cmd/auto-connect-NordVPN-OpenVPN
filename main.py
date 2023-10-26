import requests
import subprocess
import os
import re
import random
import configparser


# Main function for pulling webpage
def main():
    # Before we start, parse the config file
    config = configparser.ConfigParser()
    file = config.read('server_target.cfg')
    if not file:
        raise Exception('Failed to read config file')

    country_code = config.get('CONFIG', 'country')
    country_code = country_code.strip('\'\"')

    protocol = config.get('CONFIG', 'protocol')
    protocol = protocol.strip('\'\"')

    # --- DOWNLOAD THE OVPN FILE --- #
    print("downloading random ovpn config")

    # First execute the bash script
    script_result = exec_bash_script(country_code)
    # There is an error where the script won't catch the results correctly.
    # This results in an output string with no characters. If this happens just re-run
    while script_result.__len__() <= 0:
        script_result = exec_bash_script(country_code)

    # Second, put result into a list
    vpn_server_addresses = vpn_list(script_result)

    # Third, shuffle the list of vpn servers
    random.shuffle(vpn_server_addresses)

    # Fourth, get the link for the download address
    i = random.randrange(0, 19)
    url = ""
    try:
        url = get_download_link(vpn_server_addresses[i], protocol)
    except IndexError:  # Just in case my fix does not work for the bash script
        print("nordvpn-server-find failed to respond")

    # Finally download the ovpn config file
    download(url)

    # Done
    print("Downloaded ovpn server config for: " + vpn_server_addresses[i])

    # --- APPLY THE OVPN CONFIG FILE --- #




    return 0


def exec_bash_script(location):
    """
    Executes the bash script for finding a nordvpn server address
    """
    # First change working dir
    wd = os.getcwd()
    bd = "/nordvpn-server-find-master"  # Bash directory
    bd = wd + bd
    os.chdir(bd)

    # Run Script
    r = subprocess.run(['./nordvpn-server-find.sh', '-l', location], capture_output=True)

    # Change back
    os.chdir(wd)
    if r.returncode == 1:
        raise SyntaxError(r.stdout)
    elif r.returncode == 0:
        return r.stdout
    else:
        return "That ain't right"


def vpn_list(result):
    """
    Makes a python list of the vpn servers found
    """
    decompile = result.decode()
    output = re.findall(r"([a-z]{2}[0-9]+\.nordvpn\.com)", decompile) # This regex finds the server address
    return output


def get_download_link(link, protocol):
    """
    Gets the associated openvpn download link to the associated server link
    param: protocol = 'udp' || 'tcp' else err
    """
    # append the protocol for download link
    search = link
    if protocol.__eq__('udp'):
        search = search + '.udp1194.ovpn'
    elif protocol.__eq__('tcp'):
        search = search + '.tcp443.ovpn'
    else:
        raise SyntaxError("invalid input for the protocol: input \'tcp\' or \'udp\'")

    # hard code the server dir
    servers_dir = "https://downloads.nordcdn.com/configs/files/ovpn_legacy/servers/"

    # output download link
    output = servers_dir + search
    return output


def download(url):
    """
    Sends a request to download from a download link using python requests
    """
    req = requests.get(url, allow_redirects=True)
    try:
        open('saved-config-file/config.ovpn', 'wb').write(req.content)
    except: # If the file does not exist create it
        open('saved-config-file/config.ovpn', 'x')
        open('saved-config-file/config.ovpn', 'wb').write(req.content)

    return 0


# Execute python code
main()
