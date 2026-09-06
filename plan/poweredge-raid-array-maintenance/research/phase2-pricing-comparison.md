# Phase 2 — what the options actually cost

Researched 2026-08-28, US retailers, USD. Prices the four hardware paths the
Phase 2 analysis identified, so the optimization decision can be made on cost
rather than on assumption.

**Every number here is distorted by an ongoing NAND shortage and will be stale
within weeks. Re-check before ordering.**

## Bottom line

Three findings, each of which inverts advice that was correct a year ago:

1. **Consumer SATA now costs MORE than consumer NVMe** for the same capacity.
   "Just fill the bays with cheap consumer SATA" — the intuitive budget option —
   is the **worst value on this page**, dominated in every configuration.
2. **Used enterprise NVMe is competitive with new consumer NVMe**, and it keeps
   power-loss protection. This makes the PLP trade-off largely moot rather than
   merely acceptable.
3. **The R630's Slot 1 supports x4x4x4x4 bifurcation**, confirmed in Dell's own
   manual. So a mirrored NVMe pair needs only a **$40 passive dual-M.2 card**,
   not a $128–250 PCIe-switch card.

**Best performance per dollar: two 2TB consumer NVMe + a $40 dual-M.2 card in
Slot 1, mirrored with Linux `md` — roughly $560–820.**

## The market context, because it explains every number

- NAND contract prices rose **33–38% QoQ in Q1 2026**, then a further
  **70–75% QoQ in Q2 2026**.
- Consumer SSD prices roughly **doubled since late 2025** — 2TB NVMe went from
  ~$120 to $260+.
- **All 2026 NAND production is already sold out**; new capacity is not expected
  until late 2027–2028.
- Manufacturers are prioritising high-margin AI datacenter parts, which has
  **gutted the new enterprise drive channel** — hence the four-figure prices and
  out-of-stock listings below.

The 2.5" SATA form factor is being wound down, so it is absorbing the shortage
*worse* than M.2. That is the mechanism behind finding 1.

## Summary comparison

Totals include adapters and caddies.

| Option | Configuration | Qty | Unit | Adapters/caddies | **Total** |
|---|---|---|---|---|---|
| **A** Consumer NVMe 2TB | single scratch | 1 | $260–390 | $30–36 | **$290–426** |
| **A** Consumer NVMe 2TB | **mirrored pair** | 2 | $260–390 | $40 dual card | **$560–820** |
| A′ Consumer NVMe 2TB | mirrored, switch card | 2 | $260–390 | $128–250 | $648–1,030 |
| **B** Enterprise NVMe 1.92TB — **new** | single | 1 | $1,469–2,112 | $31 | **$1,500–2,143** |
| **B** Enterprise NVMe 1.92TB — **used** | single | 1 | $299–486 | $31 | **$330–517** |
| **B** Enterprise NVMe 1.92TB — **used** | mirrored pair | 2 | $299–486 | $62 | **$660–1,034** |
| **C** Enterprise SATA 1.92TB — new | add one | 1 | $1,300–1,569 | $20 | $1,320–1,589 |
| **C** Enterprise SATA 1.92TB — **used** | add one | 1 | $229–400 | $20 | **$249–420** |
| **C** Enterprise SATA 1.92TB — **used** | fresh 4-drive RAID 10 | 4 | $229–400 | $80 | **$996–1,680** |
| **C** Enterprise SATA 1.92TB — **used** | fill all 8 bays | 5 | $229–400 | $100 | **$1,245–2,100** |
| **D** Consumer SATA 2TB | add one | 1 | $400–600 | $20 | $420–620 |
| **D** Consumer SATA 2TB | fresh 4-drive RAID 10 | 4 | $400–600 | $80 | $1,680–2,480 |
| **D** Consumer SATA 2TB | fill all 8 bays | 5 | $400–600 | $100 | $2,100–3,100 |

## Option D is dominated — the direct answer to "just fill out with consumer SATA"

Consumer SATA 2TB runs **$400–600** (Samsung 870 EVO $400 — and that is a
*62%-off promotional* price against a $1,040 list; Crucial MX500 $600). Consumer
NVMe 2TB runs **$260–390**.

