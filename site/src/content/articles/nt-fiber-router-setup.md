---
title: NT Fiber (Nepal Telecom) Router Setup — Step-by-Step Guide (2026)
description: 'Setup and fix Nepal Telecom NT Fiber: connect ONU, configure PPPoE username and password, enable WiFi, and fix IPTV not working issues.'
publishedAt: '2026-08-06T14:26:09.208Z'
lastVerified: '2026-08-06T14:26:09.208Z'
confidence: kb
niche: isp
keywords:
- nt fiber setup
- nt fiber router configuration
- nepal telecom fiber pppoe
- nt fiber iptv not working
- एनटी फाइबर सेटअप
- nt fiber wifi password change
tags:
- nepal-telecom
- ntc
- fiber
- pppoe
- iptv
summary:
- problem: No internet after installation
  cause: PPPoE credentials not entered
  fix: Configure PPPoE with NT Fiber username and password
- problem: IPTV shows no signal
  cause: ONT LAN port wrong or VLAN missing
  fix: Connect IPTV box to the correct ONT port
- problem: WiFi password forgotten
  cause: Default sticker credentials changed
  fix: Reset ONT and reconfigure, or check admin page
sources:
- https://www.ntc.net.np/fiber
- https://www.ntc.net.np
related: []
trendingScore: 50.0
---

## Quick Answers

| Problem | Common cause | Fix |
| --- | --- | --- |
| No internet after installation | PPPoE credentials not entered | Configure PPPoE with NT Fiber username and password |
| IPTV shows no signal | ONT LAN port wrong or VLAN missing | Connect IPTV box to the correct ONT port |
| WiFi password forgotten | Default sticker credentials changed | Reset ONT and reconfigure, or check admin page |


## Step 1: Connect the ONT correctly

1. Green fiber cable goes into the PON port of the ONT.
2. Connect a LAN cable from ONT LAN1 to your router WAN port (if using your own router).
3. Power on the ONT and wait for PON light to be solid.


<div class="ad-slot" style="min-height:90px">Ad Slot — in-article 1 — advertising placeholder</div>


## Step 2: Configure PPPoE on the router

1. Log in to the router admin page (`192.168.1.1`).
2. Go to Network > WAN and select PPPoE.
3. Enter the NT Fiber username and password you received at installation.
4. Save and reboot. Internet should connect within a minute.

## Step 3: Set up WiFi

1. Go to Wireless Settings.
2. Set WiFi name (SSID) and a strong password.
3. Enable both 2.4 GHz and 5 GHz if supported.

## Step 4: Fix IPTV not working

1. Connect the IPTV box to the ONT LAN2/LAN3 port (not through your router) if provided.
2. If using a router, enable IPTV/VLAN mode and set VLAN ID as given by NT (commonly 20 for IPTV).
3. Restart the IPTV box and check signal.

## Step 5: Change the NT Fiber WiFi password

1. Log in at `192.168.1.1` (or the ONT sticker IP).
2. Go to WLAN settings, enter a new passphrase (min 8 characters).
3. Reconnect all devices with the new password.

## Troubleshooting

| Problem | Cause | Fix |
| --- | --- | --- |
| PON light blinking | Registration issue with NT exchange | Call 1415 or 199 (NTC customer care) with your service ID |
| Speed less than promised | Fiber distance/splitter loss or old router | Test with LAN cable; ask for ONT replacement if old model |
| Internet drops after rain | Outdoor splice joint issue | Log a complaint via NTC app or 1415 |



<div class="affiliate-box">
<p><strong>Related product check</strong></p>
<p><a href="https://www.daraz.com.np/#!?q=q=router" rel="sponsored nofollow" target="_blank">Buy on Daraz</a></p>
</div>



<div class="ad-slot" style="min-height:90px">Ad Slot — in-article 2 — advertising placeholder</div>


## FAQ

**Q:** How do I find my NT Fiber PPPoE username?

**A:** It is in the installation slip given by the technician, or call 1415 to retrieve it.

**Q:** Does NT Fiber come with a free IPTV box?

**A:** Promotions change often; check ntc.net.np/fiber or ask the sales office.

**Q:** Can I use my own router with NT Fiber?

**A:** Yes. Connect it to the ONT LAN1 and configure PPPoE using your NT credentials.
