"""ZombieBench: can a model tell a bug coming back from a new one?

Paste this whole file into one cell of a Kaggle Benchmarks notebook and run it.
Then, in the notebook's last cell, pick this task for the leaderboard with:

    %choose zombiebench

Each case gives the model a short history of fixed bugs and one new bug report,
and asks for JSON only:

    {"verdict": "regression" | "new", "bug_id": <number or null>, "reason": "<one sentence>"}

A case passes only when both the verdict and the bug_id are right. A reply that
can't be read as that JSON scores 0 for its case and never stops the run.
The task's score is the share of cases passed, from 0.0 to 1.0.
"""

import json
import re

import kaggle_benchmarks as kbench

# --- CASES: copied from cases.json by embed_cases.py; edit cases.json, then run it ---
CASES = [{'id': 'zb-01',
  'type': 'A',
  'history': [{'id': 211,
               'name': 'Two patients in one slot',
               'cause': 'Race condition',
               'language': 'Python',
               'component': 'booking',
               'symptoms': 'Two patients who booked the same 10:30 slot within the same second both got a '
                           'confirmation, and the doctor had a double booking.',
               'fix_summary': 'Added a unique constraint on doctor and slot, and offered the second patient '
                              'the next free slot.'},
              {'id': 214,
               'name': 'Walk-in patients crash the patient list',
               'cause': 'Null reference',
               'language': 'Python',
               'component': 'patients',
               'symptoms': "The patient list crashed with AttributeError: 'NoneType' object has no attribute "
                           "'strip' whenever a walk-in patient had no phone number.",
               'fix_summary': 'Treated a missing phone number as an empty string before formatting it.'},
              {'id': 219,
               'name': 'Month view without its last day',
               'cause': 'Off-by-one',
               'language': 'JavaScript',
               'component': 'calendar',
               'symptoms': "The month view of the doctor's calendar never showed the last day of the month, "
                           'so appointments on the 30th or 31st were invisible.',
               'fix_summary': 'Looped up to and including the last day instead of stopping one day early.'},
              {'id': 226,
               'name': 'Reminders an hour early after the clock change',
               'cause': 'Timezone',
               'language': 'Python',
               'component': 'reminders',
               'symptoms': 'After the clocks went forward in March, appointment reminder SMSes arrived an '
                           'hour early, because reminder times were saved as local times without a timezone.',
               'fix_summary': "Saved reminder times in UTC together with the clinic's timezone and converted "
                              'them when sending.'},
              {'id': 230,
               'name': 'Devanagari names as boxes on receipts',
               'cause': 'Encoding',
               'language': 'Python',
               'component': 'receipts',
               'symptoms': 'Patient names written in Devanagari printed as empty boxes on PDF receipts.',
               'fix_summary': 'Embedded a Unicode font in the PDF and passed the names through as UTF-8.'},
              {'id': 233,
               'name': 'Receipt a paisa off from the payment',
               'cause': 'Floating point',
               'language': 'Python',
               'component': 'billing',
               'symptoms': 'Consultation fees with GST were calculated as floats, so some receipts showed '
                           '₹1,180.01 while the card was charged ₹1,180.00.',
               'fix_summary': 'Calculated fees in whole paise and rounded once with Decimal.'}],
  'new_report': {'title': 'Appointment reminders an hour early again after the clock change',
                 'description': 'Since the clocks went forward on Sunday, reminder SMSes for our London '
                                'clinics arrive an hour early: a patient booked at 9:00 gets the 8:00 '
                                'reminder at 7:00. The new recurring-appointments feature seems to save '
                                'reminder times as local times without a timezone.',
                 'language': 'Python',
                 'component': 'reminders'},
  'expected': {'verdict': 'regression', 'bug_id': 226},
  'why': 'Same symptom (reminders an hour early after the clock change), same component, and the same cause: '
         'reminder times saved without a timezone.'},
 {'id': 'zb-02',
  'type': 'A',
  'history': [{'id': 302,
               'name': 'Rider app crash before the first GPS fix',
               'cause': 'Null reference',
               'language': 'Kotlin',
               'component': 'rider-app',
               'symptoms': 'The rider app crashed with a NullPointerException when a rider accepted an order '
                           'before the phone had found its location.',
               'fix_summary': 'Waited for the first location before drawing the route.'},
              {'id': 307,
               'name': 'Two orders from one double tap',
               'cause': 'Race condition',
               'language': 'JavaScript',
               'component': 'checkout',
               'symptoms': 'Tapping Place Order twice quickly created two orders and charged the customer '
                           'twice.',
               'fix_summary': 'Sent an idempotency key with each order and disabled the button while it was '
                              'submitting.'},
              {'id': 311,
               'name': 'Old menu prices after a restaurant update',
               'cause': 'Cache',
               'language': 'JavaScript',
               'component': 'menu',
               'symptoms': 'When a restaurant changed its prices, customers kept seeing the old prices for '
                           'up to an hour.',
               'fix_summary': 'Purged the menu cache whenever a restaurant saves its menu.'},
              {'id': 316,
               'name': 'Coupons that died at 5:30 AM',
               'cause': 'Timezone',
               'language': 'JavaScript',
               'component': 'coupons',
               'symptoms': 'Coupons valid until 31 March stopped working at 5:30 AM on 31 March, because the '
                           'expiry was stored as midnight UTC.',
               'fix_summary': "Stored each coupon's expiry as the end of the day in India's timezone."},
              {'id': 320,
               'name': 'Emoji turned delivery notes into ????',
               'cause': 'Encoding',
               'language': 'Python',
               'component': 'orders',
               'symptoms': 'Delivery instructions with emoji were saved as ???? and a few orders failed to '
                           'save at all.',
               'fix_summary': 'Moved the orders table to utf8mb4.'},
              {'id': 325,
               'name': 'Earnings screen that never stops loading',
               'cause': 'Infinite loop',
               'language': 'Kotlin',
               'component': 'rider-app',
               'symptoms': 'The rider earnings screen kept requesting the next page forever when the last '
                           'page came back empty.',
               'fix_summary': 'Stopped paging when a page comes back empty.'},
              {'id': 329,
               'name': 'The ₹249.30000000000004 cart',
               'cause': 'Floating point',
               'language': 'JavaScript',
               'component': 'cart',
               'symptoms': 'Cart totals with a percentage discount showed long decimals like '
                           '₹249.30000000000004, and the payment gateway rejected the amount.',
               'fix_summary': 'Kept all money as whole paise in integers and formatted it only for '
                              'display.'}],
  'new_report': {'title': 'Cart total showing long decimals again (₹399.90000000000003)',
                 'description': 'Since the combo-discount release, carts with a combo show totals like '
                                '₹399.90000000000003 and the payment gateway rejects the amount. The combo '
                                'discount is computed on rupee floats instead of whole paise, so it looks '
                                'like the floating point money problem is back.',
                 'language': 'JavaScript',
                 'component': 'cart'},
  'expected': {'verdict': 'regression', 'bug_id': 329},
  'why': 'Same long-decimal cart totals rejected by the payment gateway, in the cart, caused again by '
         'floating point money math.'},
 {'id': 'zb-03',
  'type': 'A',
  'history': [{'id': 403,
               'name': 'Deadlines shown in UTC',
               'cause': 'Timezone',
               'language': 'TypeScript',
               'component': 'homework',
               'symptoms': 'Homework deadlines of 11:59 PM showed as 6:29 PM, because the page displayed the '
                           'UTC time.',
               'fix_summary': "Displayed deadlines in the school's timezone."},
              {'id': 406,
               'name': '<<<<<<< HEAD on the timetable',
               'cause': 'Merge conflict',
               'language': 'TypeScript',
               'component': 'timetable',
               'symptoms': "The timetable page went live with '<<<<<<< HEAD' and '>>>>>>> exams-week' "
                           "printed above the table, and both versions of Friday's periods.",
               'fix_summary': 'Resolved the conflict and added a CI step that fails the build on conflict '
                              'markers.'},
              {'id': 410,
               'name': 'Class average is NaN',
               'cause': 'Null reference',
               'language': 'TypeScript',
               'component': 'gradebook',
               'symptoms': 'The class average showed NaN whenever any student had an ungraded assignment '
                           'with a null mark.',
               'fix_summary': 'Left ungraded work out of the average.'},
              {'id': 415,
               'name': 'Big uploads vanish with a green tick',
               'cause': 'Works on my machine',
               'language': 'TypeScript',
               'component': 'uploads',
               'symptoms': 'Homework PDFs over 10 MB showed a green tick but never arrived, because the '
                           "production proxy had a 10 MB body limit that the local setup didn't.",
               'fix_summary': 'Raised the proxy limit to 50 MB, added it to the local setup, and showed an '
                              'error for bigger files.'},
              {'id': 419,
               'name': 'Login redirect loop',
               'cause': 'Infinite loop',
               'language': 'TypeScript',
               'component': 'auth',
               'symptoms': 'Students with an expired session bounced between /login and /dashboard forever.',
               'fix_summary': 'Cleared the expired session cookie before redirecting to login.'}],
  'new_report': {'title': 'Merge conflict markers on the timetable page again',
                 'description': "After this morning's deploy the timetable page shows '<<<<<<< HEAD', "
                                "'=======' and '>>>>>>> sports-day' above the table, with two versions of "
                                "Friday's periods. Two branches edited the timetable at once and the "
                                'conflict was committed. Did the CI check for conflict markers get removed?',
                 'language': 'TypeScript',
                 'component': 'timetable'},
  'expected': {'verdict': 'regression', 'bug_id': 406},
  'why': 'Same conflict markers shipped on the same timetable page: the merge conflict bug is back, and the '
         'CI check that stopped it may be gone.'},
 {'id': 'zb-04',
  'type': 'B',
  'history': [{'id': 502,
               'name': "Shares that don't add up to the bill",
               'cause': 'Rounding',
               'language': 'Python',
               'component': 'splits',
               'symptoms': 'Splitting ₹1,000 three ways gave everyone ₹333.33, and ₹0.01 went missing from '
                           'the group total.',
               'fix_summary': 'Stored shares in whole paise and gave the leftover paise to the first '
                              'person.'},
              {'id': 505,
               'name': 'Every reminder email sent twice',
               'cause': 'Race condition',
               'language': 'Python',
               'component': 'notifications',
               'symptoms': "Two reminder workers picked up the same job, so people got every 'you owe' "
                           'reminder email twice.',
               'fix_summary': 'Locked each reminder job while a worker sends it.'},
              {'id': 509,
               'name': 'Accented names garbled in emails',
               'cause': 'Encoding',
               'language': 'Python',
               'component': 'notifications',
               'symptoms': "People with accents in their names saw them garbled in emails, like 'JosÃ©' or "
                           "'MÃ¼ller', because the email body was encoded as Latin-1.",
               'fix_summary': 'Encoded all outgoing emails as UTF-8.'},
              {'id': 512,
               'name': 'Crash creating a group without a photo',
               'cause': 'Null reference',
               'language': 'Swift',
               'component': 'groups',
               'symptoms': 'Creating a group without a photo crashed the iOS app, because the code '
                           'force-unwrapped the optional image.',
               'fix_summary': 'Used a default group image when none is chosen.'},
              {'id': 516,
               'name': 'Monthly summary skips the last day',
               'cause': 'Off-by-one',
               'language': 'Python',
               'component': 'reports',
               'symptoms': 'The monthly spending summary left out expenses added on the last day of the '
                           'month.',
               'fix_summary': 'Included the last day in the date range.'},
              {'id': 521,
               'name': 'Currency rates a day old',
               'cause': 'Cache',
               'language': 'Python',
               'component': 'currency',
               'symptoms': "Expenses in euros were converted with yesterday's rate, because the rate cache "
                           'only expired at midnight UTC.',
               'fix_summary': 'Expired cached rates every hour.'}],
  'new_report': {'title': 'My name looks broken in the message you sent',
                 'description': "Hi! This morning I got the 'you owe Aarav' message in my inbox and it "
                                "greets me as 'RenÃ©' instead of René. My friend Zoë says hers greets her as "
                                "'ZoÃ«'. Inside the app our names look fine, and these messages used to show "
                                'them correctly.',
                 'language': 'Python',
                 'component': None},
  'expected': {'verdict': 'regression', 'bug_id': 509},
  'why': "Accented names turned into 'Ã©'-style characters only in the emailed message is the Latin-1 email "
         'encoding bug (#509) coming back; the duplicate-email bug (#505) is in the same component but has a '
         'different symptom.'},
 {'id': 'zb-05',
  'type': 'B',
  'history': [{'id': 603,
               'name': 'Audio stops when the screen locks',
               'cause': 'Lifecycle',
               'language': 'Kotlin',
               'component': 'player',
               'symptoms': 'Guided audio stopped a few seconds after the screen locked, because playback ran '
                           'in the activity instead of a foreground service.',
               'fix_summary': 'Moved playback to a foreground service.'},
              {'id': 607,
               'name': 'Paywall shows ₹0.00',
               'cause': 'Null reference',
               'language': 'Kotlin',
               'component': 'paywall',
               'symptoms': "The paywall showed ₹0.00 and crashed on tap when the store price hadn't loaded "
                           'yet.',
               'fix_summary': 'Showed a loading state until the store price arrives.'},
              {'id': 610,
               'name': 'Downloads stuck at 99%',
               'cause': 'Off-by-one',
               'language': 'Kotlin',
               'component': 'downloads',
               'symptoms': 'Offline course downloads stuck at 99%, because the last chunk was never marked '
                           'as finished.',
               'fix_summary': 'Marked the final chunk as finished when its last byte arrives.'},
              {'id': 614,
               'name': 'Japanese course titles as mojibake',
               'cause': 'Encoding',
               'language': 'Python',
               'component': 'catalog',
               'symptoms': "Japanese course titles showed as 'ç‘æƒ³' on Android, because the catalog API "
                           'sent Shift_JIS text labelled as UTF-8.',
               'fix_summary': 'Stored and served all catalog text as UTF-8.'},
              {'id': 618,
               'name': 'Streaks reset by the clock change',
               'cause': 'Timezone',
               'language': 'Kotlin',
               'component': 'streaks',
               'symptoms': 'After daylight saving ended, the streak counter used a fixed UTC offset to '
                           'decide which day a session belonged to, so late-evening sessions counted for the '
                           'wrong day and streaks reset to 1.',
               'fix_summary': "Worked out each session's day from the user's timezone rules instead of a "
                              'stored offset.'},
              {'id': 621,
               'name': 'Streak gone after reinstalling',
               'cause': 'Data sync',
               'language': 'Kotlin',
               'component': 'streaks',
               'symptoms': 'Streaks showed 0 after reinstalling the app or switching phones, because they '
                           'were only stored on the device.',
               'fix_summary': 'Synced streaks to the server and restored them at sign-in.'},
              {'id': 625,
               'name': 'Double minutes in the year in review',
               'cause': 'Race condition',
               'language': 'Python',
               'component': 'stats',
               'symptoms': 'Total minutes in the year in review were sometimes doubled, because two sync '
                           'requests from the same phone saved the same session at once.',
               'fix_summary': 'Made session uploads idempotent with a session ID.'}],
  'new_report': {'title': 'My 212-night run went back to 1 for no reason',
                 'description': 'I meditate every night at about 11:15 before bed and had 212 nights in a '
                                'row. On the first weekend after summer time finished here in Germany, the '
                                "app said I had missed Saturday and my run went back to 1. Saturday's "
                                'meditation is right there in my history, just listed under Sunday. Please '
                                'give me my nights back!',
                 'language': 'Kotlin',
                 'component': None},
  'expected': {'verdict': 'regression', 'bug_id': 618},
  'why': 'A late-evening session filed under the next day, on the weekend daylight saving ended, resetting '
         "the run to 1, is #618's fixed-offset timezone bug; #621 (streak gone after reinstalling) showed 0, "
         'not a one-day slip.'},
 {'id': 'zb-06',
  'type': 'B',
  'history': [{'id': 702,
               'name': 'Event dates a day early in Australia',
               'cause': 'Timezone',
               'language': 'Java',
               'component': 'events',
               'symptoms': 'Events listed for 8 PM showed the previous day for buyers in Australia, because '
                           "dates were formatted in the server's timezone.",
               'fix_summary': "Formatted event dates in the venue's timezone."},
              {'id': 705,
               'name': 'Seat map shows sold seats as free',
               'cause': 'Cache',
               'language': 'JavaScript',
               'component': 'seat-map',
               'symptoms': 'The seat map showed seats as free for up to five minutes after they sold; buyers '
                           "who picked them got a 'seat no longer available' error at payment.",
               'fix_summary': 'Pushed seat changes to the map live instead of caching it.'},
              {'id': 709,
               'name': 'Ticket PDFs without a QR code',
               'cause': 'Null reference',
               'language': 'Java',
               'component': 'tickets',
               'symptoms': 'Ticket PDFs for guest checkouts had a blank square instead of the QR code, '
                           'because the code generator was given a null account email.',
               'fix_summary': 'Generated the QR code from the order ID instead of the email.'},
              {'id': 713,
               'name': 'Same seat sold twice',
               'cause': 'Race condition',
               'language': 'Java',
               'component': 'seat-booking',
               'symptoms': 'Two buyers who picked the same seat a moment apart were both charged and both '
                           'received a ticket for it, because the availability check and the reservation '
                           'were separate queries.',
               'fix_summary': 'Reserved the seat with a single conditional update and refunded the second '
                              'buyer automatically.'},
              {'id': 716,
               'name': 'Partial refunds a paisa short',
               'cause': 'Floating point',
               'language': 'Java',
               'component': 'refunds',
               'symptoms': 'Partial refunds were a paisa short on some orders, because the refund was '
                           'computed with doubles.',
               'fix_summary': 'Computed refunds in whole paise with BigDecimal.'},
              {'id': 720,
               'name': 'Waitlist emails one person too many',
               'cause': 'Off-by-one',
               'language': 'Java',
               'component': 'waitlist',
               'symptoms': "When 100 returned seats were released, 101 people on the waitlist got the 'your "
                           "turn' email and the last one found nothing left.",
               'fix_summary': 'Used < instead of <= when picking people from the waitlist.'}],
  'new_report': {'title': 'Another family had our exact places at the show',
                 'description': 'We got to the Saturday show and an usher found another family already in '
                                'row F, numbers 11 to 14. The passes on their phones showed the identical '
                                'row and numbers as ours. The usher said two other groups had this problem '
                                'tonight. We bought the second sales opened, and so did they. We had to '
                                'stand at the back.',
                 'language': 'Java',
                 'component': None},
  'expected': {'verdict': 'regression', 'bug_id': 713},
  'why': 'Two parties holding valid passes for identical places, both bought the instant sales opened, is '
         "#713's double-sale race condition; the cache bug (#705) only caused an error at payment, never two "
         'tickets.'},
 {'id': 'zb-07',
  'type': 'C',
  'history': [{'id': 803,
               'name': 'Leave approved twice',
               'cause': 'Race condition',
               'language': 'Java',
               'component': 'leave',
               'symptoms': 'Two managers approving the same leave request at once took the days off the '
                           "employee's balance twice.",
               'fix_summary': "Approved leave in one transaction that checks the request's status first."},
              {'id': 806,
               'name': 'Tamil names as boxes on payslips',
               'cause': 'Encoding',
               'language': 'Java',
               'component': 'payslips',
               'symptoms': 'Employee names written in Tamil printed as empty boxes on payslip PDFs.',
               'fix_summary': 'Embedded a Unicode font that covers Tamil.'},
              {'id': 810,
               'name': 'Night shifts with negative hours',
               'cause': 'Date math',
               'language': 'Java',
               'component': 'attendance',
               'symptoms': 'Night shifts that crossed midnight were counted as negative hours, because only '
                           'the time of day was subtracted.',
               'fix_summary': 'Subtracted full date-times instead of times of day.'},
              {'id': 812,
               'name': 'Manager dashboard crash for new teams',
               'cause': 'Null reference',
               'language': 'TypeScript',
               'component': 'dashboard',
               'symptoms': 'The manager dashboard crashed for teams with no members yet, because the code '
                           "read the first member's name without checking.",
               'fix_summary': 'Showed an empty state for teams without members.'},
              {'id': 815,
               'name': "Last year's tax slabs after the budget",
               'cause': 'Cache',
               'language': 'Java',
               'component': 'tax',
               'symptoms': 'After the new tax slabs went live on 1 April, TDS was still calculated with last '
                           "year's slabs until the server restarted.",
               'fix_summary': 'Reloaded tax slabs from the database at the start of each payroll run.'},
              {'id': 819,
               'name': 'Bonus import stops at 1,000 rows',
               'cause': 'Config',
               'language': 'Python',
               'component': 'imports',
               'symptoms': 'Bonus spreadsheets with more than 1,000 rows were imported only up to row 1,000, '
                           'with no error, because of the default page size.',
               'fix_summary': 'Read the file in pages until the end and showed the row count after import.'},
              {'id': 823,
               'name': 'Net salary a rupee short',
               'cause': 'Floating point',
               'language': 'Java',
               'component': 'payroll',
               'symptoms': 'Net salary on payslips was sometimes ₹1 lower than the bank transfer, because '
                           'deductions were calculated with doubles and rounded separately.',
               'fix_summary': 'Calculated pay with BigDecimal and rounded once at the end.'},
              {'id': 827,
               'name': 'Payslips broken by a library update',
               'cause': 'Dependency hell',
               'language': 'Java',
               'component': 'build',
               'symptoms': 'A fresh build pulled a new major version of the PDF library and payslip '
                           'generation failed with NoSuchMethodError.',
               'fix_summary': 'Pinned the PDF library version and added a payslip test to CI.'}],
  'new_report': {'title': 'Net salary on payslips lower than the bank transfer',
                 'description': "This month's payslips show a net salary lower than the bank transfer for 14 "
                                "employees, all in the Pune office. The difference is exactly one day's pay "
                                'for each of them. All 14 joined on the 1st of the month, and their payslips '
                                'count 29 working days instead of 30, as if counting starts on the 2nd.',
                 'language': 'Java',
                 'component': 'payroll'},
  'expected': {'verdict': 'new', 'bug_id': None},
  'why': "Shares many words with #823, but the gap is exactly one day's pay from a working-days count that "
         'skips the joining day: a counting bug, not floating point rounding.'},
 {'id': 'zb-08',
  'type': 'C',
  'history': [{'id': 904,
               'name': 'Hotel price goes up at checkout',
               'cause': 'Cache',
               'language': 'Python',
               'component': 'hotels',
               'symptoms': 'The hotel price on the results page was sometimes lower than at checkout, '
                           'because search results were cached for an hour.',
               'fix_summary': 'Re-checked prices before showing results older than five minutes.'},
              {'id': 907,
               'name': 'Two bookings for one payment',
               'cause': 'Race condition',
               'language': 'Python',
               'component': 'payments',
               'symptoms': 'A slow payment callback and a user retry both confirmed the booking, so '
                           'travellers got two booking numbers for one payment.',
               'fix_summary': 'Confirmed bookings with an idempotency key from the payment.'},
              {'id': 911,
               'name': 'Flight times an hour off after daylight saving',
               'cause': 'Timezone',
               'language': 'Python',
               'component': 'itinerary',
               'symptoms': 'After daylight saving started, departure times in itinerary emails were an hour '
                           'off, because flight times were converted with a fixed UTC offset.',
               'fix_summary': "Converted flight times with each airport's timezone rules."},
              {'id': 914,
               'name': 'Passenger names cut at 20 letters',
               'cause': 'Data truncation',
               'language': 'Python',
               'component': 'passengers',
               'symptoms': 'Long passenger names were cut to 20 letters on tickets, and the airline rejected '
                           'them at check-in.',
               'fix_summary': "Widened the name column to the airline's 57-letter limit."},
              {'id': 918,
               'name': 'Visa page crashes for unlisted countries',
               'cause': 'Null reference',
               'language': 'TypeScript',
               'component': 'visa-info',
               'symptoms': "The visa information page crashed when a passport country wasn't in the visa "
                           'table.',
               'fix_summary': "Showed 'check with the embassy' when the country isn't listed."},
              {'id': 922,
               'name': 'Baggage fees in dollars for Indian users',
               'cause': 'Config',
               'language': 'Python',
               'component': 'baggage',
               'symptoms': 'Baggage fees showed in USD for users in India, because the currency fell back to '
                           'the default setting.',
               'fix_summary': "Picked the currency from the user's country, with INR as the default for "
                              'India.'}],
  'new_report': {'title': 'Flight departure times wrong in itinerary emails',
                 'description': "Since Monday's release, itinerary emails for round-trip bookings show the "
                                'wrong departure time for the outbound flight: it is always the return '
                                "flight's departure time, usually days apart. The website shows the right "
                                'times. The new email template seems to read the return leg for both '
                                'flights.',
                 'language': 'Python',
                 'component': 'itinerary'},
  'expected': {'verdict': 'new', 'bug_id': None},
  'why': "Shares many words with #911, but the outbound flight shows the return flight's time because the "
         'template reads the wrong leg, not a one-hour daylight saving shift.'},
 {'id': 'zb-09',
  'type': 'C',
  'history': [{'id': 1003,
               'name': 'Messages out of order on slow networks',
               'cause': 'Race condition',
               'language': 'Go',
               'component': 'delivery',
               'symptoms': 'On slow networks, messages sent quickly one after another arrived in the wrong '
                           'order, because each was sent on its own connection.',
               'fix_summary': 'Numbered messages per chat and sorted them by number.'},
              {'id': 1006,
               'name': 'Typing indicator stuck on',
               'cause': 'Missing timeout',
               'language': 'Go',
               'component': 'presence',
               'symptoms': "The 'typing…' indicator stayed on forever when the other person lost their "
                           'connection mid-message.',
               'fix_summary': 'Expired typing status after five seconds without an update.'},
              {'id': 1010,
               'name': 'Hindi push notifications as ????',
               'cause': 'Encoding',
               'language': 'Go',
               'component': 'notifications',
               'symptoms': 'Push notifications for Hindi messages showed ???? because the payload was '
                           'converted to ASCII.',
               'fix_summary': 'Sent push payloads as UTF-8.'},
              {'id': 1013,
               'name': 'Chat export misses the newest message',
               'cause': 'Off-by-one',
               'language': 'Swift',
               'component': 'export',
               'symptoms': 'Exported chats always left out the newest message.',
               'fix_summary': 'Included the last index in the export loop.'},
              {'id': 1017,
               'name': 'Crash opening a chat with a deleted user',
               'cause': 'Null reference',
               'language': 'Swift',
               'component': 'chat',
               'symptoms': 'Opening a conversation with someone who had deleted their account crashed the '
                           'iOS app, because the missing profile was force-unwrapped.',
               'fix_summary': "Showed 'Deleted user' when the profile is missing."},
              {'id': 1021,
               'name': "'Seen at' times hours off abroad",
               'cause': 'Timezone',
               'language': 'Swift',
               'component': 'read-receipts',
               'symptoms': "'Seen at' times were hours off for people in other countries, because the server "
                           'sent local times without an offset.',
               'fix_summary': 'Sent all times in UTC and formatted them on the phone.'},
              {'id': 1024,
               'name': 'Battery drain from the reconnect loop',
               'cause': 'Infinite loop',
               'language': 'Swift',
               'component': 'connection',
               'symptoms': 'With no network, the app tried to reconnect hundreds of times a second and '
                           'drained the battery.',
               'fix_summary': 'Added exponential backoff between reconnect attempts.'}],
  'new_report': {'title': 'iOS app crashes when opening a chat',
                 'description': 'Since version 4.2, opening any conversation that contains a long video (40 '
                                'MB or more) crashes the iOS app a few seconds after it opens. In Xcode, '
                                'memory climbs past 1.5 GB right before the crash, because the app loads the '
                                'whole video into memory to make its thumbnail. Chats without big videos '
                                'open fine.',
                 'language': 'Swift',
                 'component': 'chat'},
  'expected': {'verdict': 'new', 'bug_id': None},
  'why': 'Shares many words with #1017 (crash opening a chat), but the cause is running out of memory while '
         'loading a whole video, not a missing profile.'},
 {'id': 'zb-10',
  'type': 'D',
  'history': [{'id': 1102,
               'name': 'Stock count goes negative',
               'cause': 'Race condition',
               'language': 'Go',
               'component': 'stock',
               'symptoms': 'Two pickers scanning the last unit at the same time both succeeded, and the '
                           'stock count went to -1.',
               'fix_summary': 'Decremented stock with a conditional update that refuses to go below zero.'},
              {'id': 1105,
               'name': 'Barcode labels with ? instead of ü',
               'cause': 'Encoding',
               'language': 'Go',
               'component': 'labels',
               'symptoms': "Product names with umlauts printed as '?' on barcode labels.",
               'fix_summary': 'Sent label text to the printer as UTF-8 with the matching code page.'},
              {'id': 1109,
               'name': 'Stock CSV drops the last product',
               'cause': 'Off-by-one',
               'language': 'Python',
               'component': 'export',
               'symptoms': 'The nightly stock CSV left out the last product in every warehouse.',
               'fix_summary': 'Fixed the loop bound to include the last product.'},
              {'id': 1113,
               'name': 'Same-day cutoff an hour late in summer',
               'cause': 'Timezone',
               'language': 'Go',
               'component': 'shipping',
               'symptoms': 'During summer time, orders placed until 3 PM were promised same-day shipping, '
                           'although the real cutoff was 2 PM.',
               'fix_summary': "Checked the cutoff with the warehouse's timezone rules."},
              {'id': 1116,
               'name': 'Crash on products without a supplier',
               'cause': 'Null reference',
               'language': 'Go',
               'component': 'purchasing',
               'symptoms': "Generating purchase orders panicked with 'nil pointer dereference' for products "
                           'that had no supplier.',
               'fix_summary': 'Skipped products without a supplier and listed them for review.'},
              {'id': 1120,
               'name': 'Pallet weights off by a few grams',
               'cause': 'Floating point',
               'language': 'Go',
               'component': 'pallets',
               'symptoms': 'Pallet weight totals were off by a few grams, so the scales flagged correct '
                           'pallets as wrong.',
               'fix_summary': 'Stored weights in whole grams.'}],
  'new_report': {'title': 'Low-stock badge unreadable in dark mode',
                 'description': "In dark mode, the red 'Low stock' badge on the dashboard is dark red text "
                                'on a dark red background, so nobody can read it. Light mode is fine. The '
                                "badge's colours are hard-coded instead of using the theme's colour "
                                'variables.',
                 'language': 'CSS',
                 'component': 'dashboard'},
  'expected': {'verdict': 'new', 'bug_id': None},
  'why': "A dark-mode colour problem in the dashboard's CSS; nothing in the history is about styling or the "
         'dashboard.'},
 {'id': 'zb-11',
  'type': 'D',
  'history': [{'id': 1203,
               'name': 'Due dates a day early',
               'cause': 'Timezone',
               'language': 'Ruby',
               'component': 'loans',
               'symptoms': 'Books borrowed late in the evening got a due date one day early, because due '
                           'dates were calculated in UTC.',
               'fix_summary': "Calculated due dates in the library's timezone."},
              {'id': 1207,
               'name': 'Two members reserve the last copy',
               'cause': 'Race condition',
               'language': 'Ruby',
               'component': 'reservations',
               'symptoms': 'Two members reserving the last copy of a book at the same moment were both told '
                           'it was theirs.',
               'fix_summary': "Locked the copy's row while reserving it."},
              {'id': 1210,
               'name': 'Late fees with fifteen decimal places',
               'cause': 'Floating point',
               'language': 'Ruby',
               'component': 'fines',
               'symptoms': 'Late fees showed as ₹4.999999999999999 on receipts.',
               'fix_summary': 'Stored fines in whole paise.'},
              {'id': 1214,
               'name': 'Page 2 of search repeats a book',
               'cause': 'Off-by-one',
               'language': 'Ruby',
               'component': 'search',
               'symptoms': 'The second page of search results started with the last book from the first '
                           'page.',
               'fix_summary': 'Started each page at page × size instead of page × size − 1.'},
              {'id': 1218,
               'name': 'Overdue notices crash on members without email',
               'cause': 'Null reference',
               'language': 'Ruby',
               'component': 'members',
               'symptoms': "Sending overdue notices crashed with NoMethodError: undefined method 'downcase' "
                           'for nil for members who signed up without an email address.',
               'fix_summary': 'Sent paper notices to members without an email address.'}],
  'new_report': {'title': 'Nightly catalogue import gets slower until it is killed',
                 'description': 'The nightly import of new books from the publisher feed takes longer every '
                                "night (40 minutes last week, 3 hours last night), and the worker's memory "
                                'keeps growing until the server kills it. Restarting the worker makes it '
                                'fast again for a night or two. Every imported cover image is kept in an '
                                'in-memory hash that is never cleared.',
                 'language': 'Ruby',
                 'component': 'import'},
  'expected': {'verdict': 'new', 'bug_id': None},
  'why': 'A memory leak in the import worker; no history bug involves memory or the import.'},
 {'id': 'zb-12',
  'type': 'D',
  'history': [{'id': 1302,
               'name': 'Daily highs on the wrong day',
               'cause': 'Timezone',
               'language': 'Python',
               'component': 'charts',
               'symptoms': 'Daily high temperatures were stored on the next day for stations east of UTC, '
                           'because days were cut at midnight UTC.',
               'fix_summary': "Cut each station's days at its local midnight."},
              {'id': 1305,
               'name': 'Humidity of 100.00000001%',
               'cause': 'Floating point',
               'language': 'C++',
               'component': 'humidity-sensor',
               'symptoms': 'Saturated air was reported as 100.00000001% humidity and the server rejected the '
                           'reading as invalid.',
               'fix_summary': 'Clamped humidity to 0–100 and sent it as tenths of a percent.'},
              {'id': 1308,
               'name': 'Stations bricked by a power cut during updates',
               'cause': 'Data corruption',
               'language': 'C++',
               'component': 'firmware-update',
               'symptoms': "Stations that lost power during a firmware update wouldn't boot, because the new "
                           'image was written over the old one without a checksum.',
               'fix_summary': 'Wrote updates to a second slot and switched only after the checksum passed.'},
              {'id': 1311,
               'name': 'Wind always from the north',
               'cause': 'Missing value',
               'language': 'C++',
               'component': 'wind',
               'symptoms': 'Stations with an unplugged wind vane reported 0° (north) instead of no reading, '
                           'because a missing value was read as 0.',
               'fix_summary': 'Reported missing readings as missing.'},
              {'id': 1315,
               'name': 'Station names garbled on the map',
               'cause': 'Encoding',
               'language': 'Python',
               'component': 'map',
               'symptoms': "Station names like 'Säntis' showed as 'SÃ¤ntis' on the public map.",
               'fix_summary': 'Served the station list as UTF-8.'},
              {'id': 1319,
               'name': 'Readings saved twice after reconnecting',
               'cause': 'Race condition',
               'language': 'Python',
               'component': 'ingest',
               'symptoms': 'When a station reconnected, it re-sent its buffer while the server was still '
                           'saving the first copy, so readings appeared twice.',
               'fix_summary': 'Ignored readings with a timestamp the station had already sent.'},
              {'id': 1322,
               'name': "Dashboard shows yesterday's weather",
               'cause': 'Cache',
               'language': 'TypeScript',
               'component': 'dashboard',
               'symptoms': 'The public dashboard showed readings up to a day old, because the CDN cached the '
                           'API response.',
               'fix_summary': 'Set a 60-second cache time on readings.'},
              {'id': 1326,
               'name': 'Battery flat in a week',
               'cause': 'Infinite loop',
               'language': 'C++',
               'component': 'power',
               'symptoms': 'Stations without a GPS fix kept the radio on in a retry loop and drained the '
                           'battery in a week instead of a year.',
               'fix_summary': 'Gave up on GPS after two minutes and retried hourly.'}],
  'new_report': {'title': 'Rain gauge total drops to zero in very wet months',
                 'description': 'At three of our stations in Meghalaya, the monthly rain total suddenly '
                                'dropped to 0 partway through July and started counting up again. Each time, '
                                'the gauge had just passed 65,535 bucket tips. The firmware stores the tip '
                                'count in a 16-bit unsigned integer.',
                 'language': 'C++',
                 'component': 'rain-gauge'},
  'expected': {'verdict': 'new', 'bug_id': None},
  'why': 'A 16-bit tip counter overflowing after 65,535; no history bug involves an overflowing counter or '
         'the rain gauge.'}]
