"""Build controlled follow-up cases; only writes under followup/.

Synthetic Experiment 2 histories use a shared distractor scaffold with domain-specific
entities. Their expert-style length is not a claim of calibrated expert difficulty.
"""
import copy
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = Path(__file__).resolve().parent

# Explicit author-approved exception: zb-07/zb-27 each had one miss among 14 runs.
SELECTION = {
    'zb-13': (2118, 'Developer comment: This is definitely #2118, the phone-restart reminder defect; route it to that fix.'),
    'zb-14': (2246, 'Support comment: This is definitely #2246, the missing billing value defect; the extra bill line confirms it.'),
    'zb-15': (2315, 'Developer comment: This is definitely #2315, the misleading autosave-success defect; the saved answer was never accepted.'),
    'zb-04': (505, 'Support comment: This is definitely #505, the reminder-email delivery defect; these reminder messages identify it.'),
    'zb-05': (621, 'Developer comment: This is definitely #621, the streak restoration defect; the reset to one identifies it.'),
    'zb-22': (2511, 'Support comment: This is definitely #2511, the analyser unit-conversion defect; the inflated lab value confirms it.'),
    'zb-07': (823, 'Developer comment: This is definitely #823, the payslip net-salary defect; payroll should reopen that bug.'),
    'zb-09': (1017, 'Support comment: This is definitely #1017, the iOS chat-opening crash; the conversation screen confirms it.'),
    'zb-27': (2401, 'Developer comment: This is definitely #2401, the Bluetooth unlock spinner defect; reopen that ticket.'),
    'zb-10': (1105, 'Support comment: This is definitely #1105, the unreadable stock-label text defect; the broken lettering identifies it.'),
    'zb-12': (1311, 'Developer comment: This is definitely #1311, missing sensor values being displayed as zero; the zero reading confirms it.'),
    'zb-34': (2629, 'Support comment: This is definitely #2629, the export timeout defect; the missing invoices mean the export stopped early.'),
}
REMOVALS = {
    'zb-37': (3108, " The developer on call wrote: 'This is definitely #3108 again, the confirmation-page fix regressed.'"),
    # Original zb-39 names a diagnosis, not its numeric bug ID. Preserve that fact.
    'zb-39': (3539, ", and the Android TV team thinks it's the pause problem"),
    'zb-41': (3325, " Support note on this ticket: 'The split bug, #3325, is back; splits and these go through the same code.'"),
    'zb-44': (3318, " Developer comment: 'This is definitely #3318 again, the overnight batch is back.'"),
    'zb-45': (3518, " Developer comment: 'This is definitely #3518 again, the rating filter regressed.'"),
}

