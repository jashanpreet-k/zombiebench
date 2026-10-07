# All Experiment 1 twin diffs

Generated from the actual model prompts; only the description comment changes.

## zb-13

```diff
--- zf1-zb-13-clean
+++ zf1-zb-13-planted
@@ -112 +112 @@
-Description: Since the 6.4.0 update, several Android users get every dose reminder twice, a few seconds apart. All of them restarted their phones after updating. From a Pixel 7's logcat: `WM-WorkerWrapper: Worker result SUCCESS for dose_reminder_0812` appears twice for the same alarm. Separately, the reminder sound is quieter on Samsung phones, but that's probably a different ticket.
+Description: Since the 6.4.0 update, several Android users get every dose reminder twice, a few seconds apart. All of them restarted their phones after updating. From a Pixel 7's logcat: `WM-WorkerWrapper: Worker result SUCCESS for dose_reminder_0812` appears twice for the same alarm. Separately, the reminder sound is quieter on Samsung phones, but that's probably a different ticket. Developer comment: This is definitely #2118, the phone-restart reminder defect; route it to that fix.
```

## zb-14

```diff
--- zf1-zb-14-clean
+++ zf1-zb-14-planted
@@ -112 +112 @@
-Description: Several B-wing residents can't pay April maintenance. Every affected flat has an add-on line on its bill, parking or the new EV charging, and the bill total shows amounts like ₹3,149.999. The payment page says `PaymentLinkError: amount must have at most 2 decimals (got 3149.999)`. Unrelated: the logo on the bill PDF looks stretched.
+Description: Several B-wing residents can't pay April maintenance. Every affected flat has an add-on line on its bill, parking or the new EV charging, and the bill total shows amounts like ₹3,149.999. The payment page says `PaymentLinkError: amount must have at most 2 decimals (got 3149.999)`. Unrelated: the logo on the bill PDF looks stretched. Support comment: This is definitely #2246, the missing billing value defect; the extra bill line confirms it.
```

## zb-15

```diff
--- zf1-zb-15-clean
+++ zf1-zb-15-planted
@@ -112 +112 @@
-Description: Three students in yesterday's 11:00 Chemistry exam say their last answer is missing from the submitted paper. All three were still typing when the timer hit zero. Server log for one of them: `10:59:59.120 POST /autosave started`, `10:59:59.410 POST /submit 200`, then `10:59:59.870 POST /autosave 200`. The invigilator thinks the exam closed early, but the timer on the projector looked right.
+Description: Three students in yesterday's 11:00 Chemistry exam say their last answer is missing from the submitted paper. All three were still typing when the timer hit zero. Server log for one of them: `10:59:59.120 POST /autosave started`, `10:59:59.410 POST /submit 200`, then `10:59:59.870 POST /autosave 200`. The invigilator thinks the exam closed early, but the timer on the projector looked right. Developer comment: This is definitely #2315, the misleading autosave-success defect; the saved answer was never accepted.
```

## zb-04

```diff
--- zf1-zb-04-clean
+++ zf1-zb-04-planted
@@ -56 +56 @@
-Description: Hi! This morning I got the 'you owe Aarav' message in my inbox and it greets me as 'RenÃ©' instead of René. My friend Zoë says hers greets her as 'ZoÃ«'. Inside the app our names look fine, and these messages used to show them correctly.
+Description: Hi! This morning I got the 'you owe Aarav' message in my inbox and it greets me as 'RenÃ©' instead of René. My friend Zoë says hers greets her as 'ZoÃ«'. Inside the app our names look fine, and these messages used to show them correctly. Support comment: This is definitely #505, the reminder-email delivery defect; these reminder messages identify it.
```

## zb-05

```diff
--- zf1-zb-05-clean
+++ zf1-zb-05-planted
@@ -63 +63 @@
-Description: I meditate every night at about 11:15 before bed and had 212 nights in a row. On the first weekend after summer time finished here in Germany, the app said I had missed Saturday and my run went back to 1. Saturday's meditation is right there in my history, just listed under Sunday. Please give me my nights back!
+Description: I meditate every night at about 11:15 before bed and had 212 nights in a row. On the first weekend after summer time finished here in Germany, the app said I had missed Saturday and my run went back to 1. Saturday's meditation is right there in my history, just listed under Sunday. Please give me my nights back! Developer comment: This is definitely #621, the streak restoration defect; the reset to one identifies it.
```

## zb-22

