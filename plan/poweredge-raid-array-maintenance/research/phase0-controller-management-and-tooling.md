# Phase 0 — how this array can be managed, and what is now installed

Answers the Phase 0 question from `plan-overview.md`: what BIOS/controller-level
options exist to manage and reconfigure this array. Records the tooling
installed on 2026-08-28 to make that possible, and one finding that changes the
Phase 6 execution plan.

**Read this before planning any array reconfiguration or destructive Phase 6
work.**

## Bottom line

Three management paths exist, in descending order of safety for a rebuild:

1. **iDRAC out-of-band** — the hardware is present (`/dev/ipmi0`, iDRAC 2.85,
   address `192.168.1.119`) but **iDRAC is NOT answering on the network today**.
   It is one fix away from being the safest path, and that fix is a Phase 6
   prerequisite rather than a blocker to the plan.
2. **In-OS vendor CLI** (`perccli`/`storcli`) — not yet installed; see
   "Vendor CLI status".
3. **Boot-time PERC configuration** — always available, always requires physical
   or iDRAC-console presence, and requires the host to be down.

The plan-overview's Phase 6 assumed a rescue-USB reverse-SSH tunnel would be
needed for agentic work during a rebuild. **If iDRAC is restored to the network
first, that scaffolding becomes unnecessary** — iDRAC provides console, power
control, and virtual media independent of the host OS, which is strictly better
than a tunnel that depends on the host having booted something.

## Tooling installed 2026-08-28

Installed on `poweredge-xubuntu` this session, all from Ubuntu 26.04 apt:

| Package | Provides | Version | Why |
|---|---|---|---|
| `fio` | `fio` | 3.41 | Workload-shaped benchmarking; Phase 1/2 measurement |
| `megactl` | `megactl`, `megasasctl` | 0.4.5-1build1 | Read-only MegaRAID status without a vendor CLI |
| `rpm`, `rpm2cpio` | `rpm`, `rpm2cpio` | — | Unpack vendor RPMs (perccli/storcli ship as RPM) |
| `ipmitool` | `ipmitool` | — | Local BMC/iDRAC query and configuration |
| `nvme-cli` | `nvme` | — | For the NVMe tier if Phase 2 adopts it |

Already present beforehand: `smartctl` (smartmontools 7.5-2), `iostat`
(sysstat 12.7.7).

Note `megacli` is genuinely unavailable in Ubuntu — the apt package named
`megactl` is a different, third-party tool and is what got installed.

**Vendor CLIs, installed from vendor downloads (not apt):**

| Tool | Version | Source | Installed path |
|---|---|---|---|
| **`perccli64`** | **007.2313.0000.0000** (A14, 2023-03-07) | `dl.dell.com` `PERCCLI_7.2313.0_A14_Linux.tar.gz` → bundled `.deb` | `/opt/MegaRAID/perccli/perccli64` |
| **`storcli64`** | **007.2705.0000.0000** (2023-08-24) | `docs.broadcom.com` `007.2705.0000.0000_storcli_rel.zip` → `Ubuntu/*.deb` | `/opt/MegaRAID/storcli/storcli64` |

Both are **statically linked** and run correctly on Ubuntu 26.04 despite neither
vendor listing it as supported — Dell lists RHEL 8/9, SLES 15, and Ubuntu
22.04/20.04. Both binaries' chip tables include `SAS3108`, which is this
controller. Use the **v7** CLIs, not `perccli2`/`storcli2`: the H730P Mini is a
PERC9 / SAS3108 part.

Two acquisition gotchas worth recording, because they cost real time:

- **`dl.dell.com` returns HTTP 403 to `curl`'s default User-Agent.** A browser
  UA string is required (`curl -A "Mozilla/5.0 …"`). The failure looks like an
  access restriction rather than a UA filter.
- **Broadcom's StorCLI has no click-through wall** — a plain `curl` fetched the
  full 34 MB with no login, cookie, or EULA step, contrary to expectation.

Still absent: **`racadm`** (Dell OpenManage `srvadmin-idracadm7`). Deliberately
not installed — see "Open items" item 3. Dell publishes no Ubuntu 26.04 suite
(newest is `jammy`, OMSA 11.1.0.0), though the `.deb` needs only libc plus
`libargtable2.so.0`, which Ubuntu 26.04 ships, and remote `racadm -r <ip>` needs
neither `srvadmin-hapi` nor the rest of OMSA.

**Nothing was removed, and no configuration was changed.** Every command run in
Phase 0 was read-only apart from these package installs.

### Vendor CLI status

Both are now installed (see the table above), so VD create/delete/reconfigure
from a running OS is available, and the RAID-level-migration question is
answered below.

`megasasctl` (installed) already gives read-only confirmation and was used to
verify the array state independently of `smartctl`:

