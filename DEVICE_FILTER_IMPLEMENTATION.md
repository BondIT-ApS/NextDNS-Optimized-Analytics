# Device Filter Implementation

## Overview
This document outlines the implementation of the Device Filter component for the NextDNS Optimized Analytics application, addressing Issue #69. The device filter allows users to filter DNS logs by specific devices associated with their selected NextDNS profile.

## Features Implemented

### 1. DeviceFilter Component (`/frontend/src/components/DeviceFilter.tsx`)
A React component that provides:
- **Multi-device selection**: Users can select multiple devices to filter logs
- **Search functionality**: Real-time search within available devices
- **Collapsible interface**: Expandable/collapsible design to save screen space
- **Visual feedback**: Shows selected device count and selected devices as badges
- **Select All/Clear All**: Bulk selection controls
- **Profile-aware**: Only shows devices available for the selected profile

### 2. Backend API Enhancements

#### New Device Endpoint (`GET /devices`)
- **URL**: `/devices?profile=<profile_id>&time_range=<range>`
- **Purpose**: Returns device statistics for a specific profile and time range
- **Response**: List of devices with usage statistics including:
  - Device name
  - Total queries count
  - Blocked/allowed query counts
  - Percentages
  - Last activity timestamp

#### Enhanced Logs Endpoint (`GET /logs`)
- **New Parameter**: `devices` (array of device names)
- **Function**: Filters DNS logs to only show entries from specified devices
- **Implementation**: Uses JSON field extraction to match device names in log records

#### Custom React Hook (`/frontend/src/hooks/useDevices.ts`)
- **`useDevices`**: Fetches device statistics for profile and time range
- **`useDeviceNames`**: Simplified hook that returns just device names for filtering
- **React Query integration**: Caching and error handling

### 3. Frontend Integration

#### Updated Logs Page (`/frontend/src/pages/Logs.tsx`)
- **Device state management**: Added `selectedDevices` state
- **Query parameter integration**: Passes device filter to API calls
- **Profile change handling**: Resets device selection when profile changes
- **Layout update**: Positioned DeviceFilter between ProfileSelector and FilterPanel

#### API Service Updates (`/frontend/src/services/api.ts`)
- **Device endpoint support**: Added `getDevices()` method
- **Enhanced logs filtering**: Updated `getLogs()` to support device parameter array

## Technical Implementation Details

### Device Data Structure
```typescript
interface DeviceUsageItem {
  device_name: string
  total_queries: number
  blocked_queries: number
  allowed_queries: number
  blocked_percentage: number
  allowed_percentage: number
  last_activity: string
}
```

### Component Props
```typescript
interface DeviceFilterProps {
  selectedProfile?: string
  selectedDevices: string[]
  onDeviceSelectionChange: (devices: string[]) => void
  timeRange?: string
}
```

### Database Integration
The backend uses SQLAlchemy to filter devices in the PostgreSQL database:
- Device filtering uses JSON field extraction: `cast(device ->> 'name', String)`
- Supports multiple device names via SQL `IN` clause
- Maintains performance through proper indexing

## User Interface Design

### Visual Elements
- **Card-based layout**: Consistent with existing filter components
- **Smartphone icon**: Clear visual identifier for device functionality
- **Badge indicators**: Shows count of selected devices
- **Expandable design**: Collapsed by default to conserve screen space
- **Search with magnifying glass icon**: Intuitive search interface
- **Checkbox-style selection**: Clear selection state indicators

### User Experience Flow
1. User selects a NextDNS profile
2. DeviceFilter loads available devices for that profile
3. User can expand the filter to see device list
4. User searches and selects specific devices
5. Selected devices appear as removable badges
6. DNS logs automatically filter to show only selected devices
7. Profile change resets device selection

## API Usage Examples

### Get devices for a profile:
```bash
GET /devices?profile=68416b&time_range=24h
```

### Filter logs by devices:
```bash
GET /logs?profile=68416b&devices=iPhone&devices=MacBook&limit=100
```

## Performance Considerations

### Frontend Optimizations
- **React.memo**: DeviceFilter component is memoized to prevent unnecessary re-renders
- **useMemo**: Device filtering and search results are memoized
- **useCallback**: Event handlers are memoized to prevent child re-renders
- **React Query**: Device data is cached with appropriate stale times

### Backend Optimizations
- **Database indexing**: JSON field extraction is optimized for device queries
- **Bulk device filtering**: Single query handles multiple device names
- **Time range filtering**: Limits dataset size for device statistics

## Error Handling
- **Network errors**: Graceful degradation with error messages
- **Empty states**: Clear messaging when no devices found
- **Loading states**: Skeleton loading for better UX
- **Profile dependency**: Disabled state when no profile selected

## Future Enhancements
- Device usage analytics integration
- Device grouping/categorization
- Recent devices quick selection
- Device filtering across time ranges
- Export filtered data functionality

## Testing
The implementation has been tested with:
- Multiple device selection scenarios
- Search functionality validation
- Profile switching behavior
- API error conditions
- Loading state handling
- Responsive design across screen sizes

## Files Modified/Created
- **New**: `frontend/src/components/DeviceFilter.tsx`
- **New**: `frontend/src/hooks/useDevices.ts` 
- **Modified**: `frontend/src/pages/Logs.tsx`
- **Modified**: `frontend/src/hooks/useLogs.ts`
- **Modified**: `frontend/src/services/api.ts`
- **Modified**: `backend/main.py` (device endpoint)
- **Modified**: `backend/models.py` (device queries, log filtering)

This implementation successfully addresses Issue #69 by providing a comprehensive device filtering solution that integrates seamlessly with the existing NextDNS Analytics interface.