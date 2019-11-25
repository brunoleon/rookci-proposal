#!/bin/bash

terraform apply -auto-approve
skuba cluster init --control-plane $TR_IP_LB cluster
cd cluster
skuba node bootstrap --user sles --sudo --target $TR_IP_MASTER my-master
skuba node join --role worker --user sles --sudo --target $TR_WORKER1 worker1
skuba node join --role worker --user sles --sudo --target $TR_WORKER2 worker2
