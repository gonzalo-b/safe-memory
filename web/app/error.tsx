'use client';
import { Button } from '../vendor/memory-ds/react/core';
export default function ErrorBoundary({ reset }: { reset: () => void }) {
  return <main className="memory-auth"><section className="memory-auth-card memory-stack"><h1 className="m-page">This page could not load</h1><p className="m-body">Your private data could not be displayed. Try again to request a fresh response.</p><Button variant="primary" onClick={reset}>Try again</Button></section></main>;
}