# --- end CASES ---

VERDICTS = ("regression", "new")


def build_prompt(case):
    lines = [
        "You are triaging bug reports for a software team.",
        "",
        "Below are bugs the team has already fixed, then one new bug report. Decide whether the new",
        "report is a REGRESSION (one of the fixed bugs coming back: the same defect with the same",
        "underlying cause) or a NEW bug that is not any of the fixed ones.",
        "",
        "FIXED BUGS",
    ]
    for bug in case["history"]:
        lines += [
            "",
            f"#{bug['id']} {bug['name']}",
            f"- Cause: {bug['cause']}",
            f"- Language: {bug['language']}",
            f"- Component: {bug['component']}",
            f"- Symptoms: {bug['symptoms']}",
            f"- Fix: {bug['fix_summary']}",
        ]
    report = case["new_report"]
    lines += [
        "",
        "NEW BUG REPORT",
        "",
        f"Title: {report['title']}",
        f"Language: {report['language'] or 'not given'}",
        f"Component: {report['component'] or 'not given'}",
        f"Description: {report['description']}",
        "",
        "Reply with JSON only, no other text, in exactly this shape:",
        '{"verdict": "regression" or "new", "bug_id": the fixed bug\'s number if it is a regression, '
        'otherwise null, "reason": "one sentence"}',
    ]
    return "\n".join(lines)