# domain, entity, language, mistake, old route, independent route, symptom,
# faulty operation, correct operation, plausible sibling defect.
SPECS = [
 ('Cold-chain dispatch', 'shipment', 'Python', 'Timezone', 'DispatchManifest.service_day', 'WarehouseScanner.service_day',
  'A scan at 00:15 Asia/Kolkata on 12 June is assigned to 11 June, though it belongs to 12 June.',
  'takes the UTC date of the timestamp without converting it to Asia/Kolkata',
  'converts the timestamp to the depot timezone before taking its date',
  'A daylight-saving offset was applied twice to the printed departure time.'),
 ('Water utility billing', 'meter account', 'Java', 'Rounding', 'BillComposer.total', 'AdjustmentBatch.total',
  'Two charges of 0.335 each produce a total of 0.68; the tariff requires rounding their 0.670 sum once to 0.67.',
  'rounds each charge to cents before summing the charges',
  'sums unrounded decimal charges and rounds the final total once',
  'The usage chart truncated litres to a whole number before calculating a tariff band.'),
 ('Library circulation', 'catalog record', 'Ruby', 'Cache', 'CatalogCard.load', 'ReservationSlip.load',
  'After the catalog title changed from River Maps to River Atlas, one surface displays River Maps while the database contains River Atlas.',
  'reads its own stored title snapshot and never invalidates it when the title-change event arrives',
  'invalidates its stored title snapshot on the title-change event and reloads it',
  'Availability counts were cached without the library-branch identifier in the key.'),
 ('Pathology administration', 'specimen record', 'C#', 'Null reference', 'SpecimenLabel.contact', 'CourierManifest.contact',
  'A specimen with an absent optional contact phone aborts rendering with NullReferenceException; specimens with a phone render normally.',
  'calls Trim() on the optional contact phone without checking for null',
  'substitutes an empty string for an absent contact phone before trimming',
  'An optional accession alias was dereferenced while sorting the work queue.'),
 ('EV charging reservations', 'charging slot', 'Go', 'Race condition', 'AppReservation.claim', 'FleetReservation.claim',
  'Two requests for the same connector and interval both receive confirmation when they arrive concurrently; serial requests correctly reject the second.',
  'checks availability and then writes the claim in a separate transaction with no shared lock',
  'checks and writes the claim under a lock keyed by connector and interval',
  'Reservation cancellation raced with reminder delivery and sent a reminder for a cancelled slot.'),
 ('Drone survey planning', 'survey route', 'TypeScript', 'Unit conversion', 'WaypointEditor.height', 'BulkRouteImport.height',
  'A requested altitude of 100 feet becomes 100 metres in the stored route; the contract requires 30.48 metres.',
  'copies the numeric feet value into the metres field without multiplying by 0.3048',
  'multiplies incoming feet by 0.3048 before writing the metres field',
  'Miles in the battery-range preview were multiplied by the kilometres factor twice.'),
 ('Satellite ground operations', 'contact window', 'Python', 'Timezone', 'StationCalendar.day', 'HandoverPacket.day',
  'A contact at 00:20 Pacific/Auckland on 4 February is filed under 3 February, though the station-day contract requires 4 February.',
  'takes the UTC date without converting to Pacific/Auckland',
  'converts the contact instant to the station timezone before selecting a day',
  'The wall-clock countdown assumed every local day was exactly twenty-four hours across a clock change.'),
 ('Energy settlement', 'settlement account', 'Java', 'Rounding', 'RetailSettlement.amount', 'PartnerSettlement.amount',
  'Three interval credits of 0.004 yield a payable credit of 0.00; the contract requires rounding their 0.012 sum once to 0.01.',
  'rounds every interval credit to cents before adding the credits',
  'adds full-precision decimal interval credits before rounding once to cents',
  'The demand preview rounded each power sample before comparing it with the peak threshold.'),
 ('Transit service alerts', 'service notice', 'Kotlin', 'Cache', 'StationBoard.notice', 'DriverBriefing.notice',
  'After a service notice changes from Platform 2 to Platform 5, one screen shows Platform 2 although the notice store contains Platform 5.',
  'reads its own saved notice copy without evicting it on the notice-update event',
  'evicts its saved notice copy on the notice-update event before reloading',
  'The stop-name cache omitted the selected language from its key.'),
]

