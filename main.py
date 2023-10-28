import requests
import subprocess
import os
import re
import random
import configparser


# Main function for pulling webpage
def main():
    # ------------------ PARSE CONFIG ---------------------- #
    # Before we start, parse the config file
    config = configparser.ConfigParser()
    file = config.read('server_target.cfg')
    if not file:
        raise Exception('python3: Failed to read config file')

    country_code = config.get('CONFIG', 'country')
    country_code = strip_quotes(country_code)

    protocol = config.get('CONFIG', 'protocol')
    protocol = strip_quotes(protocol)

    nord_user = config.get('CONFIG', 'nord_user')
    nord_user = strip_quotes(nord_user)

    nord_pass = config.get('CONFIG','nord_pass')
    nord_pass = strip_quotes(nord_pass)
    # ---------------------------------------------------- #


    # -------------- DOWNLOAD THE OVPN FILE -------------- #
    print('\n')
    print("python3: Downloading random ovpn config")

    # First execute the bash script
    script_result = exec_server_find(country_code)

    # There is an error where the script won't catch the results correctly.
    # This results in an output string with no characters. If this happens just re-run
    while script_result.__len__() <= 0:
        print("python3: FAILOVER")
        script_result = exec_server_find(country_code)

    print("python3: Found")

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
        print("python3: nordvpn-server-find failed to respond")

    # Finally download the ovpn config file
    download(url)

    # Done
    print("python3: Downloaded ovpn server config for: " + vpn_server_addresses[i])

    # -------------- KILL DAEMON -------------- #
    # Kill any running openvpn daemon before we start a new openvpn daemon
    print("python3: Init killing openVPN daemon")
    exec_stop_daemon()

    # -------------- APPLY THE OVPN CONFIG FILE -------------- #
    print('\n')
    print("python3: Init starting daemon")
    # Exec script
    exec_start_daemon(nord_user, nord_pass)

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

    # Run Script, and capture stdout, ignore std error
    print("python3: Start subprocess \n")
    r = subprocess.run(['./nordvpn-server-find.sh', '-l', location], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)

    # Change back working dir
    os.chdir(wd)

    # Check codes
    if r.returncode == 1:
        raise BrokenPipeError("python3: Something went wrong with the bash script. Check your country code. Raising error:")
    elif r.returncode == 0:
        # Decode to string
        out = r.stdout.decode('utf-8')

        # Alert user to results of script
        print('\n')
        print("BASH ./nordvpn-server-find-master.sh: \n"+ out)

        # Output the results
        return out
    else:
        # The code block should not be read.
        raise ProcessLookupError("python3: final else case triggered in exec_server_find() somehow.")


def exec_start_daemon(user, paswd):
    """
    Sets up and runs the ./start-openVPN.sh bash script to stop openVPN daemons
    params:
        user: string value with dVPN username
        paswd: string value with VPN password
    """
    # Set up file path
    wd = os.getcwd()
    bd = "/start-stop-OpenVPN"  # bd -> bash directory
    bd = wd + bd

    # Change dir
    os.chdir(bd)

    # Run script
    r = subprocess.run(['./start-openVPN.sh', user, paswd], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    if r.returncode == 1:
        print("python3: Something went wrong starting the daemon. Is openvpn installed?")
        raise BrokenPipeError("script exited with returncode 1")

    # Change dir back and return
    os.chdir(wd)

    print('\n')
    print("BASH ./start-openVPN.sh: \n"+r.stdout.decode('utf-8'))

    return 0


def exec_stop_daemon():
    """
    Sets up and runs the ./stop-openVPN.sh bash script to stop openVPN daemons
    """
    # Set up file path
    wd = os.getcwd()
    bd = "/start-stop-OpenVPN"  # bd -> bash directory
    bd = wd + bd

    # Change dir
    os.chdir(bd)

    # Run Script, and capture stdout, ignore std error
    r = subprocess.run(['./stop-openVPN.sh'], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    if r.returncode == 1:
        print("python3: Something went wrong stopping the daemon. Is openvpn installed?")
        raise BrokenPipeError("script exited with returncode 1")

    # Change dir back and return
    os.chdir(wd)

    print('\n')
    print("BASH ./stop-OpenVPN.sh: \n"+ r.stdout.decode('utf-8'))

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
        raise SyntaxError("python3: invalid input for the protocol: input \'tcp\' or \'udp\'")

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
    arg:
        result: is to be a string
    """
    output = re.findall(r"([a-z]{2}[0-9]+\.nordvpn\.com)", result)  # This regex finds the server address
    return output


def strip_quotes(str):
    """
    Strips ' and " characters from the input string, str
    """
    return str.strip('\'\"')

# Execute python code
main()
