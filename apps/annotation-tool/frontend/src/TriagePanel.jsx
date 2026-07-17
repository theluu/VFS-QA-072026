import { CheckCircle2, Film, Play, RefreshCw, RotateCw, Upload, Users, XCircle } from "lucide-react";
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

export default function TriagePanel({ apiBase }) {
  const [inputs, setInputs] = useState([]);
  const [inputDir, setInputDir] = useState("data/raw");
  const [rawVideos, setRawVideos] = useState([]);
  const [checked, setChecked] = useState(() => new Set());
  const [model, setModel] = useState("yolov4");
  const [intervalMs, setIntervalMs] = useState(2000);
  // 0.3, not 0.5: YOLOv4 scores distant CCTV figures at 0.35-0.69, so the
  // usual 0.5 silently drops them.
  const [minConfidence, setMinConfidence] = useState(0.3);
  const [minHits, setMinHits] = useState(2);
  const [state, setState] = useState({ status: "idle" });
  const [preview, setPreview] = useState(null);
  const [error, setError] = useState("");
  const [uploading, setUploading] = useState(false);
  const pollRef = useRef(null);
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
    let nearest = null;
    let bestGap = interval;
    for (const hit of hits) {
      const gap = Math.abs(hit.timestamp_ms - nowMs);
      if (gap <= bestGap) {
        bestGap = gap;
        nearest = hit;
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
            <option value="yolov4">YOLOv4 (608px) - chinh xac</option>
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
        {model === "yolov4" ? (
          <>
            <strong>YOLOv4</strong> - input 608x608, bat duoc nguoi o xa tren footage CCTV.
            ~0.8s/frame. License darknet: public domain.
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
        </div>
      )}
    </section>
  );
}
