// src/app/features/dashboard/dashboard.component.ts

import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Observable } from 'rxjs';
import { DashboardService, DashboardData, SyncStatus } from './dashboard.service';
import { Router, RouterLink } from '@angular/router';

// --- Third-Party Modules ---
import { NgxChartsModule, LegendPosition } from '@swimlane/ngx-charts';

// --- CORRECTED ANGULAR MATERIAL IMPORTS ---
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatIconModule } from '@angular/material/icon';
import { MatCardModule } from '@angular/material/card';
import { MatGridListModule } from '@angular/material/grid-list';
import { MatListModule } from '@angular/material/list';
import { MatDividerModule } from '@angular/material/divider';


@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [
    CommonModule,
    RouterLink,
    NgxChartsModule,
    MatProgressSpinnerModule,
    MatIconModule,
    MatCardModule,
    MatGridListModule,
    MatListModule,
    MatDividerModule
  ],
  templateUrl: './dashboard.component.html',
  styleUrls: ['./dashboard.component.scss']
})
export class DashboardComponent implements OnInit {
  dashboardData$!: Observable<DashboardData>;
  legendPosition: LegendPosition = LegendPosition.Below;

  customChartColors = [
    { name: 'Enabled', value: 'var(--mat-sys-primary)' },
    { name: 'Disabled', value: 'var(--mat-sys-tertiary)' },
    { name: 'Pending Deletion', value: 'var(--mat-sys-error)' }
  ];

  constructor(private dashboardService: DashboardService) {}

  ngOnInit(): void {
    this.dashboardData$ = this.dashboardService.getDashboardData();
  }

  getDeletionDateFromStatus(status: string): string | null {
    if (status && status.includes(' | ')) {
      return status.split(' | ')[1];
    }
    return null;
  }

  calculateDaysRemaining(dateString: string | undefined | null): number {
    if (!dateString) return 0;
    const today = new Date();
    const futureDate = new Date(dateString);
    today.setHours(0, 0, 0, 0);
    futureDate.setHours(0, 0, 0, 0);
    const differenceInTime = futureDate.getTime() - today.getTime();
    const differenceInDays = Math.ceil(differenceInTime / (1000 * 3600 * 24));
    return differenceInDays >= 0 ? differenceInDays : 0;
  }

  hasStaleSync(statuses: SyncStatus[]): boolean {
    return statuses.some(s => s.isStale);
  }

  formatTimeSince(date: Date | null): string {
    if (!date) return 'Never';
    const seconds = Math.floor((new Date().getTime() - date.getTime()) / 1000);
    if (seconds < 60) return "Just now";
    const minutes = Math.floor(seconds / 60);
    if (minutes < 60) return `${minutes}m ago`;
    const hours = Math.floor(minutes / 60);
    if (hours < 24) return `${hours}h ago`;
    const days = Math.floor(hours / 24);
    return `${days}d ago`;
  }
}