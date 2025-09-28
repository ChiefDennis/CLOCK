import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { finalize, catchError } from 'rxjs/operators';
import { of } from 'rxjs';

// Angular Material Modules
import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';
import { MatButtonModule } from '@angular/material/button';
import { MatExpansionModule } from '@angular/material/expansion';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatDialog } from '@angular/material/dialog';

import { NotificationService } from '../../core/notification.service';
import { AlertsService } from './alerts.service';
import { Alarm } from './alerts.model';
import { TruncatePipe } from '../../shared/truncate-pipe';
import { AlarmDetailDialogComponent } from '../../dialogs/alarm-detail-dialog/alarm-detail-dialog.component';

@Component({
  selector: 'app-alarms',
  standalone: true,
  imports: [
    CommonModule,
    MatCardModule,
    MatIconModule,
    MatButtonModule,
    MatExpansionModule,
    MatProgressSpinnerModule,
    TruncatePipe,
  ],
  providers: [AlertsService],
  templateUrl: './alerts.component.html',
  styleUrls: ['./alerts.component.scss']
})
export class AlertsComponent implements OnInit {
  private alertsService = inject(AlertsService);
  private notificationService = inject(NotificationService);
  private dialog = inject(MatDialog);

  isLoading = false;
  errorMessage: string | null = null;
  allAlarms: Alarm[] = [];
  nextPageToken: number | null = null;

  highAlarms: Alarm[] = [];
  mediumAlarms: Alarm[] = [];
  lowAlarms: Alarm[] = [];
  infoAlarms: Alarm[] = [];
  
  highAlarms_ack: Alarm[] = [];
  mediumAlarms_ack: Alarm[] = [];
  lowAlarms_ack: Alarm[] = [];
  infoAlarms_ack: Alarm[] = [];

  ngOnInit() {
    this.loadAlarms();
  }

  loadAlarms(): void {
    this.isLoading = true;
    this.errorMessage = null;
    this.alertsService.getAlarms().pipe(
      finalize(() => this.isLoading = false),
      catchError(err => {
        this.errorMessage = 'Failed to load alarms. Please try again later.';
        console.error(err);
        return of(null);
      })
    ).subscribe(response => {
      if (response) {
        this.allAlarms = response.alarms;
        this.nextPageToken = response.next_page_token;
        this.categorizeAlarms();
      }
    });
  }

  loadMoreAlarms(): void {
    if (!this.nextPageToken) return;
    this.alertsService.getAlarms(20, this.nextPageToken).subscribe(response => {
      this.allAlarms.push(...response.alarms);
      this.nextPageToken = response.next_page_token;
      this.categorizeAlarms();
    });
  }

  acknowledgeAlarm(alarmToAck: Alarm): void {
    this.alertsService.acknowledgeAlarm(alarmToAck.id).pipe(
      catchError(err => {
        console.error(err);
        this.notificationService.showError('Error: Could not acknowledge the alarm.');
        return of(null);
      })
    ).subscribe(updatedAlarm => {
      if (updatedAlarm) {
        this.updateAlarmInList(updatedAlarm);
        this.notificationService.showSuccess(`Alarm "${updatedAlarm.event_type}" acknowledged.`);
      }
    });
  }

  unacknowledgeAlarm(alarmToReactivate: Alarm): void {
    this.alertsService.unacknowledgeAlarm(alarmToReactivate.id).pipe(
      catchError(err => {
        console.error(err);
        this.notificationService.showError('Error: Could not re-activate the alarm.');
        return of(null);
      })
    ).subscribe(updatedAlarm => {
      if (updatedAlarm) {
        this.updateAlarmInList(updatedAlarm);
        this.notificationService.showSuccess(`Alarm "${updatedAlarm.event_type}" re-activated.`);
      }
    });
  }

  private updateAlarmInList(updatedAlarm: Alarm): void {
    const index = this.allAlarms.findIndex(a => a.id === updatedAlarm.id);
    if (index !== -1) {
      this.allAlarms[index] = updatedAlarm;
      this.categorizeAlarms();
    }
  }

  categorizeAlarms(): void {
    const unacknowledged = this.allAlarms.filter(a => !a.is_acknowledged);
    const acknowledged = this.allAlarms.filter(a => a.is_acknowledged);

    this.highAlarms = unacknowledged.filter(a => a.severity.toLowerCase() === 'high');
    this.mediumAlarms = unacknowledged.filter(a => a.severity.toLowerCase() === 'medium');
    this.lowAlarms = unacknowledged.filter(a => a.severity.toLowerCase() === 'low');
    this.infoAlarms = unacknowledged.filter(a => a.severity.toLowerCase() === 'info');
    
    this.highAlarms_ack = acknowledged.filter(a => a.severity.toLowerCase() === 'high');
    this.mediumAlarms_ack = acknowledged.filter(a => a.severity.toLowerCase() === 'medium');
    this.lowAlarms_ack = acknowledged.filter(a => a.severity.toLowerCase() === 'low');
    this.infoAlarms_ack = acknowledged.filter(a => a.severity.toLowerCase() === 'info');
  }

  getSeverityIcon(severity: string): string {
    switch (severity.toLowerCase()) {
      case 'high': return 'error';
      case 'medium': return 'warning';
      case 'low': return 'info';
      case 'info': return 'notifications';
      default: return 'help';
    }
  }

  /**
   * Opens the alarm detail dialog.
   * @param alarm The alarm data to display in the dialog.
   */
  openAlarmDialog(alarm: Alarm): void {
    const dialogRef = this.dialog.open(AlarmDetailDialogComponent, {
      width: '600px',
      data: alarm, // Pass the alarm data to the dialog
      backdropClass: 'dialog-backdrop-blur', // blur effect
      panelClass: `alarm-dialog-${alarm.severity.toLowerCase()}` 
    });

    // After the dialog closes, check if an action was returned
    dialogRef.afterClosed().subscribe(result => {
      if (result === 'acknowledge') {
        this.acknowledgeAlarm(alarm);
      } else if (result === 'reactivate') {
        this.unacknowledgeAlarm(alarm);
      }
    });
  }
}