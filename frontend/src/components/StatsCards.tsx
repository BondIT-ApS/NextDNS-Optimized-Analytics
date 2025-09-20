import { memo } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Database, Shield, CheckCircle } from "lucide-react";
import { formatNumber } from "@/lib/utils";

interface StatsCardsProps {
  stats: {
    total: number;
    blocked: number;
    allowed: number;
    totalInDatabase: number;
    blockedPercentage: number;
    allowedPercentage: number;
  };
  debouncedSearchQuery: string;
  statusFilter: "all" | "blocked" | "allowed";
}

export const StatsCards = memo<StatsCardsProps>(
  ({ stats, debouncedSearchQuery, statusFilter }) => {
    return (
      <div className="grid gap-6 md:grid-cols-3">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">DNS Queries</CardTitle>
            <Database className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-lego-blue">
              {formatNumber(stats.total)}
            </div>
            <p className="text-xs text-muted-foreground">
              {debouncedSearchQuery || statusFilter !== "all"
                ? `Filtered from ${formatNumber(stats.totalInDatabase)} total queries`
                : `From ${formatNumber(stats.totalInDatabase)} total queries`}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Blocked</CardTitle>
            <Shield className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-lego-red">
              {formatNumber(stats.blocked)}
            </div>
            <p className="text-xs text-muted-foreground">
              {stats.blockedPercentage}% of all queries
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Allowed</CardTitle>
            <CheckCircle className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-lego-green">
              {formatNumber(stats.allowed)}
            </div>
            <p className="text-xs text-muted-foreground">
              {stats.allowedPercentage}% of all queries
            </p>
          </CardContent>
        </Card>
      </div>
    );
  },
);

StatsCards.displayName = "StatsCards";
