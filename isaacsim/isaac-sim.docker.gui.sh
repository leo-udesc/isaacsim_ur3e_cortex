#!/bin/bash

set -e

# How to run. e.g.:
# "ACCEPT_EULA=Y ./isaac-sim.docker.gui.sh ./runapp.sh"
# Note: This script is recommended to be run on a workstation with a physical display.

echo "Setting variables..."
command="$@"
if [[ -z "$@" ]]; then
    command="bash"
fi
# Set to desired Nucleus
omni_server="http://omniverse-content-production.s3-us-west-2.amazonaws.com/Assets/Isaac/4.5"
if ! [[ -z "${OMNI_SERVER}" ]]; then
	omni_server="${OMNI_SERVER}"
fi
# Set to desired Nucleus username
omni_user="admin"
if ! [[ -z "${OMNI_USER}" ]]; then
	omni_user="${OMNI_USER}"
fi
# Set to desired Nucleus password
omni_password="admin"
if ! [[ -z "${OMNI_PASS}" ]]; then
	omni_password="${OMNI_PASS}"
fi
# Set to "Y" to accept EULA
accept_eula=""
if ! [[ -z "${ACCEPT_EULA}" ]]; then
	accept_eula="${ACCEPT_EULA}"
fi
# Set to "Y" to opt-in
privacy_consent=""
if ! [[ -z "${PRIVACY_CONSENT}" ]]; then
	privacy_consent="${PRIVACY_CONSENT}"
fi
# Set to an email or unique user name
privacy_userid="${omni_user}"
if ! [[ -z "${PRIVACY_USERID}" ]]; then
	privacy_userid="${PRIVACY_USERID}"
fi

# echo "Logging in to nvcr.io..."
# docker login nvcr.io

echo "Pulling docker image..."
docker pull nvcr.io/nvidia/isaac-sim:4.5.0

echo "Running Isaac Sim container with X11 forwarding..."
xhost +
docker run --name isaac-sim --entrypoint bash --runtime=nvidia --gpus all -e "ACCEPT_EULA=${accept_eula}" -it --rm --network=host \
	-v $HOME/.Xauthority:/root/.Xauthority \
	-e DISPLAY \
	-e "OMNI_USER=${omni_user}" -e "OMNI_PASS=${omni_password}" \
	-e "OMNI_SERVER=${omni_server}" \
    -e "PRIVACY_CONSENT=${privacy_consent}" -e "PRIVACY_USERID=${privacy_userid}" \
	-v ~/docker/isaac-sim/cache/ov:/root/.cache/ov:rw \
	-v ~/docker/isaac-sim/cache/pip:/root/.cache/pip:rw \
	-v ~/docker/isaac-sim/cache/glcache:/root/.cache/nvidia/GLCache:rw \
	-v ~/docker/isaac-sim/cache/computecache:/root/.nv/ComputeCache:rw \
	-v ~/docker/isaac-sim/cache/asset_browser:/isaac-sim/exts/isaacsim.asset.browser/cache:rw \
	-v ~/docker/isaac-sim/logs:/root/.nvidia-omniverse/logs:rw \
	-v ~/docker/isaac-sim/data:/root/.local/share/ov/data:rw \
	-v ~/docker/isaac-sim/pkg:/root/.local/share/ov/pkg:rw \
	-v ~/docker/isaac-sim/documents:/root/Documents:rw \
	nvcr.io/nvidia/isaac-sim:4.5.0 \
	-c "${command}"

echo "Isaac Sim container run completed!"
