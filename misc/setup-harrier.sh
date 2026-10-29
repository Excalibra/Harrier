#!/bin/bash
# Harrier automated installation and configuration script
# Version: 2.0
#-----------------------------
# Formatting configuration
#-----------------------------
RED='\033[31m'
GREEN='\033[32m'
YELLOW='\033[33m'
BLUE='\033[34m'
RESET='\033[0m'
BOLD='\033[1m'

#-----------------------------
# Global variables
#-----------------------------
HARRIER_VERSION="2.0"
BASE_DIR="/opt"
HARRIER_DIR="$BASE_DIR/Harrier"
HARRIER_NPOC_DIR="$BASE_DIR/Harrier-NPoC"
GEO_DATA_DIR="/data/GeoLite2"

#-----------------------------
# Download URLs for third-party tools
#-----------------------------
# Harrier project repositories
HARRIER_REPO="https://github.com/Excalibra/Harrier"
# NPoC plugin package (kept at the original upstream author for now)
HARRIER_NPOC_REPO="https://github.com/Aabyss-Team/ARL-NPoC"

# Prebuilt third-party binaries hosted in this project's releases
# (adjust to wherever the wih/ncrack binaries are hosted)
BIN_RELEASE_URL="https://github.com/Excalibra/Harrier/releases/download/tools"

NUCLEI_URL="https://github.com/projectdiscovery/nuclei/releases/download/v3.3.9/nuclei_3.3.9_linux_amd64.zip"
NUCLEI_URL_CN="$NUCLEI_URL"

WIH_URL="$BIN_RELEASE_URL/wih_linux_amd64"
WIH_URL_CN="$WIH_URL"

NCRACK_URL="$BIN_RELEASE_URL/ncrack"
NCRACK_URL_CN="$NCRACK_URL"

NCRACK_SERVICES_URL="$BIN_RELEASE_URL/ncrack-services"
NCRACK_SERVICES_URL_CN="$NCRACK_SERVICES_URL"

# GeoLite2 databases require a MaxMind account/license key.
# Place GeoLite2-ASN.mmdb and GeoLite2-City.mmdb under /data/GeoLite2 manually,
# or set these variables to your own download URLs.
GEO_ASN_URL=""
GEO_CITY_URL=""
GEO_ASN_URL_CN=""
GEO_CITY_URL_CN=""

GET_PIP_SCRIPT="https://bootstrap.pypa.io/pip/3.6/get-pip.py"
GET_PIP_SCRIPT_CN="$GET_PIP_SCRIPT"

#-----------------------------
# Basic utility functions
#-----------------------------

# Print a colored message
color_echo() {
    local color="$1"
    shift
    echo -e "${color}${BOLD}$@${RESET}"
}
# Print a separator line
print_separator() {
    local char="${1:-=}"
    local length="${2:-60}"
    printf '%*s\n' "$length" | tr ' ' "$char"
}
# Check whether a command exists
check_command() {
    if ! command -v "$1" &> /dev/null; then
        color_echo $RED "Error: command '$1' not found, please install it first."
        exit 1
    fi
}
# Check and install a package (auto-detects the distribution)
install_package() {
    local package_name="$1"
    if ! command -v "$package_name" &> /dev/null; then
        color_echo $YELLOW "Installing $package_name ..."
        if [[ -f /etc/debian_version ]]; then
             # Debian/Ubuntu family
            sudo apt-get update && sudo apt-get install -y "$package_name"
        elif [[ -f /etc/redhat-release ]]; then
            # CentOS/RHEL family
            sudo yum install -y "$package_name"
        elif [[ -f /etc/fedora-release ]]; then
            # Fedora family
            sudo dnf install -y "$package_name"
        elif [[ -f /etc/arch-release ]]; then
            # Arch Linux family
            sudo pacman -S --noconfirm "$package_name"
        else
            color_echo $RED "Unsupported Linux distribution, please install $package_name manually."
            exit 1
        fi
        color_echo $GREEN "$package_name installation completed."
    else
        color_echo $GREEN "$package_name is already installed."
    fi
}
# Check and install git
check_and_install_git() {
    install_package git
}
# Install the management tool
manage_harrier() {
  local script_source="/opt/Harrier/misc/manage.sh" 
  local command_path="/usr/local/bin/harrier"     

  if [ ! -f "$command_path" ]; then
    color_echo "$YELLOW" "Installing the Harrier management panel..."

    # Use cp and chmod, and capture errors
    if cp "$script_source" "$command_path" && chmod +x "$command_path"; then
      color_echo "$YELLOW" "The Harrier management panel has been installed successfully"
      color_echo "$YELLOW" "Use the 'harrier' command to open the panel"
    else
      # Installation failed
      color_echo "$RED" "Error: failed to install the Harrier management panel."
      color_echo "$RED" "Please check the following possible causes:"
      color_echo "$RED" "  1. Make sure /opt/Harrier/misc/manage.sh exists and is readable."
      color_echo "$RED" "  2. Make sure you have sufficient permissions to write to $command_path."
      color_echo "$RED" "  3. Check that there is enough disk space."
      exit 1  # Exit with a non-zero status to indicate an error
    fi
  else
    color_echo "$YELLOW" "The Harrier management panel already exists at $command_path, no need to install."
  fi
}
# Download a file (automatically picks wget or curl)
download_file() {
    local url="$1"
    local output_file="$2"
    local quiet="${3:-true}"  # Quiet download by default
    local q_flag=""

    if [ "$quiet" = true ]; then
        q_flag="-q"
    fi

    if command -v curl &> /dev/null; then
        curl -sSL "$url" -o "$output_file"
    elif command -v wget &> /dev/null; then
        wget $q_flag --continue "$url" -O "$output_file"
    else
        color_echo $RED "Error: neither curl nor wget exists, cannot download the file."
        exit 1
    fi

    if [ $? -ne 0 ]; then
        color_echo $RED "File download failed: $url"
        exit 1
    fi
}