def first_json_object(text):
    """The first {...} in the text that has a "verdict" key, or None."""
    decoder = json.JSONDecoder()
    for match in re.finditer(r"\{", text):
        try:
            data, _ = decoder.raw_decode(text, match.start())
        except ValueError:
            continue
        if isinstance(data, dict) and "verdict" in data:
            return data
    return None


def read_bug_id(value):
    """(True, id or None) for a usable bug_id, (False, None) for anything else."""
    if value is None:
        return True, None
    if isinstance(value, bool):
        return False, None
    if isinstance(value, int):
        return True, value
    if isinstance(value, float) and value.is_integer():
        return True, int(value)
    if isinstance(value, str):
        text = value.strip().lower()
        if text in ("", "null", "none"):
            return True, None
        match = re.fullmatch(r"#?\s*(\d+)", text)
        if match:
            return True, int(match.group(1))
    return False, None


def parse_answer(reply):
    """(verdict, bug_id, reason) from the model's reply, or None if it isn't the JSON we asked for."""
    data = first_json_object(reply if isinstance(reply, str) else "")
    if data is None:
        return None
    verdict = data.get("verdict")
    if not isinstance(verdict, str) or verdict.strip().lower() not in VERDICTS:
        return None
    ok, bug_id = read_bug_id(data.get("bug_id"))
    if not ok:
        return None
    reason = data.get("reason")
    return verdict.strip().lower(), bug_id, reason if isinstance(reason, str) else ""


