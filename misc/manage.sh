#!/bin/bash

# --- Configuration ---
services=(
  "mongod"
  "rabbitmq-server"
  "harrier-web"
  "harrier-worker"
  "harrier-worker-github"
  "harrier-scheduler"
  "nginx"
)

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m'

# --- Functions ---
function systemctl_all() {
  local cmd="$1"
  if [[ -z "$cmd" ]]; then
    echo -e "${RED}Error: no command provided to systemctl_all${NC}"
    return 1
  fi

  # Exclude the status command
  if [[ "$cmd" == "status" ]]; then
    echo -e "${RED}Error: for status, call the status function directly${NC}"
    return 2
  fi

  for service in "${services[@]}"; do
    echo -e "\n${YELLOW}Processing $service...${NC}"
    systemctl "$cmd" "$service"
    if [[ $? -ne 0 ]]; then
      echo -e "${RED}Error: $cmd ${service} failed (exit code $?)${NC}"
      echo -e "Try debugging with the following command:"
      echo -e "journalctl -u $service -n 50 --no-pager"
    else
      echo -e "${GREEN}Success: $service $cmd${NC}"
    fi
  done
}

# Implementation of each function
function start() {
  systemctl_all start
}

function stop() {
  for service in "${services[@]}"; do
    echo -e "\n${YELLOW}Stopping $service...${NC}"
    systemctl stop "$service"
    if [[ $? -ne 0 ]]; then
      echo -e "${RED}Error: failed to stop ${service} (exit code $?)${NC}"
    else
      echo -e "${GREEN}Stopped successfully: $service${NC}"
    fi
  done
}

function status() {
  for service in "${services[@]}"; do
    echo -e "\n${YELLOW}------ ${BOLD}$service status check ------${NC}"
    
    # Check whether the service exists
    if ! systemctl list-unit-files | grep -q "$service.service"; then
      echo -e "${RED}Error: service $service does not exist${NC}"
      continue
    fi

    # Use --no-pager to prevent paging
    systemctl --no-pager status "$service" | head -n 20
    
    # Add a status summary
    active_status=$(systemctl is-active "$service")
    enabled_status=$(systemctl is-enabled "$service" || echo "unknown")
    
    echo -e "\n${BLUE}Status summary:${NC}"
    echo -e "Active state: ${active_status^}"
    echo -e "Enabled at boot: ${enabled_status^}"
    
    # Add pacing between services
    if [ ${#services[@]} -gt 1 ]; then
      read -r -p "View next service? [Enter to continue / q to quit] " input
      if [[ $input = "q" ]] || [[ $input = "Q" ]]; then
        break
      fi
    fi
  done
}

function disable() {
  systemctl_all disable
}

function enable() {
  systemctl_all enable
}

function showLog() {
  for service in "${services[@]}"; do
    echo -e "\n${YELLOW}------ $service logs ------${NC}"
    journalctl -n 15 --no-pager -u "$service"
    if [[ $? -ne 0 ]]; then
        echo -e "${RED}Error: unable to retrieve logs for ${service}${NC}"
    fi
    read -r -p "Press Enter to continue..."
  done
}

function restart() {
  stop
  start
}

function reset_password() {
  echo -e "${YELLOW}Resetting the Harrier admin password...${NC}"

  if ! systemctl is-active --quiet mongod; then
      echo -e "${RED}Error: MongoDB is not running. Please start MongoDB first.${NC}"
      return 1
  fi

  mongo <<EOF
use harrier
db.user.drop()
db.user.insert({ username: 'admin',  password: hex_md5('harriersalt!@#'+'admin123') })
exit
EOF

  if [[ $? -eq 0 ]]; then
    echo -e "${GREEN}The Harrier admin password has been reset to 'admin123'.${NC}"
  else
    echo -e "${RED}Password reset failed. Please check the MongoDB connection and the commands in this script.${NC}"
  fi
  read -r -p "Press Enter to continue..."
}

# --- Help/Menu ---
function show_menu() {
    clear
    echo -e "${BLUE}${BOLD}=====================================${NC}"
    echo -e "${BLUE}${BOLD}       Harrier Service Management Tool   ${NC}"
    echo -e "${BLUE}${BOLD}=====================================${NC}"
    echo -e "\n${YELLOW}Please choose an action:${NC}"
    echo -e "  ${BOLD}1)${NC} Start all services"
    echo -e "  ${BOLD}2)${NC} Stop all services"
    echo -e "  ${BOLD}3)${NC} Restart all services"
    echo -e "  ${BOLD}4)${NC} Show service status"
    echo -e "  ${BOLD}5)${NC} Disable auto-start on boot"
    echo -e "  ${BOLD}6)${NC} Enable auto-start on boot"
    echo -e "  ${BOLD}7)${NC} View service logs"
    echo -e "  ${BOLD}8)${NC} Reset admin password"
    echo -e "  ${BOLD}9)${NC} Exit the script"
    echo -e "\nEnter an option [1-9]: "
}

# --- Main script logic ---
if [[ $EUID -ne 0 ]]; then
  echo -e "${RED}This script must be run as root or with sudo${NC}"
  exit 1
fi

while true; do
  show_menu
  read -r choice

  case "$choice" in
    1) start ;;
    2) stop ;;
    3) restart ;;
    4) status ;;
    5) disable ;;
    6) enable ;;
    7) showLog ;;
    8) reset_password ;;
    9)
      echo "Exiting the script."
      exit 0
      ;;
    *)
      echo -e "${RED}Invalid choice. Please enter again.${NC}"
      sleep 1
      ;;
  esac
done