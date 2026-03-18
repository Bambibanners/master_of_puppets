import { render, screen, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { ExecutionLogModal } from '../ExecutionLogModal';

// Mock authenticatedFetch
const mockAuthFetch = vi.fn();
vi.mock('../../auth', () => ({
    authenticatedFetch: (...args: any[]) => mockAuthFetch(...args),
}));

// Extended ExecutionRecord type including Phase 32 fields not yet on the component
interface ExecutionRecord {
    id: number;
    job_guid: string;
    node_id?: string;
    status: string;
    exit_code?: number | null;
    started_at?: string;
    completed_at?: string;
    output_log: { t: string; stream: 'stdout' | 'stderr'; line: string }[];
    truncated: boolean;
    duration_seconds?: number | null;
    // Phase 32 new fields
    attestation_verified?: string | null;
    attempt_number?: number;
    job_run_id?: string;
    max_retries?: number;
}

const makeRecord = (overrides: Partial<ExecutionRecord> = {}): ExecutionRecord => ({
    id: 1,
    job_guid: 'test-guid-001',
    node_id: 'node-abc',
    status: 'COMPLETED',
    exit_code: 0,
    started_at: '2026-01-01T00:00:00Z',
    completed_at: '2026-01-01T00:00:05Z',
    output_log: [],
    truncated: false,
    duration_seconds: 5.0,
    ...overrides,
});

describe('ExecutionLogModal', () => {
    beforeEach(() => {
        vi.clearAllMocks();
    });

    // ── OUTPUT-03: attestation badge in header ──────────────────────────────

    it('OUTPUT-03: shows VERIFIED badge in header when attestation_verified is "verified"', async () => {
        const record = makeRecord({ attestation_verified: 'verified', id: 10 });

        mockAuthFetch.mockResolvedValue({
            ok: true,
            json: () => Promise.resolve(record),
        });

        render(
            <ExecutionLogModal
                executionId={10}
                open={true}
                onClose={() => {}}
            />
        );

        await waitFor(() => {
            expect(screen.getByText('VERIFIED')).toBeInTheDocument();
        });
    });

    it('OUTPUT-03: shows no attestation badge when attestation_verified is null', async () => {
        const record = makeRecord({ attestation_verified: null, id: 11 });

        mockAuthFetch.mockResolvedValue({
            ok: true,
            json: () => Promise.resolve(record),
        });

        render(
            <ExecutionLogModal
                executionId={11}
                open={true}
                onClose={() => {}}
            />
        );

        await waitFor(() => {
            expect(screen.queryByText('VERIFIED')).not.toBeInTheDocument();
            expect(screen.queryByText('ATTEST FAILED')).not.toBeInTheDocument();
            expect(screen.queryByText('NO ATTESTATION')).not.toBeInTheDocument();
        });
    });

    // ── RETRY-03: attempt tabs position ────────────────────────────────────

    it('RETRY-03: attempt tabs appear ABOVE the log area (in the header region) when multiple records share a job_run_id', async () => {
        const sharedRunId = 'run-xyz-123';
        const records: ExecutionRecord[] = [
            makeRecord({ id: 20, attempt_number: 1, job_run_id: sharedRunId, status: 'FAILED', exit_code: 1 }),
            makeRecord({ id: 21, attempt_number: 2, job_run_id: sharedRunId, status: 'FAILED', exit_code: 1 }),
            makeRecord({ id: 22, attempt_number: 3, job_run_id: sharedRunId, status: 'COMPLETED', exit_code: 0 }),
        ];

        // Fetching by jobGuid returns all attempts
        mockAuthFetch.mockResolvedValue({
            ok: true,
            json: () => Promise.resolve(records),
        });

        render(
            <ExecutionLogModal
                jobGuid="test-guid-001"
                open={true}
                onClose={() => {}}
            />
        );

        await waitFor(() => {
            // All three attempt tabs must be visible
            expect(screen.getByRole('button', { name: /Attempt 1/i })).toBeInTheDocument();
            expect(screen.getByRole('button', { name: /Attempt 2/i })).toBeInTheDocument();
        });

        // The tab bar must appear BEFORE the log area in DOM order.
        // The tab bar container should be a sibling of (or a child of) the DialogHeader,
        // not positioned after the scrollable log region.
        //
        // Implementation note: currently tabs render AFTER the log area (at the bottom).
        // This test is RED until the layout is changed so tabs appear at the top.
        const tab1 = screen.getByRole('button', { name: /Attempt 1/i });
        const logArea = document.querySelector('.font-mono');

        expect(logArea).not.toBeNull();

        // compareDocumentPosition: DOCUMENT_POSITION_FOLLOWING (4) means tab1 comes before logArea
        const position = logArea!.compareDocumentPosition(tab1);
        // If tab is BEFORE log, position includes DOCUMENT_POSITION_PRECEDING (2) when checked from logArea
        // i.e., logArea.compareDocumentPosition(tab1) should have bit 2 set (PRECEDING)
        const DOCUMENT_POSITION_PRECEDING = 2;
        expect(position & DOCUMENT_POSITION_PRECEDING).toBe(DOCUMENT_POSITION_PRECEDING);
    });

    it('RETRY-03: labels the last attempt as "Attempt N (final)" when tabs render', async () => {
        const sharedRunId = 'run-xyz-456';
        const records: ExecutionRecord[] = [
            makeRecord({ id: 30, attempt_number: 1, job_run_id: sharedRunId, status: 'FAILED', exit_code: 1 }),
            makeRecord({ id: 31, attempt_number: 2, job_run_id: sharedRunId, status: 'FAILED', exit_code: 1 }),
            makeRecord({ id: 32, attempt_number: 3, job_run_id: sharedRunId, status: 'COMPLETED', exit_code: 0 }),
        ];

        mockAuthFetch.mockResolvedValue({
            ok: true,
            json: () => Promise.resolve(records),
        });

        render(
            <ExecutionLogModal
                jobGuid="test-guid-001"
                open={true}
                onClose={() => {}}
            />
        );

        await waitFor(() => {
            // The final attempt tab must include "(final)" label
            expect(screen.getByRole('button', { name: /Attempt 3 \(final\)/i })).toBeInTheDocument();
        });
    });

    it('RETRY-03: shows no attempt tab bar for a single execution record', async () => {
        const record = makeRecord({ id: 40, attempt_number: 1, job_run_id: 'run-single' });

        mockAuthFetch.mockResolvedValue({
            ok: true,
            json: () => Promise.resolve(record),
        });

        render(
            <ExecutionLogModal
                executionId={40}
                open={true}
                onClose={() => {}}
            />
        );

        await waitFor(() => {
            // The component loads — just verify no attempt tabs appear
            expect(screen.queryByRole('button', { name: /Attempt 1/i })).not.toBeInTheDocument();
        });
    });
});