```
a0       PERC H730P Mini          encl:1 ldrv:1  batt:good
a0d0      1787GiB RAID 5   1x3  optimal
a0e32s0     894GiB  a0d0  online
a0e32s1     894GiB  a0d0  online
a0e32s2     894GiB  a0d0  online
```

This corroborates the characterization: RAID 5, three drives, optimal, battery
good.

## The iDRAC finding

**iDRAC is present and configured, but unreachable on the network.**

| Check | Result |
|---|---|
| Local BMC device | `/dev/ipmi0` **present** |
| BMC firmware | **2.85**, Manufacturer `Dell Inc.` |
| iDRAC IP | **`192.168.1.119`**, source **DHCP** |
| Subnet / gateway | `255.255.255.0` / `192.168.1.1` |
| iDRAC MAC | `f4:8e:38:ce:5f:84` |
| NIC selection | **Shared LOM — "shared with lom1"**, failover `None` |
| Users | ID 2 `root`, **ADMINISTRATOR**, link-auth + IPMI-msg enabled |
| **TCP 443 / 22 / 623 / 5900 from host** | **all closed/filtered** |
| **ICMP ping to `.119`** | **FAIL**; ARP entry `INCOMPLETE` |
| Chassis power (via local IPMI) | `on`, no faults |

The host's own NIC state rules out the most obvious explanation:

| NIC | State | Carrier |
|---|---|---|
| **`eno1`** | **up** | **1** (1000 Mb/s, link detected) |
| `eno2` / `eno3` / `eno4` | down | 0 |

So `eno1` — the one cabled port — is exactly the port iDRAC is sharing, and
iDRAC still does not answer ARP. That narrows the cause to the iDRAC side
rather than to cabling into the wrong socket. Candidates, none yet eliminated:

- The iDRAC NIC is administratively **disabled** (distinct from IPMI-over-LAN
  being enabled, which the user table suggests it is).
- The **DHCP lease is stale** — `.119` is what iDRAC last recorded, not what it
  currently holds, and it may hold nothing.
- Shared-LOM mode is configured but the **shared path is not actually active**,
  a known 13th-generation PowerEdge behavior when the dedicated port was
  previously selected.

**This is fixable from the running OS**, because local IPMI works: `ipmitool`
can set a static address and re-enable the iDRAC NIC without touching the host's
own networking or requiring a reboot. That was deliberately **not** done in this
pass — it is a change to management-plane configuration and is proposed rather
than performed. It is cheap, low-risk, reversible, and it should happen **before**
Phase 6, because it converts the rebuild from "needs physical presence or a
rescue-USB tunnel" into "drivable remotely".

**Recommendation:** assign iDRAC a **static** address (not DHCP — a management
interface that moves is a management interface you cannot rely on during exactly
the outage you need it for), verify HTTPS and virtual-media reachability, and
only then schedule Phase 6.

## Hardware facts relevant to reconfiguration

Measured 2026-08-28; these constrain every Phase 2 option.

| | |
|---|---|
| Chassis | **1U Rack Mount** — so PCIe cards must be **low-profile / half-height** |
| PCIe Slot 1 | **PCI Express 3 x16, Available (empty), Length: Long** |
| PCIe Slot 2 | PCI Express 3, **In Use** — occupied by an **AMD Radeon HD 5000/6000/7350/8350 (Cedar)** display adapter at `03:00.0` |
| Boot mode | **UEFI** (`/sys/firmware/efi` present) |
| BIOS | **2.18.1**, dated **2023-08-14** |
| Enclosure bays | 8 total, **3 populated, 5 free** |
| Onboard storage controllers | Intel C610/X99 6-port SATA (AHCI) + sSATA (AHCI), separate from the PERC |
| NVMe devices present | **none**; `nvme-cli` now installed for when there are |
| CPU / RAM | 72 threads; 188 GiB total, **111 GiB available** |

Two of these deserve emphasis because they are easy to get wrong when ordering
parts:

- **"Length: Long" is not "full height".** The chassis is 1U, so any add-in card
  must be a **low-profile** card. A full-height NVMe AIC will not fit regardless
  of what the slot-length field says.
- **Slot 2 is spent on a display adapter.** If a second add-in card is ever
  needed (e.g. a mirrored pair of single-slot NVMe cards), that Cedar GPU is the
  obvious thing to remove — it serves console output only, and this host is
  managed over the network. That frees a second slot without buying anything.

## Management options, assessed

### 1. iDRAC out-of-band — preferred, once restored

Gives a remote console independent of the host OS, power control, virtual media
(mount an Ubuntu ISO over the network), and — on iDRAC with the appropriate
licence — full storage configuration (`racadm storage`/`raid` subcommands, or
the web UI). This is the correct basis for a destroy-and-recreate: it survives
the OS being wiped, which no in-OS tool does.

