'use client';
import { useState } from 'react';
import { Button } from '../vendor/memory-ds/react/core';
import { Icon } from '../vendor/memory-ds/react/Icon';
import type { Source, SourcePolicyInput } from '../lib/types';
const flags = [['include_hidden', 'Include Hidden'], ['include_shared_library', 'Include Shared Library'], ['include_shared_albums', 'Include Shared Albums']] as const;
function valid(value: unknown) { return value === true || value === false || value === 0 || value === 1; }
export function SourcePolicy({ source, busy, save }: { source: Source; busy: boolean; save: (policy: SourcePolicyInput) => void }) {
  const [draft, setDraft] = useState(() => Object.fromEntries(flags.map(([key]) => [key, source[key] === 1 || source[key] === true])) as Omit<SourcePolicyInput, 'connection_id'>);
  if (!flags.every(([key]) => valid(source[key]))) return <p className="m-help memory-spaced">Source policy is unavailable. Refresh before changing consent.</p>;
  const changed = flags.some(([key]) => draft[key] !== (source[key] === 1 || source[key] === true));
  return <div className="memory-stack memory-spaced" role="group" aria-label={`Source policy for ${source.name}`}>
    <div><h3 className="m-title">Included collections</h3><p className="m-help memory-spaced">Each choice is separate. Saving changes what Memory may display and interrupts the current import. It never changes your Photos library.</p></div>
    {flags.map(([key, label]) => <Button key={key} role="checkbox" aria-checked={draft[key]} className="memory-comparison" size="lg" disabled={busy} onClick={() => setDraft(value => ({ ...value, [key]: !value[key] }))}>
      <span className="m-check" aria-checked={draft[key]} aria-hidden="true">{draft[key] && <Icon name="check" />}</span><span>{label}</span>
    </Button>)}
    <p className="m-help">Unknown shared provenance requires both shared choices. If source chronology is uncertain, restrictions remain until you explicitly include the relevant category.</p>
    <div><Button variant="tonal" size="lg" disabled={!changed || busy} onClick={() => save({ connection_id: source.id, ...draft })}>Save source policy</Button></div>
  </div>;
}
