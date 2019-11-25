#!/bin/bash

skuba cluster init --control-plane $IP_LB cluster
skuba node bootstrap --user sles --sudo --target $IP_MASTER my-master
skuba node join --role worker --user sles --sudo --target 10.86.2.243 worker1
skuba node join --role worker --user sles --sudo --target 10.86.2.215 worker2
