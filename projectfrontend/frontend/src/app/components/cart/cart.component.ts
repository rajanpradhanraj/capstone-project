import { Component, OnInit } from '@angular/core';
import { Router } from '@angular/router';
import { MatSnackBar } from '@angular/material/snack-bar';
import { CartService } from '../../services/cart.service';
import { Cart, CartItem } from '../../services/api.service';

@Component({
  selector: 'app-cart',
  templateUrl: './cart.component.html',
  styleUrls: ['./cart.component.scss']
})
export class CartComponent implements OnInit {
  cart: Cart = {
    user_id: '',
    items: [],
    total_amount: 0,
    item_count: 0
  };
  loading = false;
  updating: { [key: number]: boolean } = {};

  constructor(
    private cartService: CartService,
    private router: Router,
    private snackBar: MatSnackBar
  ) {}

  ngOnInit(): void {
    this.cartService.cart$.subscribe(cart => {
      this.cart = cart;
    });
  }

  updateQuantity(item: CartItem, newQuantity: number): void {
    if (newQuantity < 1) {
      this.removeItem(item);
      return;
    }

    if (newQuantity > item.available_stock) {
      this.snackBar.open(`Only ${item.available_stock} items available`, 'Close', { duration: 3000 });
      return;
    }

    this.updating[item.product_id] = true;
    
    this.cartService.updateCartItem(item.product_id, newQuantity).subscribe({
      next: () => {
        this.updating[item.product_id] = false;
        this.snackBar.open('Cart updated', 'Close', { duration: 2000 });
      },
      error: (error) => {
        console.error('Error updating cart:', error);
        this.updating[item.product_id] = false;
        this.snackBar.open('Error updating cart', 'Close', { duration: 3000 });
      }
    });
  }

  removeItem(item: CartItem): void {
    this.updating[item.product_id] = true;
    
    this.cartService.removeFromCart(item.product_id).subscribe({
      next: () => {
        this.updating[item.product_id] = false;
        this.snackBar.open(`${item.product_name} removed from cart`, 'Close', { duration: 2000 });
      },
      error: (error) => {
        console.error('Error removing item:', error);
        this.updating[item.product_id] = false;
        this.snackBar.open('Error removing item', 'Close', { duration: 3000 });
      }
    });
  }

  clearCart(): void {
    if (confirm('Are you sure you want to clear your cart?')) {
      this.loading = true;
      
      this.cartService.clearCart().subscribe({
        next: () => {
          this.loading = false;
          this.snackBar.open('Cart cleared', 'Close', { duration: 2000 });
        },
        error: (error) => {
          console.error('Error clearing cart:', error);
          this.loading = false;
          this.snackBar.open('Error clearing cart', 'Close', { duration: 3000 });
        }
      });
    }
  }

  proceedToCheckout(): void {
    if (this.cart.items.length === 0) {
      this.snackBar.open('Your cart is empty', 'Close', { duration: 3000 });
      return;
    }

    // Check for out of stock items
    const outOfStockItems = this.cart.items.filter(item => item.quantity > item.available_stock);
    if (outOfStockItems.length > 0) {
      this.snackBar.open('Some items in your cart are out of stock', 'Close', { duration: 3000 });
      return;
    }

    this.router.navigate(['/user/checkout']);
  }

  continueShopping(): void {
    this.router.navigate(['/user/products']);
  }

  trackByProductId(index: number, item: CartItem): number {
    return item.product_id;
  }
}
