// src/app/key-management/key-list/key-list.component.ts

import { Component, OnInit, ViewChild } from '@angular/core';
import { Router, RouterLink } from '@angular/router';
import { CommonModule, DatePipe } from '@angular/common';

// Angular Material Modules
import { MatTableDataSource, MatTableModule } from '@angular/material/table';
import { MatSort, MatSortModule } from '@angular/material/sort';
import { MatPaginator, MatPaginatorModule } from '@angular/material/paginator';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';

// Custom Service & Model
import { KeyManagementService } from '../key-management.service';
import { Key } from '../key.model';

@Component({
  selector: 'app-key-list',
  standalone: true,
  imports: [
    CommonModule,
    RouterLink,
    DatePipe,
    MatTableModule,
    MatSortModule,
    MatPaginatorModule,
    MatButtonModule,
    MatIconModule,
    MatProgressSpinnerModule
  ],
  templateUrl: './key-list.component.html',
  styleUrls: ['./key-list.component.scss']
})
export class KeyListComponent implements OnInit {
  displayedColumns: string[] = ['cloud_provider', 'key_id', 'algorithm', 'created_at', 'status'];
  dataSource = new MatTableDataSource<Key>();
  isLoading = true;

  @ViewChild(MatSort) sort!: MatSort;
  @ViewChild(MatPaginator) paginator!: MatPaginator;

  constructor(
    private keyService: KeyManagementService,
    private router: Router
  ) {}

  ngOnInit() {
    this.loadKeys();
  }

  loadKeys() {
    this.isLoading = true;
    this.keyService.listLocalKeys().subscribe(keys => {
      this.dataSource.data = keys;
      this.dataSource.sort = this.sort;
      this.dataSource.paginator = this.paginator;
      this.isLoading = false;
    });
  }

  viewKeyDetails(key: Key) {
    this.router.navigate(['/app/key-management', key.id]);
  }
}