# Install nmap (supports .rpm and alien conversion)
install_nmap() {
    if ! command -v nmap &> /dev/null; then
        color_echo $YELLOW "Installing nmap..."
        local nmap_rpm="nmap-7.95-3.x86_64.rpm"
        local nmap_deb="nmap_7.95-4_amd64.deb"
        local nmap_url="https://nmap.org/dist/$nmap_rpm"

        if [[ -f /etc/debian_version ]]; then
            # Debian/Ubuntu family, alien must be installed first
            install_package alien
            download_file "$nmap_url" "$nmap_rpm"
            sudo alien "./$nmap_rpm"
            sudo dpkg -i "$nmap_deb"
            rm -f "$nmap_rpm" "$nmap_deb"
        elif [[ -f /etc/redhat-release || -f /etc/fedora-release ]]; then
            # CentOS/RHEL/Fedora family
            download_file "$nmap_url" "$nmap_rpm"
            sudo rpm -Uvh "$nmap_rpm"
            rm -f "$nmap_rpm"
        else
             color_echo $RED "Unsupported Linux distribution, please install nmap manually."
             exit 1
        fi
    fi
}

# Install nuclei (different mirrors for China and abroad)
install_nuclei() {
    if ! command -v nuclei &> /dev/null; then
        color_echo $YELLOW "Installing nuclei..."
        local nuclei_zip="nuclei_3.3.9_linux_amd64.zip"
        local nuclei_url

        if is_cn_env; then
            nuclei_url="$NUCLEI_URL_CN"
        else
            nuclei_url="$NUCLEI_URL"
        fi

        download_file "$nuclei_url" "$nuclei_zip"
        unzip "$nuclei_zip" && sudo mv nuclei /usr/bin/ && rm -f "$nuclei_zip"
        nuclei -ut
    fi
}

# Install wih (different mirrors for China and abroad)
install_wih() {
    if ! command -v wih &> /dev/null; then
        color_echo $YELLOW "Installing wih..."
        local wih_url
        if is_cn_env; then
            wih_url="$WIH_URL_CN"
        else
            wih_url="$WIH_URL"
        fi
        download_file "$wih_url" "/usr/bin/wih"
        sudo chmod +x /usr/bin/wih
        wih --version
    fi
}

# Install ncrack (different mirrors for China and abroad)
install_ncrack() {
    if [ ! -f /usr/local/bin/ncrack ]; then
        color_echo $YELLOW "Installing ncrack..."
        local ncrack_url
        if is_cn_env; then
            ncrack_url="$NCRACK_URL_CN"
        else
            ncrack_url="$NCRACK_URL"
        fi
        download_file "$ncrack_url" "/usr/local/bin/ncrack"
        sudo chmod +x /usr/local/bin/ncrack
    fi

    mkdir -p /usr/local/share/ncrack
    if [ ! -f /usr/local/share/ncrack/ncrack-services ]; then
        color_echo $YELLOW "Downloading ncrack-services..."
         local ncrack_services_url
        if is_cn_env; then
            ncrack_services_url="$NCRACK_SERVICES_URL_CN"
        else
            ncrack_services_url="$NCRACK_SERVICES_URL"
        fi
        download_file "$ncrack_services_url" "/usr/local/share/ncrack/ncrack-services"
    fi
}

# Download GeoLite2 databases (different mirrors for China and abroad)
download_geolite2() {
    mkdir -p "$GEO_DATA_DIR"
    for db in GeoLite2-ASN.mmdb GeoLite2-City.mmdb; do
        if [ ! -f "$GEO_DATA_DIR/$db" ]; then
            local geo_url
            if is_cn_env; then
                case "$db" in
                    GeoLite2-ASN.mmdb) geo_url="$GEO_ASN_URL_CN" ;;
                    GeoLite2-City.mmdb) geo_url="$GEO_CITY_URL_CN" ;;
                esac
            else
               case "$db" in
                    GeoLite2-ASN.mmdb) geo_url="$GEO_ASN_URL" ;;
                    GeoLite2-City.mmdb) geo_url="$GEO_CITY_URL" ;;
                esac
            fi

            if [ -z "$geo_url" ]; then
                color_echo $YELLOW "No download URL configured for $db; place it under $GEO_DATA_DIR manually."
                continue
            fi

            color_echo $YELLOW "Downloading $db..."
            download_file "$geo_url" "$GEO_DATA_DIR/$db"
        fi
    done
}

# Install pip3.6 (different mirrors for China and abroad)
install_pip36() {
  if [ ! -f /usr/local/bin/pip3.6 ]; then
    color_echo $YELLOW "Installing pip3.6..."
    local get_pip_url
    local pip_mirror=""

    if is_cn_env; then
      get_pip_url="$GET_PIP_SCRIPT_CN"
      pip_mirror="-i https://mirrors.aliyun.com/pypi/simple/"
    else
      get_pip_url="$GET_PIP_SCRIPT"
    fi

    download_file "$get_pip_url" "get-pip.py"
    python3.6 get-pip.py $pip_mirror
    pip3.6 --version

    if is_cn_env; then
      pip3.6 config set global.index-url https://mirrors.aliyun.com/pypi/simple/
    fi
    rm -f get-pip.py
  fi
}
# Set massdns permissions
fix_permission() {
    local massdns_path="/opt/Harrier/app/tools/massdns"
    local phantomjs_path="/usr/bin/phantomjs"
    
    # 1. Check that the files exist
    if [ ! -f "$massdns_path" ]; then
        color_echo $RED "Error: massdns file does not exist at $massdns_path"
        color_echo $YELLOW "Please make sure Harrier is installed correctly"
        return 1
    fi
    if [ ! -f "$phantomjs_path" ]; then
        color_echo $RED "Error: phantomjs file does not exist at $phantomjs_path"
        color_echo $YELLOW "Please make sure Harrier is installed correctly"
        return 1
    fi

    # 2. Grant execute permission
    if sudo chmod +x "$massdns_path"; then
        color_echo $GREEN "Execute permission added for massdns"
    else
        color_echo $RED "Unable to add execute permission, please check the file path or permissions"
        return 1
    fi
    # 3. Verify execute permission
    if [ -x "$massdns_path" ]; then
        color_echo $GREEN "Verification passed: massdns can now be executed"
    else
        color_echo $RED "Verification failed: please check massdns permissions manually"
        return 1
    fi
        if [ -x "$phantomjs_path" ]; then
        color_echo $GREEN "Verification passed: phantomjs can now be executed"
    else
        color_echo $RED "Verification failed: please check phantomjs permissions manually"
        return 1
    fi
}

