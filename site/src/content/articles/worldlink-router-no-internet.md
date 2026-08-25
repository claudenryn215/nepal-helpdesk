---
title: WorldLink Router No Internet Light — 7 Fixes That Work (2026)
description: Your WorldLink router shows no internet light? Try these verified fixes — power cycle, fiber check, router login at 192.168.1.1, DNS change, and calling WorldLink support at 01-5970050.
publishedAt: '2026-08-25T01:06:18.074Z'
lastVerified: '2026-08-25T01:06:18.074Z'
confidence: kb
niche: isp
keywords:
- worldlink router no internet
- worldlink no internet light
- worldlink wifi connected but no internet
- वर्ल्डलिंक इन्टरनेट नचलेको
- 192.168.1.1 worldlink
- worldlink router reset
tags:
- worldlink
- router
- wifi
- fiber
summary:
- problem: WiFi connected but no internet
  cause: DHCP lease expired or DNS failure
  fix: Reboot router, then set DNS to 8.8.8.8 / 1.1.1.1
- problem: No PON / optical light on ONT
  cause: Fiber line cut, loose connector, or OLT port fault
  fix: Reseat the green fiber cable gently, then call support
- problem: Internet light blinking fast
  cause: Line fault registered with the ISP
  fix: Wait 10 minutes, power cycle, then call 01-5970050
sources:
- https://www.worldlink.com.np/support
- https://www.worldlink.com.np/contact
related: []
trendingScore: 50.0
---

## Quick Answers

| Problem | Common cause | Fix |
| --- | --- | --- |
| WiFi connected but no internet | DHCP lease expired or DNS failure | Reboot router, then set DNS to 8.8.8.8 / 1.1.1.1 |
| No PON / optical light on ONT | Fiber line cut, loose connector, or OLT port fault | Reseat the green fiber cable gently, then call support |
| Internet light blinking fast | Line fault registered with the ISP | Wait 10 minutes, power cycle, then call 01-5970050 |


## Step 1: Power cycle the router and ONT

1. Switch off the router and the ONT unit.
2. Wait 60 seconds.
3. Switch both back on and wait 2 minutes for the PON and internet lights to sync.


<div class="ad-slot" style="min-height:90px">Ad Slot — in-article 1 — advertising placeholder</div>


## Step 2: Check the fiber connection

1. Look at the back of the ONT for the green fiber cable.
2. Push the connector in until it clicks.
3. Check for sharp bends or cuts in the fiber near the window or wall.

## Step 3: Log in to the router admin page

1. Connect to the router WiFi.
2. Open a browser and visit `192.168.1.1`.
3. Use the admin password printed on the router sticker (default user is often `admin`).

## Step 4: Set a working DNS

1. In the admin page go to Network > WAN > DNS.
2. Set primary DNS `8.8.8.8` and secondary `1.1.1.1`.
3. Save and reboot the router.

## Step 5: Factory reset the router

1. Press and hold the reset button at the back for 10 seconds until all lights blink.
2. Wait for the router to reboot, then reconnect WiFi.
3. Re-enter WiFi name and password from the sticker.

## Step 6: Call WorldLink support

1. If the PON light is still off after 15 minutes, call **01-5970050**.
2. Give them your customer ID (from your bill) and report the OLT port issue.
3. Ask for a ticket number and expected resolution time.

## Troubleshooting

| Problem | Cause | Fix |
| --- | --- | --- |
| Only power light is on | ONT firmware crashed or hardware fault | Hold reset for 30 seconds; if no change, request ONT replacement |
| WiFi slow on all devices | Congestion or old firmware | Enable 5 GHz band, update firmware from admin page |
| Internet drops every few hours | WAN lease or port flapping | Change WAN DHCP lease to weekly or ask ISP to reset OLT port |



<div class="affiliate-box">
<p><strong>Related product check</strong></p>
<p><a href="https://www.daraz.com.np/#!?q=q=router" rel="sponsored nofollow" target="_blank">Buy on Daraz</a></p>
</div>



<div class="ad-slot" style="min-height:90px">Ad Slot — in-article 2 — advertising placeholder</div>


## FAQ

**Q:** What does the red internet light on my WorldLink router mean?

**A:** The router is not receiving signal from the fiber line. Check the ONT PON light first; if PON is off, call support.

**Q:** How do I reset my WorldLink router?

**A:** Hold the reset button at the back for 10 seconds until all lights blink, then reconfigure via 192.168.1.1.

**Q:** Why is my WorldLink WiFi slow at night?

**A:** Peak-hour congestion. Try the 5 GHz band and restart the router before 8 PM.
