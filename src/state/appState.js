// Centralized Application State

export const state = {
    project: {
        version: "1.0",
        name: "Untitled Project",
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString()
    },
    features: {
        buildings: [],
        roads: [],
        fields: []
    },
    selectedFeature: null,
    editingFeature: null,
    originalGeometry: null,
    layersVisibility: {
        buildings: true,
        roads: true,
        fields: true
    }
};