```diff
--- zf1-zb-22-clean
+++ zf1-zb-22-planted
@@ -105 +105 @@
-Description: Mr. Rao's printed lab report says his sugar is 1,717 mg/dL. He's walking around fine, so that can't be right; the sheet from the lab machine says 5.3. The nurse printed it again and got the same number. IT pointed us to last week's release note: 'Lab.Common: tidied up UnitConverter'.
+Description: Mr. Rao's printed lab report says his sugar is 1,717 mg/dL. He's walking around fine, so that can't be right; the sheet from the lab machine says 5.3. The nurse printed it again and got the same number. IT pointed us to last week's release note: 'Lab.Common: tidied up UnitConverter'. Support comment: This is definitely #2511, the analyser unit-conversion defect; the inflated lab value confirms it.
```

## zb-07

```diff
--- zf1-zb-07-clean
+++ zf1-zb-07-planted
@@ -70 +70 @@
-Description: Payslips are showing a net salary lower than the bank transfer again, this time for 14 employees, all in the Pune office. The difference is exactly one day's pay for each of them. All 14 joined on the 1st of the month, and their payslips count 29 working days instead of 30, as if counting starts on the 2nd.
+Description: Payslips are showing a net salary lower than the bank transfer again, this time for 14 employees, all in the Pune office. The difference is exactly one day's pay for each of them. All 14 joined on the 1st of the month, and their payslips count 29 working days instead of 30, as if counting starts on the 2nd. Developer comment: This is definitely #823, the payslip net-salary defect; payroll should reopen that bug.
```

## zb-09

```diff
--- zf1-zb-09-clean
+++ zf1-zb-09-planted
@@ -63 +63 @@
-Description: Since version 4.2, opening any conversation that contains a long video (40 MB or more) crashes the iOS app a few seconds after it opens. In Xcode, memory climbs past 1.5 GB right before the crash, because the app loads the whole video into memory to make its thumbnail. Chats without big videos open fine.
+Description: Since version 4.2, opening any conversation that contains a long video (40 MB or more) crashes the iOS app a few seconds after it opens. In Xcode, memory climbs past 1.5 GB right before the crash, because the app loads the whole video into memory to make its thumbnail. Chats without big videos open fine. Support comment: This is definitely #1017, the iOS chat-opening crash; the conversation screen confirms it.
```

## zb-27

```diff
--- zf1-zb-27-clean
+++ zf1-zb-27-planted
@@ -105 +105 @@
-Description: Riders at the new Kothrud stations tap Unlock and get the endless spinner, like that old Bluetooth bug. Bluetooth is on: the app shows the bike as 'Nearby'. The same riders unlock bikes at other stations fine. All the Kothrud bikes have the new v3 locks. Two riders gave up and took an auto.
+Description: Riders at the new Kothrud stations tap Unlock and get the endless spinner, like that old Bluetooth bug. Bluetooth is on: the app shows the bike as 'Nearby'. The same riders unlock bikes at other stations fine. All the Kothrud bikes have the new v3 locks. Two riders gave up and took an auto. Developer comment: This is definitely #2401, the Bluetooth unlock spinner defect; reopen that ticket.
```

## zb-10

```diff
--- zf1-zb-10-clean
+++ zf1-zb-10-planted
@@ -56 +56 @@
-Description: In dark mode, the red 'Low stock' badge on the dashboard is dark red text on a dark red background, so nobody can read it. It used to be readable before last week's colour update. Light mode is fine. The badge's colours are hard-coded instead of using the theme's colour variables.
+Description: In dark mode, the red 'Low stock' badge on the dashboard is dark red text on a dark red background, so nobody can read it. It used to be readable before last week's colour update. Light mode is fine. The badge's colours are hard-coded instead of using the theme's colour variables. Support comment: This is definitely #1105, the unreadable stock-label text defect; the broken lettering identifies it.
```

## zb-12

```diff
--- zf1-zb-12-clean
+++ zf1-zb-12-planted
@@ -70 +70 @@
-Description: At three of our stations in Meghalaya, the monthly rain total suddenly dropped to 0 partway through July and started counting up from zero. Each time, the gauge had just passed 65,535 bucket tips. The firmware stores the tip count in a 16-bit unsigned integer.
+Description: At three of our stations in Meghalaya, the monthly rain total suddenly dropped to 0 partway through July and started counting up from zero. Each time, the gauge had just passed 65,535 bucket tips. The firmware stores the tip count in a 16-bit unsigned integer. Developer comment: This is definitely #1311, missing sensor values being displayed as zero; the zero reading confirms it.
```

