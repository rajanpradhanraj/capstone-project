import { Injectable } from '@angular/core';
import { BehaviorSubject, Observable } from 'rxjs';
import { ApiService, Cart } from './api.service';

@Injectable({
  providedIn: 'root'
})
export class CartService {
  private cartSubject = new BehaviorSubject<Cart>({
    user_id: '',
    items: [],
    total_amount: 0,
    item_count: 0
  });
  
  public cart$ = this.cartSubject.asObservable();

  constructor(private apiService: ApiService) {}

  getCurrentCart(): Cart {
    return this.cartSubject.value;
  }

  loadCart(): void {
    this.apiService.getCart().subscribe({
      next: (cart) => {
        this.cartSubject.next(cart);
      },
      error: (error) => {
        console.error('Error loading cart:', error);
      }
    });
  }

  addToCart(productId: number, quantity: number = 1): Observable<any> {
    return new Observable(observer => {
      this.apiService.addToCart(productId, quantity).subscribe({
        next: (response) => {
          this.loadCart(); // Refresh cart
          observer.next(response);
          observer.complete();
        },
        error: (error) => {
          observer.error(error);
        }
      });
    });
  }

  updateCartItem(productId: number, quantity: number): Observable<any> {
    return new Observable(observer => {
      this.apiService.updateCartItem(productId, quantity).subscribe({
        next: (response) => {
          this.loadCart(); // Refresh cart
          observer.next(response);
          observer.complete();
        },
        error: (error) => {
          observer.error(error);
        }
      });
    });
  }

  removeFromCart(productId: number): Observable<any> {
    return new Observable(observer => {
      this.apiService.removeFromCart(productId).subscribe({
        next: (response) => {
          this.loadCart(); // Refresh cart
          observer.next(response);
          observer.complete();
        },
        error: (error) => {
          observer.error(error);
        }
      });
    });
  }

  clearCart(): Observable<any> {
    return new Observable(observer => {
      this.apiService.clearCart().subscribe({
        next: (response) => {
          this.loadCart(); // Refresh cart
          observer.next(response);
          observer.complete();
        },
        error: (error) => {
          observer.error(error);
        }
      });
    });
  }

  getCartItemCount(): number {
    return this.cartSubject.value.item_count;
  }
}

