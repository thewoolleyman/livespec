# Adding SATA SSDs to this host — compatibility, proven two ways

Verified 2026-08-28 before committing to a hardware purchase. Two **independent**
passes — one from vendor documentation, one against the live machine — were run
deliberately so that neither could reproduce the other's blind spot. They agree
on every load-bearing point.

**Read this before buying drives for `poweredge-xubuntu`, and before planning
the Phase 6 rebuild.**

## Bottom line

**Four more 2.5" SATA SSDs can go into the free bays. No cable is needed. The
PCIe video card stays installed. No chassis-internal work is required at all.**

The specific drive verified: **Dell part `0X31G3` = Intel/Solidigm D3-S4610,
`SSDSC2KG960G8R`, 960 GB, SATA 6 Gb/s, 2.5", 3 DWPD**.

## Why two passes

A single verification can be confidently wrong when its instrument is wrong —
the failure mode recorded in `.ai/verifying-against-the-right-source.md`, where
independent reviewers sharing one flawed method produce agreement that reads as
corroboration but is one answer counted twice. So the two passes were given
**different instruments and forbidden each other's**:

- **Documentary** — Dell manuals, the PERC 9 User's Guide, Solidigm spec sheets.
  Explicitly barred from touching the host.
- **Empirical** — `perccli64`, `ipmitool`, `lspci`, `dmidecode`, `smartctl`
  against the live machine, strictly read-only. Explicitly barred from resting
  its verdict on vendor documentation.

The split paid off concretely: the empirical pass could not verify the *new*
drive's capacity, because it cannot measure a drive that is not installed. The
documentary pass proved it independently. Each closed a gap the other could not
reach.

## The video card stays — proven twice

This was the maintainer's explicit constraint.

**Documentary** — R630 Owner's Manual, §"Integrated storage controller card":

> "Your system includes a **dedicated expansion card slot on the system board**
> for an integrated controller card."

The mini-PERC appears **nowhere** in the manual's Table 20 enumeration of
general-purpose expansion slots.

**Empirical** — SMBIOS lists exactly two system slots, and the PERC is in
neither:

| | |
|---|---|
| `dmidecode -t slot` → PCIe Slot 1 | x16, **Available** (empty, no Bus Address) |
| `dmidecode -t slot` → PCIe Slot 2 | **In Use**, Bus Address `0000:03:00.0` |
| `lspci` → Radeon Cedar (VGA) | **`03:00.0`** — i.e. Slot 2 |
| `lspci` → MegaRAID SAS-3 3108 (PERC) | **`02:00.0`** — **in neither slot record** |

The two also hang off different root ports (`00:01.0`→bus 02 for the PERC,
`00:02.0`→bus 03 for the GPU), and iDRAC independently reports
`PCIe Slot1 | Disabled` (empty) / `PCIe Slot2 | ok`.

**Conclusion: drive bays and PCIe slots are structurally independent
subsystems.** Drives are front-loading hot-swap units mating with the backplane;
the chassis lid never comes off. Dell separately documents an eight-drive R630
running a 75 W GPU — the Cedar is a ~20 W passive part, well inside that.

## No cable is needed — proven twice

This was the question behind "do I need to buy cables?", and it was a real risk:
an R630's 8-bay backplane can be wired with one or two SFF-8643 cables, and three
working drives prove only that the *first* lanes are connected.

**Documentary** — the Owner's Manual's x8 cabling figures show
`SAS A connector on system board` **and** `SAS B connector on system board`; two
×4 links = 8 lanes, direct-attached. There is no partial-cabling SKU for the x8
backplane. (The x10 backplane, by contrast, uses an expander.)

**Empirical** — iDRAC's own cable-presence sensors, a direct hardware reading:

```
Cable SAS A0 | E4h | ok | 26.2 | Connected
Cable SAS B0 | E5h | ok | 26.2 | Connected
Cable SAS A1 | E6h | ns | 26.2 | No Reading    ← unused, larger-backplane connectors
BP2 Presence | 55h | ok | 26.2 | Present
```

