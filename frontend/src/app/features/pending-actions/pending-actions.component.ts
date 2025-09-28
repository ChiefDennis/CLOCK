import { Component, OnInit, AfterViewInit, ViewChild } from '@angular/core';
import { CommonModule, DatePipe } from '@angular/common';
import { PendingActionsService, PendingAction } from './pending-actions.service';
import { MatTableDataSource, MatTableModule } from '@angular/material/table';
import { MatPaginator, MatPaginatorModule } from '@angular/material/paginator';
import { MatSort, MatSortModule } from '@angular/material/sort'; 
import { MatIconModule } from '@angular/material/icon';
import { MatButtonModule } from '@angular/material/button';

@Component({
  selector: 'app-pending-actions',
  standalone: true,
  imports: [
    CommonModule, DatePipe, MatIconModule, MatButtonModule,
    MatTableModule, MatPaginatorModule, MatSortModule 
  ],
  templateUrl: './pending-actions.component.html',
  styleUrls: ['./pending-actions.component.scss'],
})
export class PendingActionsComponent implements OnInit, AfterViewInit {
  displayedColumns: string[] = ['action', 'resource', 'status', 'requested', 'expires', 'reviewed', 'actions'];
  dataSource = new MatTableDataSource<PendingAction>();
  loading = true;

  @ViewChild(MatPaginator) paginator!: MatPaginator;
  @ViewChild(MatSort) sort!: MatSort; 

  constructor(private actionsService: PendingActionsService) {}

  ngOnInit(): void {
    this.fetchActions();
  }

  ngAfterViewInit(): void {
    this.dataSource.paginator = this.paginator;
    this.dataSource.sort = this.sort;
  }

  fetchActions(): void {
    this.loading = true;
    this.actionsService.getPendingActions().subscribe({
      next: (res) => {
        this.dataSource.data = res;
        this.loading = false;
      },
      error: (err) => {
        console.error(err);
        this.loading = false;
      }
    });
  }

  approve(action: PendingAction): void {
    this.actionsService.approveAction(action.id).subscribe(() => this.fetchActions());
  }

  deny(action: PendingAction): void {
    this.actionsService.denyAction(action.id).subscribe(() => this.fetchActions());
  }
  
  refreshActions() {
    this.fetchActions();
  }
}