import { useState } from "react";
import { X, ShieldCheck, ShieldX, FileDown } from "lucide-react";
import { submitReview, challanUrl, mediaUrl, type Violation } from "../api/client";
import { Chip, StatusChip, formatConfidence } from "./Chip";

const REVIEWER_STORAGE_KEY = "tv_last_reviewer";

interface Props {
  violation: Violation;
  onClose: () => void;
  onDone: () => void;
}

export default function ReviewModal({ violation, onClose, onDone }: Props) {
  const stored = (() => {
    try {
      return JSON.parse(localStorage.getItem(REVIEWER_STORAGE_KEY) || "{}");
    } catch {
      return {};
    }
  })();

  const [officerName, setOfficerName] = useState(stored.officerName || "");
  const [officerBadgeId, setOfficerBadgeId] = useState(stored.officerBadgeId || "");
  const [notes, setNotes] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [justVerified, setJustVerified] = useState(false);

  const isPending = violation.status === "Pending Review";
  const hasImage = !!violation.annotated_image_path;
  const isRepeatOffender = (violation.repeat_count ?? 0) >= 2;
  const canSubmit = hasImage && officerName.trim() && officerBadgeId.trim() && !submitting;

  const decide = async (decision: "Verified" | "Rejected") => {
    if (!canSubmit) return;
    setSubmitting(true);
    setError(null);
    try {
      localStorage.setItem(REVIEWER_STORAGE_KEY, JSON.stringify({ officerName, officerBadgeId }));
      await submitReview(violation.violation_id, decision, officerName, officerBadgeId, notes || undefined);
      if (decision === "Verified") {
        setJustVerified(true);
      } else {
        onDone();
      }
    } catch {
      setError("Could not submit review. Please try again.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4" onClick={onClose}>
      <div className="tv-card w-full max-w-2xl p-6 max-h-[90vh] overflow-y-auto" onClick={(e) => e.stopPropagation()}>
        <div className="flex items-center justify-between gap-4">
          <div>
            <div className="text-lg font-black text-tv-text">{violation.violation_id}</div>
            <div className="text-tv-muted text-sm mt-0.5">{violation.violation_type}</div>
          </div>
          <div className="flex items-center gap-3">
            <StatusChip status={violation.status} />
            <button onClick={onClose} className="text-tv-muted hover:text-tv-text">
              <X size={20} />
            </button>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-5">
          <div>
            <div className="text-[11px] font-bold text-tv-muted uppercase tracking-wide mb-1">Original</div>
            {violation.original_image_path ? (
              <img src={mediaUrl(violation.original_image_path)} className="rounded-xl w-full object-contain max-h-[280px] border border-tv-border" />
            ) : (
              <div className="border border-dashed border-tv-border rounded-xl py-10 text-center text-tv-muted text-sm">No image</div>
            )}
          </div>
          <div>
            <div className="text-[11px] font-bold text-tv-muted uppercase tracking-wide mb-1">Annotated (AI Detection)</div>
            {violation.annotated_image_path ? (
              <img src={mediaUrl(violation.annotated_image_path)} className="rounded-xl w-full object-contain max-h-[280px] border border-tv-border" />
            ) : (
              <div className="border border-dashed border-tv-border rounded-xl py-10 text-center text-tv-muted text-sm">
                No image captured for this record
              </div>
            )}
          </div>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mt-4 text-sm">
          <div>
            <div className="text-[11px] font-bold text-tv-muted uppercase">Vehicle</div>
            <div className="text-tv-text font-semibold">{violation.vehicle_number || "—"}</div>
            {isRepeatOffender && (
              <div className="mt-1">
                <Chip text={`Repeat Offender — #${violation.repeat_count} recorded`} variant="orange" />
              </div>
            )}
          </div>
          <div>
            <div className="text-[11px] font-bold text-tv-muted uppercase">Confidence</div>
            <div className="text-tv-text font-semibold">{formatConfidence(violation.confidence)}</div>
          </div>
          <div>
            <div className="text-[11px] font-bold text-tv-muted uppercase">City</div>
            <div className="text-tv-text font-semibold">{violation.city || "—"}</div>
          </div>
          <div>
            <div className="text-[11px] font-bold text-tv-muted uppercase">Timestamp</div>
            <div className="text-tv-text font-semibold">{new Date(violation.created_at).toLocaleString()}</div>
          </div>
        </div>

        {justVerified ? (
          <div className="mt-5 border-t border-tv-border pt-4">
            <div className="text-[13px] font-bold text-tv-success mb-3">
              ✅ Violation verified. An e-challan is now available for this record.
            </div>
            <div className="flex gap-3">
              <a
                href={challanUrl(violation.violation_id)}
                className="flex-1 flex items-center justify-center gap-2 bg-gradient-to-br from-tv-primary to-tv-primary/85 text-white font-bold px-4 py-2.5 rounded-xl hover:-translate-y-0.5 transition"
              >
                <FileDown size={16} /> Download E-Challan
              </a>
              <button
                onClick={onDone}
                className="px-5 py-2.5 rounded-xl border border-tv-border text-tv-text font-bold hover:bg-black/3 transition"
              >
                Done
              </button>
            </div>
          </div>
        ) : isPending ? (
          <div className="mt-5 border-t border-tv-border pt-4">
            {!hasImage && (
              <div className="mb-3 text-[12px] font-semibold text-tv-warning bg-tv-warning/10 border border-tv-warning/30 rounded-xl px-3 py-2">
                No captured image is attached to this record, so it cannot be verified or rejected — an officer must be able to see the evidence before deciding. This happens on synthetic demo entries; real detections from Live Detection / Wrong-Side Driving always attach an image.
              </div>
            )}
            <div className="text-[12px] font-bold text-tv-text mb-2">Reviewing Officer</div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              <input
                value={officerName}
                onChange={(e) => setOfficerName(e.target.value)}
                placeholder="Officer Name"
                disabled={!hasImage}
                className="bg-tv-bg-soft border border-tv-border rounded-xl px-3 py-2 text-sm text-tv-text outline-none focus:border-tv-primary/55 disabled:opacity-50"
              />
              <input
                value={officerBadgeId}
                onChange={(e) => setOfficerBadgeId(e.target.value)}
                placeholder="Badge ID"
                disabled={!hasImage}
                className="bg-tv-bg-soft border border-tv-border rounded-xl px-3 py-2 text-sm text-tv-text outline-none focus:border-tv-primary/55 disabled:opacity-50"
              />
            </div>
            <input
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="Notes (optional)"
              disabled={!hasImage}
              className="mt-3 w-full bg-tv-bg-soft border border-tv-border rounded-xl px-3 py-2 text-sm text-tv-text outline-none focus:border-tv-primary/55 disabled:opacity-50"
            />

            {error && <div className="text-[12px] font-semibold text-tv-violation mt-2">{error}</div>}

            <div className="flex gap-3 mt-4">
              <button
                onClick={() => decide("Verified")}
                disabled={!canSubmit}
                className="flex-1 flex items-center justify-center gap-2 bg-gradient-to-br from-tv-success to-tv-success/85 text-white font-bold px-4 py-2.5 rounded-xl hover:-translate-y-0.5 transition disabled:opacity-50 disabled:translate-y-0"
              >
                <ShieldCheck size={16} /> Verify (Violation Confirmed)
              </button>
              <button
                onClick={() => decide("Rejected")}
                disabled={!canSubmit}
                className="flex-1 flex items-center justify-center gap-2 bg-gradient-to-br from-tv-violation to-tv-violation/85 text-white font-bold px-4 py-2.5 rounded-xl hover:-translate-y-0.5 transition disabled:opacity-50 disabled:translate-y-0"
              >
                <ShieldX size={16} /> Reject (False Positive)
              </button>
            </div>
          </div>
        ) : (
          <div className="mt-5 border-t border-tv-border pt-4">
            <div className="text-sm text-tv-muted font-semibold">
              This record has already been reviewed. See Review History for who decided and when.
            </div>
            {violation.status === "Verified" && (
              <a
                href={challanUrl(violation.violation_id)}
                className="mt-3 inline-flex items-center gap-2 bg-gradient-to-br from-tv-primary to-tv-primary/85 text-white font-bold px-4 py-2.5 rounded-xl hover:-translate-y-0.5 transition"
              >
                <FileDown size={16} /> Download E-Challan
              </a>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
