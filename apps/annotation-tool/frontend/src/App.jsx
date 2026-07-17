import {
  ArrowLeft,
  ArrowRight,
  Brain,
  CheckCircle2,
  Download,
  FileJson,
  RefreshCw,
  Save,
} from "lucide-react";
import { useCallback, useEffect, useMemo, useState } from "react";

const API_BASE = import.meta.env.VITE_API_BASE ?? "";
const DEFAULT_MANIFEST = "data/samples/candidate-manifest.sample.json";

function nowIso() {
  return new Date().toISOString().replace(/\.\d{3}Z$/, "Z");
}

function encodeClipPath(path) {
  return path
    .split("/")
    .map((part) => encodeURIComponent(part))
    .join("/");
}

function defaultAnnotation(sample, config) {
  const firstLabel = config?.event_labels?.[0]?.value || "";
  return {
    sample_id: sample.sample_id,
    event_label: firstLabel,
    event_start_ms: sample.start_ms,
    event_end_ms: sample.end_ms,
    ground_truth_status: "unreviewed",
    reviewer: config?.default_reviewer || "",
    reviewed_at: nowIso(),
    comment: "",
    annotation_version: 1,
  };
}

function loadStoredAnnotations(manifestPath) {
  try {
    const raw = localStorage.getItem(`vsf-annotations:${manifestPath}`);
    return raw ? JSON.parse(raw) : {};
  } catch {
    return {};
  }
}

function saveStoredAnnotations(manifestPath, annotations) {
  localStorage.setItem(`vsf-annotations:${manifestPath}`, JSON.stringify(annotations));
}

