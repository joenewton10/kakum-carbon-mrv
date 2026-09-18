# Value memo: satellite forest monitoring for MEL and certification

In one line: a low-cost, repeatable satellite method that measures forest extent against a defined boundary, with a stated accuracy, and extends to change over time with a second image date. It is the objective evidence that monitoring reports and certification claims depend on.

## The cost of not having this

Programs and certification schemes make claims about forests: that a protected area is holding, that a certified concession is not losing cover, that a reforestation grant is working. Verifying those claims usually means field visits and manual review, which are expensive, infrequent, and hard to defend when a donor or auditor asks "how do you know?" Without an objective, repeatable measurement:

- Audits stay costly and slow, because verification is manual and periodic.
- Certification claims rest on thin evidence between site visits, which is a credibility risk for the scheme that sells the certification.
- Program reporting against forest indicators stays qualitative, which weakens donor confidence and grant renewal.

## What it does

It maps forest against non-forest from free satellite imagery, clipped to an official boundary, and reports forest extent with a measured classification accuracy (95.5% in the Kakum prototype) and an explicit uncertainty range. The Kakum prototype is a single-date snapshot; a second image date is what turns extent into change. It is built as a reproducible pipeline that can be re-run whenever new imagery is available. Its parameters live in a config file, so pointing it at another site takes a boundary and a fresh set of training points, not a rewrite.

## Why it maps to MEL

In MEL terms this is a monitoring indicator (forest extent, and change over time once a second date is added) measured against a baseline, with an accuracy figure that makes it audit-defensible. It speaks directly to two OECD-DAC criteria: effectiveness (is the forest actually being protected?) and efficiency (at a fraction of field-survey cost). Add a second image date and the indicator becomes a trend, which is the encroachment-and-leakage signal a certification body or protected-area program watches over time.

## The value line

- **Audit cost down.** Automated, repeatable monitoring reduces reliance on field verification and lets scarce field budget go where the satellite flags a problem.
- **Certification claim defended.** Objective evidence the forest is intact, between and beyond site visits, protects the credibility the certification sells.
- **Reporting made defensible.** A quantified indicator with a stated accuracy, not a qualitative assertion, is stronger for donor reporting and grant renewal.

## Scope, stated honestly

This is the measurement layer, not a full monitoring system. The prototype is a single-date snapshot; the natural next step is a multi-date time series, which is the actual trend a monitoring dashboard would display. It uses open global datasets, so it is a screening and monitoring tool, not a legal boundary survey.