And a second, independent line of evidence from the PHY map. This matters
because the enclosure's `Slots = 8` arrives over the SGPIO/I2C sideband
(`Auto detect BackPlane = SGPIO/i2c SEP`), so it reports the backplane *model's*
bay count and proves nothing about SAS lanes. But the live drives are not
confined to one lane group:

| PD | SAS Addr | Port | **Phy** |
|---|---|---|---|
| 0 | `4433221104000000` | 01 | **04** |
| 1 | `4433221100000000` | 00 | **00** |
| 2 | `4433221106000000` | 02 | **06** |

Bays sit on PHYs **0, 4, and 6** — spanning *both* ×4 quads. A single SFF-8643
carries one contiguous quad and cannot be half-seated, so **no one cable could
serve PHYs 0, 4 and 6 simultaneously**. Two instruments, same answer.

Topology confirmed direct-attach from the firmware's own discovery log:
`Expander devHandle=x0000`, `On Board Expander = Absent`, every device
`Device_Type = End Device`.

**Honest caveat recorded by the empirical pass:** an unlinked PHY and an
uncabled PHY are indistinguishable in software (PHYs 1, 2, 3, 5, 7 all show
`linkRate 00` with zero error counters). The verdict rests on the iDRAC cable
sensors plus the cross-quad PHY distribution — two independent lines — not on
the empty PHYs. Physical confirmation, if ever wanted, is simply looking at the
backplane rear for two seated cables.

## Vendor lock-out — disproven by observation, not datasheet

The strongest single result, because it is a fact about this machine rather than
a claim about a product line:

```
Un-Certified Hard Disk Drives = Allow

/c0/e32/s0 show all  →  Certified = No
/c0/e32/s1 show all  →  Certified = No
/c0/e32/s2 show all  →  Certified = No
Model: MZ7GE960HMHP-000V3   00FN363 00FN366IBM   FRU/CRU = 00FN363
```

**The production boot array is already running on IBM-OEM drives that
self-report as uncertified.** Non-Dell drives are not merely permitted in
principle; they are load-bearing here today.

The trade-off is still real and worth stating: a non-Dell-firmware drive raises
a non-dismissible advisory in iDRAC/OMSA, parking the storage subsystem in a
permanent warning state. That is a cost — it trains an operator to ignore the
health indicator — not a functional barrier.

## Mixing models in one RAID 10 — permitted

The PERC 9 User's Guide states the **complete** set of prohibitions, and the
controller reports the same two:

| Rule | Applies here? |
|---|---|
| SAS + SATA in one VD — not supported | No — both are SATA |
| HDD + SSD in one VD — not supported | No — both are SSD |
| 4 KB + 512n/512e in one VD — not supported | No — Samsung is **512n**, D3-S4610 is **512e**; only true **4Kn** mixing is banned |

Live controller: `Mix of SAS/SATA of SSD type in VD = Not Allowed`,
`Mix of SSD/HDD in VD = Not Allowed`. **No vendor or model restriction exists in
either source.**

Documented consequence: the array runs at the **slowest** member and is capped
by the **smallest**. The 2014-era Samsungs therefore set the ceiling.

## Everything else that was checked

