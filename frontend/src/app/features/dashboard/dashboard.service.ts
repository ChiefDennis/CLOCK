// src/app/features/dashboard/dashboard.service.ts

import { Injectable } from '@angular/core';
import { Observable, forkJoin, map } from 'rxjs';
import { KeyManagementService } from '../key-management/key-management.service';
import { Key } from '../key-management/key.model';
import { ModulesService, ModuleStatus } from '../modules/modules.service';
import { PendingActionsService } from '../pending-actions/pending-actions.service';
import { AlertsService } from '../alerts/alerts.service';

// A type for the processed sync status data.
export interface SyncStatus {
  provider: string;
  lastSync: Date | null;
  isStale: boolean;
}

// The final, clean data structure the component will receive.
export interface DashboardData {
  totalKeys: number;
  enabledModules: number;
  totalModules: number;
  pendingActions: number;
  activeAlarms: number;
  keysByStatus: { name: string; value: number }[];
  keysNearingDeletion: Key[];
  keysByProvider: { name: string; value: number }[];
  syncStatuses: SyncStatus[];
}

@Injectable({
  providedIn: 'root'
})
export class DashboardService {

  constructor(
    private keyService: KeyManagementService,
    private modulesService: ModulesService,
    private pendingActionsService: PendingActionsService,
    private alertsService: AlertsService
  ) {}

  getDashboardData(): Observable<DashboardData> {
    // forkJoin runs all API calls in parallel for efficiency.
    return forkJoin({
      keys: this.keyService.listLocalKeys(),
      modules: this.modulesService.getModulesStatus(),
      pendingActions: this.pendingActionsService.getPendingActions(),
      alarmsResponse: this.alertsService.getAlarms(100)
    }).pipe(
      // The map operator processes the raw results into our final DashboardData shape.
      map(({ keys, modules, pendingActions, alarmsResponse }) => {

        // Process module sync statuses. A sync is "stale" if it's over 24 hours old.
        const now = new Date();
        const syncStatuses: SyncStatus[] = modules.map(module => {
          const lastSync = module.last_synced_at ? new Date(module.last_synced_at) : null;
          const hoursDiff = lastSync ? (now.getTime() - lastSync.getTime()) / 3600000 : Infinity;
          return {
            provider: module.provider_name,
            lastSync: lastSync,
            isStale: hoursDiff > 24
          };
        });

        // Filter and sort keys that are pending deletion.
        const keysNearingDeletion = keys
          .filter(key => key.status.startsWith('PendingDeletion | '))
          .sort((a, b) => {
            const dateA = new Date(a.status.split(' | ')[1]).getTime();
            const dateB = new Date(b.status.split(' | ')[1]).getTime();
            return dateA - dateB;
          });

        const keysByProvider = this.groupKeysByProvider(keys);
        const enabledModules = modules.filter(m => m.is_enabled).length;
        const keysByStatus = this.groupKeysByStatus(keys);
        const activeAlarms = alarmsResponse.alarms.filter(a => !a.is_acknowledged).length;
        // Return the final, assembled object.
        return {
          totalKeys: keys.length,
          enabledModules,
          totalModules: modules.length,
          pendingActions: pendingActions.filter(action => action.status === 'PENDING').length,
          activeAlarms,
          keysByStatus,
          keysNearingDeletion,
          keysByProvider,
          syncStatuses
        };
      })
    );
  }

  private groupKeysByStatus(keys: Key[]): { name: string; value: number }[] {
    const statusCounts = keys.reduce((acc, key) => {
      const status = key.status.startsWith('PendingDeletion') ? 'Pending Deletion' : key.status;
      acc[status] = (acc[status] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);
    return Object.entries(statusCounts).map(([name, value]) => ({ name, value }));
  }

  private groupKeysByProvider(keys: Key[]): { name: string; value: number }[] {
    const providerCounts = keys.reduce((acc, key) => {
      const provider = key.cloud_provider.toUpperCase();
      acc[provider] = (acc[provider] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);
    return Object.entries(providerCounts).map(([name, value]) => ({ name, value }));
  }
}