So filling the bays with consumer SATA costs **more per drive than consumer
NVMe** while delivering roughly **one tenth the throughput** and none of the
random-IOPS improvement the Phase 2 measurement says is the actual problem. It
also inherits the RAID 5 read-modify-write penalty unless the array is
rebuilt — which means paying the full Phases 3–7 destructive cost for the
slowest option on the page.

**There is no configuration in which Option D is the right answer.** Used
enterprise SATA (Option C) costs *less* per drive ($229–400) and is a better
drive in every respect.

## Per-option notes

### A — Consumer NVMe (M.2 + low-profile adapter)

New, 2TB class: Kingston NV3 $260 · WD Black SN770 $270 · Silicon Power UD90
$290 · Crucial P310 $290 · WD Black SN7100 $302 · WD Black SN850X $368 ·
Samsung 990 Pro $390.

**Adapter — the part that must fit a 1U chassis.** The **Vantec UGT-M2PC130
($30–35)** is explicitly marketed for 1U rackmount, is 130×31×10 mm, stands
23 mm above the slot, supports 22110, and ships with a heatsink. StarTech
PEX4M2E1 ($36) is the alternative. For a mirrored pair, a passive dual-M.2
bifurcation card is **$40**.

**Bifurcation is confirmed supported.** Dell's PowerEdge R630 Owner's Manual
(Integrated Devices) documents **Slot 1 (x16): Default / x8x8 / x4x4x4x4, in
both two-slot and three-slot riser configurations**. The setting is per-slot in
BIOS → Integrated Devices. Slot 1's x16 electrical width means four M.2 drives
on one card is possible if ever wanted.

Caveat: this verifies the *documented platform capability*, not this specific
BIOS revision's behavior. Keep the PCIe-switch card (row A′, $128–250) as a
known-cost escape hatch rather than a planned purchase.

**Do not buy a cheap card that claims to avoid bifurcation.** A genuine PCIe
switch chip costs more than a $29 card's total price; cards in the $22–40 band
advertising "without PCIe Bifurcation Function" are usually SATA+NVMe combo
boards or mislabeled passive cards. Moot here, since Slot 1 bifurcates natively.

### B — Enterprise NVMe with power-loss protection

**New is not a sane purchase right now.** Micron 7450 PRO 1.92TB $1,469;
Solidigm D7-P5520 1.92TB $1,675–2,112. Samsung PM9A3 is **out of stock** at
ServerPartDeals — the most reputable US enterprise-drive vendor having zero
PM9A3 inventory is itself the finding.

**Used is the competitive line:** Samsung PM9A3 1.92TB U.2 at ~$435 + $50
shipping. **A used PM9A3 landed at ~$485 versus a new Samsung 990 Pro at
$390** — about 25% more for power-loss protection, ~1 DWPD endurance, and a
drive built for continuous server duty. Against the cheapest consumer NVMe
($260) the gap is wider.

**Prefer AIC/HHHL over U.2 if you can find one.** An AIC drive plugs straight
into Slot 1 with no adapter and no cable. Low-profile candidates: Intel DC P3520
2TB, Intel DC P4500 (Intel documents it as half-height half-length low-profile),
Micron 9100, Samsung PM1725b. **Current street prices for these could not be
verified** — older Gen3 parts trading thinly on eBay. Promising unpriced lead,
not a costed option.

**U.2 bracket trap:** StarTech's PEX4SFF8639 U.2 adapter is described with a
*"vented full-profile bracket"*. **Confirm a low-profile bracket is included
before buying any U.2 adapter** — this is exactly the 1U trap that the Phase 0
note flags for add-in cards generally.

### C — Enterprise SATA 2.5" (1.92TB)

New is broken the same way ($1,300–1,569). **Used is the realistic line:**
Samsung PM863a ~$229 · Intel D3-S4510 (2 DWPD) ~$265 · Samsung SM883 $270 ·
HP-badged SM883 $400. Verified range **$119–208/TB**.