# Determine whether this is a China network environment (based on whether google.com is reachable)
is_cn_env() {
  if  ping -c 1 -W 3  www.google.com &>/dev/null;then
    return 1
  else
    return 0
  fi
}

# Get the MongoDB repository configuration (based on distribution, version and network environment)
get_mongodb_repo_config() {
    local os_id="$1"
    local os_version_id="$2"
    local repo_config=""

    case "$os_id$os_version_id" in
        centos7|centos8|rhel8|rocky8.10)
            repo_config=$(cat <<EOF
[mongodb-org-4.4]
name=MongoDB Repository
baseurl=https://repo.mongodb.org/yum/redhat/\$releasever/mongodb-org/4.4/x86_64/
gpgcheck=1
enabled=1
gpgkey=https://www.mongodb.org/static/pgp/server-4.4.asc
EOF
)
            ;;
        ubuntu20.04)
            repo_config="deb [ arch=amd64,arm64 ] https://repo.mongodb.org/apt/ubuntu focal/mongodb-org/4.4 multiverse"
            ;;
        *)
            color_echo $RED "Unsupported operating system: $os_id$os_version_id"
            exit 1
            ;;
    esac
    echo "$repo_config"
}

# Get the RabbitMQ repository configuration (based on distribution and version)
get_rabbitmq_repo_config() {
    local os_id="$1"
    local os_version_id="$2"
    local repo_config=""

    case "$os_id$os_version_id" in
        centos8|rhel8|rocky8.10)
            repo_config=$(cat <<EOF
[rabbitmq_erlang]
name=rabbitmq_erlang
baseurl=https://packagecloud.io/rabbitmq/erlang/el/8/\$basearch
repo_gpgcheck=1
gpgcheck=0
enabled=1
gpgkey=https://packagecloud.io/rabbitmq/erlang/gpgkey
sslverify=1
sslcacert=/etc/pki/tls/certs/ca-bundle.crt
metadata_expire=300

[rabbitmq_erlang-source]
name=rabbitmq_erlang-source
baseurl=https://packagecloud.io/rabbitmq/erlang/el/8/SRPMS
repo_gpgcheck=1
gpgcheck=0
enabled=1
gpgkey=https://packagecloud.io/rabbitmq/erlang/gpgkey
sslverify=1
sslcacert=/etc/pki/tls/certs/ca-bundle.crt
metadata_expire=300

[rabbitmq_rabbitmq-server]
name=rabbitmq_rabbitmq-server
baseurl=https://packagecloud.io/rabbitmq/rabbitmq-server/el/8/\$basearch
repo_gpgcheck=1
gpgcheck=0
enabled=1
gpgkey=https://packagecloud.io/rabbitmq/rabbitmq-server/gpgkey
sslverify=1
sslcacert=/etc/pki/tls/certs/ca-bundle.crt
metadata_expire=300

[rabbitmq_rabbitmq-server-source]
name=rabbitmq_rabbitmq-server-source
baseurl=https://packagecloud.io/rabbitmq/rabbitmq-server/el/8/SRPMS
repo_gpgcheck=1
gpgcheck=0
enabled=1
gpgkey=https://packagecloud.io/rabbitmq/rabbitmq-server/gpgkey
sslverify=1
sslcacert=/etc/pki/tls/certs/ca-bundle.crt
metadata_expire=300
EOF
)
            ;;
        ubuntu20.04)
            repo_config=""  # Ubuntu installs directly via apt, no extra repository configuration needed
            ;;
        centos7)
            repo_config=""
            ;;
        *)
            color_echo $RED "Unsupported operating system or version: $os_id$os_version_id"
            exit 1
            ;;
    esac
    echo "$repo_config"
}

#----------------------------------
# Remaining functions (modify URLs and paths as needed)
#----------------------------------

