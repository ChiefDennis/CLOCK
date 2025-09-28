import { Component, ViewChild, AfterViewInit } from '@angular/core';
import { trigger, state, style, transition, animate } from '@angular/animations';
import { CommonModule } from '@angular/common';
import { SelectionModel } from '@angular/cdk/collections';
import { of, merge } from 'rxjs';
import { startWith, switchMap, map, catchError, tap } from 'rxjs/operators';

// Angular Material Modules
import { MatButtonModule } from '@angular/material/button';
import { MatCheckboxModule } from '@angular/material/checkbox';
import { MatDialog } from '@angular/material/dialog';
import { MatIconModule } from '@angular/material/icon';
import { MatPaginator, MatPaginatorModule, PageEvent } from '@angular/material/paginator';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatSort, MatSortModule } from '@angular/material/sort';
import { MatTableDataSource, MatTableModule } from '@angular/material/table';

// Custom Components, Pipes, and Services
import { TruncatePipe } from '../../shared/truncate-pipe';
import { LogDetailDialogComponent } from './log-detail-dialog/log-detail-dialog';
import { LogService, Log, LogsApiResponse } from './logs.service';
import { NotificationService } from '../../core/notification.service';

const MAX_CACHE_PAGES = 10; // A sensible limit for the cache size

@Component({
  selector: 'app-logs',
  standalone: true,
  templateUrl: './logs.component.html',
  styleUrls: ['./logs.component.scss'],
  imports: [
    CommonModule,
    MatTableModule,
    MatSortModule,
    MatPaginatorModule,
    MatButtonModule,
    MatIconModule,
    MatCheckboxModule,
    TruncatePipe,
    MatProgressSpinnerModule,
  ],
  animations: [
    trigger('detailExpand', [
      state('collapsed', style({ height: '0px', minHeight: '0', display: 'none' })),
      state('expanded', style({ height: '*' })),
      transition('expanded <=> collapsed', animate('225ms cubic-bezier(0.4, 0.0, 0.2, 1)')),
    ]),
  ],
})
export class LogsComponent implements AfterViewInit {
  displayedColumns: string[] = ['select', 'id', 'username', 'action', 'timestamp', 'actions'];
  dataSource = new MatTableDataSource<Log>([]);
  selection = new SelectionModel<Log>(true, []);
  expandedElement: Log | null = null;
  
  resultsLength = 0;
  loading = true;
  private nextPageToken: number | null = null;
  private pageCache = new Map<number, Log[]>();
  private currentPageSize: number = 50;

  @ViewChild(MatSort) sort!: MatSort;
  @ViewChild(MatPaginator) paginator!: MatPaginator;

  constructor(
    private dialog: MatDialog,
    private logService: LogService,
    private notificationService: NotificationService
  ) {}

  ngAfterViewInit() {
    this.dataSource.sort = this.sort;
    this.currentPageSize = this.paginator.pageSize;
    this.sort.sortChange.subscribe(() => (this.paginator.pageIndex = 0));

    merge(this.sort.sortChange, this.paginator.page)
      .pipe(
        startWith({}),
        tap(() => {
          if (this.paginator.pageSize !== this.currentPageSize) {
            this.paginator.pageIndex = 0;
            this.nextPageToken = null;
            this.pageCache.clear();
            this.currentPageSize = this.paginator.pageSize;
          }
        }),
        switchMap(() => {
          this.loading = true;
          this.selection.clear();

          if (this.pageCache.has(this.paginator.pageIndex)) {
            return of(this.pageCache.get(this.paginator.pageIndex));
          }

          const token = this.nextPageToken === null ? undefined : this.nextPageToken;

          return this.logService.getLogs(this.paginator.pageSize, token).pipe(
            catchError(err => {
              console.error('Failed to fetch logs:', err);
              this.notificationService.showError('Could not load logs. Please try refreshing.');
              return of(null);
            })
          );
        }),
        map((data: LogsApiResponse | Log[] | null | undefined): Log[] => {
          this.loading = false;

          if (!data) {
            return [];
          }

          if ('logs' in data) {
            this.nextPageToken = data.next_page_token;
            const logs = data.logs;

            if (data.next_page_token === null) {
              this.resultsLength = this.paginator.pageIndex * this.paginator.pageSize + logs.length;
            } else {
              this.resultsLength = (this.paginator.pageIndex + 2) * this.paginator.pageSize;
            }

            this.pageCache.set(this.paginator.pageIndex, logs);
            
            if (this.pageCache.size > MAX_CACHE_PAGES) {
              const oldestKey = this.pageCache.keys().next().value;
              // Add a guard to ensure the key is not undefined before deleting.
              if (oldestKey !== undefined) {
                this.pageCache.delete(oldestKey);
              }
            }
            return logs;
          }
          return data;
        })
      )
      .subscribe(logs => {
        this.dataSource.data = logs;
      });
  }

  refreshLogs() {
    this.paginator.pageIndex = 0;
    this.nextPageToken = null;
    this.pageCache.clear();
    this.paginator.page.emit({
      pageIndex: 0,
      pageSize: this.paginator.pageSize,
      length: this.paginator.length,
    });
  }

  isAllSelected() {
    const numSelected = this.selection.selected.length;
    const numRows = this.dataSource.data.length;
    return numSelected === numRows;
  }

  toggleAllRows() {
    if (this.isAllSelected()) {
      this.selection.clear();
      return;
    }
    this.selection.select(...this.dataSource.data);
  }

  checkboxLabel(row?: Log): string {
    if (!row) {
      return `${this.isAllSelected() ? 'deselect' : 'select'} all`;
    }
    return `${this.selection.isSelected(row) ? 'deselect' : 'select'} row ${row.id}`;
  }

  downloadLogs() {
    if (this.selection.selected.length === 0) {
      alert('Please select logs to download.');
      return;
    }
    const selectedLogs = this.selection.selected;
    const csvData = this.convertToCSV(selectedLogs);
    const blob = new Blob([csvData], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    link.setAttribute('href', url);
    link.setAttribute('download', 'logs.csv');
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  }

  private convertToCSV(data: Log[]): string {
    if (data.length === 0) return '';
    const header = Object.keys(data[0]).join(',');
    const rows = data.map(row =>
      Object.values(row)
        .map(value => {
          const strValue = String(value);
          return strValue.includes(',') ? `"${strValue}"` : strValue;
        })
        .join(',')
    );
    return [header, ...rows].join('\n');
  }

  openDataDialog(data: string): void {
    this.dialog.open(LogDetailDialogComponent, {
      width: '80%',
      maxWidth: '800px',
      data: data,
    });
  }
}