import { Component, OnInit } from '@angular/core';
import { AuthService, User } from '../../services/auth.service';
import { CartService } from '../../services/cart.service';

@Component({
  selector: 'app-user-layout',
  templateUrl: './user-layout.component.html',
  styleUrls: ['./user-layout.component.scss']
})
export class UserLayoutComponent implements OnInit {
  currentUser: User | null = null;
  cartItemCount = 0;

  constructor(
    private authService: AuthService,
    private cartService: CartService
  ) {}

  ngOnInit(): void {
    this.authService.currentUser$.subscribe(user => {
      this.currentUser = user;
    });

    this.cartService.cart$.subscribe(cart => {
      this.cartItemCount = cart.item_count;
    });

    // Load cart data
    this.cartService.loadCart();
  }

  logout(): void {
    this.authService.logout();
  }
}

