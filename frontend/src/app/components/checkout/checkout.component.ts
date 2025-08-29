import { Component, OnInit } from '@angular/core';
import { Router } from '@angular/router';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';
import { MatSnackBar } from '@angular/material/snack-bar';
import { ApiService } from '../../services/api.service';
import { CartService } from '../../services/cart.service';
import { Cart } from '../../services/api.service';

@Component({
  selector: 'app-checkout',
  templateUrl: './checkout.component.html',
  styleUrls: ['./checkout.component.scss']
})
export class CheckoutComponent implements OnInit {
  cart: Cart = {
    user_id: '',
    items: [],
    total_amount: 0,
    item_count: 0
  };
  checkoutForm: FormGroup;
  processing = false;

  constructor(
    private fb: FormBuilder,
    private apiService: ApiService,
    private cartService: CartService,
    private router: Router,
    private snackBar: MatSnackBar
  ) {
    this.checkoutForm = this.fb.group({
      email: ['', [Validators.required, Validators.email]],
      firstName: ['', Validators.required],
      lastName: ['', Validators.required],
      address: ['', Validators.required],
      city: ['', Validators.required],
      state: ['', Validators.required],
      zipCode: ['', Validators.required],
      cardNumber: ['4111111111111111', Validators.required],
      expiryDate: ['12/25', Validators.required],
      cvv: ['123', Validators.required],
      cardName: ['', Validators.required]
    });
  }

  ngOnInit(): void {
    this.cartService.cart$.subscribe(cart => {
      this.cart = cart;
      
      // Redirect if cart is empty
      if (cart.items.length === 0) {
        this.router.navigate(['/user/cart']);
        this.snackBar.open('Your cart is empty', 'Close', { duration: 3000 });
      }
    });
  }

  onSubmit(): void {
    if (this.checkoutForm.valid && this.cart.items.length > 0) {
      this.processing = true;

      this.apiService.checkout().subscribe({
        next: (response) => {
          this.processing = false;
          this.snackBar.open('Order placed successfully!', 'Close', { duration: 3000 });
          this.router.navigate(['/user/orders']);
        },
        error: (error) => {
          this.processing = false;
          console.error('Checkout error:', error);
          
          let errorMessage = 'Failed to place order. Please try again.';
          if (error.error && error.error.error) {
            errorMessage = error.error.error;
          }
          
          this.snackBar.open(errorMessage, 'Close', { duration: 5000 });
        }
      });
    }
  }

  goBack(): void {
    this.router.navigate(['/user/cart']);
  }
}



