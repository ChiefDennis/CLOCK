// src/app/features/users/users.component.ts

import { Component, ViewChild, AfterViewInit, TemplateRef, OnInit } from '@angular/core';
import { MatTableDataSource } from '@angular/material/table';
import { MatSort } from '@angular/material/sort';
import { MatPaginator } from '@angular/material/paginator';
import { MatDialog } from '@angular/material/dialog';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { MatTableModule } from '@angular/material/table';
import { MatPaginatorModule } from '@angular/material/paginator';
import { MatSortModule } from '@angular/material/sort';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatCheckboxModule } from '@angular/material/checkbox';
import { MatDialogModule } from '@angular/material/dialog';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatSelectModule } from '@angular/material/select';
import { MatInputModule } from '@angular/material/input';

// Import the service, dialog, and the shared User interface
import { UserService, User, CreateUserPayload, UpdateUserPayload } from './users.service';
import { UserCreateDialogComponent } from '../../dialogs/user-create-dialog/user-create-dialog.component';
import { NotificationService } from '../../core/notification.service';

@Component({
  standalone: true,
  selector: 'app-users',
  templateUrl: './users.component.html',
  styleUrls: ['./users.component.scss'],
  imports: [
    CommonModule, FormsModule, MatTableModule, MatPaginatorModule, MatSortModule,
    MatButtonModule, MatIconModule, MatCheckboxModule, MatDialogModule,
    MatFormFieldModule, MatSelectModule, MatInputModule
  ]
})
export class UsersComponent implements OnInit, AfterViewInit {
  displayedColumns: string[] = ['username', 'role', 'id', 'enabled', 'actions'];
  dataSource = new MatTableDataSource<User>();
  editingRow: User | null = null;
  private originalData: { [id: number]: User } = {};

  @ViewChild(MatSort) sort!: MatSort;
  @ViewChild(MatPaginator) paginator!: MatPaginator;
  @ViewChild('deleteDialog') deleteDialog!: TemplateRef<any>;

  constructor(
    private userService: UserService,
    private dialog: MatDialog,
    private notificationService: NotificationService
  ) {}

  ngOnInit() {
    this.getUsers();
  }

  ngAfterViewInit() {
    this.dataSource.sort = this.sort;
    this.dataSource.paginator = this.paginator;
  }

  getUsers(): void {
    this.userService.getUsers().subscribe(users => {
      this.dataSource.data = users;
    });
  }

  addUser(): void {
    const dialogRef = this.dialog.open(UserCreateDialogComponent, {
      width: '400px',
    });

    dialogRef.afterClosed().subscribe((result: CreateUserPayload) => {
      if (result) {
        this.userService.createUser(result).subscribe({
          next: () => {
            this.notificationService.showError('User created successfully.');
            this.getUsers();
          },
        });
      }
    });
  }

  startEdit(user: User) {
    this.editingRow = user;
    this.originalData[user.id] = { ...user };
  }

  saveEdit(user: User) {
    const payload: UpdateUserPayload = {
      username: user.username,
      role: user.role,
      enabled: user.enabled
    };
    this.userService.updateUser(user.id, payload).subscribe({
      next: () => {
        this.notificationService.showError('User updated successfully.');
        delete this.originalData[user.id];
        this.editingRow = null;
        this.getUsers(); // Refresh data to ensure consistency
      },
      error: () => {
        this.cancelEdit(user); // Revert on error
      }
    });
  }

  cancelEdit(user: User) {
    const originalUser = this.originalData[user.id];
    if (originalUser) {
      const userIndex = this.dataSource.data.findIndex(u => u.id === user.id);
      if (userIndex > -1) {
        this.dataSource.data[userIndex] = originalUser;
        this.dataSource.data = [...this.dataSource.data];
      }
      delete this.originalData[user.id];
    }
    this.editingRow = null;
  }

  confirmDelete(user: User) {
    const dialogRef = this.dialog.open(this.deleteDialog, {
      backdropClass: 'dialog-backdrop-blur',
      panelClass: 'warn-dialog-outline',
    });
    dialogRef.afterClosed().subscribe(result => {
      if (result) {
        this.userService.deleteUser(user.id).subscribe({
          next: (res) => {
            this.notificationService.showError(res.message);
            this.getUsers();
          }
        });
      }
    });
  }
}