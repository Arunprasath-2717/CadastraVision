import React, { useState } from 'react';
import { useMapSelection } from '../../context/MapContext';
import { Edit3, Save, X, Plus, Trash2, Split, GitMerge, Loader2, CheckCircle2 } from 'lucide-react';

export function BoundaryEditor() {
  const {
    selectedParcel,
    isEditing,
    cancelEditing,
    editedGeometry,
    setEditedGeometry,
    saveEditedGeometry,
    revalidationState
  } = useMapSelection();

  const [activeTab, setActiveTab] = useState('vertices');
  const [splitRatio, setSplitRatio] = useState(50);
  const [mergeAdjacentId, setMergeAdjacentId] = useState('P-1025');

  if (!isEditing || !selectedParcel || !editedGeometry) return null;

  const vertices = editedGeometry.coordinates[0];

  const handleVertexChange = (index, coordIdx, newValue) => {
    const val = parseFloat(newValue);
    if (isNaN(val)) return;

    const newCoords = JSON.parse(JSON.stringify(vertices));
    newCoords[index][coordIdx] = val;
    
    if (index === 0) {
      newCoords[newCoords.length - 1][coordIdx] = val;
    } else if (index === newCoords.length - 1) {
      newCoords[0][coordIdx] = val;
    }

    setEditedGeometry({
      ...editedGeometry,
      coordinates: [newCoords]
    });
  };

  const handleAddVertex = (index) => {
    const newCoords = JSON.parse(JSON.stringify(vertices));
    const v1 = newCoords[index];
    const v2 = newCoords[(index + 1) % (newCoords.length - 1)];
    const midPoint = [(v1[0] + v2[0]) / 2, (v1[1] + v2[1]) / 2];

    newCoords.splice(index + 1, 0, midPoint);
    setEditedGeometry({
      ...editedGeometry,
      coordinates: [newCoords]
    });
  };

  const handleDeleteVertex = (index) => {
    if (vertices.length <= 4) {
      alert('A polygon boundary requires at least 3 vertices plus closure.');
      return;
    }
    const newCoords = JSON.parse(JSON.stringify(vertices));
    newCoords.splice(index, 1);
    newCoords[newCoords.length - 1] = [...newCoords[0]];

    setEditedGeometry({
      ...editedGeometry,
      coordinates: [newCoords]
    });
  };

  return (
    <div className="fixed top-20 left-1/2 -translate-x-1/2 z-40 w-full max-w-xl bg-white p-6 rounded-3xl border border-pastel-border shadow-pastel-lg text-pastel-text animate-fade-in">
      
      {/* Editor Header */}
      <div className="flex items-center justify-between border-b border-pastel-border pb-3 mb-4">
        <div className="flex items-center space-x-2 text-pastel-action">
          <Edit3 className="w-5 h-5 animate-pulse" />
          <h3 className="font-bold text-sm font-mono text-pastel-text">
            Boundary Editing Mode: Parcel {selectedParcel.id}
          </h3>
        </div>
        <button
          onClick={cancelEditing}
          className="text-pastel-subtle hover:text-pastel-text p-1 rounded-xl hover:bg-pastel-surface-soft"
        >
          <X className="w-5 h-5" />
        </button>
      </div>

      {/* Editor Mode Tabs */}
      <div className="flex border-b border-pastel-border mb-4 text-xs font-medium">
        <button
          onClick={() => setActiveTab('vertices')}
          className={`pb-2.5 px-3 border-b-2 transition-colors flex items-center space-x-1.5 ${
            activeTab === 'vertices' ? 'border-pastel-action text-pastel-action font-bold' : 'border-transparent text-pastel-muted hover:text-pastel-text'
          }`}
        >
          <Edit3 className="w-3.5 h-3.5" />
          <span>Vertex Dragging ({vertices.length - 1})</span>
        </button>

        <button
          onClick={() => setActiveTab('split')}
          className={`pb-2.5 px-3 border-b-2 transition-colors flex items-center space-x-1.5 ${
            activeTab === 'split' ? 'border-pastel-action text-pastel-action font-bold' : 'border-transparent text-pastel-muted hover:text-pastel-text'
          }`}
        >
          <Split className="w-3.5 h-3.5" />
          <span>Split Parcel</span>
        </button>

        <button
          onClick={() => setActiveTab('merge')}
          className={`pb-2.5 px-3 border-b-2 transition-colors flex items-center space-x-1.5 ${
            activeTab === 'merge' ? 'border-pastel-action text-pastel-action font-bold' : 'border-transparent text-pastel-muted hover:text-pastel-text'
          }`}
        >
          <GitMerge className="w-3.5 h-3.5" />
          <span>Merge Adjacent</span>
        </button>
      </div>

      {/* Revalidation Overlay */}
      {revalidationState.isRevalidating && (
        <div className="p-4 bg-pastel-lavender border border-pastel-border rounded-2xl mb-4 text-center text-xs space-y-2 animate-pulse">
          <Loader2 className="w-6 h-6 animate-spin text-pastel-action mx-auto" />
          <p className="font-semibold text-pastel-action">Server Topology Re-Validation in Progress...</p>
          <p className="text-pastel-muted text-[11px]">Executing Shapely overlap, gap, and self-intersection calculations.</p>
        </div>
      )}

      {revalidationState.result && (
        <div className="p-3.5 bg-pastel-mint/30 border border-emerald-200 rounded-2xl mb-4 text-xs flex items-center space-x-2 text-pastel-mint-text font-medium">
          <CheckCircle2 className="w-5 h-5 text-emerald-700 shrink-0" />
          <span>{revalidationState.result.message}</span>
        </div>
      )}

      {/* Tab 1: Vertex Coordinates Editor */}
      {activeTab === 'vertices' && (
        <div className="space-y-3 max-h-48 overflow-y-auto pr-1">
          <div className="grid grid-cols-12 gap-2 text-[10px] font-mono uppercase text-pastel-muted border-b border-pastel-border pb-1">
            <span className="col-span-2">Vertex</span>
            <span className="col-span-4">Longitude (°E)</span>
            <span className="col-span-4">Latitude (°N)</span>
            <span className="col-span-2 text-right">Actions</span>
          </div>

          {vertices.slice(0, -1).map((coord, idx) => (
            <div key={idx} className="grid grid-cols-12 gap-2 items-center text-xs font-mono">
              <span className="col-span-2 font-semibold text-pastel-action">V-{idx + 1}</span>
              <input
                type="number"
                step="0.0001"
                value={coord[0]}
                onChange={(e) => handleVertexChange(idx, 0, e.target.value)}
                className="col-span-4 px-2 py-1 bg-pastel-surface-soft border border-pastel-border rounded-lg text-pastel-text"
              />
              <input
                type="number"
                step="0.0001"
                value={coord[1]}
                onChange={(e) => handleVertexChange(idx, 1, e.target.value)}
                className="col-span-4 px-2 py-1 bg-pastel-surface-soft border border-pastel-border rounded-lg text-pastel-text"
              />
              <div className="col-span-2 flex items-center justify-end space-x-1">
                <button
                  onClick={() => handleAddVertex(idx)}
                  className="p-1 text-pastel-muted hover:text-emerald-700 hover:bg-emerald-50 rounded"
                  title="Add Vertex After"
                >
                  <Plus className="w-3.5 h-3.5" />
                </button>
                <button
                  onClick={() => handleDeleteVertex(idx)}
                  className="p-1 text-pastel-muted hover:text-rose-700 hover:bg-rose-50 rounded"
                  title="Delete Vertex"
                >
                  <Trash2 className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Tab 2: Split Parcel UI */}
      {activeTab === 'split' && (
        <div className="space-y-3 text-xs">
          <p className="text-pastel-muted">Split parcel boundary into two sub-parcels along specified bisector ratio:</p>
          <div className="space-y-1">
            <div className="flex justify-between text-pastel-muted">
              <span>Bisector Ratio:</span>
              <span className="font-mono text-pastel-action font-bold">{splitRatio}% / {100 - splitRatio}%</span>
            </div>
            <input
              type="range"
              min="10"
              max="90"
              value={splitRatio}
              onChange={(e) => setSplitRatio(e.target.value)}
              className="w-full"
            />
          </div>
        </div>
      )}

      {/* Tab 3: Merge Parcel UI */}
      {activeTab === 'merge' && (
        <div className="space-y-3 text-xs">
          <p className="text-pastel-muted">Merge boundary with adjacent parcel geometry:</p>
          <div>
            <label className="block text-pastel-muted mb-1">Target Adjacent Parcel ID:</label>
            <select
              value={mergeAdjacentId}
              onChange={(e) => setMergeAdjacentId(e.target.value)}
              className="w-full px-3.5 py-2 bg-pastel-surface-soft border border-pastel-border rounded-xl text-pastel-text font-mono"
            >
              <option value="P-1025">P-1025 (Adjacent East)</option>
              <option value="P-1027">P-1027 (Adjacent North)</option>
            </select>
          </div>
        </div>
      )}

      {/* Action Footer Bar */}
      <div className="mt-5 pt-3 border-t border-pastel-border flex items-center justify-between">
        <button
          onClick={cancelEditing}
          disabled={revalidationState.isRevalidating}
          className="px-4 py-2 bg-pastel-surface-soft hover:bg-slate-200/60 text-pastel-muted rounded-xl text-xs font-medium"
        >
          Cancel
        </button>

        <button
          onClick={() => saveEditedGeometry()}
          disabled={revalidationState.isRevalidating}
          className="px-5 py-2 bg-pastel-action hover:bg-pastel-action-hover disabled:bg-slate-300 text-white rounded-xl text-xs font-semibold shadow-pastel-md transition-all flex items-center space-x-1.5"
        >
          <Save className="w-4 h-4" />
          <span>Save Changes & Re-Validate</span>
        </button>
      </div>

    </div>
  );
}