export default function App() {
  const [config, setConfig] = useState(null);
  const [manifestPath, setManifestPath] = useState(DEFAULT_MANIFEST);
  const [loadedPath, setLoadedPath] = useState(DEFAULT_MANIFEST);
  const [manifest, setManifest] = useState(null);
  const [index, setIndex] = useState(0);
  const [annotations, setAnnotations] = useState({});
  const [form, setForm] = useState(null);
  const [status, setStatus] = useState("Idle");
  const [error, setError] = useState("");
  const [videoMissing, setVideoMissing] = useState(false);
  const [reviewNote, setReviewNote] = useState("");

  const samples = manifest?.samples || [];
  const current = samples[index] || null;
  const progress = useMemo(() => {
    const reviewed = Object.values(annotations).filter(
      (item) => item.ground_truth_status && item.ground_truth_status !== "unreviewed"
    ).length;
    return { reviewed, total: samples.length };
  }, [annotations, samples.length]);

  const persistAnnotation = useCallback(
    (nextForm) => {
      if (!current) return;
      const next = {
        ...annotations,
        [current.sample_id]: {
          ...nextForm,
          sample_id: current.sample_id,
          reviewed_at: nowIso(),
          annotation_version: nextForm.annotation_version || 1,
        },
      };
      setAnnotations(next);
      saveStoredAnnotations(loadedPath, next);
    },
    [annotations, current, loadedPath]
  );

  const setField = (field, value) => {
    const nextForm = { ...form, [field]: value };
    setForm(nextForm);
    persistAnnotation(nextForm);
  };

  const loadConfig = useCallback(async () => {
    const response = await fetch(`${API_BASE}/config`);
    if (!response.ok) throw new Error("Cannot load config");
    setConfig(await response.json());
  }, []);

  const loadManifest = useCallback(
    async (path) => {
      setStatus("Loading manifest");
      setError("");
      const response = await fetch(`${API_BASE}/manifest?path=${encodeURIComponent(path)}`);
      if (!response.ok) {
        const detail = await response.text();
        throw new Error(detail);
      }
      const payload = await response.json();
      setManifest(payload.manifest);
      setLoadedPath(path);
      setManifestPath(path);
      setIndex(0);
      setAnnotations(loadStoredAnnotations(path));
      setStatus("Manifest loaded");
    },
    []
  );

  const resolveDefaultManifest = useCallback(async () => {
    try {
      const response = await fetch(`${API_BASE}/manifests`);
      if (!response.ok) return DEFAULT_MANIFEST;
      const payload = await response.json();
      return payload.manifests?.[0] || DEFAULT_MANIFEST;
    } catch {
      return DEFAULT_MANIFEST;
    }
  }, []);

  useEffect(() => {
    loadConfig()
      .then(resolveDefaultManifest)
      .then((path) => loadManifest(path))
      .catch((exc) => setError(exc.message));
  }, [loadConfig, loadManifest, resolveDefaultManifest]);

  useEffect(() => {
    if (!current || !config) {
      setForm(null);
      return;
    }
    const saved = annotations[current.sample_id];
    setForm(saved || defaultAnnotation(current, config));
    setVideoMissing(false);
    setReviewNote("");
  }, [annotations, config, current]);

  useEffect(() => {
    const onKeyDown = (event) => {
      if (event.key === "ArrowLeft") {
        setIndex((value) => Math.max(0, value - 1));
      }
      if (event.key === "ArrowRight") {
        setIndex((value) => Math.min(samples.length - 1, value + 1));
      }
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "s") {
        event.preventDefault();
        if (form) {
          persistAnnotation(form);
          setStatus("Saved locally");
        }
      }
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [form, persistAnnotation, samples.length]);

  const exportAnnotations = async () => {
    if (!manifest || !config) return;
    const allAnnotations = samples.map((sample) => annotations[sample.sample_id] || defaultAnnotation(sample, config));
    setStatus("Exporting annotations");
    setError("");
    const response = await fetch(`${API_BASE}/annotations/export`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        manifest_path: loadedPath,
        annotation_batch_id: `${manifest.dataset_id}-${Date.now()}`,
        annotations: allAnnotations,
      }),
    });
    const payload = await response.json();
    if (!response.ok) {
      setError(JSON.stringify(payload.detail || payload, null, 2));
      setStatus("Export failed");
      return;
    }
    setStatus(`Exported ${payload.output_path}`);
  };

  const requestReviewNote = async () => {
    if (!current) return;
    setStatus("Drafting review note");
    const response = await fetch(`${API_BASE}/llm/review-note`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ sample: current, annotation: form }),
    });
    const payload = await response.json();
    if (!response.ok) {
      setError(JSON.stringify(payload.detail || payload));
      return;
    }
    setReviewNote(payload.note);
    setStatus(payload.source === "openai" ? "LLM note drafted" : "Fallback note drafted");
  };

  const clipUrl = current ? `${API_BASE}/clips/${encodeClipPath(current.clip_path)}` : "";

  return (
    <main className="app-shell">
      <header className="topbar">
        <div>
          <h1>AI Camera Annotation</h1>
          <p>{manifest?.dataset_id || "No dataset loaded"}</p>
        </div>
        <div className="topbar-actions">
          <input
            value={manifestPath}
            onChange={(event) => setManifestPath(event.target.value)}
            aria-label="Manifest path"
          />
          <button onClick={() => loadManifest(manifestPath).catch((exc) => setError(exc.message))}>
            <RefreshCw size={16} />
            Load
          </button>
          <button onClick={exportAnnotations} disabled={!manifest}>
            <Download size={16} />
            Export
          </button>
        </div>
      </header>

      <section className="workspace">
        <aside className="queue-panel">
          <div className="panel-header">
            <FileJson size={18} />
            <span>
              {progress.reviewed}/{progress.total}
            </span>
          </div>
          <div className="queue-list">
            {samples.map((sample, sampleIndex) => {
              const saved = annotations[sample.sample_id];
              return (
                <button
                  className={`queue-item ${sampleIndex === index ? "active" : ""}`}
                  key={sample.sample_id}
                  onClick={() => setIndex(sampleIndex)}
                >
                  <span>{sample.clip_type}</span>
                  <strong>{sample.candidate_rule}</strong>
                  <small>{saved?.ground_truth_status || "unreviewed"}</small>
                </button>
              );
            })}
          </div>
        </aside>

        <section className="review-panel">
          <div className="video-frame">
            {current && !videoMissing ? (
              <video
                src={clipUrl}
                controls
                onError={() => setVideoMissing(true)}
                key={current.sample_id}
              />
            ) : (
              <div className="missing-video">Clip file is not available locally.</div>
            )}
          </div>

          {current && (
            <div className="sample-grid">
              <div>
                <span>Sample</span>
                <strong>{current.sample_id}</strong>
              </div>
              <div>
                <span>Window</span>
                <strong>
                  {current.start_ms} - {current.end_ms} ms
                </strong>
              </div>
              <div>
                <span>Source</span>
                <strong>{current.source_video_id}</strong>
              </div>
              <div>
                <span>Clip</span>
                <strong>{current.clip_path}</strong>
              </div>
            </div>
          )}

          <div className="navigation-bar">
            <button onClick={() => setIndex((value) => Math.max(0, value - 1))} disabled={index === 0}>
              <ArrowLeft size={16} />
              Previous
            </button>
            <button
              onClick={() => setIndex((value) => Math.min(samples.length - 1, value + 1))}
              disabled={index >= samples.length - 1}
            >
              Next
              <ArrowRight size={16} />
            </button>
          </div>
        </section>

        <aside className="annotation-panel">
          <div className="panel-header">
            <CheckCircle2 size={18} />
            <span>Annotation</span>
          </div>

          {form && config ? (
            <form className="annotation-form">
              <label>
                Event label
                <select value={form.event_label} onChange={(event) => setField("event_label", event.target.value)}>
                  {config.event_labels.map((label) => (
                    <option value={label.value} key={label.value}>
                      {label.label}
                    </option>
                  ))}
                </select>
              </label>
              <div className="field-row">
                <label>
                  Start ms
                  <input
                    type="number"
                    value={form.event_start_ms}
                    onChange={(event) => setField("event_start_ms", Number(event.target.value))}
                  />
                </label>
                <label>
                  End ms
                  <input
                    type="number"
                    value={form.event_end_ms}
                    onChange={(event) => setField("event_end_ms", Number(event.target.value))}
                  />
                </label>
              </div>
              <label>
                Status
                <select
                  value={form.ground_truth_status}
                  onChange={(event) => setField("ground_truth_status", event.target.value)}
                >
                  {config.ground_truth_statuses.map((item) => (
                    <option value={item} key={item}>
                      {item}
                    </option>
                  ))}
                </select>
              </label>
              <label>
                Reviewer
                <input value={form.reviewer} onChange={(event) => setField("reviewer", event.target.value)} />
              </label>
              <label>
                Comment
                <textarea value={form.comment} onChange={(event) => setField("comment", event.target.value)} />
              </label>
              <div className="form-actions">
                <button
                  type="button"
                  onClick={() => {
                    persistAnnotation(form);
                    setStatus("Saved locally");
                  }}
                >
                  <Save size={16} />
                  Save
                </button>
                <button type="button" onClick={requestReviewNote}>
                  <Brain size={16} />
                  Note
                </button>
              </div>
              {reviewNote && <p className="review-note">{reviewNote}</p>}
            </form>
          ) : (
            <div className="empty-state">Load a manifest to start reviewing.</div>
          )}

          <footer className="status-bar">
            <span>{status}</span>
            {error && <pre>{error}</pre>}
          </footer>
        </aside>
      </section>
    </main>
  );
}