# Get the public IP and show the Harrier access URL
ipinfo() {
    local ip=$(curl -s https://ipinfo.io/ip)
    if [[ -z "$ip" ]]; then
        color_echo $YELLOW "Warning: unable to get the public IP, Harrier access may be affected."
    else
        color_echo $GREEN "Harrier access URL: https://${ip}:5003"
    fi
}

# Global variable storing the randomly generated password
HARRIER_RANDOM_PASS=""

# Generate a random password and initialize the MongoDB user
rand_pass() {
    # Generate a 16-character random password
    HARRIER_RANDOM_PASS=$(tr -cd '[:alnum:]' < /dev/urandom | head -c 16)
    local SALT="harriersalt!@#" # Define the salt

  # Create the mongo-init.js file (overwrites any old file)
    cat <<EOF > /opt/Harrier/docker/mongo-init.js
db.user.drop();
db.user.insert({ username: 'admin',  password: hex_md5('${SALT}'+'${HARRIER_RANDOM_PASS}') });
EOF
    color_echo $GREEN "MongoDB initialization script generated."
}

# Print the username and password
out_pass() {
    color_echo $GREEN "Username: admin"
    color_echo $GREEN "Initial password: ${HARRIER_RANDOM_PASS}"
}

# Add fingerprints feature
add_finger() {
    local download_dir="/opt/Harrier/misc"
    local target_url="https://127.0.0.1:5003/"
    local admin_user="admin"
    local admin_pass="harrier123"
    local method="old"
    local finger_file="$download_dir/finger.json"
    local script_file="$download_dir/ADD-Harrier-Finger.py"

    # Check the /opt/Harrier/misc directory; use /root if it does not exist
    if [ ! -d /opt/Harrier/misc ]; then
        color_echo $YELLOW "/opt/Harrier/misc does not exist, /root will be used as the download directory."
        download_dir="/root"
    fi
   
    # User interaction: get the target URL
    read -r -p "Enter the target URL (default: ${target_url}): " user_input
    target_url="${user_input:-$target_url}"

    # User interaction: get the admin username and password
    read -r -p "Enter the admin username (default: ${admin_user}): " user_input
    admin_user="${user_input:-$admin_user}"
    read -r -p "Enter the admin password (default: ${admin_pass}): " user_input
    admin_pass="${user_input:-$admin_pass}"

    # User interaction: choose the add method
    print_separator "-" 30
    echo "Choose how to add fingerprints:"
    echo "1. old - legacy mode: add fingerprints one by one (suitable for existing JSON data)"
    echo "   Format example:"
    echo '     { "cms": "Seeyon OA", "method": "keyword", "location": "rule: body", "keyword": ["/seeyon/USER-DATA/IMAGES/LOGIN/login.gif"] }'
    echo "2. new - new mode: bulk-upload a fingerprint file (suitable for importing large batches)"
    echo "   Format example:"
    echo '      - name: Seeyon OA'
    echo '        rule: body="/seeyon/USER-DATA/IMAGES/LOGIN/login.gif"'
    print_separator "-" 30
    read -r -p "Enter the add method (new or old, default: ${method}): " user_input
    method="${user_input:-$method}"
  
    # User interaction: fingerprint file path
    read -r -p "Enter the fingerprint file path (e.g. /opt/Harrier/misc/finger.json, leave empty to use the default ${finger_file}): " user_input
    finger_file="${user_input:-$finger_file}"
  

    # The fingerprint-adding script and fingerprint data are bundled in the
    # Harrier repository under misc/ and are expected at /opt/Harrier/misc/.
    if [ ! -s "$script_file" ]; then
        color_echo $RED "ADD-Harrier-Finger.py was not found at $script_file."
        color_echo $RED "It is bundled in the Harrier repository under misc/."
        exit 1
    fi

    if [ ! -s "$finger_file" ]; then
        color_echo $RED "Fingerprint file was not found at $finger_file."
        color_echo $RED "It is bundled in the Harrier repository under misc/finger.json."
        exit 1
    fi


    # Check the Python command (prefer python3.6)
    local python_cmd="python3"
    if command -v python3.6 &>/dev/null; then
        python_cmd="python3.6"
    fi


    # Run the fingerprint import
    color_echo $GREEN "Starting to add fingerprints (using file: $finger_file)..."
    "$python_cmd" "$script_file" "$target_url" "$admin_user" "$admin_pass" "$method" "$finger_file"
     if [ $? -eq 0 ];then
        color_echo $GREEN "Fingerprints added successfully."
     else
       color_echo $RED "Errors occurred while adding fingerprints, please check the logs."
     fi
}

# Switch mirror sources (via LinuxMirrors)
sources_shell() {
    color_echo $YELLOW "Switching mirror sources (using LinuxMirrors)..."
    color_echo $YELLOW "https://github.com/SuperManito/LinuxMirrors"
    local mirrors_script="/opt/ChangeMirrors.sh"
    local script_url="https://linuxmirrors.cn/main.sh"

    if [ ! -f "$mirrors_script" ]; then
        color_echo $YELLOW "Downloading the ChangeMirrors.sh script..."
        download_file "$script_url" "$mirrors_script"
    fi

    if [ -f "$mirrors_script" ]; then
        bash "$mirrors_script"
        color_echo $GREEN "Mirror source switch completed."
    else
        color_echo $RED "Failed to switch mirror sources, please check the network connection or configure manually."
    fi
}

# Check and install Docker-related tools
check_and_install_docker_tools() {
    local tools=("wget" "tar" "iptables")
    for tool in "${tools[@]}"; do
        install_package "$tool"
    done
}

# Check and disable SELinux and the firewall
check_selinux() {
    # Disable the firewall
    for service in firewalld iptables; do
        if systemctl is-enabled "$service" &>/dev/null; then
            sudo systemctl stop "$service" &>/dev/null
            sudo systemctl disable "$service" &>/dev/null
            color_echo $YELLOW "Firewall $service disabled."
        fi
    done
    # Disable ufw (if present)
    if command -v ufw &> /dev/null; then
        sudo ufw disable &> /dev/null
        color_echo $YELLOW "Firewall ufw disabled."
    fi

    # Check and disable SELinux
    if sestatus &>/dev/null && sestatus | grep "SELinux status" | grep -q "enabled"; then
        color_echo $YELLOW "SELinux is enabled, disabling..."
        sudo setenforce 0
        sudo sed -i 's/SELINUX=enforcing/SELINUX=disabled/g' /etc/selinux/config
        color_echo $GREEN "SELinux disabled."
    else
        color_echo $GREEN "SELinux is disabled or not installed."
    fi
}

# Detect the OS version (more precise matching)
fixed_check_osver() {
    if [ -f /etc/os-release ]; then
        . /etc/os-release
    else
        color_echo $RED "Unable to determine the distribution."
        exit 1
    fi

    # Use a case statement for more precise matching
    case "$ID$VERSION_ID" in
        centos7)
            os_ver="CentOS Linux 7"
            ;;
        centos8|rhel8|rocky8.10)  # Compatible with CentOS 8, RHEL 8, Rocky 8.10
            os_ver="CentOS/RHEL 8/Rocky 8.10"
            ;;
        ubuntu20.04)
            os_ver="Ubuntu 20.04"
            ;;
        *)
            color_echo $RED "This script does not currently support your system: $NAME $VERSION_ID"
            exit 1
            ;;
    esac
    color_echo $GREEN "Detected operating system: $os_ver"
}

