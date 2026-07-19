import { CheckCircle2, FileJson, Film, Play, RefreshCw, RotateCw, Upload, Users, XCircle } from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";

function encodePath(path) {
  return path
    .split("/")
    .map((part) => encodeURIComponent(part))
    .join("/");
}

function formatMs(ms) {
  const total = Math.round(ms / 1000);
  const minutes = String(Math.floor(total / 60)).padStart(2, "0");
  const seconds = String(total % 60).padStart(2, "0");
  return `${minutes}:${seconds}`;
}

export default function TriagePanel({ apiBase, onManifestReady }) {
  const [inputs, setInputs] = useState([]);
  const [inputDir, setInputDir] = useState("data/raw");
  const [rawVideos, setRawVideos] = useState([]);
  const [checked, setChecked] = useState(() => new Set());
  const [model, setModel] = useState("yolov8");
  const [intervalMs, setIntervalMs] = useState(2000);
  // 0.3, not 0.5: YOLOv4 scores distant CCTV figures at 0.35-0.69, so the
  // usual 0.5 silently drops them.
  const [minConfidence, setMinConfidence] = useState(0.3);
  const [minHits, setMinHits] = useState(2);
  const [state, setState] = useState({ status: "idle" });
  const [preview, setPreview] = useState(null);
  const [error, setError] = useState("");
  const [uploading, setUploading] = useState(false);
  const [mining, setMining] = useState(false);
  const [mineResult, setMineResult] = useState(null);
  const [bboxing, setBboxing] = useState(false);
  const [bboxResult, setBboxResult] = useState(null);
  const [exportState, setExportState] = useState({ status: "idle" });
  const pollRef = useRef(null);
  const exportPollRef = useRef(null);
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const fileRef = useRef(null);

  const fetchStatus = useCallback(async () => {
    try {
      const response = await fetch(`${apiBase}/triage/status`);
      if (!response.ok) return;
      const payload = await response.json();
      setState(payload);
      if (payload.status !== "running" && pollRef.current) {
        clearInterval(pollRef.current);
        pollRef.current = null;
      }
    } catch {
      /* keep last state; poll retries */
    }
  }, [apiBase]);

  const loadVideos = useCallback(
    async (dir, { reset = true } = {}) => {
      try {
        const response = await fetch(`${apiBase}/triage/videos?path=${encodeURIComponent(dir)}`);
        if (!response.ok) {
          setRawVideos([]);
          return;
        }
        const payload = await response.json();
        setRawVideos(payload.videos || []);
        if (reset) {
          setChecked(new Set());
          setPreview(null);
        }
      } catch {
        setRawVideos([]);
      }
    },
    [apiBase]
  );

  useEffect(() => {
    fetch(`${apiBase}/triage/inputs`)
      .then((response) => response.json())
      .then((payload) => {
        const list = payload.inputs || [];
        setInputs(list);
        if (list.length) {
          setInputDir(list[0].path);
          loadVideos(list[0].path);
        }
      })
      .catch(() => setInputs([]));
    fetchStatus();
    return () => {
      if (pollRef.current) clearInterval(pollRef.current);
      if (exportPollRef.current) clearInterval(exportPollRef.current);
    };
  }, [apiBase, fetchStatus, loadVideos]);

  const changeDir = (dir) => {
    setInputDir(dir);
    loadVideos(dir);
  };

  const toggle = (path) => {
    setChecked((previous) => {
      const next = new Set(previous);
      if (next.has(path)) next.delete(path);
      else next.add(path);
      return next;
    });
  };

  const toggleAll = () => {
    setChecked((previous) =>
      previous.size === rawVideos.length ? new Set() : new Set(rawVideos.map((v) => v.path))
    );
  };

  const startRun = async (paths) => {
    setError("");
    setMineResult(null);
    try {
      const response = await fetch(`${apiBase}/triage/run`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          videos: paths,
          model,
          sample_interval_ms: Number(intervalMs),
          min_confidence: Number(minConfidence),
          min_hits: Number(minHits),
        }),
      });
      if (!response.ok) {
        const detail = await response.json().catch(() => ({}));
        setError(detail.detail || "Cannot start");
        return;
      }
      setState({ status: "running", processed: 0, total: paths.length });
      if (pollRef.current) clearInterval(pollRef.current);
      pollRef.current = setInterval(fetchStatus, 1000);
    } catch (exc) {
      setError(String(exc));
    }
  };

  const mineCandidates = async () => {
    const selectedKept = kept.filter((video) => checked.has(video.video_path));
    const paths = (selectedKept.length ? selectedKept : kept).map((video) => video.video_path);
    if (!paths.length) return;

    setError("");
    setMining(true);
    try {
      const response = await fetch(`${apiBase}/triage/mine`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          videos: paths,
          random_seed: 42,
        }),
      });
      const payload = await response.json();
      if (!response.ok) {
        setError(JSON.stringify(payload.detail || payload, null, 2));
        return;
      }
      setMineResult(payload);
      const firstManifest = payload.outputs?.[0]?.manifest_path;
      if (firstManifest && onManifestReady) {
        await onManifestReady(firstManifest);
      }
      if (payload.errors?.length) {
        setError(payload.errors.join(" | "));
      }
    } catch (exc) {
      setError(String(exc));
    } finally {
      setMining(false);
    }
  };

  const renderBboxVideo = async () => {
    if (!preview) return;
    setError("");
    setBboxing(true);
    setBboxResult(null);
    try {
      const response = await fetch(`${apiBase}/triage/bbox`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          path: preview.path,
          model,
          sample_fps: 0.5,
          min_confidence: Number(minConfidence),
        }),
      });
      const payload = await response.json();
      if (!response.ok) {
        setError(JSON.stringify(payload.detail || payload, null, 2));
        return;
      }
      setBboxResult(payload.result);
    } catch (exc) {
      setError(String(exc));
    } finally {
      setBboxing(false);
    }
  };

  const fetchExportStatus = useCallback(async () => {
    try {
      const response = await fetch(`${apiBase}/triage/suspicious/status`);
      if (!response.ok) return;
      const payload = await response.json();
      setExportState(payload);
      if (payload.status !== "running" && exportPollRef.current) {
        clearInterval(exportPollRef.current);
        exportPollRef.current = null;
      }
    } catch {
      /* keep last state; poll retries */
    }
  }, [apiBase]);

  // Cut a 60s clip (30s before/after the person appears) for every selected
  // video that has a person, with YOLO boxes burned in, into outputs/suspicious/.
  const exportSuspicious = async (paths) => {
    if (!paths.length) return;
    setError("");
    try {
      const response = await fetch(`${apiBase}/triage/suspicious`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          videos: paths,
          model,
          sample_interval_ms: Number(intervalMs),
          min_confidence: Number(minConfidence),
          min_hits: Number(minHits),
        }),
      });
      if (!response.ok) {
        const detail = await response.json().catch(() => ({}));
        setError(detail.detail || "Cannot start export");
        return;
      }
      setExportState({ status: "running", processed: 0, total: paths.length, clips: [], skipped: [] });
      if (exportPollRef.current) clearInterval(exportPollRef.current);
      exportPollRef.current = setInterval(fetchExportStatus, 1500);
    } catch (exc) {
      setError(String(exc));
    }
  };

  const uploadFiles = async (files) => {
    if (!files?.length) return;
    setError("");
    setUploading(true);
    const failed = [];
    for (const file of files) {
      const body = new FormData();
      body.append("file", file);
      body.append("path", inputDir);
      try {
        const response = await fetch(`${apiBase}/triage/upload`, { method: "POST", body });
        if (!response.ok) {
          const detail = await response.json().catch(() => ({}));
          failed.push(`${file.name}: ${detail.detail || response.status}`);
        }
      } catch (exc) {
        failed.push(`${file.name}: ${exc}`);
      }
    }
    setUploading(false);
    if (failed.length) setError(failed.join(" | "));
    await loadVideos(inputDir, { reset: false });
    if (fileRef.current) fileRef.current.value = "";
  };

  const report = state.report;
  const running = state.status === "running";
  const exportRunning = exportState.status === "running";
  const kept = report?.videos?.filter((v) => v.decision === "keep") || [];
  const rejected = report?.videos?.filter((v) => v.decision === "rejected") || [];
  const percent = state.percent ?? 0;
  const resultFor = (path) => report?.videos?.find((v) => v.video_path === path);

  const seek = (ms) => {
    if (videoRef.current) {
      videoRef.current.currentTime = ms / 1000;
      videoRef.current.play();
    }
  };

  const previewResult = preview ? resultFor(preview.path) : null;

  useEffect(() => {
    setBboxResult(null);
  }, [preview?.path]);

  // Boxes are sampled, not continuous: show the nearest sampled frame's boxes
  // while the video plays within half a sample interval of it.
  const drawBoxes = useCallback(() => {
    const canvas = canvasRef.current;
    const video = videoRef.current;
    if (!canvas || !video) return;
    const ctx = canvas.getContext("2d");
    canvas.width = video.clientWidth;
    canvas.height = video.clientHeight;
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    const hits = previewResult?.hits;
    if (!hits?.length) return;

    const nowMs = video.currentTime * 1000;
    const interval = report?.settings?.sample_interval_ms || 2000;
    // Hold the most recent detection's boxes until the next sample, like the
    // reference "held sample" overlay, so boxes stay on screen instead of
    // flickering at each sampled instant. Clear if the gap is more than one
    // interval (nobody was detected around now).
    let nearest = null;
    for (const hit of hits) {
      if (hit.timestamp_ms <= nowMs + interval / 2 && Math.abs(hit.timestamp_ms - nowMs) <= interval) {
        if (!nearest || hit.timestamp_ms > nearest.timestamp_ms) nearest = hit;
      }
    }
    if (!nearest?.boxes?.length) return;

    ctx.lineWidth = 2;
    ctx.strokeStyle = "#22c55e";
    ctx.fillStyle = "rgba(34,197,94,0.85)";
    ctx.font = "12px system-ui, sans-serif";
    for (const box of nearest.boxes) {
      const x = box.x * canvas.width;
      const y = box.y * canvas.height;
      const w = box.w * canvas.width;
      const h = box.h * canvas.height;
      ctx.strokeRect(x, y, w, h);
      const label = `${Math.round(box.confidence * 100)}%`;
      const tw = ctx.measureText(label).width + 6;
      ctx.fillStyle = "rgba(34,197,94,0.85)";
      ctx.fillRect(x, y - 15, tw, 15);
      ctx.fillStyle = "#052e16";
      ctx.fillText(label, x + 3, y - 4);
    }
  }, [previewResult, report]);

  useEffect(() => {
    const video = videoRef.current;
    if (!video) return;
    let raf = 0;
    const loop = () => {
      drawBoxes();
      raf = requestAnimationFrame(loop);
    };
    raf = requestAnimationFrame(loop);
    return () => cancelAnimationFrame(raf);
  }, [drawBoxes, preview]);

  return (
    <section className="triage">
      <div className="triage-controls">
        <label>
          Folder video input
          <select value={inputDir} onChange={(event) => changeDir(event.target.value)}>
            {inputs.map((item) => (
              <option key={item.path} value={item.path}>
                {item.path} ({item.video_count} video)
              </option>
            ))}
          </select>
        </label>
        <label>
          Model detect
          <select value={model} onChange={(event) => setModel(event.target.value)}>
            <option value="yolov8">YOLOv8 (1920px) - giong video mau</option>
            <option value="yolov4">YOLOv4 (832px) - chinh xac</option>
            <option value="mobilenet-ssd">MobileNet-SSD (300px) - nhanh</option>
          </select>
        </label>
        <label>
          Nhip lay mau (ms)
          <input
            type="number"
            step="500"
            min="200"
            value={intervalMs}
            onChange={(event) => setIntervalMs(event.target.value)}
          />
        </label>
        <label>
          Nguong confidence
          <input
            type="number"
            step="0.05"
            min="0"
            max="1"
            value={minConfidence}
            onChange={(event) => setMinConfidence(event.target.value)}
          />
        </label>
        <label>
          Frame toi thieu
          <input
            type="number"
            min="1"
            value={minHits}
            onChange={(event) => setMinHits(event.target.value)}
          />
        </label>
        <button onClick={() => startRun([...checked])} disabled={running || !checked.size}>
          <RefreshCw size={16} />
          {running ? "Dang chay..." : `Chay ${checked.size || ""} da chon`}
        </button>
        <button
          className="secondary"
          onClick={() => startRun(rawVideos.map((v) => v.path))}
          disabled={running || !rawVideos.length}
        >
          Chay tat ca ({rawVideos.length})
        </button>
        <button
          onClick={() =>
            exportSuspicious(
              (checked.size ? [...checked] : rawVideos.map((v) => v.path))
            )
          }
          disabled={exportRunning || !rawVideos.length}
          title="Cat clip 60s (30s truoc/sau khi nguoi xuat hien) + ve box YOLO, luu outputs/suspicious/"
        >
          <Film size={15} />
          {exportRunning ? "Dang xuat clip..." : "Xuat clip kha nghi (bbox)"}
        </button>
        <button
          className="secondary"
          onClick={() => fileRef.current?.click()}
          disabled={uploading}
        >
          <Upload size={15} />
          {uploading ? "Dang upload..." : "Them video"}
        </button>
        <input
          ref={fileRef}
          type="file"
          accept="video/mp4,video/quicktime,video/x-matroska,video/x-msvideo"
          multiple
          hidden
          onChange={(event) => uploadFiles([...event.target.files])}
        />
      </div>

      <p className={`model-note ${model === "mobilenet-ssd" ? "warn" : ""}`}>
        {model === "yolov8" ? (
          <>
            <strong>YOLOv8</strong> (Ultralytics, 1920px) - bat nguoi o xa tot nhat, giong het video
            mau. ~2.5s/frame CPU. Chay bang torch trong venv Python 3.11. License AGPL-3.0.
          </>
        ) : model === "yolov4" ? (
          <>
            <strong>YOLOv4</strong> - input 832x832, NMS, bat duoc nguoi o xa tren footage CCTV.
            ~3s/frame. License darknet: public domain.
          </>
        ) : (
          <>
            <strong>Canh bao:</strong> MobileNet-SSD ep anh ve 300x300. Do tren footage CCTV
            that (VIRAT, nguoi cao ~44px) no cho <strong>0.000 - truot toan bo</strong>, ke ca
            khi chia luoi 3x3. Chi dung khi nguoi chiem phan lon khung hinh.
          </>
        )}
      </p>

      {error && <p className="triage-error">{error}</p>}
      {state.status === "error" && <p className="triage-error">{state.error}</p>}
      {exportState.status === "error" && (
        <p className="triage-error">Xuat clip loi: {exportState.error}</p>
      )}

      {(exportRunning || exportState.clips?.length > 0 || exportState.skipped?.length > 0) && (
        <div className="triage-progress">
          <div className="progress-head">
            <strong>
              Clip kha nghi (60s, ±30s quanh luc nguoi xuat hien, co box YOLO)
            </strong>
            <span className="percent">{exportState.percent ?? 0}%</span>
          </div>
          <div className="progress-bar">
            <div className="progress-fill" style={{ width: `${exportState.percent ?? 0}%` }} />
          </div>
          {exportRunning && (
            <small>
              Video {Math.min((exportState.processed ?? 0) + 1, exportState.total)}/
              {exportState.total} - {exportState.current}
            </small>
          )}
          {exportState.clips?.map((clip) => (
            <div key={clip.output_path} className="bbox-output">
              <small>
                {clip.source_video} - nguoi xuat hien {formatMs(clip.person_appears_ms)} - clip{" "}
                {formatMs(clip.clip_start_ms)}→{formatMs(clip.clip_end_ms)} (conf{" "}
                {clip.max_confidence})
              </small>
              <video src={`${apiBase}/clips/${encodePath(clip.output_path)}`} controls />
            </div>
          ))}
          {exportState.skipped?.length > 0 && (
            <small>Bo qua (khong co nguoi): {exportState.skipped.join(", ")}</small>
          )}
        </div>
      )}

      {running && (
        <div className="triage-progress">
          <div className="progress-head">
            <strong>Dang lam sach du lieu video</strong>
            <span className="percent">{percent}%</span>
          </div>
          <div className="progress-bar">
            <div className="progress-fill" style={{ width: `${percent}%` }} />
          </div>
          <small>
            Video {Math.min(state.processed + 1, state.total)}/{state.total} - {state.current}
            {state.frame_total
              ? ` - frame ${state.frame_done}/${state.frame_total}`
              : " - dang mo video"}
          </small>
        </div>
      )}

      <div className="triage-columns">
        <div className="triage-column">
          <h3>
            <Film size={16} /> Video thô ({rawVideos.length})
            <button className="link-button" onClick={toggleAll}>
              {checked.size === rawVideos.length && rawVideos.length ? "Bo chon" : "Chon tat ca"}
            </button>
          </h3>
          {rawVideos.map((video) => {
            const result = resultFor(video.path);
            return (
              <div
                key={video.path}
                className={[
                  "triage-item raw",
                  preview?.path === video.path ? "active" : "",
                  result ? `processed ${result.decision}` : "",
                  state.current === video.name && running ? "in-progress" : "",
                ]
                  .filter(Boolean)
                  .join(" ")}
              >
                <input
                  type="checkbox"
                  checked={checked.has(video.path)}
                  onChange={() => toggle(video.path)}
                  aria-label={`Chon ${video.name}`}
                />
                <button className="raw-open" onClick={() => setPreview(video)}>
                  <Play size={12} />
                  <strong>{video.name}</strong>
                  <small>
                    {video.size_mb} MB
                    {result ? ` - conf ${result.max_confidence}` : " - chua chay"}
                  </small>
                </button>
                {result && (
                  <span className={`tag ${result.decision === "keep" ? "tag-keep" : "tag-reject"}`}>
                    {result.decision === "keep" ? "co nguoi" : "khong"}
                  </span>
                )}
                <button
                  className="recheck"
                  title={result ? "Chay lai video nay" : "Chay video nay"}
                  disabled={running}
                  onClick={() => startRun([video.path])}
                >
                  <RotateCw size={13} />
                </button>
              </div>
            );
          })}
          {!rawVideos.length && <p className="triage-empty">Folder khong co video</p>}
        </div>

        <div className="triage-viewer">
          {preview ? (
            <>
              <div className="video-wrap">
                <video
                  key={preview.path}
                  ref={videoRef}
                  src={`${apiBase}/triage/preview?path=${encodeURIComponent(preview.path)}`}
                  controls
                  onLoadedMetadata={drawBoxes}
                />
                <canvas ref={canvasRef} className="box-overlay" />
              </div>
              {previewResult?.hits?.length > 0 && (
                <p className="overlay-hint">
                  Khung xanh = nguoi YOLO phat hien. Tua toi cac moc ben duoi de thay.
                </p>
              )}
              <p className="triage-viewer-name">{preview.path}</p>
              {previewResult ? (
                <div className="triage-meta">
                  <span>
                    Ket luan:{" "}
                    <strong>
                      {previewResult.decision === "keep" ? "Co nguoi" : "Khong co nguoi"}
                    </strong>
                  </span>
                  <span>Confidence cao nhat: {previewResult.max_confidence}</span>
                  <span>
                    Frame co nguoi: {previewResult.frames_with_person}/
                    {previewResult.frames_sampled}
                  </span>
                </div>
              ) : (
                <p className="triage-empty">Chua chay detect cho video nay</p>
              )}
              {previewResult?.person_timestamps_ms?.length > 0 && (
                <div className="triage-stamps">
                  <small>Moc thay nguoi (bam de tua):</small>
                  <div>
                    {previewResult.person_timestamps_ms.slice(0, 40).map((ms) => (
                      <button key={ms} onClick={() => seek(ms)}>
                        {formatMs(ms)}
                      </button>
                    ))}
                  </div>
                </div>
              )}
              <div className="bbox-actions">
                <button onClick={renderBboxVideo} disabled={bboxing}>
                  <Film size={14} />
                  {bboxing ? "Dang tao video bbox..." : "Tao video bbox MP4"}
                </button>
                {bboxResult && (
                  <div className="bbox-output">
                    <small>{bboxResult.output_path}</small>
                    <video
                      src={`${apiBase}/clips/${encodePath(bboxResult.output_path)}`}
                      controls
                    />
                  </div>
                )}
              </div>
            </>
          ) : (
            <p className="triage-empty">Bam mot video ben trai de xem</p>
          )}
        </div>

        <div className="triage-outputs">
          <div className="triage-column">
            <h3>
              <CheckCircle2 size={16} /> Co nguoi ({kept.length})
            </h3>
            {kept.map((video) => (
              <button
                key={video.video_path}
                className={`triage-item ${preview?.path === video.video_path ? "active" : ""}`}
                onClick={() => setPreview({ path: video.video_path, name: video.video_path })}
              >
                <Play size={13} />
                <strong>{video.video_path.split("/").pop()}</strong>
                <small>
                  conf {video.max_confidence} - {video.frames_with_person}/{video.frames_sampled}
                </small>
              </button>
            ))}
            {!kept.length && <p className="triage-empty">Chua co</p>}
          </div>

          <div className="triage-column">
            <h3>
              <XCircle size={16} /> Khong co nguoi ({rejected.length})
            </h3>
            {rejected.map((video) => (
              <button
                key={video.video_path}
                className={`triage-item ${preview?.path === video.video_path ? "active" : ""}`}
                onClick={() => setPreview({ path: video.video_path, name: video.video_path })}
              >
                <Play size={13} />
                <strong>{video.video_path.split("/").pop()}</strong>
                <small>conf {video.max_confidence}</small>
              </button>
            ))}
            {!rejected.length && <p className="triage-empty">Chua co</p>}
          </div>
        </div>
      </div>

      {report && (
        <div className="triage-summary">
          <span className="pill pill-keep">
            <Users size={14} /> Co nguoi: {report.summary.kept}
          </span>
          <span className="pill pill-reject">
            <XCircle size={14} /> Khong co nguoi: {report.summary.rejected}
          </span>
          <span className="detector-badge">{report.detector}</span>
          <small>
            nhip {report.settings.sample_interval_ms}ms - conf &ge; {report.settings.min_confidence}{" "}
            - min {report.settings.min_hits} frame
          </small>
          <button onClick={mineCandidates} disabled={running || mining || !kept.length}>
            <FileJson size={15} />
            {mining ? "Dang tao..." : "Tao manifest/clips"}
          </button>
        </div>
      )}
      {mineResult?.outputs?.length > 0 && (
        <div className="triage-manifest-output">
          {mineResult.outputs.map((output) => (
            <button
              key={output.manifest_path}
              onClick={() => onManifestReady?.(output.manifest_path)}
            >
              <FileJson size={14} />
              <span>{output.manifest_path}</span>
              <small>
                {output.event_count} event, {output.background_count} background
              </small>
            </button>
          ))}
        </div>
      )}
    </section>
  );
}
