import { BASE_URL, USE_MOCK } from './apiClient';

const MOCK_JOB_SEQUENCE = ['queued', 'processing_ai', 'processing_gis', 'validating', 'completed'];
const MOCK_JOB_STATE = new Map();

function getAuthHeaders(extraHeaders = {}) {
  const token = localStorage.getItem('cadastral_jwt');
  return {
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...extraHeaders,
  };
}

export function validateImageryFile(file) {
  if (!file) {
    return { ok: false, message: 'Please select a ZIP file to continue.' };
  }

  if (file.size <= 0) {
    return { ok: false, message: 'The selected file is empty.' };
  }

  if (file.size > 250 * 1024 * 1024) {
    return { ok: false, message: 'Imagery ZIP files must be under 250 MB.' };
  }

  const name = file.name.toLowerCase();
  if (!name.endsWith('.zip')) {
    return { ok: false, message: 'Please upload a ZIP archive containing drone imagery or orthophoto tiles.' };
  }

  return { ok: true };
}

function buildMockJob(file) {
  const jobId = `mock-imagery-${Date.now()}`;
  MOCK_JOB_STATE.set(jobId, {
    index: 0,
    fileName: file.name,
    fileSize: file.size,
    status: 'queued',
    metadata: {
      imageryReceived: true,
      layersGenerated: 0,
      validationFlagsDetected: 0,
      processingCompletedAt: null,
    },
  });

  return {
    jobId,
    status: 'queued',
    fileName: file.name,
    fileSize: file.size,
    mock: true,
    metadata: {
      imageryReceived: true,
      layersGenerated: 0,
      validationFlagsDetected: 0,
    },
  };
}

async function requestJson(endpoint, options = {}) {
  const response = await fetch(`${BASE_URL}${endpoint}`, {
    ...options,
    headers: {
      Accept: 'application/json',
      ...getAuthHeaders(),
      ...options.headers,
    },
  });

  if (!response.ok) {
    throw new Error(`Request failed (${response.status}) for ${endpoint}`);
  }

  return response.json().catch(() => ({}));
}

export const imageryApi = {
  async uploadImagery(file) {
    const validation = validateImageryFile(file);
    if (!validation.ok) {
      throw new Error(validation.message);
    }

    if (USE_MOCK) {
      return buildMockJob(file);
    }

    try {
      const formData = new FormData();
      formData.append('file', file);

      const response = await fetch(`${BASE_URL}/v1/imagery/upload`, {
        method: 'POST',
        headers: getAuthHeaders(),
        body: formData,
      });

      if (!response.ok) {
        throw new Error('Imagery upload endpoint is not available yet.');
      }

      return await response.json();
    } catch (error) {
      console.warn('[imageryApi] Real upload endpoint unavailable. Using mock fallback for UI flow demonstration.', error);
      return buildMockJob(file);
    }
  },

  async getProcessingStatus(jobId) {
    if (!jobId) {
      throw new Error('Missing job identifier.');
    }

    if (USE_MOCK || MOCK_JOB_STATE.has(jobId)) {
      const current = MOCK_JOB_STATE.get(jobId) || {
        status: 'queued',
        index: 0,
        metadata: {
          imageryReceived: true,
          layersGenerated: 0,
          validationFlagsDetected: 0,
        },
      };

      const nextIndex = Math.min(current.index + 1, MOCK_JOB_SEQUENCE.length - 1);
      const status = MOCK_JOB_SEQUENCE[current.index] || 'queued';
      const nextStatus = current.status === 'completed' ? 'completed' : status;

      const updated = {
        ...current,
        status: nextStatus,
        index: nextStatus === 'completed' ? MOCK_JOB_SEQUENCE.length - 1 : current.index,
        metadata: {
          ...current.metadata,
          layersGenerated: nextStatus === 'completed' ? 12 : current.metadata.layersGenerated,
          validationFlagsDetected: nextStatus === 'completed' ? 4 : current.metadata.validationFlagsDetected,
        },
      };

      if (nextStatus !== 'completed' && nextStatus !== 'failed') {
        updated.index = nextIndex;
        updated.status = MOCK_JOB_SEQUENCE[nextIndex];
        updated.metadata.layersGenerated = updated.metadata.layersGenerated || 3;
      }

      MOCK_JOB_STATE.set(jobId, updated);

      return {
        jobId,
        status: updated.status,
        mock: true,
        metadata: updated.metadata,
      };
    }

    const endpoints = [
      `/v1/imagery/jobs/${jobId}/status`,
      `/v1/imagery/jobs/${jobId}`,
    ];

    let lastError = null;
    for (const endpoint of endpoints) {
      try {
        const data = await requestJson(endpoint, { method: 'GET' });
        if (data && data.status) {
          return data;
        }
      } catch (error) {
        lastError = error;
      }
    }

    throw lastError || new Error('Unable to fetch job status.');
  },
};

export function mapStatusToProgress(status) {
  const progressMap = {
    queued: 8,
    uploading: 20,
    processing_ai: 45,
    processing_gis: 68,
    validating: 82,
    completed: 100,
    failed: 100,
  };

  return progressMap[status] ?? 8;
}