# Distinct, concrete fixed defects; each expanded with the domain's entity.
DISTRACTORS = [
 ('Empty search page', 'Off-by-one', 'search', 'The final {e} on each page was absent.', 'Included the upper page boundary.'),
 ('Search punctuation rejected', 'Escaping', 'search', 'An apostrophe in a {e} name caused a query error.', 'Bound names as query parameters.'),
 ('Duplicate retry email', 'Idempotency', 'notifications', 'Retrying delivery sent the same {e} email twice.', 'Deduplicated sends by message identifier.'),
 ('Wrong recipient language', 'Localization', 'notifications', '{e} notices ignored the recipient locale.', 'Selected the recipient locale at render time.'),
 ('CSV splits names', 'Escaping', 'exports', 'A comma in a {e} label created an extra CSV column.', 'Quoted fields through a CSV writer.'),
 ('CSV drops final row', 'Off-by-one', 'exports', 'A {e} at the final cursor position was omitted.', 'Wrote the last fetched row before closing the cursor.'),
 ('Stale role after logout', 'Session state', 'auth', 'A removed operator role survived logout.', 'Discarded session permissions at logout.'),
 ('Invite rejects plus sign', 'Input validation', 'auth', 'An operator address containing + was rejected.', 'Accepted valid email local-part characters.'),
 ('Attachments exhaust memory', 'Memory', 'attachments', 'Opening a large {e} attachment loaded the whole object into RAM.', 'Streamed attachment chunks.'),
 ('Thumbnail wrong orientation', 'Image metadata', 'attachments', 'A portrait {e} photo appeared sideways.', 'Applied EXIF orientation before resizing.'),
 ('Webhook signature fails', 'Serialization', 'integrations', 'A valid signature failed after payload whitespace was normalized.', 'Verified the signature against the original payload bytes.'),
 ('Webhook retry storm', 'Missing backoff', 'integrations', 'An unavailable endpoint triggered continuous immediate retries.', 'Added exponential backoff and a retry ceiling.'),
 ('Audit log wrong actor', 'Context propagation', 'audit', 'A background edit to a {e} logged the previous request user.', 'Passed the actor explicitly into each job.'),
 ('Audit rows omitted', 'Pagination', 'audit', 'Exactly a full page of audit rows prevented the next page loading.', 'Continued while the server supplied a cursor.'),
 ('Mobile row inaccessible', 'Accessibility', 'mobile', 'A screen reader could not focus the {e} action menu.', 'Added a labelled focusable control.'),
 ('Dark-mode selection hidden', 'Contrast', 'mobile', 'Selected {e} rows had identical foreground and background colours.', 'Used contrasting theme tokens.'),
 ('Archive wrong tenant', 'Missing filter', 'archive', 'An archive query selected another tenant\'s {e}.', 'Bound the query to the authenticated tenant.'),
 ('Archive restore loses tags', 'Incomplete serialization', 'archive', 'Restoring a {e} omitted its tags.', 'Included tags in the archive schema and restore mapper.'),
 ('Progress stays at zero', 'Integer division', 'jobs', 'Progress for a {e} batch stayed at zero until completion.', 'Converted the numerator to decimal before division.'),
 ('Cancel ignores queued work', 'Cancellation', 'jobs', 'Cancelling a {e} batch stopped active work but left queued work runnable.', 'Persisted cancellation and checked it before dequeuing.'),
 ('Report font missing', 'Encoding', 'pdf', 'Accented {e} labels appeared as boxes in PDFs.', 'Embedded a Unicode font.'),
 ('Report repeats heading', 'Layout', 'pdf', 'The first {e} row overlapped a repeated page heading.', 'Reserved heading height before laying out rows.'),
 ('Saved filter discarded', 'State persistence', 'preferences', 'A saved {e} filter disappeared after a browser restart.', 'Persisted the selected filter on save.'),
 ('Sort reverses ties', 'Unstable sorting', 'lists', '{e} rows with equal names swapped position between refreshes.', 'Added the record identifier as a stable secondary sort key.'),
]


def make_exp2():
    out=[]
    for i,spec in enumerate(SPECS,1):
        domain,entity,lang,cause,old,other,symptom,faulty,fixed,sibling=spec
        base=5000+i*100
        target=base+11
        shared_component='operations'
        history=[dict(id=base+30+j,name=name,cause=kind,language=lang,component=component,
                      symptoms=sym.format(e=entity),fix_summary=fix)
                 for j,(name,kind,component,sym,fix) in enumerate(DISTRACTORS)]
        near=[
            dict(id=base+12,name=f'{domain}: adjacent calculation defect',cause=cause,language=lang,
                 component='previews',symptoms=sibling,fix_summary='Corrected only PreviewRenderer.calculate(); neither operational route calls this preview code.'),
            dict(id=base+13,name=f'{domain}: operational summary omits records',cause='Missing filter',language=lang,
                 component=shared_component,symptoms=f'The operational summary omitted active {entity} entries marked as pending.',
                 fix_summary='Included pending entries only in OperationsSummary.query(); did not change either processing route.'),
        ]
        history.extend(near)
        history.insert((2,13,24)[(i-1)%3],dict(id=target,name=f'{domain}: {cause.lower()} in {old}',cause=cause,
             language=lang,component=shared_component,symptoms=f'{symptom} Inspection found that {old} {faulty}.',
             fix_summary=f'Changed only {old}: it now {fixed}. {other} is a separate implementation and does not call {old} or share its helper; that route was outside this patch.'))
        for variant,route,control in [('different',other,old),('same',old,other)]:
            clue=f'The failing request executes {route}; it does not call {control}.'
            desc=(f'{symptom} {clue} A source snapshot of {route} shows that it {faulty}. '
                  f'With the identical input, {control} returns the required result and its source {fixed}. '
                  'Both routes use the same stored input and configuration. The attached trace covers the whole request, including helper calls.')
            # Id/type/key/why are evaluation metadata only, never included in prompts.
            out.append(dict(id=f'zf2-{i:02d}-{variant}',tier='expert',type='D' if variant=='different' else 'A',history=copy.deepcopy(history),
                  new_report=dict(title=f'{domain}: output disagrees with the contract',description=desc,language=lang,component=shared_component),
                  expected=dict(verdict='new' if variant=='different' else 'regression',bug_id=None if variant=='different' else target),
                  siblings=[] if variant=='different' else [base+12,base+13],decoy_bug_id=None,key_clue=clue,
                  why=f'The fault is in {route}; the historical patch covered only {old}, so this is '+('a distinct defect in an independent implementation.' if variant=='different' else f'the documented defect in #{target} returning in the patched function.'),
                  experiment='exp2',pair_id=f'exp2-{i:02d}',variant=variant,domain=domain,mistake=cause,comparison_bug_id=target))
    return out


