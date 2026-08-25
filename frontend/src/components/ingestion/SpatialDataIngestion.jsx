import React, { useCallback, useEffect, useRef, useState } from 'react';
import {
  AlertCircle,
  ArrowRight,
  Check,
  CheckCircle2,
  FileArchive,
  FileImage,
  FolderOpen,
  Loader2,
  Sparkles,
  Trash2,
  UploadCloud,
  X,
} from 'lucide-react';
import { imageryApi, mapStatusToProgress, validateImageryFile } from '../../services/imageryApi';

const PIPELINE_STEPS = [
  'DRONE DATA',
  'AI EXTRACTION',
  'GIS PROCESSING',
  'VALIDATION',
  'SURVEYOR REVIEW',
];

const STATUS_ORDER = ['queued', 'uploading', 'processing_ai', 'processing_gis', 'validating', 'completed'];

const formatFileSize = (size) => {
  if (!size) return '0 KB';
  const units = ['B', 'KB', 'MB', 'GB'];
  const power = Math.min(Math.floor(Math.log(size) / Math.log(1024)), units.length - 1);
  const value = size / 1024 ** power;
  return `${value.toFixed(value >= 10 || power === 0 ? 0 : 1)} ${units[power]}`;
};

const getStatusLabel = (status) => {
  switch (status) {
    case 'queued':
      return 'Queued';
    case 'uploading':
      return 'Uploading';
    case 'processing_ai':
      return 'AI Analysis';
    case 'processing_gis':
      return 'GIS Processing';
    case 'validating':
      return 'Validation';
    case 'completed':
      return 'Completed';
    case 'failed':
      return 'Failed';
    default:
      return 'Idle';
  }
};