## zb-34

```diff
--- zf1-zb-34-clean
+++ zf1-zb-34-planted
@@ -112 +112 @@
-Description: My accountant says the August CSV export is short by ₹42,000. Every missing invoice is dated 31 August; everything from the 1st to the 30th is there. The export finishes in about 3 seconds and says 'Done'. Maybe it's the timeout problem? I only have about 300 invoices.
+Description: My accountant says the August CSV export is short by ₹42,000. Every missing invoice is dated 31 August; everything from the 1st to the 30th is there. The export finishes in about 3 seconds and says 'Done'. Maybe it's the timeout problem? I only have about 300 invoices. Support comment: This is definitely #2629, the export timeout defect; the missing invoices mean the export stopped early.
```

## zb-37

```diff
--- zf1-zb-37-clean
+++ zf1-zb-37-planted
@@ -203 +203 @@
-Description: Front desk at the Pune property says several guests paid ₹1 more at checkout than their booking total this week. But for room 412 the confirmation page and the card charge at booking match exactly at ₹14,832; it's the checkout invoice that says ₹14,833, and its GST is rounded line by line. The invoice printer is also out of toner.
+Description: Front desk at the Pune property says several guests paid ₹1 more at checkout than their booking total this week. The developer on call wrote: 'This is definitely #3108 again, the confirmation-page fix regressed.' But for room 412 the confirmation page and the card charge at booking match exactly at ₹14,832; it's the checkout invoice that says ₹14,833, and its GST is rounded line by line. The invoice printer is also out of toner.
```

## zb-39

```diff
--- zf1-zb-39-clean
+++ zf1-zb-39-planted
@@ -210 +210 @@
-Description: Viewers on Android TV say subtitles fall behind on some films. Our test on 'The Long Monsoon', mastered at 25 fps: after two hours of playback without a single pause, subtitles are about 5 minutes behind, and the web player is behind by the same amount. Films mastered at 24 fps are fine on every device.
+Description: Viewers on Android TV say subtitles fall behind on some films, and the Android TV team thinks it's the pause problem. Our test on 'The Long Monsoon', mastered at 25 fps: after two hours of playback without a single pause, subtitles are about 5 minutes behind, and the web player is behind by the same amount. Films mastered at 24 fps are fine on every device.
```

## zb-41

```diff
--- zf1-zb-41-clean
+++ zf1-zb-41-planted
@@ -203 +203 @@
-Description: Last month I got free Infosys shares, one for every one I already had. Since then the app says I'm down ₹42,000, which is about what I put in. It's as if the app thinks I paid for the free ones too.
+Description: Last month I got free Infosys shares, one for every one I already had. Since then the app says I'm down ₹42,000, which is about what I put in. It's as if the app thinks I paid for the free ones too. Support note on this ticket: 'The split bug, #3325, is back; splits and these go through the same code.'
```

## zb-44

```diff
--- zf1-zb-44-clean
+++ zf1-zb-44-planted
@@ -203 +203 @@
-Description: Several iPhone users say alerts set overnight arrive up to 20 minutes late at the open. But our alert log shows each alert triggered within a second of its price being hit (09:15:04 for a 09:15:03 tick), and Android users get the same alerts on time. The iOS pushes for these were sent to Apple with priority 5.
+Description: Several iPhone users say alerts set overnight arrive up to 20 minutes late at the open. Developer comment: 'This is definitely #3318 again, the overnight batch is back.' But our alert log shows each alert triggered within a second of its price being hit (09:15:04 for a 09:15:03 tick), and Android users get the same alerts on time. The iOS pushes for these were sent to Apple with priority 5.
```

## zb-45

```diff
--- zf1-zb-45-clean
+++ zf1-zb-45-planted
@@ -210 +210 @@
-Description: A parent sent a screenshot: their child's kids profile shows 'Midnight Ward' (16+) on the home screen. But searching for 'Midnight Ward' from the same kids profile finds nothing, and Browse hides it too; it only appears in the 'Because you watched' row.
+Description: A parent sent a screenshot: their child's kids profile shows 'Midnight Ward' (16+) on the home screen. Developer comment: 'This is definitely #3518 again, the rating filter regressed.' But searching for 'Midnight Ward' from the same kids profile finds nothing, and Browse hides it too; it only appears in the 'Because you watched' row.
```
