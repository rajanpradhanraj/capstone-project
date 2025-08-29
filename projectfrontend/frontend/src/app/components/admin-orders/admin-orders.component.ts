import { Component, OnInit } from '@angular/core';
import { MatSnackBar } from '@angular/material/snack-bar';
import { ApiService, Order } from '../../services/api.service';

@Component({
  selector: 'app-admin-orders',
  templateUrl: './admin-orders.component.html',
  styleUrls: ['./admin-orders.component.scss']
})
export class AdminOrdersComponent implements OnInit {
  orders: Order[] = [];
  filteredOrders: Order[] = [];
  loading = true;
  searchTerm = '';
  selectedStatus = '';
  selectedDateRange = '';

  displayedColumns: string[] = ['id', 'customer', 'items', 'amount', 'status', 'actions'];

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
        this.filteredOrders = orders;
        this.loading = false;
      },
      error: (error) => {
        console.error('Error loading orders:', error);
        this.snackBar.open('Error loading orders', 'Close', { duration: 3000 });
        this.loading = false;
      }
    });
  }

  onSearch(): void {
    this.applyFilters();
  }

  onStatusChange(): void {
    this.applyFilters();
  }

  onDateRangeChange(): void {
    this.applyFilters();
  }

  applyFilters(): void {
    this.filteredOrders = this.orders.filter(order => {
      const matchesSearch = !this.searchTerm || 
        order.id.toString().includes(this.searchTerm) ||
        order.items?.some(item => item.product_name.toLowerCase().includes(this.searchTerm.toLowerCase()));

      const matchesStatus = !this.selectedStatus || order.status.toLowerCase() === this.selectedStatus.toLowerCase();

      const matchesDateRange = !this.selectedDateRange || this.matchesDateRange(order.created_at, this.selectedDateRange);

      return matchesSearch && matchesStatus && matchesDateRange;
    });
  }

  matchesDateRange(orderDate: string, range: string): boolean {
    const order = new Date(orderDate);
    const now = new Date();
    
    switch (range) {
      case 'today':
        return order.toDateString() === now.toDateString();
      case 'week':
        const weekAgo = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
        return order >= weekAgo;
      case 'month':
        return order.getMonth() === now.getMonth() && order.getFullYear() === now.getFullYear();
      case 'quarter':
        const quarterStart = new Date(now.getFullYear(), Math.floor(now.getMonth() / 3) * 3, 1);
        return order >= quarterStart;
      default:
        return true;
    }
  }

  clearFilters(): void {
    this.searchTerm = '';
    this.selectedStatus = '';
    this.selectedDateRange = '';
    this.filteredOrders = this.orders;
  }

  getTotalValue(): number {
    return this.filteredOrders.reduce((total, order) => total + order.total_amount, 0);
  }

  getPendingOrdersCount(): number {
    return this.filteredOrders.filter(order => order.status.toLowerCase() === 'pending').length;
  }

  getAverageOrderValue(): number {
    if (this.filteredOrders.length === 0) return 0;
    return this.getTotalValue() / this.filteredOrders.length;
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

  viewOrderDetails(order: Order): void {
    // TODO: Implement order details view
    console.log('View order details:', order);
    this.snackBar.open(`Viewing order #${order.id}`, 'Close', { duration: 2000 });
  }

  updateOrderStatus(order: Order, newStatus: string): void {
    // TODO: Implement order status update
    console.log(`Update order ${order.id} status to ${newStatus}`);
    this.snackBar.open(`Order #${order.id} status updated to ${newStatus}`, 'Close', { duration: 3000 });
  }

  exportOrders(): void {
    // TODO: Implement export functionality
    console.log('Exporting orders...');
    this.snackBar.open('Export functionality coming soon!', 'Close', { duration: 3000 });
  }
}

