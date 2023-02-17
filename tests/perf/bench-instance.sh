#!/bin/bash
set -o errexit -o nounset -o pipefail
__SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
if [[ -z "${GOOGLE_APPLICATION_CREDENTIALS:-}" ]]; then
  source ~/.gcloud/profile/recipe-gen-ml.bash
fi
INSTANCE_NAME=gcs5-bench-us-west1
INSTANCE_ZONE=us-west1-b
IMAGE_NAME=ubuntu-2004-focal-v20210702
IMAGE_PROJECT=ubuntu-os-cloud
GVNIC_IMAGE_NAME="${IMAGE_NAME}-gvnic"
PROJECT_ID=$(gcloud config get-value project)
# https://cloud.google.com/compute/docs/networking/using-gvnic
function create() {
#  gcloud compute \
#    images create ${GVNIC_IMAGE_NAME} \
#      --source-image=${IMAGE_NAME} \
#      --source-image-project=${IMAGE_PROJECT} \
#      --guest-os-features=GVNIC
      
  gcloud compute \
    instances create ${INSTANCE_NAME} \
      --project=devrel-testing \
      --zone=${INSTANCE_ZONE} \
      --machine-type=c2-standard-60 \
      --network-interface=network-tier=PREMIUM,subnet=default,nic-type=GVNIC \
      --maintenance-policy=MIGRATE \
      --service-account=testing@devrel-testing.iam.gserviceaccount.com \
      --scopes=https://www.googleapis.com/auth/cloud-platform \
      --no-boot-disk-auto-delete \
      --image=${GVNIC_IMAGE_NAME} \
      --image-project=${PROJECT_ID} \
      --boot-disk-size=250GB \
      --boot-disk-type=pd-ssd \
      --boot-disk-device-name=${INSTANCE_NAME} \
      --no-shielded-secure-boot \
      --shielded-vtpm \
      --shielded-integrity-monitoring \
      --reservation-affinity=any
}
function ssh() {
  gcloud beta compute \
    ssh ${INSTANCE_NAME} \
      --zone=${INSTANCE_ZONE} \
      "$@"
}
function scp() {
  gcloud beta compute \
    scp --zone=${INSTANCE_ZONE} \
      "$@" \
      "${INSTANCE_NAME}:~"
}
function get() {
  gcloud beta compute \
    scp --zone=${INSTANCE_ZONE} \
      "${INSTANCE_NAME}:$@" .
}
function setup() {
  echo "Setup..."
  sudo apt-get install tmux wget iptraf-ng vnstat openjdk-11-jdk-headless maven
}
function gcLog() {
  while true; do
    local pid="$(jps 2>/dev/null | grep ForkedMain | tail -n 1 | cut -d" " -f 1)"
    echo "running jstat for pid: $pid" | tee -a gc-stats.log
    jstat -gcutil -h 10 "$pid" 2s 2>/dev/null | tee -a gc-stats.log;
  done
}
function now { date +"%Y-%m-%d %H:%M:%S" | tr -d '\n' ;}
function msg { println "$(now) $*" >&2 ;}
function err { local x=$? ; msg "$*" ; return $(( $x == 0 ? 1 : $x )) ;}
function println { printf '%s\n' "$*" ;}
function print { printf '%s ' "$(now) $*" ;}
######################## Delegates to subcommands or runs main, as appropriate
if [[ ${1:-} ]] && declare -F | cut -d' ' -f3 | fgrep -qx -- "${1:-}"
then "$@"
else err "unknown command"; exit 1
fi
