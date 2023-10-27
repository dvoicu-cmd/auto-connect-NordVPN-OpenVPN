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

    # ---------------------------------------------------- #
    country_code = config.get('CONFIG', 'country')
    country_code = strip_quotes(country_code)

    protocol = config.get('CONFIG', 'protocol')
    protocol = strip_quotes(protocol)

    nord_user = config.get('CONFIG', 'nord_user')
    nord_user = strip_quotes(nord_user)

    nord_pass = config.get('CONFIG','nord_pass')
    nord_pass = strip_quotes(nord_pass)
    # ---------------------------------------------------- #

    # -------------- KILL DAEMON -------------- #
    # Before starting the download, for safe measure, kill any running openvpn daemon
    print("Killing openVPN daemon")
    exec_start_stop_daemon(None,None, False)


    # -------------- DOWNLOAD THE OVPN FILE -------------- #
    print('\n')
    print("Downloading random ovpn config")

    # First execute the bash script
    script_result = exec_server_find(country_code)
    # There is an error where the script won't catch the results correctly.
    # This results in an output string with no characters. If this happens just re-run
    while script_result.__len__() <= 0:
        script_result = exec_server_find(country_code)

    # Second, put result into a list
    vpn_server_addresses = vpn_list(script_result)

    # Third, shuffle the list of vpn servers
    random.shuffle(vpn_server_addresses)

    # Fourth, get the link for the download address
    i = random.randrange(0, 19)
    url = None
    try:
        url = get_download_link(vpn_server_addresses[i], protocol)
    except IndexError:  # Just in case my fix does not work for the bash script
        print("nordvpn-server-find failed to respond")

    # Finally download the ovpn config file
    download(url)

    # Done
    print("Downloaded ovpn server config for: " + vpn_server_addresses[i])

    # -------------- APPLY THE OVPN CONFIG FILE -------------- #
    print('\n')
    print("Starting openvpn daemon")

    # Exec script
    exec_start_stop_daemon(nord_user, nord_pass, True)

    return 0


# ---------------- Functions ---------------- #

# ---- Bash execs --- #
# Functions involving a shell script
def exec_server_find(location):
    """
    Executes the bash script for finding a nordVPN server address
    """
    # First change working dir
    wd = os.getcwd()
    bd = "/nordvpn-server-find-master"  # Bash directory
    bd = wd + bd
    os.chdir(bd)

    # Run Script
    r = subprocess.run(['./nordvpn-server-find.sh', '-l', location], capture_output=True)

    # Change back working dir
    os.chdir(wd)

    # Check codes
    if r.returncode == 1:
        print("Something went wrong with the bash script. Check your country code. Raising error:")
        raise SyntaxError(r.stderr)
    elif r.returncode == 0:
        return r.stdout
    else:
        return "That ain't right"


def exec_start_stop_daemon(user, paswd, to_start):
    # Set up file path
    wd = os.getcwd()
    bd = "/start-stop-OpenVPN" # bd -> bash directory
    bd = wd + bd

    # Change dir
    os.chdir(bd)

    # Run script
    script = None
    r = None
    if to_start:
        script = './start-openVPN.sh'
        r = subprocess.run([script, user, paswd])
        if r.returncode == 1:
            print("Something went wrong starting the daemon")
            raise BrokenPipeError(r.stderr)
    else:
        script = './stop-openVPN.sh'
        r = subprocess.run([script])
        if r.returncode == 1:
            print("Something went wrong stopping the daemon")
            raise BrokenPipeError(r.stderr)

    # Change dir back and return
    os.chdir(wd)
    return 0


# ---- Web Requests ---- #
# Functions involving a web request

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

# ---- Formatting ---- #
# Functions involving formatting a string or data structure

def vpn_list(result):
    """
    Makes a python list of the vpn servers found
    """
    decompile = result.decode()
    output = re.findall(r"([a-z]{2}[0-9]+\.nordvpn\.com)", decompile) # This regex finds the server address
    return output


def strip_quotes(str):
    """
    Strips ' and " characters from string
    """
    return str.strip('\'\"')


# Execute python code
main()