| Question | Verdict | Evidence |
|---|---|---|
| Capacity match | **Exact** | Existing raw `894.252 GB` / coerced `893.750 GB`; 960 GB standard = 960,197,124,096 B = **894.25 GiB**. `Drive Coercion Mode = 128MB` gives ~259 MiB slack |
| RAID 10 creatable | **Yes** | `RAID Level Supported = ... RAID10(2 or more drives per span)`; `Max Spans Per VD = 8`, `Max Arms Per VD = 32`. 6 drives = 3 spans × 2 — well inside |
| Hot spare | **Yes** | `Dedicated Hot Spare = Yes`, `Global Hot Spares = Yes`, **`Auto Rebuild = On`** |
| Power headroom | **Ample** | 210 W current draw vs `upper-crit 1176 W`; 4 × D3-S4610 ≈ 14.8 W max (3.7 W each) |
| Thermal headroom | **Ample** | Inlet 23 °C, exhaust 33 °C, drives 28–32 °C, ROC 46 °C, 7 fans `Fully Redundant` |
| Bay/PHY count | **8** | `Backend Port Count = 8`; enclosure `Slots = 8`; `/c0/pall show` lists PHYs 0–7 |
| Controller firmware | **Current** | `25.5.9.0001` is Dell release **A17** — the latest. Its notes fix a hot-plug bug where "a hot-plug drive was incorrectly set to non-RAID mode causing auto-rebuild to not start" — directly relevant, and already have it |

## Build notes for Phase 6

Carry these into the rebuild; they are cheap to honour and expensive to
retrofit.

1. **Pair each Samsung with an Intel drive when creating the mirror spans.**
   Otherwise one span carries two 2014-era drives and becomes the array's
   reliability floor. **Drive selection order in the PERC HII utility determines
   span membership** — this is not automatic.
2. **Assign a NEW drive as the hot spare, not a Samsung.** The Samsungs are at
   33,453 / 35,603 / 35,992 power-on hours with 55–77 TB written. Healthy —
   `SMART PASSED`, 0 reallocated sectors, 0 UDMA CRC errors, ~95% life — but
   they will fail first, so the spare should be the drive most likely to
   outlive them.
3. **Keep a drive blank in the unused 8th bay.** The Owner's Manual is explicit
   and repeats it: "To maintain proper system cooling, **all empty hard drive
   slots must have hard drive blanks installed**." Going to 7 drives leaves 1
   blank. **Blanks are not carriers** — a blank cannot mount a drive, and a
   carrier does not substitute for a blank.
4. **7 of 8 bays leaves no room for a second spare** later without displacing a
   member. Worth knowing before settling the layout.

## Purchasing traps found

Recorded because each could have cost money.

- **The same part `0X31G3` ships in two different sleds.** "Generation 13"
  listings include the **G176J** tray (fits); "Generation 14" listings include
  **`DXD9H`** (does **not** fit an R630). The bare drive is identical in both —
  Dell does not generation-lock the firmware; **only the carrier differs**, and
  the two are not interchangeable. *Sidestepped in practice*: the chosen listing
  ships **bare drives**, with G176J caddies bought separately.
- **SAS masquerading in the same price band.** A Seagate Nytro 3350 960GB
  **SAS 12Gb/s** sits at $219 among the SATA parts, and one listing carried the
  SATA part number `SSDSC2KG960G8` in a title reading "12G SAS". A SAS drive
  fits the bay and does not work. Physical tell on a connector photo: **SATA
  separates the data and power segments with a gap; SAS bridges them into one
  continuous connector.**
- **3.5"/hybrid-carrier SKUs at the same price** — `345-BECI`, `089Y1`,
  `0089Y1`, `Y1KT5`, `400-ATED` — will not fit a 2.5" SFF bay.
- **An "800GB" substitute is 745 GiB**, far below the 894 GiB floor.
- A Dell **Owner's Manual typo** says the eight-drive system supports a
  "2.5-inch **(x4)**" backplane; every figure in the same chapter says **(x8)**.
  Do not be alarmed by it.

## What this does NOT resolve

**The rebuild is still destructive, and the array is the boot volume.** The
RAID 5 VD *is* `/dev/sda` — `/boot/efi`, `/`, and `/var/cache/ci-runner` all
live on it. RAID 5 → RAID 10 is not an online migration path on this controller
(see `phase0-controller-management-and-tooling.md`), so it requires
destroy-and-recreate. **Phases 3–5 — backup, verify the backup, prove the CI
fallback — are mandatory prerequisites, not precautions.**

Nothing in this note reduces that. It establishes only that the *hardware* will
accept the drives.
