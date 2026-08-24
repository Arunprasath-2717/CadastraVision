/**
 * CadastralMap Domain Data Types & API Specifications (PRD-CM-04)
 */

/**
 * @typedef {'AI-generated' | 'existing-GIS' | 'human-edited'} FeatureSource
 */

/**
 * @typedef {'draft' | 'needs_review' | 'validated' | 'approved' | 'rejected' | 'conflict'} ValidationStatus
 */

/**
 * @typedef {'HIGH' | 'MEDIUM' | 'LOW'} ConfidenceBand
 */

/**
 * @typedef {'overlap' | 'gap' | 'self_intersection' | 'low_confidence' | 'boundary_discrepancy'} FlagType
 */

/**
 * @typedef {'high' | 'medium' | 'low'} FlagSeverity
 */

/**
 * @typedef {Object} ValidationFlag
 * @property {string} id
 * @property {string} parcel_id
 * @property {FlagType} flag_type
 * @property {FlagSeverity} severity
 * @property {string} description
 * @property {string|null} resolved_by
 * @property {string|null} resolved_at
 */

/**
 * @typedef {Object} Parcel
 * @property {string} id
 * @property {string} zone
 * @property {string} jurisdiction
 * @property {FeatureSource} source
 * @property {number} confidence_score - Range 0-1 (e.g., 0.62)
 * @property {ConfidenceBand} confidence_band
 * @property {ValidationStatus} validation_status
 * @property {string[]} linked_buildings
 * @property {ValidationFlag[]} flags
 * @property {Object} geometry - GeoJSON Polygon geometry
 * @property {number} area_sqm
 * @property {string} last_updated
 * @property {string|null} updated_by
 * @property {Object|null} gis_conflict - Details if AI geometry conflicts with GIS record
 */

/**
 * @typedef {Object} Building
 * @property {string} id
 * @property {string} parcel_id
 * @property {number} height_m
 * @property {number} confidence_score
 * @property {Object} geometry
 */

/**
 * @typedef {Object} ReviewQueueItem
 * @property {string} id
 * @property {string} parcel_id
 * @property {string} feature_type
 * @property {number} confidence_score
 * @property {ConfidenceBand} confidence_band
 * @property {string} issue
 * @property {FlagSeverity} severity
 * @property {ValidationStatus} status
 * @property {string} jurisdiction
 * @property {string} created_at
 */

/**
 * @typedef {Object} User
 * @property {string} id
 * @property {string} name
 * @property {string} email
 * @property {string} staff_id
 * @property {string} department
 * @property {string} role - e.g. 'Surveyor', 'GIS Administrator', 'Municipal Officer'
 * @property {string} jurisdiction
 */

/**
 * @typedef {'online' | 'offline' | 'pending_sync' | 'syncing' | 'sync_conflict'} OfflineState
 */

/**
 * @typedef {Object} OfflineStatus
 * @property {OfflineState} state
 * @property {number} pendingCount
 * @property {string|null} lastSyncedAt
 */
export {};