**⚠️ Quantity-1 is a capacity trap.** Adding one **1.92TB** drive to the three
existing **960GB** drives yields a 4-drive RAID 10 sized by the *smallest*
member — 960GB × 4 = 1.92TB usable — wasting half the new drive. **If buying one
drive to complete a RAID 10 with the existing three, buy a ~960GB drive**, at
roughly half the cost. The 1.92TB quantity-1 row exists because it was asked
for; it is the wrong purchase.

**⚠️ Interface check on used drives.** One source cites "$55 for a 1.92TB data
center drive" and $30–50/TB generally — 4–8× below every verified listing.
Those are likely **SAS** drives, very high-wear units, or expired listings. **A
SAS drive physically fits a SATA port and does not work**, and it is the most
common used-market mistake. Verified pricing is used here.

**Used-drive hygiene:** check SMART for power-on hours (<20,000), endurance
consumed (<10%), total bytes written against rated endurance, and zero
reallocated sectors. Run `badblocks -wsv` before trusting one — about a day per
2TB drive.

### D — Consumer SATA 2.5" (2TB)

Samsung 870 EVO $400 (promotional, against $1,040 list) · Crucial MX500 $600.
See "Option D is dominated" above.

## The easily-forgotten items

- **Drive caddies — needed for every bay drive.** Genuine Dell **G176J, new,
  $19.99** with a 3-year warranty at ServerPartDeals, listing explicitly naming
  the R630. ServerSupply lists the same part at $40. Third-party multipacks work
  (a caddy is a purely mechanical sled with no electronics) and historically run
  $8–15/unit, but **at $19.99 for a genuine new part the saving is not worth
  chasing**. The R630 needs the **G176J-type 11th/12th/13th-generation 2.5" SFF
  sled** — 14th-generation servers use a different tray.
- **SATA interposer: NOT needed, $0.** Dell's documentation is explicit that an
  interposer is not required for SATA drives in PowerEdge servers; SATA mounts
  exactly as SAS does. Interposers were for SATA drives in PowerVault
  MD1000-class external enclosures and for mixed SAS+SATA dual-path redundancy.

## Two architectural consequences to price in

**The PERC H730P cannot see NVMe.** Options A and B bypass the RAID controller
entirely via Slot 1, so those devices get **no hardware RAID and no
battery-backed writeback cache** — you use Linux `md`, LVM, or ZFS instead. For
a rebuildable CI host that is arguably better (no controller lock-in, portable
arrays), but it is a different operational model from the existing H730P array.
Options C and D keep everything under the H730P.

**Non-Dell drives on the H730P work but get flagged.** They show as
"non-certified" in OMSA/iDRAC with a yellow warning, which Dell notes can reduce
predictive-failure alerting. Arrays build and run normally. For a rebuildable lab
host this is cosmetic, but **it will make iDRAC health permanently amber** —
worth knowing before it alarms someone at 3am.

## Confidence

**Verified by direct page fetch 2026-08-28:** ServerPartDeals G176J $19.99;
Newegg Samsung PM893, Solidigm D7-P5520, Crucial MX500, Samsung 990 Pro,
StarTech PEX4M2E1, dual-M.2 cards; ServerPartDeals PM9A3 out-of-stock; Dell R630
manual bifurcation table.

**From aggregators dated within three weeks:** the 2TB consumer NVMe table
(2026-08-27); Samsung 870 EVO $400 (2026-08-11).

**Could not verify:** AIC/HHHL enterprise NVMe street prices; third-party caddy
multipack prices; whether the StarTech U.2 adapter ships a low-profile bracket.

**Rejected as unreliable:** a $30–50/TB used-drive figure (4–8× below verified
listings); a $9,999.99 listing (an out-of-stock placeholder, not a price); a
$1,111 used U.2 (reseller markup); a $148 MX500 and a $150/$366 PM893 (stale
cache or phantom stock, against a consistent $1,150+ new channel).

**Volatility.** eBay pages timed out repeatedly, so used-market numbers come
from search snippets — treat as ±25%. The Samsung 990 Pro traded between $360
and $918 within 2026. **Do not treat any figure here as valid in a month.**