export function SpatialDataIngestion() {
  const fileInputRef = useRef(null);
  const pollRef = useRef(null);

  const [selectedFile, setSelectedFile] = useState(null);
  const [status, setStatus] = useState('idle');
  const [jobId, setJobId] = useState(null);
  const [jobStatus, setJobStatus] = useState('queued');
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState('');
  const [isDragging, setIsDragging] = useState(false);
  const [processingSummary, setProcessingSummary] = useState(null);
  const [isMockMode, setIsMockMode] = useState(false);

  const clearPolling = useCallback(() => {
    if (pollRef.current) {
      clearTimeout(pollRef.current);
      pollRef.current = null;
    }
  }, []);

  const resetWorkflow = useCallback(() => {
    clearPolling();
    setSelectedFile(null);
    setStatus('idle');
    setJobId(null);
    setJobStatus('queued');
    setProgress(0);
    setError('');
    setProcessingSummary(null);
    setIsMockMode(false);
  }, [clearPolling]);

  const handleFileSelection = useCallback((file) => {
    const validation = validateImageryFile(file);
    if (!validation.ok) {
      setStatus('error');
      setError(validation.message);
      return;
    }

    setSelectedFile(file);
    setStatus('selected');
    setError('');
    setProcessingSummary(null);
  }, []);

  const handleBrowseClick = () => {
    fileInputRef.current?.click();
  };

  const handleInputChange = (event) => {
    const file = event.target.files?.[0];
    if (file) {
      handleFileSelection(file);
    }
    event.target.value = '';
  };

  const handleDrop = (event) => {
    event.preventDefault();
    setIsDragging(false);
    const file = event.dataTransfer.files?.[0];
    if (file) {
      handleFileSelection(file);
    }
  };

  const pollJobStatus = useCallback(async (currentJobId) => {
    if (!currentJobId) return;

    try {
      const result = await imageryApi.getProcessingStatus(currentJobId);
      const currentStatus = result.status || 'queued';
      setJobStatus(currentStatus);
      setProgress(mapStatusToProgress(currentStatus));
      setIsMockMode(Boolean(result.mock));

      if (currentStatus === 'completed') {
        setStatus('completed');
        setProcessingSummary({
          imageryReceived: true,
          processingCompleted: true,
          layersGenerated: result.metadata?.layersGenerated ?? 12,
          validationFlagsDetected: result.metadata?.validationFlagsDetected ?? 4,
          fileName: selectedFile?.name || 'imagery.zip',
        });
        window.dispatchEvent(new CustomEvent('cadastra:refresh-map-layers'));
        return;
      }

      if (currentStatus === 'failed') {
        setStatus('error');
        setError('Unable to process imagery. Please retry with a valid ZIP archive.');
        return;
      }

      setStatus('processing');
      pollRef.current = setTimeout(() => pollJobStatus(currentJobId), 1600);
    } catch (error) {
      setStatus('error');
      setError(error.message || 'Unable to process imagery.');
    }
  }, [selectedFile?.name]);

  useEffect(() => {
    return () => clearPolling();
  }, [clearPolling]);

  useEffect(() => {
    if (!jobId || status !== 'processing') {
      return;
    }

    pollJobStatus(jobId);

    return () => clearPolling();
  }, [jobId, pollJobStatus, status, clearPolling]);

  const handleStartAnalysis = async () => {
    if (!selectedFile) return;

    setError('');
    setStatus('uploading');
    setProgress(15);

    try {
      const result = await imageryApi.uploadImagery(selectedFile);
      setJobId(result.jobId);
      setJobStatus(result.status || 'queued');
      setIsMockMode(Boolean(result.mock));
      setStatus('processing');
      setProgress(mapStatusToProgress(result.status || 'queued'));
    } catch (error) {
      setStatus('error');
      setError(error.message || 'Unable to process imagery.');
    }
  };

  const activeStageIndex = (() => {
    if (status === 'completed') return PIPELINE_STEPS.length - 1;
    if (status === 'error') return -1;
    if (status === 'selected' || status === 'uploading') return 0;
    if (status === 'processing') {
      switch (jobStatus) {
        case 'processing_ai':
          return 1;
        case 'processing_gis':
          return 2;
        case 'validating':
          return 3;
        default:
          return 0;
      }
    }
    return 0;
  })();

  const renderPipeline = () => (
    <div className="mt-4">
      <div className="mb-2 flex items-center justify-between text-[10px] font-mono uppercase tracking-[0.2em] text-[#4F7285]">
        <span>Pipeline</span>
        {isMockMode && <span className="rounded-full border border-[#A7EBF2] bg-[#EAF8FB] px-1.5 py-0.5 text-[9px] text-[#266580]">demo mode</span>}
      </div>
      <div className="grid grid-cols-5 gap-1.5">
        {PIPELINE_STEPS.map((step, index) => {
          const isComplete = index < activeStageIndex || status === 'completed';
          const isActive = index === activeStageIndex;
          return (
            <div
              key={step}
              className={`rounded-xl border px-1.5 py-2 text-center transition-all duration-300 ${
                isComplete
                  ? 'border-[#A7EBF2] bg-[linear-gradient(135deg,rgba(167,235,242,0.22),rgba(84,172,191,0.08))] text-[#023859]'
                  : isActive
                    ? 'border-[#54ACBF] bg-[linear-gradient(135deg,rgba(84,172,191,0.18),rgba(167,235,242,0.10))] text-[#023859] shadow-[0_8px_20px_rgba(2,56,89,0.1)]'
                    : 'border-[#D9EDF5] bg-white/60 text-[#6F8DA0]'
              }`}
            >
              <div className="flex items-center justify-center gap-1 text-[9px] font-semibold">
                {isComplete ? <Check className="h-3 w-3" /> : isActive ? <Sparkles className="h-3 w-3" /> : <span className="h-2 w-2 rounded-full bg-current/70" />}
                <span>{index + 1}</span>
              </div>
              <div className="mt-1 text-[8px] font-medium tracking-[0.14em]">{step}</div>
            </div>
          );
        })}
      </div>
    </div>
  );

  const renderContent = () => {
    if (status === 'idle') {
      return (
        <div>
          <div
            onDragOver={(event) => {
              event.preventDefault();
              setIsDragging(true);
            }}
            onDragLeave={() => setIsDragging(false)}
            onDrop={handleDrop}
            className={`relative rounded-2xl border border-dashed p-4 text-center transition-all duration-300 ${
              isDragging
                ? 'border-[#54ACBF] bg-[radial-gradient(circle_at_center,rgba(167,235,242,0.26),rgba(255,255,255,0.1))] shadow-[0_0_0_1px_rgba(84,172,191,0.35),0_14px_30px_rgba(2,56,89,0.08)]'
                : 'border-[#C9E5EE] bg-[linear-gradient(135deg,rgba(247,252,254,0.9),rgba(232,246,252,0.88))]'
            }`}
          >
            <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-2xl bg-[linear-gradient(135deg,rgba(167,235,242,0.35),rgba(84,172,191,0.15))] text-[#266580] shadow-[0_10px_22px_rgba(2,56,89,0.08)]">
              <UploadCloud className="h-6 w-6" />
            </div>
            <p className="mt-3 text-sm font-semibold text-[#011C40]">Drop your imagery ZIP here</p>
            <p className="mt-1 text-xs text-[#4F7285]">or browse from your computer</p>
            <p className="mt-3 text-[10px] font-mono uppercase tracking-[0.18em] text-[#6F8DA0]">ZIP files • Drone imagery / Orthophotos</p>
            <button
              type="button"
              onClick={handleBrowseClick}
              className="mt-4 inline-flex items-center justify-center rounded-xl border border-[#54ACBF] bg-[linear-gradient(135deg,#023859,#266580)] px-3.5 py-2 text-xs font-semibold text-white shadow-[0_12px_24px_rgba(2,56,89,0.18)] transition-all duration-200 hover:-translate-y-0.5 hover:shadow-[0_16px_30px_rgba(2,56,89,0.2)]"
            >
              Browse Files
            </button>
          </div>
        </div>
      );
    }

    if (status === 'selected') {
      return (
        <div className="space-y-3">
          <div className="rounded-2xl border border-[#A7EBF2] bg-[linear-gradient(135deg,rgba(167,235,242,0.18),rgba(255,255,255,0.82))] p-3 shadow-[0_12px_24px_rgba(2,56,89,0.06)]">
            <div className="flex items-center justify-between gap-2">
              <div className="flex items-center gap-3">
                <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-[linear-gradient(135deg,#023859,#266580)] text-white shadow-[0_10px_20px_rgba(2,56,89,0.2)]">
                  <FileArchive className="h-5 w-5" />
                </div>
                <div className="min-w-0">
                  <div className="truncate text-xs font-semibold text-[#011C40]">{selectedFile.name}</div>
                  <div className="text-[10px] font-mono uppercase tracking-[0.18em] text-[#4F7285]">{formatFileSize(selectedFile.size)}</div>
                </div>
              </div>
              <button
                type="button"
                onClick={resetWorkflow}
                className="rounded-lg border border-[#C9E5EE] bg-white/80 p-1.5 text-[#4F7285] transition-colors hover:text-[#023859]"
                title="Remove file"
              >
                <Trash2 className="h-4 w-4" />
              </button>
            </div>
          </div>

          <button
            type="button"
            onClick={handleStartAnalysis}
            className="inline-flex w-full items-center justify-center gap-2 rounded-xl border border-[#54ACBF] bg-[linear-gradient(135deg,#011C40,#023859)] px-4 py-2.5 text-xs font-semibold uppercase tracking-[0.18em] text-white shadow-[0_12px_24px_rgba(1,28,64,0.18)] transition-all duration-200 hover:-translate-y-0.5 hover:shadow-[0_16px_30px_rgba(2,56,89,0.22)]"
          >
            <FolderOpen className="h-4 w-4" />
            Start Spatial Analysis
          </button>
        </div>
      );
    }

    if (status === 'uploading') {
      return (
        <div className="space-y-3">
          <div className="flex items-center justify-between rounded-2xl border border-[#A7EBF2] bg-[linear-gradient(135deg,rgba(167,235,242,0.22),rgba(255,255,255,0.84))] p-3">
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-[linear-gradient(135deg,#023859,#54ACBF)] text-white">
                <Loader2 className="h-5 w-5 animate-spin" />
              </div>
              <div>
                <div className="text-sm font-semibold text-[#011C40]">Uploading imagery...</div>
                <div className="text-[10px] font-mono uppercase tracking-[0.18em] text-[#4F7285]">{selectedFile?.name}</div>
              </div>
            </div>
          </div>
          <div>
            <div className="mb-1 flex items-center justify-between text-[10px] uppercase tracking-[0.18em] text-[#4F7285] font-mono">
              <span>Upload progress</span>
              <span>{progress}%</span>
            </div>
            <div className="h-2.5 overflow-hidden rounded-full bg-[#DFF4F8]">
              <div className="h-full rounded-full bg-[linear-gradient(90deg,#54ACBF,#266580,#023859)] transition-all duration-300" style={{ width: `${progress}%` }} />
            </div>
          </div>
        </div>
      );
    }

    if (status === 'processing') {
      return (
        <div className="space-y-3">
          <div className="rounded-2xl border border-[#A7EBF2] bg-[linear-gradient(135deg,rgba(167,235,242,0.18),rgba(255,255,255,0.82))] p-3">
            <div className="flex items-center justify-between gap-2">
              <div className="flex items-center gap-3">
                <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-[linear-gradient(135deg,#023859,#54ACBF)] text-white">
                  <Sparkles className="h-4 w-4 animate-pulse" />
                </div>
                <div>
                  <div className="text-sm font-semibold text-[#011C40]">Processing spatial analysis</div>
                  <div className="text-[10px] font-mono uppercase tracking-[0.18em] text-[#4F7285]">{getStatusLabel(jobStatus)}</div>
                </div>
              </div>
            </div>
          </div>

          {renderPipeline()}

          <div>
            <div className="mb-1 flex items-center justify-between text-[10px] uppercase tracking-[0.18em] text-[#4F7285] font-mono">
              <span>Pipeline progress</span>
              <span>{progress}%</span>
            </div>
            <div className="h-2.5 overflow-hidden rounded-full bg-[#DFF4F8]">
              <div className="h-full rounded-full bg-[linear-gradient(90deg,#A7EBF2,#54ACBF,#266580)] transition-all duration-300" style={{ width: `${progress}%` }} />
            </div>
          </div>
        </div>
      );
    }

    if (status === 'completed') {
      return (
        <div className="space-y-3">
          <div className="rounded-2xl border border-[#A7EBF2] bg-[linear-gradient(135deg,rgba(167,235,242,0.20),rgba(255,255,255,0.82))] p-3 shadow-[0_12px_24px_rgba(2,56,89,0.06)]">
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-[linear-gradient(135deg,#023859,#54ACBF)] text-white shadow-[0_10px_20px_rgba(2,56,89,0.2)]">
                <CheckCircle2 className="h-5 w-5" />
              </div>
              <div>
                <div className="text-sm font-semibold text-[#011C40]">Spatial analysis ready</div>
                <div className="text-[10px] font-mono uppercase tracking-[0.18em] text-[#4F7285]">{getStatusLabel(jobStatus)}</div>
              </div>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-2 text-[10px] text-[#4F7285]">
            <div className="rounded-xl border border-[#C9E5EE] bg-white/80 p-2">
              <div className="font-mono uppercase tracking-[0.18em] text-[#6F8DA0]">Imagery</div>
              <div className="mt-1 font-semibold text-[#011C40]">Received</div>
            </div>
            <div className="rounded-xl border border-[#C9E5EE] bg-white/80 p-2">
              <div className="font-mono uppercase tracking-[0.18em] text-[#6F8DA0]">Processing</div>
              <div className="mt-1 font-semibold text-[#011C40]">Completed</div>
            </div>
            <div className="rounded-xl border border-[#C9E5EE] bg-white/80 p-2">
              <div className="font-mono uppercase tracking-[0.18em] text-[#6F8DA0]">Layers</div>
              <div className="mt-1 font-semibold text-[#011C40]">{processingSummary?.layersGenerated ?? 12}</div>
            </div>
            <div className="rounded-xl border border-[#C9E5EE] bg-white/80 p-2">
              <div className="font-mono uppercase tracking-[0.18em] text-[#6F8DA0]">Flags</div>
              <div className="mt-1 font-semibold text-[#011C40]">{processingSummary?.validationFlagsDetected ?? 4}</div>
            </div>
          </div>

          <button
            type="button"
            onClick={() => document.getElementById('gis-map-panel')?.scrollIntoView({ behavior: 'smooth', block: 'center' })}
            className="inline-flex w-full items-center justify-center gap-2 rounded-xl border border-[#54ACBF] bg-[linear-gradient(135deg,#011C40,#023859)] px-4 py-2.5 text-xs font-semibold uppercase tracking-[0.18em] text-white transition-all duration-200 hover:-translate-y-0.5"
          >
            View Results
            <ArrowRight className="h-4 w-4" />
          </button>
        </div>
      );
    }

    if (status === 'error') {
      return (
        <div className="space-y-3 rounded-2xl border border-rose-200 bg-[linear-gradient(135deg,rgba(255,255,255,0.95),rgba(254,242,242,0.9))] p-3 text-left shadow-[0_12px_24px_rgba(1,28,64,0.06)]">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-rose-100 text-rose-700">
              <AlertCircle className="h-5 w-5" />
            </div>
            <div>
              <div className="text-sm font-semibold text-[#011C40]">Unable to process imagery</div>
              <div className="text-[10px] font-mono uppercase tracking-[0.18em] text-[#4F7285]">Validation failed</div>
            </div>
          </div>
          <p className="text-xs text-[#4F7285]">{error || 'The ZIP archive could not be processed. Please review the file and try again.'}</p>
          <button
            type="button"
            onClick={() => {
              setStatus('selected');
              setError('');
            }}
            className="inline-flex items-center justify-center rounded-xl border border-rose-200 bg-rose-50 px-3 py-2 text-xs font-semibold text-rose-700 transition-all duration-200 hover:bg-rose-100"
          >
            Try Again
          </button>
        </div>
      );
    }

    return null;
  };

  return (
    <div className="cv-panel-elevated rounded-2xl p-4 text-pastel-text transition-all duration-200 hover:-translate-y-0.5 hover:shadow-[0_16px_38px_rgba(1,28,64,0.12)]">
      <div className="mb-3 flex items-center gap-2 border-b border-[#C9E5EE] pb-2.5">
        <div className="rounded-lg bg-[linear-gradient(135deg,rgba(167,235,242,0.25),rgba(84,172,191,0.12))] p-2 text-[#266580]">
          <FileImage className="h-4 w-4" />
        </div>
        <div>
          <h3 className="text-[11px] font-bold uppercase tracking-[0.2em] text-[#011C40]">SPATIAL DATA INGESTION</h3>
          <p className="text-[10px] text-[#4F7285]">Upload drone imagery to begin spatial analysis</p>
        </div>
      </div>

      <input
        ref={fileInputRef}
        type="file"
        accept=".zip,application/zip"
        className="hidden"
        onChange={handleInputChange}
      />

      {renderContent()}

      {status !== 'idle' && status !== 'error' && <div className="mt-4 border-t border-[#C9E5EE] pt-3">{renderPipeline()}</div>}
    </div>
  );
}
