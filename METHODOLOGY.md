# Methodology note: the VM0048 jurisdictional baseline

## Why this note exists

This project reproduces the *measurement* side of a forest-carbon estimate: it maps
forest and quantifies the carbon standing in it. A real Verra REDD+ registration
needs one more thing that this prototype deliberately does not generate: a
**baseline**, the counterfactual against which forest loss is measured. This note
explains what that baseline is under the current methodology (VM0048), why it sits
outside the developer's hands, and how it would slot into the workflow here. It's
here so the repo shows an understanding of the piece it doesn't build, rather than
quietly ignoring it.

## What changed in 2023

Older REDD+ methodologies let each project set its own baseline: its own estimate
of how much deforestation "would have happened" without the project. That freedom
was a well-documented source of over-crediting, because developers could choose
assumptions that inflated the counterfactual and therefore the credits.

VM0048, approved in late 2023, removes that freedom. Baselines are now standardised
at the level of a whole jurisdiction (a country or a state/province) and produced by
independent data providers appointed by Verra, not by the project. The project no
longer draws its own baseline; it is allocated a share of a jurisdiction-wide one.

## What the jurisdictional baseline actually is

At its core it is a **deforestation-risk map**: a spatial layer covering an entire
jurisdiction that estimates, pixel by pixel, how likely forest loss is. It is built
from two time components:

- A **historical reference period (HRP)**, roughly ten years, over which past forest
  cover and loss are mapped for the whole jurisdiction.
- A **baseline validity period (BVP)**, the six years following the HRP, over which
  that historical pattern is projected forward as expected deforestation risk.

Two versions exist. An open-access, lower-resolution version (1 ha pixels) lets
developers do feasibility and due diligence. To actually register, a developer must
obtain the finer, methodology-compliant (VMD0055) risk data for their specific
project area, through Verra's data-allocation process. The project's expected
baseline emissions are then the share of jurisdictional deforestation risk allocated
to its polygon.

## How it would slot into this project

The important precision: the baseline would **not replace the classification** in
this repo. It replaces the *counterfactual*, the "what would have happened anyway"
line. The measurement machinery here still does its job. In a full registration the
pieces fit together like this:

1. **Activity data (this project's classification).** Map forest, and (with a second
   image date, which this prototype doesn't yet have) measure actual forest loss
   over the period.
2. **Baseline (external, from Verra).** The allocated jurisdictional risk gives the
   expected loss for the same area over the same period.
3. **Emission reductions.** Compare measured loss against the allocated baseline; the
   difference, converted to CO2e with emission factors, is what gets credited.

So the classification and carbon accounting built here are steps 1 and part of 3. The
baseline is the input to step 2 that only Verra's jurisdictional data can provide.

## Where the baseline comes from, and Ghana's current status

The risk maps are being rolled out jurisdiction by jurisdiction, on a rolling basis,
rather than all at once. As of Verra's jurisdictional data table dated May 2026,
released maps covered a limited set of jurisdictions: several Brazilian states had
provisional maps, and a first round of 2026 assignments covered jurisdictions such as
Argentina, Equateur Province in the DRC, and the Philippines. Ghana was not among the
jurisdictions publicly reported as having a released map at that point.

Because this status changes as Verra publishes more maps, the authoritative place to
check whether Ghana (and therefore Kakum) has an available baseline is **Verra's
VMD0055 Jurisdictional Data Table**, which Verra updates as each jurisdiction moves
through the mapping pipeline. If and when Ghana's map is published, a project in Kakum
would draw its baseline from that, not from any layer produced in this repo.

## What this means for this prototype

Two honest consequences, both worth stating rather than hiding:

- This prototype **cannot** produce a registration-grade baseline, by design. Under
  VM0048 that would be an external input, and for Ghana it may not exist yet.
- What this prototype *does* build (the forest map, the area, the emission factors,
  the carbon stock, the uncertainty) is exactly the developer-side measurement work
  that sits alongside the jurisdictional baseline. That is the honest scope: the
  measurement half, done properly, with the baseline half correctly identified as
  external.

## Sources

- Verra, VMD0055 Jurisdictional Data Table (status of risk maps by jurisdiction):
  https://verra.org/methodologies-main/vmd0055-jurisdictional-data-table/
- Verra, "Releases Provisional Versions of Allocated Deforestation Risk Maps":
  https://verra.org/verra-releases-provisional-versions-of-allocated-deforestation-risk-maps-for-new-redd-methodology/
- Space Intelligence, "Breaking Down VM0048: How Risk Maps Change REDD+ Baselines":
  https://www.space-intelligence.com/breaking-down-vm0048-how-risk-maps-change-redd-baselines/
- Space Intelligence, "Verra's VM0048 Frequently Asked Questions" (HRP vs BVP):
  https://www.space-intelligence.com/verra-vm0048-faq/

*Note: the Ghana status above reflects information available around mid-2026. Confirm
the current status against Verra's data table before relying on it.*