def ask(llm, case):
    """The model's reply, in a fresh chat so no case sees another. None if the call fails twice."""
    prompt = build_prompt(case)
    for attempt in (1, 2):
        with kbench.chats.new(case["id"]):
            try:
                return llm.prompt(prompt)
            except Exception as error:  # a failed call scores 0 for its case instead of stopping the run
                print(f"{case['id']}: model call {attempt} of 2 failed: {error}")
    return None


def describe(verdict, bug_id):
    return f"regression #{bug_id}" if verdict == "regression" else verdict


@kbench.task(
    name="zombiebench",
    description="Given fixed bugs and a new report, say which old bug came back, or that it's new.",
)
def zombiebench(llm) -> float:
    results = {}
    failed_calls = 0
    print(f"{'case':<7}{'type':<6}{'expected':<17}{'answer':<17}ok")
    for case in CASES:
        reply = ask(llm, case)
        failed_calls += reply is None
        answer = parse_answer(reply)
        expected = case["expected"]
        passed = answer is not None and answer[:2] == (expected["verdict"], expected["bug_id"])
        results.setdefault(case["type"], []).append(passed)

        got = "unreadable" if answer is None else describe(*answer[:2])
        print(f"{case['id']:<7}{case['type']:<6}{describe(expected['verdict'], expected['bug_id']):<17}"
              f"{got:<17}{'✓' if passed else '✗'}")
        if not passed:
            said = answer[2] if answer else "no reply" if reply is None else repr(str(reply)[:200])
            print(f"{'':13}reason: {said}")

    all_results = [ok for oks in results.values() for ok in oks]
    print()
    for case_type in sorted(results):
        oks = results[case_type]
        print(f"Type {case_type}: {sum(oks)}/{len(oks)} = {sum(oks) / len(oks):.0%}")
    print(f"Overall: {sum(all_results)}/{len(all_results)} = {sum(all_results) / len(all_results):.0%}")
    if failed_calls:
        print(f"Warning: {failed_calls} model call(s) failed and scored 0.")
    return sum(all_results) / len(all_results)


if __name__ == "__main__":
    zombiebench.run(kbench.llm)