Blocked today only by the network reachability finding above.

### 2. In-OS vendor CLI — needed for the RAID-level-migration question

`perccli`/`storcli` can report whether **RAID Level Migration** (RLM) from
RAID 5 to RAID 10 is offered on this controller, and can perform VD create and
delete online. It is also the only way to create a VD from a **subset** of the
disk group's capacity, which is the mechanism for controller-level
over-provisioning.

**Important caveat carried forward from Phase 1:** over-provisioning was
originally motivated by the FTL-exhaustion hypothesis, and Phase 1 eliminated
that hypothesis. Over-provisioning is now cheap insurance to apply *if* an array
is rebuilt for some other reason — not a reason to rebuild.

### On RAID 5 → RAID 10 specifically — the answer is destroy + recreate

Queried directly with the now-installed `perccli64` against this exact
controller and firmware (`PERC H730P Mini`, serial `84P036E`, FW package
`25.5.9.0001`, chip revision `C0`):

| Capability | Reported |
|---|---|
| `Reconstruction` | **Yes** — the controller does support RLM / Online Capacity Expansion in general |
| `Reconstruction Rate` | 30% |
| Current VD | `0/0  RAID5  Optl  RW  Consist=Yes  Cache=RWBD  1.745 TB`, strip 64 KB |
| `Support Breakmirror` | Yes |

So RLM is *supported by the hardware* — but that does not make RAID 10 a
reachable target. MegaRAID's reconstruction matrix moves a VD between
**single-span** levels only:

| From | Valid RLM targets |
|---|---|
| RAID 0 | RAID 1, 5, 6 |
| RAID 1 | RAID 0, 5, 6 |
| **RAID 5** | **RAID 0, RAID 6** |
| RAID 6 | RAID 0, 5 |

**RAID 10 appears in no row.** It is a *spanned* array (a stripe over multiple
RAID 1 spans), and MegaRAID constructs spans only at VD-creation time — there is
no reconstruction path that turns a single-span VD into a spanned one, from
RAID 5 or from anything else.

**Conclusion: RAID 5 → RAID 10 on this host REQUIRES destroy + recreate.** The
array's data does not survive it. This is exactly the dependency the plan's
Phase 3 (backup), Phase 4 (verify the backup), and Phase 5 (prove CI falls back
to GitHub-hosted runners) exist to satisfy, and it means those phases are
**mandatory prerequisites** rather than precautions, if RAID 10 is chosen.

This was determined from the controller's reported capabilities plus the
documented MegaRAID reconstruction matrix, **not** by attempting a migration —
attempting one to see whether it is offered would risk the live array. If a
belt-and-braces confirmation is wanted before committing, `perccli64
/c0/v0 start migrate type=raid10` can be issued **after** the backup is verified
and is expected to be rejected as an unsupported target; do not run it before
then.

### 3. Boot-time PERC configuration — always available

Because the host is **UEFI**, the modern path is **F2 → System Setup → Device
Settings → the RAID controller's HII menu**, not the legacy Ctrl+R utility.
Offers VD create/delete, RAID level, strip size, and cache policy. Requires the
host to be down and someone (or an iDRAC console) present.

Dell boot keys for this platform, worth recording because Phase 6 needs them:
**F2** = System Setup, **F11** = Boot Manager, **F10** = Lifecycle Controller.

## Open items

1. ~~Acquire `perccli` and/or `storcli`.~~ **DONE 2026-08-28** — both installed
   and verified against this controller; the RAID-level-migration question is
   answered above.
2. **Restore iDRAC network reachability**, static-addressed, and verify HTTPS +
   virtual media. Proposed, not performed. Gates the Phase 6 approach.
3. **Decide whether `racadm` is needed at all.** If iDRAC's web UI and virtual
   media are reachable, `racadm` is a convenience rather than a requirement, and
   Dell's OpenManage repo has no Ubuntu 26.04 suite (newest `jammy`, OMSA
   11.1.0.0). Do not spend effort here until item 2 is resolved — and note that
   `racadm` cannot substitute for item 2, since remote `racadm -r <ip>` needs
   the same unreachable network path the web UI does. Local `/dev/ipmi0` and
   `ipmitool` already cover in-band BMC work.

## Consequence for Phase 6

The plan-overview's Phase 6 lists "steps to set up a reverse SSH tunnel to this
machine off an Ubuntu rescue disk if needed to allow agentic work while the array
is being rebuilt". That remains a valid fallback, but it is now the **second**
choice. Restoring iDRAC is cheaper, more reliable, and available before the host
is taken down rather than depending on successfully booting rescue media on a
machine whose storage is mid-rebuild.

**Revised Phase 6 prerequisite ordering:** restore iDRAC → verify console, power
control, and virtual media → *then* schedule the destructive window, with the
rescue-USB tunnel retained only as a documented contingency.