# Check Docker running status
check_run_docker() {
    local status=$(systemctl is-active docker)
    case "$status" in
    active)
        color_echo $GREEN "Docker is running normally."
        ;;
    inactive|unknown)
        color_echo $YELLOW "Docker service is not running, trying to start it..."
        sudo systemctl start docker
        if [ $? -eq 0 ]; then
            color_echo $GREEN "Docker started successfully."
        else
            color_echo $RED "Docker failed to start, please check the Docker installation and configuration."
            exit 1
        fi
        ;;
    *)
        color_echo $RED "Unable to determine Docker status."
        exit 1
        ;;
    esac
}

# Stop and remove Harrier Docker containers
uninstall_docker() {
    local containers=("harrier_rabbitmq" "harrier_mongodb" "harrier_web" "harrier_work" "harrier_scheduler")

    # Stop containers
    color_echo $YELLOW "Stopping Harrier-related containers..."
    for container in "${containers[@]}"; do
        if docker ps -a -q --filter "name=$container" &>/dev/null; then
            docker stop "$container" &>/dev/null
            if [ $? -eq 0 ]; then
                color_echo $YELLOW "Container $container stopped."
            else
                color_echo $RED "Container $container failed to stop."  # Do not exit here; keep trying to stop the other containers
            fi
        else
            color_echo $YELLOW "Container $container not found."
        fi
    done

    # Remove containers
    color_echo $YELLOW "Removing Harrier-related containers..."
    for container in "${containers[@]}"; do
        if docker ps -a -q --filter "name=$container" &>/dev/null; then
            docker rm "$container" &>/dev/null
            if [ $? -eq 0 ]; then
                color_echo $YELLOW "Container $container removed."
            else
                color_echo $RED "Container $container failed to be removed."
            fi
        else
            color_echo $YELLOW "Container $container not found."
        fi
    done
}

# Check and install the specified version of PyYAML
check_and_install_pyyaml() {
    local required_version="5.4.1"
    local installed_version

    # Check whether python3.6 exists; fall back to python3 if not
    if command -v python3.6 &> /dev/null; then
        installed_version=$(pip3.6 show PyYAML | grep Version | cut -d ' ' -f 2)
    elif command -v python3 &> /dev/null; then
        installed_version=$(pip3 show PyYAML | grep Version | cut -d ' ' -f 2)
    else
        color_echo $RED "Error: neither python3.6 nor python3 was found."
        exit 1
    fi

    if [ "$installed_version" != "$required_version" ]; then
         color_echo $YELLOW "Installing PyYAML version $required_version ..."
        if command -v python3.6 &> /dev/null; then
            pip3.6 install --ignore-installed PyYAML=="$required_version"
        else
            pip3 install --ignore-installed PyYAML=="$required_version"
        fi
    else
        color_echo $GREEN "PyYAML version $required_version is already installed."
    fi
}

# Check and add the Nginx log format configuration
add_check_nginx_log_format() {
    local NGINX_CONF="/etc/nginx/nginx.conf"
    local NEW_CONF="/opt/Harrier/misc/nginx.conf"

    # Check whether log_format already exists
    if grep -q 'log_format main' "$NGINX_CONF"; then
        color_echo $GREEN "Nginx log format is already configured, no changes needed."
    else
        color_echo $YELLOW "Nginx log format is not configured, adding it..."
        # Back up and replace the configuration file
        sudo cp "$NGINX_CONF" "${NGINX_CONF}.bak"
        sudo cp "$NEW_CONF" "$NGINX_CONF"
        color_echo $GREEN "Nginx configuration file updated."
    fi
}

check_install_docker_CN(){
    check_and_install_docker_tools
    local MAX_ATTEMPTS=3
    local ATTEMPT=0
    local SUCCESS=false
    local CPU_ARCH=$(uname -m)
    local SAVE_PATH="/opt/docker_tgz"
    mkdir -p $SAVE_PATH
    local DCOKER_VER="docker-27.1.1.tgz"
    local DOCKER_ARCH=""
    case $CPU_ARCH in
        "arm64" | "aarch64")
            DOCKER_ARCH="aarch64"
        ;;
        "x86_64")
            DOCKER_ARCH="x86_64"
        ;;
        *)
            color_echo $RED "Unsupported CPU architecture: $CPU_ARCH"
            exit 1
        ;;
    esac
    DOCKER_COMPOSE_URL="https://download.docker.com/linux/static/stable/${DOCKER_ARCH}/${DCOKER_VER}"
