import { useQuery } from "@tanstack/react-query";
import { apiClient } from "@/services/api";
import type { LogFilters } from "@/types/api";

interface LogsParams extends LogFilters {
  status?: "all" | "blocked" | "allowed";
}

export function useLogs(params: LogsParams = {}) {
  // Create a stable query key that doesn't change frequently
  // Normalize the parameters to prevent unnecessary re-fetches
  const normalizedParams = {
    limit: params.limit || 100,
    search: params.search?.trim() || undefined,
    status: params.status === "all" ? undefined : params.status,
    profile: params.profile || undefined,
  };

  // Remove undefined values to create cleaner query key
  const queryKey = [
    "logs",
    Object.fromEntries(
      Object.entries(normalizedParams).filter(
        ([_, value]) => value !== undefined,
      ),
    ),
  ];

  return useQuery({
    queryKey,
    queryFn: () => apiClient.getLogs(params),
    staleTime: 30000, // 30 seconds
    refetchInterval:
      params.search || params.status !== "all" || params.profile
        ? false
        : 60000, // Only auto-refresh when no filters
    // Enable query deduplication and background updates
    refetchOnWindowFocus: false,
    refetchOnReconnect: false,
  });
}

export function useLogsStats(profile?: string) {
  return useQuery({
    queryKey: ["logs-stats", profile],
    queryFn: () => apiClient.getLogsStats(profile),
    staleTime: 60000, // 60 seconds
    refetchInterval: 120000, // Refetch every 2 minutes
  });
}

export function useProfiles() {
  return useQuery({
    queryKey: ["profiles"],
    queryFn: () => apiClient.getAvailableProfiles(),
    staleTime: 300000, // 5 minutes
    refetchInterval: false, // Don't auto-refresh
  });
}

export function useProfilesInfo() {
  return useQuery({
    queryKey: ["profiles-info"],
    queryFn: () => apiClient.getProfilesInfo(),
    staleTime: 300000, // 5 minutes
    refetchInterval: false, // Don't auto-refresh
  });
}