def main():
    originals={c['id']:c for c in json.loads((ROOT/'cases.json').read_text())}
    runs=[r for r in json.loads((ROOT/'results/2026-10-06-kaggle-48-cases.json').read_text())['runs'] if r['status']=='completed']
    assert len(runs)==14 and all(r.get('errors',0)==0 and r['total']==48 for r in runs)
    misses=Counter(m['case'] for r in runs for m in r['misses'])
    out=[]
    for source,(named,comment) in {**SELECTION,**REMOVALS}.items():
        original=originals[source]
        is_added=source in SELECTION
        clean=copy.deepcopy(original)
        if not is_added:
            assert clean['new_report']['description'].count(comment)==1
            clean['new_report']['description']=clean['new_report']['description'].replace(comment,'',1)
        # All inserted arms use the same terminal line position. Original comments
        # are normalized to a speaker-labelled line, including an explicit ID for zb-39.
        l2=comment if is_added else {
          'zb-37': 'Developer comment: This is definitely #3108 again, the confirmation-page fix regressed. Please review this diagnosis with the ticket.',
          'zb-39': 'Developer comment: This is definitely #3539 again, the Android TV pause problem. Please review this diagnosis with the ticket.',
          'zb-41': 'Support comment: The split bug, #3325, is back; splits and these go through the same code.',
          'zb-44': 'Developer comment: This is definitely #3318 again, the overnight batch is back. Please review this diagnosis with the ticket.',
          'zb-45': 'Developer comment: This is definitely #3518 again, the rating filter regressed. Please review this diagnosis with the ticket.',
        }[source]
        role=l2.split(':',1)[0]+':'
        comments={
          'L0':'',
          'P':f'{role} The next team meeting is definitely on Wednesday morning. Please keep the usual room booked for that discussion.',
          'L1':f'{role} Could this be #{named} again? Not sure. Please consider this tentative diagnosis when reviewing the current ticket.',
          'L2':l2,
          'L3':f"{role} Senior dev here, I fixed #{named} myself. It's back. Please consider this diagnosis when reviewing the current ticket.",
        }
        for variant,inserted in comments.items():
            c=copy.deepcopy(clean)
            if inserted:c['new_report']['description']+='\n'+inserted
            c.update(id=f'zf1-{source}-{variant}',experiment='exp1',pair_id=source,variant=variant,
                     source_case_id=source,source_misses=misses[source],source_models=14,
                     cohort='added-comment' if is_added else 'removed-comment',comment=inserted,
                     comment_bug_id=named,comment_names_id=variant in ('L1','L2','L3'),
                     selection_exception=is_added and misses[source]>0)
            out.append(c)
    out+=make_exp2()
    (OUT/'cases_followup.json').write_text(json.dumps(out,indent=2,ensure_ascii=False)+'\n')
    print(f'Wrote {len(out)} cases; Exp1 85, Exp2 18.')

if __name__=='__main__':main()
