#!/bin/bash
# Boot-test the Recovery USB in QEMU/OVMF and verify sshd + root login + tools.
set -u
DISK="/dev/disk/by-id/usb-PNY_USB_3.2.1_FD_071C556D2BABC126-0:0"
REAL=$(readlink -f "$DISK")
# ensure nothing auto-remounted it
for p in $(lsblk -lno NAME "$REAL" | tail -n +2); do umount -f "/dev/$p" 2>/dev/null || true; done
command -v sshpass >/dev/null || DEBIAN_FRONTEND=noninteractive apt-get install -y -q sshpass >/dev/null 2>&1
cp /usr/share/OVMF/OVMF_VARS_4M.fd /tmp/recovery-test-vars.fd
KVM=""; [ -e /dev/kvm ] && KVM="-enable-kvm -cpu host"
nohup qemu-system-x86_64 -machine q35 $KVM -m 4096 -smp 4 \
  -drive if=pflash,format=raw,readonly=on,file=/usr/share/OVMF/OVMF_CODE_4M.fd \
  -drive if=pflash,format=raw,file=/tmp/recovery-test-vars.fd \
  -drive file="$REAL",format=raw,if=virtio,cache=none \
  -netdev user,id=n0,hostfwd=tcp:127.0.0.1:2222-:22 -device virtio-net-pci,netdev=n0 \
  -display none -serial file:/tmp/recovery-test-serial.log > /tmp/recovery-test-qemu.log 2>&1 &
QPID=$!
echo "qemu pid=$QPID (kvm: ${KVM:-none})"
RESULT=FAIL
for i in $(seq 1 60); do
  sleep 10
  if sshpass -p password ssh -p 2222 -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o ConnectTimeout=5 root@127.0.0.1 'echo SSH_OK' 2>/dev/null | grep -q SSH_OK; then
    RESULT=PASS; break
  fi
  kill -0 $QPID 2>/dev/null || { echo "qemu exited early"; break; }
done
echo "boot-probe: $RESULT after ~$((i*10))s"
if [ "$RESULT" = PASS ]; then
  sshpass -p password ssh -p 2222 -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null root@127.0.0.1 '
    echo "hostname: $(hostname)"; echo "kernel: $(uname -r)"
    echo "sudo-nopasswd: $(sudo -n true && echo yes || echo NO)"
    for t in lvm mdadm sgdisk smartctl nvme ipmitool rsync debootstrap; do command -v $t >/dev/null && echo "tool $t: ok" || echo "tool $t: MISSING"; done
    ls /opt/MegaRAID/perccli/perccli64 >/dev/null 2>&1 && echo "perccli: ok" || echo "perccli: MISSING"
    systemctl is-enabled gdm3 2>/dev/null || systemctl is-enabled gdm 2>/dev/null || echo "gdm: not-enabled"
    cat /root/README-RECOVERY.md >/dev/null && echo "readme: ok"'
fi
kill $QPID 2>/dev/null; sleep 3; kill -9 $QPID 2>/dev/null
echo "TEST_RESULT=$RESULT"