if ! command -v docker &> /dev/null; then
  while [ $ATTEMPT -lt $MAX_ATTEMPTS ]; do
    ATTEMPT=$((attempt + 1))
    color_echo $YELLOW "Docker is not installed, installing..."
    wget -P "$SAVE_PATH" "$DOCKER_COMPOSE_URL"
    if [ $? -eq 0 ]; then
        SUCCESS=true
        break
    fi
    color_echo $RED "Docker installation failed, retrying download (attempt: $ATTEMPT)"
  done

  if $SUCCESS; then
     tar -xzf $SAVE_PATH/$DCOKER_VER -C $SAVE_PATH
     \cp $SAVE_PATH/docker/* /usr/bin/
     rm -rf $SAVE_PATH
     color_echo $GREEN "Docker installed successfully, version: $(docker --version)"
     
     cat > /usr/lib/systemd/system/docker.service <<EOF
[Unit]
Description=Docker Application Container Engine
Documentation=https://docs.docker.com
After=network-online.target firewalld.service
Wants=network-online.target
[Service]
Type=notify
ExecStart=/usr/bin/dockerd
ExecReload=/bin/kill -s HUP 
LimitNOFILE=infinity
LimitNPROC=infinity
LimitCORE=infinity
TimeoutStartSec=0
Delegate=yes
KillMode=process
Restart=on-failure
StartLimitBurst=3
StartLimitInterval=60s
[Install]
WantedBy=multi-user.target
EOF
    sudo systemctl daemon-reload
    sudo systemctl restart docker
    check_run_docker
    sudo systemctl enable --now docker
  else
    color_echo $RED "Docker installation failed, please check the network or install it manually."
    exit 1
  fi
else 
    color_echo $GREEN "Docker installed successfully, version: $(docker --version)"
fi
}

# China environment: install Docker Compose (using a domestic mirror)
check_install_docker-compose_CN() {
    if ! command -v docker-compose &> /dev/null; then
        color_echo $YELLOW "Docker Compose is not installed, installing..."

    # Download docker-compose
        local CPU_ARCH
        CPU_ARCH=$(uname -m)
        local OS
        OS=$(uname -s | tr '[:upper:]' '[:lower:]')

        case "$CPU_ARCH" in
            "x86_64"|"amd64")
                DOCKER_COMPOSE_URL="https://github.com/docker/compose/releases/download/v2.27.1/docker-compose-${OS}-x86_64"
            ;;
            "arm64" | "aarch64")
                DOCKER_COMPOSE_URL="https://github.com/docker/compose/releases/download/v2.27.1/docker-compose-${OS}-aarch64"
            ;;
            *)
                color_echo $RED "Unsupported CPU architecture: $CPU_ARCH"
                exit 1
            ;;
        esac
        sudo curl -L "$DOCKER_COMPOSE_URL" -o /usr/local/bin/docker-compose
        if [ $? -eq 0 ];then
            sudo chmod +x /usr/local/bin/docker-compose
            color_echo $GREEN "Docker Compose installed successfully, version: $(docker-compose --version)"
        else
            color_echo $RED "Docker Compose installation failed, please check the network or install it manually."
            exit 1
        fi
    else
        color_echo $GREEN "Docker Compose is already installed, version: $(docker-compose --version)"
    fi
}

# Non-China environment: install Docker (using the official source)
check_install_docker() {
    check_and_install_docker_tools

    if ! command -v docker &> /dev/null; then
        color_echo $YELLOW "Docker is not installed, installing..."
        sudo curl -fsSL "https://get.docker.com" | sudo sh
        if [ $? -eq 0 ]; then
            color_echo $GREEN "Docker installed successfully, version: $(docker --version)"
            sudo systemctl enable --now docker
            check_run_docker
        else
            color_echo $RED "Docker installation failed, please check the network or install it manually."
            exit 1
        fi
    else
        color_echo $GREEN "Docker is already installed, version: $(docker --version)"
        sudo systemctl restart docker
        check_run_docker
    fi
}

# Non-China environment: install Docker Compose (using the official source)
check_install_docker-compose() {
    if ! command -v docker-compose &> /dev/null; then
        color_echo $YELLOW "Docker Compose is not installed, installing..."
        
        # Get the latest version
        local DOCKER_COMPOSE_VERSION
        DOCKER_COMPOSE_VERSION=$(curl -s "https://api.github.com/repos/docker/compose/releases/latest" | grep 'tag_name' | cut -d\" -f4)
        
        # Get the CPU architecture
        local CPU_ARCH
        CPU_ARCH=$(uname -m)
        
        # Determine the file name and download URL
        local OS
        OS=$(uname -s | tr '[:upper:]' '[:lower:]')
        local FILE_NAME="docker-compose-${OS}-${CPU_ARCH}"
        local DOCKER_COMPOSE_URL="https://github.com/docker/compose/releases/download/${DOCKER_COMPOSE_VERSION}/${FILE_NAME}"
        local SHA256_FILE_NAME="${FILE_NAME}.sha256"
        local SHA256_URL="https://github.com/docker/compose/releases/download/${DOCKER_COMPOSE_VERSION}/${SHA256_FILE_NAME}"
        
        # Download and verify Docker Compose
        if [ -n "$DOCKER_COMPOSE_VERSION" ]; then
            
            # Download the Docker Compose binary
            sudo curl -fL "${DOCKER_COMPOSE_URL}" -o /usr/local/bin/docker-compose
            if [ $? -ne 0 ]; then
                color_echo $RED "Docker Compose download failed! Please install it manually."
                exit 1
            fi   
            # Set permissions
            sudo chmod +x /usr/local/bin/docker-compose
            color_echo $GREEN "Docker Compose installed successfully, version: $(docker-compose --version)"
        else
            color_echo $RED "Unable to get the latest Docker Compose version information!"
            exit 1
        fi
    else
        color_echo $GREEN "Docker Compose is already installed, version: $(docker-compose --version)"
    fi
}

# Common Harrier installation steps (applies to all environments and distributions)
install_harrier_common() {
    # Start services
    for svc in mongod rabbitmq-server; do
        sudo systemctl enable "$svc"
        sudo systemctl start "$svc"
    done

    # Clone Harrier (this repo) and the NPoC plugin package (original upstream)
    local harrier_repo="$HARRIER_REPO"
    local harrier_npoc_repo="$HARRIER_NPOC_REPO"

    if is_cn_env; then
        harrier_npoc_repo="https://gitee.com/ms1125/ARL-NPoC"
    fi

    if [ ! -d "$HARRIER_DIR" ]; then
        color_echo $YELLOW "Cloning the Harrier project..."
        git clone "$harrier_repo" "$HARRIER_DIR"
    fi

    if [ ! -d "$HARRIER_NPOC_DIR" ]; then
        color_echo $YELLOW "Cloning the Harrier-NPoC project..."
        git clone "$harrier_npoc_repo" "$HARRIER_NPOC_DIR"
    fi
    # Check whether PyYAML is installed at a different version
    check_and_install_pyyaml

    # Install Harrier-NPoC dependencies
    cd "$HARRIER_NPOC_DIR" || exit
    color_echo $YELLOW "Installing Harrier-NPoC dependencies..."
    pip3.6 install -r requirements.txt
    pip3.6 install -e .
    cd "$BASE_DIR" || exit

    # Install ncrack and GeoLite2
    install_ncrack
    download_geolite2

    # Configure Harrier
    cd "$HARRIER_DIR" || exit
    if [ ! -f rabbitmq_user ]; then
        color_echo $YELLOW "Configuring the RabbitMQ user..."
        rabbitmqctl add_user harrier harrierpassword
        rabbitmqctl add_vhost harriervhost
        rabbitmqctl set_user_tags harrier harriertag
        rabbitmqctl set_permissions -p harriervhost harrier ".*" ".*" ".*"
        color_echo $YELLOW "Initializing the Harrier user..."
        rand_pass  # Generate a random password and create mongo-init.js
        mongo 127.0.0.1:27017/harrier docker/mongo-init.js
        touch rabbitmq_user
    fi

    color_echo $YELLOW "Installing Harrier dependencies..."
    pip3.6 install -r requirements.txt
    if [ ! -f app/config.yaml ]; then
        color_echo $YELLOW "Creating the Harrier configuration file..."
        cp app/config.yaml.example app/config.yaml
    fi
    if [ ! -f /usr/bin/phantomjs ]; then
        color_echo $YELLOW "Installing phantomjs..."
        sudo ln -s "$(pwd)"/app/tools/phantomjs /usr/bin/phantomjs
        sudo chmod +x /usr/bin/phantomjs
        fix_permission
    fi
    
    # Configure nginx according to the system type
    if [[ -f /etc/debian_version ]]; then
        # Debian/Ubuntu
        add_check_nginx_log_format
         if [ ! -f /etc/nginx/sites-available/harrier.conf ]; then
            color_echo $YELLOW "Copying the Harrier Nginx configuration..."
            sudo cp misc/harrier.conf /etc/nginx/sites-available/
            sudo ln -s /etc/nginx/sites-available/harrier.conf /etc/nginx/sites-enabled/
         fi
    elif [[ -f /etc/redhat-release || -f /etc/fedora-release ]]; then
        # CentOS/RHEL/Fedora
        if [ ! -f /etc/nginx/conf.d/harrier.conf ]; then
            color_echo $YELLOW "Copying the Harrier Nginx configuration..."
            sudo cp misc/harrier.conf /etc/nginx/conf.d/
        fi
    fi

    if [ ! -f /etc/ssl/certs/dhparam.pem ]; then
        color_echo $YELLOW "Downloading dhparam.pem..."
        curl -s https://ssl-config.mozilla.org/ffdhe2048.txt | sudo tee /etc/ssl/certs/dhparam.pem > /dev/null
    fi

    color_echo $YELLOW "Generating certificates..."
    chmod +x ./docker/worker/gen_crt.sh
    ./docker/worker/gen_crt.sh

    # Copy systemd service files
    for service_file in harrier-web harrier-worker harrier-worker-github harrier-scheduler; do
        if [ ! -f "/etc/systemd/system/$service_file.service" ]; then
            color_echo $YELLOW "Copying the $service_file service file..."
            sudo cp "misc/$service_file.service" /etc/systemd/system/
        fi
    done

    # Reload the systemd configuration
    sudo systemctl daemon-reload

   # Start Harrier services
    color_echo $YELLOW "Starting Harrier services..."
    for service in harrier-web harrier-worker harrier-worker-github harrier-scheduler nginx; do
        sudo systemctl enable "$service"
        sudo systemctl restart "$service" # Use restart to ensure the service is up to date
    done
    
    # Restart and check MongoDB and RabbitMQ service status
    for service in mongod rabbitmq-server; do
        sudo systemctl restart "$service"
        sudo systemctl --no-pager status "$service"
    done

    # Restart and check Harrier-related service status
    for service in harrier-web harrier-worker harrier-worker-github harrier-scheduler anginx; do
        sudo systemctl restart "$service"
        sudo systemctl --no-pager status "$service"
    done

    color_echo $GREEN "Harrier installation complete!"
}

# CentOS 7 source installation
install_for_centos() {
    mkdir -p "$BASE_DIR"
    cd "$BASE_DIR" || exit

    # Configure the MongoDB repository
    local mongodb_config=$(get_mongodb_repo_config centos 7)
    echo "$mongodb_config" | sudo tee /etc/yum.repos.d/mongodb-org-4.4.repo

    # Install dependencies
    color_echo $YELLOW "Installing dependencies..."
    sudo yum install epel-release -y
    sudo yum clean all
    sudo yum makecache
    sudo yum install -y python36 mongodb-org-server mongodb-org-shell rabbitmq-server python36-devel gcc-c++ git nginx fontconfig wqy-microhei-fonts unzip wget

    # Link python3.6 
    if [ ! -f /usr/bin/python3.6 ]; then
        color_echo $YELLOW "Linking python3.6..."
        sudo ln -s /usr/bin/python36 /usr/bin/python3.6
    fi

    # Install pip3.6 
    install_pip36

    # Install nmap, nuclei, wih
    install_nmap
    install_nuclei
    install_wih

    # Install Harrier (common steps)
    install_harrier_common
}

# CentOS 8 source installation
install_for_centos8() {
    mkdir -p "$BASE_DIR"
    cd "$BASE_DIR" || exit
    # Configure the MongoDB repository
    local mongodb_config=$(get_mongodb_repo_config centos 8)
    echo "$mongodb_config" | sudo tee /etc/yum.repos.d/mongodb-org-4.4.repo

    # Configure the RabbitMQ repository
    local rabbitmq_config=$(get_rabbitmq_repo_config centos 8)
    echo "$rabbitmq_config" | sudo tee /etc/yum.repos.d/rabbitmq.repo

    # Install dependencies
    color_echo $YELLOW "Installing dependencies..."
    sudo yum install epel-release -y
    sudo yum clean all
    sudo yum makecache
    sudo yum install -y python36 mongodb-org-server mongodb-org-shell rabbitmq-server python36-devel gcc-c++ git nginx fontconfig wqy-microhei-fonts unzip wget

    # Link python3.6 (if needed)
    if [ ! -f /usr/bin/python3.6 ]; then
        color_echo $YELLOW "Linking python3.6..."
        sudo ln -s /usr/bin/python36 /usr/bin/python3.6
    fi
    
    # Install pip3.6
    install_pip36

    # Install nmap, nuclei, wih
    install_nmap
    install_nuclei
    install_wih
    
    # Install Harrier (common steps)
    install_harrier_common
}

# Ubuntu 20.04 source installation
install_for_ubuntu() {
    mkdir -p "$BASE_DIR"
    cd "$BASE_DIR" || exit

    # Add the MongoDB repository
    if ! command -v curl &> /dev/null; then
        color_echo $YELLOW "Installing curl ..."
        sudo apt-get install curl -y
    fi

    sudo apt-get update -y &&  sudo apt-get install -y gnupg
    curl -fsSL https://www.mongodb.org/static/pgp/server-4.4.asc | sudo apt-key add -

    local mongodb_config=$(get_mongodb_repo_config ubuntu 20.04)
    echo "$mongodb_config" | sudo tee /etc/apt/sources.list.d/mongodb-org-4.4.list

    # Install dependencies
    color_echo $YELLOW "Installing dependencies..."
    sudo apt-get update
    sudo apt install software-properties-common -y
    sudo add-apt-repository ppa:deadsnakes/ppa -y
    sudo apt-get update
    sudo apt-get install -y python3.6 mongodb-org rabbitmq-server python3.6-dev g++ git nginx fontconfig unzip wget  python3.6-distutils
    
    # Install pip3.6
    install_pip36
   
    # Install nmap, nuclei, wih
    install_nmap
    install_nuclei
    install_wih
    
    # Install Harrier (common steps)
    install_harrier_common
}

# Source installation (auto-selects based on OS and network environment)
code_install() {
    fixed_check_osver # Check the operating system

    case "$os_ver" in
    "CentOS Linux 7")
        check_selinux
        install_for_centos
        ;;
    "CentOS/RHEL 8/Rocky 8.10")
        check_selinux
        install_for_centos8
        ;;
    "Ubuntu 20.04")
        install_for_ubuntu
        ;;
    *)
        color_echo $RED "Unsupported operating system: $os_ver"
        exit 1
        ;;
    esac
}


# Docker installation menu (simplified)
docker_install_menu() {
    check_and_install_git
    print_separator
    echo "Select the Harrier Docker version to install:"
    echo "1) harrier-docker-all (prebuilt image, currently only supports non-China environments)"
    print_separator

    read -r -p "Enter an option (1): " version_choice

    case "$version_choice" in
        1)
        color_echo $YELLOW "Cloning the Harrier project..."
        cd /opt/ || exit
        if [ ! -d Harrier ]; then
          git clone "$HARRIER_REPO"
        fi
        cd Harrier/docker || exit
        docker volume create harrier_db
        docker compose up -d
        ;;
    *)
        color_echo $RED "Invalid input, please choose again."
        sleep 2
        docker_install_menu
        ;;
    esac
}

# Main menu
main_menu() {
    clear
    print_separator
    color_echo $BLUE "Harrier automated deployment script (version $HARRIER_VERSION)"
    print_separator
    echo "For a first-time installation, it is recommended to switch mirror sources first."
    echo "1) Switch mirror sources (using LinuxMirrors)"
    echo "2) Source installation (supports CentOS 7/8, Ubuntu 20.04; detects China vs. non-China environment)"
    echo "3) Docker installation (currently only supports non-China environments)"
    echo "4) Uninstall Harrier (stop and remove Docker containers)"
    echo "5) Add fingerprints (7k+ fingerprints by default, source installation only)"
    echo "6) Install the Harrier management panel"
    echo "7) Exit the script"
    print_separator
    read -r -p "Enter the corresponding number: " code_id

    case "$code_id" in
    1)  # Switch mirror sources
        sources_shell
        main_menu
        ;;
    2)  # Source installation
        code_install
        manage_harrier
        ipinfo
        out_pass          
        ;;
    3) # Docker installation
        print_separator
        echo "Select the installation environment:"
        echo "1) Non-China environment"
        echo "2) China environment"
        print_separator

        read -r -p "Enter an option (1 or 2): " env_choice

        case "$env_choice" in
            1)  # Non-China environment
                check_install_docker
                check_install_docker-compose
                docker_install_menu
                ;;
            2) # China environment
                check_install_docker_CN
                check_install_docker-compose_CN
                docker_install_menu
                ;;
             *)
                color_echo $RED "Invalid input, please choose again."
                sleep 2
                main_menu  # Return to the main menu
                ;;
        esac
        ;;
    4)  # Uninstall Harrier
        uninstall_docker
        color_echo $GREEN "Harrier has been uninstalled."
        ;;
    5)  # Add fingerprints
        add_finger
        ;;
    6)  # Install the panel
        manage_harrier
        ;;
    7)  # Exit
        exit 0
        ;;
    *)
        color_echo $RED "Invalid option, please enter again."
        sleep 2
        main_menu
        ;;
    esac
}

# Start execution
check_and_install_git
main_menu
