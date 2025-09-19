import React, { memo } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { SearchInput } from '@/components/SearchInput'

interface FilterPanelProps {
  searchQuery: string
  onSearchChange: (e: React.ChangeEvent<HTMLInputElement>) => void
  statusFilter: 'all' | 'blocked' | 'allowed'
  onStatusFilterChange: (status: 'all' | 'blocked' | 'allowed') => void
  debouncedSearchQuery: string
  filteredLogsCount: number
  totalLogsCount: number
}

export const FilterPanel = memo<FilterPanelProps>(({ 
  searchQuery, 
  onSearchChange, 
  statusFilter, 
  onStatusFilterChange,
  debouncedSearchQuery,
  filteredLogsCount,
  totalLogsCount
}) => {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg">Filters</CardTitle>
        <CardDescription>Search and filter DNS logs</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="flex flex-col sm:flex-row gap-4">
          {/* Search Input */}
          <SearchInput 
            value={searchQuery}
            onChange={onSearchChange}
            placeholder="Search domains..."
          />

          {/* Status Filter Buttons */}
          <div className="flex gap-2">
            {[
              { key: 'all', label: 'All', color: 'outline' },
              { key: 'blocked', label: 'Blocked', color: 'destructive' },
              { key: 'allowed', label: 'Allowed', color: 'default' }
            ].map(({ key, label, color }) => (
              <Button
                key={key}
                variant={statusFilter === key ? (color as any) : 'outline'}
                size="sm"
                onClick={() => onStatusFilterChange(key as any)}
                className={
                  statusFilter === key && key === 'allowed' 
                    ? 'bg-lego-green hover:bg-lego-green/90 text-white' 
                    : ''
                }
              >
                {label}
              </Button>
            ))}
          </div>
        </div>

        {/* Filter Summary */}
        {(debouncedSearchQuery || statusFilter !== 'all') && (
          <div className="mt-4 text-sm text-muted-foreground">
            Showing {filteredLogsCount} of {totalLogsCount} logs
            {debouncedSearchQuery && ` matching "${debouncedSearchQuery}"`}
            {statusFilter !== 'all' && ` (${statusFilter} only)`}
            {searchQuery !== debouncedSearchQuery && (
              <span className="text-muted-foreground/70"> (searching...)</span>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  )
})

FilterPanel.displayName = 'FilterPanel'