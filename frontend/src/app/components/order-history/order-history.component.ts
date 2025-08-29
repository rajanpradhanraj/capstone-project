import { Component, OnInit } from '@angular/core';
import { MatSnackBar } from '@angular/material/snack-bar';
import { ApiService, Order } from '../../services/api.service';

@Component({
  selector: 'app-order-history',
  templateUrl: './order-history.component.html',
  styleUrls: ['./order-history.component.scss']
})
export class OrderHistoryComponent implements OnInit {
  orders: Order[] = [];
  loading = true;
  expandedOrder: number | null = null;

  constructor(
    private apiService: ApiService,
    private snackBar: MatSnackBar
  ) {}

  ngOnInit(): void {
    this.loadOrders();
  }

  loadOrders(): void {
    this.loading = true;
    this.apiService.getOrderHistory().subscribe({
      next: (orders) => {
        this.orders = orders;
        this.loading = false;
      },
      error: (error) => {
        console.error('Error loading orders:', error);
        this.snackBar.open('Error loading order history', 'Close', { duration: 3000 });
        this.loading = false;
      }
    });
  }

  toggleOrderDetails(orderId: number): void {
    this.expandedOrder = this.expandedOrder === orderId ? null : orderId;
  }

  getStatusClass(status: string): string {
    switch (status.toLowerCase()) {
      case 'pending': return 'status-pending';
      case 'confirmed': return 'status-confirmed';
      case 'shipped': return 'status-shipped';
      case 'delivered': return 'status-delivered';
      case 'cancelled': return 'status-cancelled';
      default: return 'status-pending';
    }
  }

  getStatusIcon(status: string): string {
    switch (status.toLowerCase()) {
      case 'pending': return 'hourglass_empty';
      case 'confirmed': return 'check_circle';
      case 'shipped': return 'local_shipping';
      case 'delivered': return 'check_circle_outline';
      case 'cancelled': return 'cancel';
      default: return 'hourglass_empty';
    }
  }

  getTotalSpent(): number {
    return this.orders.reduce((total, order) => total + order.total_amount, 0);
  }

  getActiveOrdersCount(): number {
    return this.orders.filter(order => 
      ['pending', 'confirmed', 'shipped'].includes(order.status.toLowerCase())
    ).length;
  }

  trackOrder(index: number, order: Order): number {
    return order.id;
  }

  getExpectedDeliveryDate(orderDate: string): Date {
    const date = new Date(orderDate);
    date.setDate(date.getDate() + 5);
    return date;
  }
}

